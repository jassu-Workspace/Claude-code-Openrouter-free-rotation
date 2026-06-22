"""New CLI commands for FCC (fcc-start, fcc-install, fcc-status, fcc-doctor, fcc-update)."""

import platform
import shutil
import subprocess
import sys
import time
import webbrowser

from cli.entrypoints import _preflight_proxy, launch_claude
from config.paths import config_dir_path, managed_env_path, openrouter_keys_path
from config.settings import get_settings


def _has_valid_keys() -> bool:
    keys_path = openrouter_keys_path()
    if not keys_path.is_file():
        return False
    try:
        with open(keys_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("sk-or-v1-"):
                    return True
    except Exception:
        pass
    return False


def _open_new_terminal(command: list[str]) -> None:
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["start", "cmd", "/k", " ".join(command)], shell=True)
        elif system == "Darwin":
            subprocess.Popen(
                [
                    "osascript",
                    "-e",
                    f'tell app "Terminal" to do script "{" ".join(command)}"',
                ]
            )
        else:
            terms = [
                "x-terminal-emulator",
                "gnome-terminal",
                "konsole",
                "xfce4-terminal",
                "alacritty",
                "kitty",
            ]
            for term in terms:
                if shutil.which(term):
                    subprocess.Popen([term, "-e", *command])
                    return
            subprocess.Popen(command)
    except Exception as e:
        print(f"Failed to open new terminal: {e}", file=sys.stderr)
        subprocess.Popen(command)


def _wait_for_server(proxy_url: str, timeout: int = 30) -> str | None:
    """Wait for server to become healthy. Returns None on success, error string on failure."""
    print(f"Waiting for server at {proxy_url} (timeout: {timeout}s)...")
    deadline = time.monotonic() + timeout
    last_error = "timeout"
    while time.monotonic() < deadline:
        error = _preflight_proxy(proxy_url)
        if error is None:
            print("Server is healthy.")
            return None
        last_error = error
        time.sleep(1)
    return last_error


def fcc_start() -> None:
    """Start FCC server and Claude Code."""
    settings = get_settings()
    proxy_url = f"http://{settings.host}:{settings.port}"

    config_dir_path().mkdir(parents=True, exist_ok=True)
    keys_path = openrouter_keys_path()
    if not keys_path.exists():
        keys_path.touch()

    has_keys = _has_valid_keys()

    if not has_keys:
        print("No valid OpenRouter keys found. Starting onboarding...")
        error = _preflight_proxy(proxy_url)
        if error:
            print("Starting fcc-server in a new terminal...")
            fcc_server_bin = shutil.which("fcc-server")
            cmd = (
                [fcc_server_bin]
                if fcc_server_bin
                else [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "server:app",
                    "--host",
                    settings.host,
                    "--port",
                    str(settings.port),
                ]
            )
            _open_new_terminal(cmd)

        error = _wait_for_server(proxy_url, timeout=30)
        if error:
            print(f"ERROR: Server failed to start: {error}")
            print("Check logs for details. Run 'fcc-doctor' for diagnostics.")
            return

        print("Opening onboarding page...")
        webbrowser.open(f"{proxy_url}/onboarding")
        print(
            "Please complete setup in the browser. After adding keys, click 'Start Claude Code'."
        )
        return

    # Valid keys exist
    error = _preflight_proxy(proxy_url)
    if error:
        print("Starting fcc-server in a new terminal...")
        fcc_server_bin = shutil.which("fcc-server")
        cmd = (
            [fcc_server_bin]
            if fcc_server_bin
            else [
                sys.executable,
                "-m",
                "uvicorn",
                "server:app",
                "--host",
                settings.host,
                "--port",
                str(settings.port),
            ]
        )
        _open_new_terminal(cmd)

        error = _wait_for_server(proxy_url, timeout=30)
        if error:
            print(f"ERROR: Server failed to start: {error}")
            print("Check logs for details. Run 'fcc-doctor' for diagnostics.")
            return

    print("Launching Claude Code...")
    launch_claude()


