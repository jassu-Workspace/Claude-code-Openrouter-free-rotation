"""CLI entry points for the installed package."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import uvicorn

from api.admin_urls import local_admin_url, local_proxy_root_url
from api.app import GracefulLifespanApp, create_app
from cli.process_registry import (
    kill_all_best_effort,
    kill_pid_tree_best_effort,
    register_pid,
    unregister_pid,
)
from config.paths import config_dir_path, legacy_env_paths, managed_env_path
from config.settings import Settings, get_settings

PROXY_PREFLIGHT_PATH = "/health"
PROXY_PREFLIGHT_TIMEOUT_SECONDS = 1.5
SERVER_GRACEFUL_SHUTDOWN_SECONDS = 5


def _load_env_template() -> str:
    """Load the canonical root env template from package resources or source."""
    import importlib.resources

    packaged = importlib.resources.files("cli").joinpath("env.example")
    if packaged.is_file():
        return packaged.read_text("utf-8")

    source_template = Path(__file__).resolve().parents[1] / ".env.example"
    if source_template.is_file():
        return source_template.read_text(encoding="utf-8")

    raise FileNotFoundError("Could not find bundled or source .env.example template.")


def serve() -> None:
    """Start the FastAPI server (registered as `fcc-server` script)."""
    opened_admin_browser = False
    try:
        try:
            while True:
                _migrate_legacy_env_if_missing()
                settings = get_settings()
                if not _run_supervised_server(
                    settings, open_admin_browser=not opened_admin_browser
                ):
                    return
                opened_admin_browser = True
                get_settings.cache_clear()
        except KeyboardInterrupt:
            return
    finally:
        kill_all_best_effort()


def _admin_browser_open_enabled() -> bool:
    """Whether to open /admin when the server becomes reachable (FCC_OPEN_BROWSER)."""

    raw = os.environ.get("FCC_OPEN_BROWSER", "true").strip().lower()
    return raw not in {"", "0", "false", "no"}


def _schedule_open_admin_browser(settings: Settings) -> None:
    """After /health succeeds, open the admin UI in the default browser (daemon thread)."""

    if not _admin_browser_open_enabled():
        return

    admin_url = local_admin_url(settings)
    proxy_root_url = local_proxy_root_url(settings)

    def open_when_ready() -> None:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            if _preflight_proxy(proxy_root_url) is None:
                webbrowser.open(admin_url)
                return
            time.sleep(0.15)

    threading.Thread(
        target=open_when_ready, name="fcc-open-admin-browser", daemon=True
    ).start()


def _run_supervised_server(settings: Settings, *, open_admin_browser: bool) -> bool:
    """Run one uvicorn server instance; return whether admin requested restart."""

    restart_requested = False
    server_holder: dict[str, uvicorn.Server] = {}

    def request_restart() -> None:
        nonlocal restart_requested
        restart_requested = True
        if server := server_holder.get("server"):
            server.should_exit = True

    app = create_app(lifespan_enabled=False)
    app.state.admin_restart_callback = request_restart
    asgi_app = GracefulLifespanApp(app)
    config = uvicorn.Config(
        asgi_app,
        host=settings.host,
        port=settings.port,
        log_level="debug",
        timeout_graceful_shutdown=SERVER_GRACEFUL_SHUTDOWN_SECONDS,
    )
    server = uvicorn.Server(config)
    server_holder["server"] = server
    if open_admin_browser:
        _schedule_open_admin_browser(settings)
    server.run()
    return restart_requested


def init() -> None:
    """Scaffold config at ~/.fcc/.env (registered as `fcc-init`)."""
    config_dir = config_dir_path()
    env_file = managed_env_path()

    migrated_from = _migrate_legacy_env_if_missing()
    if migrated_from is not None:
        print(f"Config migrated from {migrated_from} to {env_file}")
        print(
            "Edit it to set your API keys and model preferences, then run: fcc-server"
        )
        return

    if env_file.exists():
        print(f"Config already exists at {env_file}")
        print("Delete it first if you want to reset to defaults.")
        return

    config_dir.mkdir(parents=True, exist_ok=True)
    template = _load_env_template()
    env_file.write_text(template, encoding="utf-8")
    print(f"Config created at {env_file}")
    print("Edit it to set your API keys and model preferences, then run: fcc-server")


def _migrate_legacy_env_if_missing() -> Path | None:
    """Copy a legacy user env into the managed config path when absent."""

    env_file = managed_env_path()
    if env_file.exists():
        return None

    # TODO: Remove after the ~/.fcc/.env migration has had a release cycle.
    for legacy_env in legacy_env_paths():
        if not legacy_env.is_file():
            continue
        env_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(legacy_env, env_file)
        return legacy_env

    return None


def _claude_child_env(
    settings: Settings, base_env: Mapping[str, str]
) -> dict[str, str]:
    """Return a Claude Code environment that targets this proxy."""

    env = {
        key: value
        for key, value in base_env.items()
        if not key.startswith("ANTHROPIC_")
    }
    env.pop("ANTHROPIC_API_KEY", None)
    env["ANTHROPIC_BASE_URL"] = local_proxy_root_url(settings)
    env["CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY"] = "1"
    env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = "190000"
    if token := settings.anthropic_auth_token.strip():
        if not token.startswith("sk-ant-"):
            token = f"sk-ant-{token}"
        env["ANTHROPIC_API_KEY"] = token
    return env


def _preflight_proxy(proxy_root_url: str) -> str | None:
    """Return an error message when the local proxy health check is unreachable."""

    url = f"{proxy_root_url.rstrip('/')}{PROXY_PREFLIGHT_PATH}"
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=PROXY_PREFLIGHT_TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
    except HTTPError as exc:
        return f"returned HTTP {exc.code}"
    except URLError as exc:
        return str(exc.reason)
    except OSError as exc:
        return str(exc)

    if not 200 <= status_code < 300:
        return f"returned HTTP {status_code}"
    return None


def launch_claude(argv: Sequence[str] | None = None) -> None:
    """Launch Claude Code with Free Claude Code proxy environment variables."""

    settings = get_settings()
    proxy_root_url = local_proxy_root_url(settings)
    if error := _preflight_proxy(proxy_root_url):
        print(
            f"Free Claude Code proxy is not reachable at {proxy_root_url}: {error}",
            file=sys.stderr,
        )
        print("Start it in another terminal with: fcc-server", file=sys.stderr)
        raise SystemExit(1)

    args = list(sys.argv[1:] if argv is None else argv)
    claude_command = shutil.which(settings.claude_cli_bin)
    if claude_command is None:
        print(
            f"Could not find Claude Code command: {settings.claude_cli_bin}",
            file=sys.stderr,
        )
        print(
            "Install Claude Code with: npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        raise SystemExit(127)

    command = [claude_command, *args]
    env = _claude_child_env(settings, os.environ)
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(command, env=env)
        if process.pid:
            register_pid(process.pid)
        return_code = process.wait()
    except FileNotFoundError:
        print(
            f"Could not find Claude Code command: {settings.claude_cli_bin}",
            file=sys.stderr,
        )
        print(
            "Install Claude Code with: npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        raise SystemExit(127) from None
    except KeyboardInterrupt:
        if process is not None and process.pid:
            kill_pid_tree_best_effort(process.pid)
            process.wait()
        raise
    finally:
        if process is not None and process.pid:
            unregister_pid(process.pid)

    raise SystemExit(return_code)

def desktop() -> None:
    """Check if server is running, start it if not, and automatically launch Claude Desktop."""
    settings = get_settings()
    proxy_root_url = local_proxy_root_url(settings)

    claude_desktop_paths = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Claude\Claude.exe")),
        Path(os.path.expandvars(r"%APPDATA%\Programs\Claude\Claude.exe")),
        Path(r"C:\Program Files\Claude\Claude.exe"),
    ]
    
    desktop_exe = None
    if sys.platform == "darwin":
        desktop_exe = "/Applications/Claude.app/Contents/MacOS/Claude" if Path("/Applications/Claude.app").exists() else None
    elif sys.platform == "win32":
        for p in claude_desktop_paths:
            if p.exists():
                desktop_exe = str(p)
                break
                
    is_windows_app = False
    if desktop_exe is None:
        if sys.platform == "win32":
            try:
                import subprocess
                result = subprocess.run(["powershell", "-Command", "Get-AppxPackage -Name '*Claude*'"], capture_output=True, text=True)
                if "Claude_pzs8sxrjxfjjc" in result.stdout:
                    is_windows_app = True
            except Exception:
                pass
                
        if not is_windows_app:
            print("Claude Desktop is not installed or could not be found.", file=sys.stderr)
            raise SystemExit(1)
        
    def launch_desktop() -> None:
        proxy_root_url = local_proxy_root_url(settings)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if _preflight_proxy(proxy_root_url) is None:
                print("Starting Claude Desktop...", file=sys.stderr)
                if is_windows_app:
                    subprocess.Popen(["powershell", "-Command", "Start-Process 'shell:AppsFolder\\Claude_pzs8sxrjxfjjc!Claude'"])
                else:
                    env = _claude_child_env(settings, os.environ)
                    subprocess.Popen([desktop_exe], env=env)
                return
            time.sleep(0.15)
        print("Server did not start in time. Cannot launch Claude Desktop.", file=sys.stderr)

    if _preflight_proxy(proxy_root_url) is None:
        print("Server is already running. Launching Claude Desktop...", file=sys.stderr)
        if is_windows_app:
            subprocess.Popen(["powershell", "-Command", "Start-Process 'shell:AppsFolder\\Claude_pzs8sxrjxfjjc!Claude'"])
        else:
            env = _claude_child_env(settings, os.environ)
            subprocess.Popen([desktop_exe], env=env)
    else:
        print("Server is not running. Starting server and launching Claude Desktop...", file=sys.stderr)
        threading.Thread(
            target=launch_desktop, name="fcc-open-claude-desktop", daemon=True
        ).start()
        serve()

def ide() -> None:
    """Detect IDEs, let user select one, check for Claude extension, start server and IDE."""
    settings = get_settings()
    proxy_root_url = local_proxy_root_url(settings)

    ides = []
    
    # Check VS Code
    vscode_path = shutil.which("code")
    if not vscode_path:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            p = Path(local_app_data) / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd"
            if p.exists(): vscode_path = str(p)
    if vscode_path:
        ides.append({"name": "VS Code", "cmd": vscode_path, "type": "vscode"})

    # Check Cursor
    cursor_path = shutil.which("cursor")
    if not cursor_path:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            p = Path(local_app_data) / "Programs" / "cursor" / "Scripts" / "cursor.cmd"
            if not p.exists():
                p = Path(local_app_data) / "Programs" / "cursor" / "Cursor.exe"
            if p.exists(): cursor_path = str(p)
    if cursor_path:
        ides.append({"name": "Cursor", "cmd": cursor_path, "type": "vscode"})

    # Check Windsurf
    windsurf_path = shutil.which("windsurf")
    if not windsurf_path:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            p = Path(local_app_data) / "Programs" / "Windsurf" / "bin" / "windsurf.cmd"
            if not p.exists():
                p = Path(local_app_data) / "Programs" / "Windsurf" / "Windsurf.exe"
            if p.exists(): windsurf_path = str(p)
    if windsurf_path:
        ides.append({"name": "Windsurf", "cmd": windsurf_path, "type": "vscode"})

    if not ides:
        print("No supported IDEs (VS Code, Cursor, Windsurf) detected on your system.", file=sys.stderr)
        raise SystemExit(1)

    print("Detected IDEs:")
    for i, d in enumerate(ides, 1):
        print(f"[{i}] {d['name']}")

    try:
        print()
        choice = int(input("Select an IDE by number: "))
        if choice < 1 or choice > len(ides):
            raise ValueError()
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\nInvalid choice.", file=sys.stderr)
        raise SystemExit(1)

    selected = ides[choice - 1]
    print(f"\nSelected {selected['name']}.")

    extension_args = []
    if selected["type"] == "vscode":
        print(f"Checking for Claude extensions in {selected['name']}...")
        try:
            # shell=True is needed on Windows for .cmd files sometimes, but we'll try direct first.
            cmd_list = [selected["cmd"], "--list-extensions"]
            # If it's an exe and not a cli wrapper, this might just open the app. We'll use a timeout.
            ext_output = subprocess.check_output(cmd_list, text=True, timeout=5)
            claude_exts = [line.strip() for line in ext_output.splitlines() if "claude" in line.lower() or "cline" in line.lower() or "roo" in line.lower()]
            if claude_exts:
                print(f"Found extension(s): {', '.join(claude_exts)}")
                # If we found one, we can ask the IDE to ensure it's loaded/opened
                extension_args.append("--extensionDevelopmentPath")
                extension_args.append(".")
            else:
                print("No Claude/Cline extensions found in this IDE.")
        except Exception:
            print("Could not silently check extensions (this is normal for some executables).")

    def launch_ide() -> None:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            if _preflight_proxy(proxy_root_url) is None:
                print(f"Starting {selected['name']}...", file=sys.stderr)
                env = _claude_child_env(settings, os.environ)
                subprocess.Popen([selected["cmd"], "."] + extension_args, env=env)
                return
            time.sleep(0.15)
        print("Server did not start in time. Cannot launch IDE.", file=sys.stderr)

    if _preflight_proxy(proxy_root_url) is None:
        print("Server is already running. Launching IDE...", file=sys.stderr)
        env = _claude_child_env(settings, os.environ)
        subprocess.Popen([selected["cmd"], "."] + extension_args, env=env)
    else:
        print("Server is not running. Starting server and launching IDE...", file=sys.stderr)
        threading.Thread(
            target=launch_ide, name="fcc-open-ide", daemon=True
        ).start()
        serve()

