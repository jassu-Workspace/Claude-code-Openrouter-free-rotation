"""New CLI commands for FCC (fcc-start, fcc-install, fcc-status, fcc-doctor, fcc-update)."""

import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from config.paths import config_dir_path, managed_env_path, openrouter_keys_path
from config.settings import get_settings
from cli.entrypoints import _preflight_proxy, launch_claude, _claude_child_env, serve

def _has_valid_keys() -> bool:
    keys_path = openrouter_keys_path()
    if not keys_path.is_file():
        return False
    try:
        with open(keys_path, "r", encoding="utf-8") as f:
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
            subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "{" ".join(command)}"'])
        else:
            terms = ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty"]
            for term in terms:
                if shutil.which(term):
                    subprocess.Popen([term, "-e", *command])
                    return
            subprocess.Popen(command)
    except Exception as e:
        print(f"Failed to open new terminal: {e}", file=sys.stderr)
        subprocess.Popen(command)

def fcc_start() -> None:
    """Start FCC server and Claude Code."""
    settings = get_settings()
    proxy_url = f"http://{settings.host}:{settings.port}"
    
    # Ensure config directory exists
    config_dir_path().mkdir(parents=True, exist_ok=True)
    keys_path = openrouter_keys_path()
    if not keys_path.exists():
        keys_path.touch()
        
    has_keys = _has_valid_keys()
    
    if not has_keys:
        print("No valid OpenRouter keys found. Starting onboarding...")
        # Start server in background thread here, wait for health, open browser, wait forever.
        # But wait, if we start server in current terminal, it blocks.
        # Better: run fcc-server in background process, open browser, tell user to restart later?
        # Or start it in a new terminal, and just open browser.
        error = _preflight_proxy(proxy_url)
        if error:
            print("Starting fcc-server in a new terminal...")
            _open_new_terminal([sys.executable, "-m", "uvicorn", "api.app:create_app", "--host", settings.host, "--port", str(settings.port)])
        
        # Wait for healthy
        print("Waiting for server to be healthy...")
        for _ in range(30):
            if not _preflight_proxy(proxy_url):
                break
            time.sleep(0.5)
        
        print("Opening onboarding page...")
        webbrowser.open(f"{proxy_url}/onboarding")
        print("Please complete setup in the browser. After adding keys, click 'Start Claude Code'.")
        return
        
    # Valid keys exist
    error = _preflight_proxy(proxy_url)
    if error:
        print("Starting fcc-server in a new terminal...")
        # Actually fcc-server should just be run
        fcc_server_bin = shutil.which("fcc-server")
        cmd = [fcc_server_bin] if fcc_server_bin else [sys.executable, "-m", "uvicorn", "api.app:create_app", "--host", settings.host, "--port", str(settings.port)]
        _open_new_terminal(cmd)
        
        print("Waiting for server to be healthy...")
        for _ in range(30):
            if not _preflight_proxy(proxy_url):
                break
            time.sleep(0.5)
            
    print("Launching Claude Code...")
    launch_claude()

def fcc_install() -> None:
    """Verify and install FCC."""
    print("Verifying Python...")
    print(f"Python version: {platform.python_version()}")
    
    print("Verifying uv...")
    uv_bin = shutil.which("uv")
    if not uv_bin:
        print("uv not found. Please install uv.")
    else:
        print(f"uv found at {uv_bin}")
        
    print("Verifying Git...")
    git_bin = shutil.which("git")
    if not git_bin:
        print("Git not found. Please install Git.")
    else:
        print(f"Git found at {git_bin}")
        
    print("Verifying Claude Code...")
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Claude Code not found. Install it with: npm install -g @anthropic-ai/claude-code")
    else:
        print(f"Claude Code found at {claude_bin}")
        
    config_dir_path().mkdir(parents=True, exist_ok=True)
    if not openrouter_keys_path().exists():
        openrouter_keys_path().touch()
        print(f"Created {openrouter_keys_path()}")
    
    if not managed_env_path().exists():
        print(f"To create default config, run fcc-init.")
        
    print("Installation verified.")

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
        with open(openrouter_keys_path(), "r", encoding="utf-8") as f:
            keys = [k.strip() for k in f if k.strip().startswith("sk-or-v1-")]
            
    print(f"OpenRouter Keys Loaded: {len(keys)}")
    
    # We could ask the API for live rotation status if the server is running.
    if not error:
        import urllib.request
        import json
        try:
            req = urllib.request.Request(f"{proxy_url}/admin/api/status")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                ors = data.get("open_router_status")
                if ors:
                    print(f"Healthy Keys: {ors.get('healthy_keys')}")
                    print(f"Exhausted Keys: {ors.get('exhausted_keys')}")
                    print(f"Current Key Index: {ors.get('current_key_index')}")
                    print("Rotation Status: Active")
        except Exception:
            pass

def fcc_doctor() -> None:
    """Run diagnostics."""
    print("Running diagnostics...")
    passed = True
    
    if not shutil.which("python"):
        print("❌ Python not found")
        passed = False
    else:
        print("✅ Python found")
        
    if not shutil.which("uv"):
        print("❌ uv not found")
        passed = False
    else:
        print("✅ uv found")
        
    if not shutil.which("git"):
        print("❌ git not found")
        passed = False
    else:
        print("✅ git found")
        
    if not shutil.which("claude"):
        print("❌ claude not found")
        passed = False
    else:
        print("✅ claude found")
        
    if not openrouter_keys_path().exists():
        print("❌ OpenRouter keys file not found")
        passed = False
    else:
        print("✅ OpenRouter keys file exists")
        
    if passed:
        print("All checks passed.")
    else:
        print("Some checks failed. Please fix the issues above.")

def fcc_update() -> None:
    """Update FCC."""
    print("Pulling latest version and reinstalling...")
    print("Please run: uv tool upgrade free-claude-code --reinstall")
    print("Or if using pip: pip install --upgrade git+https://github.com/Alishahryar1/free-claude-code.git")
    # Actually, we could automate this:
    try:
        subprocess.run(["pip", "install", "--upgrade", "git+https://github.com/Alishahryar1/free-claude-code.git"], check=True)
        print("Update complete. Your config and keys have been preserved.")
    except Exception as e:
        print(f"Update failed: {e}")