def fcc_install() -> None:
    """Verify and install FCC and all required dependencies."""
    errors = []

    print("=== FCC Installation ===\n")

    # Python
    print("Verifying Python...")
    py_version = platform.python_version()
    print(f"  Python version: {py_version}")
    major, minor, _ = py_version.split(".")
    if int(major) < 3 or (int(major) == 3 and int(minor) < 14):
        print("  WARNING: Python 3.14+ recommended")
    print()

    # uv
    print("Verifying uv...")
    uv_bin = shutil.which("uv")
    if not uv_bin:
        print("  uv not found. Install with:")
        print("    curl -LsSf https://astral.sh/uv/install.sh | sh")
        errors.append("uv not found")
    else:
        print(f"  uv found at {uv_bin}")
        # Update uv
        try:
            subprocess.run(["uv", "self", "update"], capture_output=True, timeout=30)
            print("  uv updated to latest version")
        except Exception:
            pass
    print()

    # Git
    print("Verifying Git...")
    git_bin = shutil.which("git")
    if not git_bin:
        print("  Git not found. Please install Git.")
        errors.append("git not found")
    else:
        print(f"  Git found at {git_bin}")
    print()

    # Claude Code
    print("Verifying Claude Code...")
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("  Claude Code not found.")
        print("  Install with: npm install -g @anthropic-ai/claude-code")
        errors.append("claude not found")
    else:
        print(f"  Claude Code found at {claude_bin}")
    print()

    # npm (needed for Claude Code)
    print("Verifying npm...")
    npm_bin = shutil.which("npm")
    if not npm_bin:
        print("  npm not found. Required for Claude Code.")
        errors.append("npm not found")
    else:
        print(f"  npm found at {npm_bin}")
    print()

    # SQLite
    print("Verifying SQLite...")
    try:
        import sqlite3

        print(f"  SQLite available (version: {sqlite3.sqlite_version})")
    except ImportError:
        print("  ERROR: sqlite3 module not available in Python!")
        errors.append("sqlite3 not available")
    print()

    # Install Python 3.14
    if uv_bin:
        print("Installing Python 3.14.0...")
        try:
            subprocess.run(
                ["uv", "python", "install", "3.14.0"],
                check=True,
                timeout=120,
            )
            print("  Python 3.14.0 installed")
        except Exception as e:
            print(f"  WARNING: Could not install Python 3.14.0: {e}")
    print()

    # Sync dependencies
    if uv_bin:
        print("Syncing project dependencies...")
        try:
            subprocess.run(
                ["uv", "sync"],
                check=True,
                timeout=120,
            )
            print("  Dependencies synced")
        except Exception as e:
            print(f"  WARNING: Could not sync dependencies: {e}")
            print("  Run 'uv sync' manually in the project directory.")
    print()

    # Config directory
    config_dir_path().mkdir(parents=True, exist_ok=True)
    if not openrouter_keys_path().exists():
        openrouter_keys_path().touch()
        print(f"Created {openrouter_keys_path()}")

    if not managed_env_path().exists():
        print("To create default config, run fcc-init.")

    print()
    if errors:
        print(
            f"Installation completed with {len(errors)} error(s): {', '.join(errors)}"
        )
        print("Fix the issues above, then rerun fcc-install.")
    else:
        print("All dependencies installed successfully.")
        print("Start the proxy with: fcc-server")
        print("Or launch with Claude Code: fcc-start")


def fcc_status() -> None:
    """Check FCC status."""
    import importlib.metadata

    try:
        version = importlib.metadata.version("free-claude-code")
    except Exception:
        version = "Unknown"

    print(f"FCC Version: {version}")

    settings = get_settings()
    proxy_url = f"http://{settings.host}:{settings.port}"
    error = _preflight_proxy(proxy_url)

    if error:
        print(f"Server Status: Stopped ({error})")
    else:
        print("Server Status: Running")

    keys = []
    if openrouter_keys_path().is_file():
        with open(openrouter_keys_path(), encoding="utf-8") as f:
            keys = [k.strip() for k in f if k.strip().startswith("sk-or-v1-")]

    print(f"OpenRouter Keys Loaded: {len(keys)}")

    if not error:
        import json
        import urllib.request

        try:
            req = urllib.request.Request(f"{proxy_url}/admin/api/status")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                ors = data.get("open_router_status")
                if ors:
                    print(f"Healthy Keys: {ors.get('healthy_keys')}")
                    print(f"Exhausted Keys: {ors.get('exhausted_keys')}")
                    print(f"Cooldown Keys: {ors.get('cooldown_keys', 0)}")
                    print(f"Current Key Index: {ors.get('current_key_index')}")
                    print("Rotation Status: Active")
        except Exception:
            pass


def fcc_doctor() -> None:
    """Run diagnostics."""
    print("Running diagnostics...")
    passed = True

    if not shutil.which("python"):
        print("  FAIL: Python not found")
        passed = False
    else:
        print("  OK: Python found")

    if not shutil.which("uv"):
        print("  FAIL: uv not found")
        passed = False
    else:
        print("  OK: uv found")

    if not shutil.which("git"):
        print("  FAIL: git not found")
        passed = False
    else:
        print("  OK: git found")

    if not shutil.which("claude"):
        print("  FAIL: claude not found")
        passed = False
    else:
        print("  OK: claude found")

    if not shutil.which("npm"):
        print("  FAIL: npm not found")
        passed = False
    else:
        print("  OK: npm found")

    try:
        import sqlite3

        print(f"  OK: SQLite available (version: {sqlite3.sqlite_version})")
    except ImportError:
        print("  FAIL: sqlite3 module not available")
        passed = False

    if not openrouter_keys_path().exists():
        print("  FAIL: OpenRouter keys file not found")
        passed = False
    else:
        key_count = 0
        with open(openrouter_keys_path(), encoding="utf-8") as f:
            key_count = sum(1 for line in f if line.strip().startswith("sk-or-v1-"))
        if key_count == 0:
            print("  WARN: OpenRouter keys file exists but has no valid keys")
        else:
            print(f"  OK: OpenRouter keys file exists ({key_count} keys)")

    # Check server
    settings = get_settings()
    proxy_url = f"http://{settings.host}:{settings.port}"
    error = _preflight_proxy(proxy_url)
    if error:
        print(f"  INFO: Server not running ({error})")
    else:
        print("  OK: Server is running")

    print()
    if passed:
        print("All critical checks passed.")
    else:
        print("Some checks failed. Please fix the issues above.")


def fcc_update() -> None:
    """Update FCC."""
    print("Updating Free Claude Code...")
    try:
        subprocess.run(
            ["uv", "tool", "upgrade", "free-claude-code", "--reinstall"],
            check=True,
        )
        print("Update complete. Your config and keys have been preserved.")
    except FileNotFoundError:
        print("uv not found. Run fcc-install first.")
    except subprocess.CalledProcessError as e:
        print(f"Update failed: {e}")
        print("Try: uv tool upgrade free-claude-code --reinstall")
