# ♾️ Free Claude Code (FCC)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.14-green.svg)](https://python.org)

**Free Claude Code** is an advanced, high-performance local proxy engine that enables you to use the powerful official **Anthropic Claude Code CLI** (and various IDE extensions) for absolutely **free** by dynamically rotating OpenRouter keys and routing requests through custom endpoints. 

Designed for developers who want zero interruptions, seamless proxying, and a stunning local admin dashboard to manage everything in real-time.

---

## ✨ Key Features

*   🔄 **Automatic Key Rotation:** Paste in an unlimited number of OpenRouter API keys. FCC will automatically cycle through them, instantly failing over when a key hits its rate limit or runs out of credits!
*   🎛️ **Gorgeous Local Dashboard:** A premium, glassmorphism web UI available at `http://127.0.0.1:8082/admin` to manage your keys, test provider latency, and tweak runtime settings.
*   🔌 **Zero-Config IDE Injection:** Native commands to instantly launch **VS Code** and the **Claude Desktop App** with all proxy environment variables injected automatically.
*   🧠 **Multi-Provider Support:** Supports OpenRouter, local LM Studio, Ollama, llama.cpp, DeepSeek, and more!
*   ⚡ **Lightning Fast:** Built in modern Python using FastAPI and Uvicorn.

---

## 🚀 Installation & Setup

### Prerequisites
1.  Ensure you have **Python 3.14** installed.
2.  Install `uv` (the lightning-fast Python package manager) from Astral.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

### 1. Clone & Sync
```bash
git clone https://github.com/YOUR_USERNAME/free-claude-code.git
cd free-claude-code
uv sync
```

### 2. Configure Your Keys (The Easy Way)
Start the server and open the web dashboard:
```bash
uv run fcc-server
```
Navigate to **`http://127.0.0.1:8082/admin`** in your browser.
Under the **Providers** section, look for the OpenRouter API Key box. You can paste your keys directly into the UI, **one per line**. The engine handles the rest!

---

## 🛠️ Commands Reference

Free Claude Code comes with a suite of built-in commands to fit your exact workflow. Run these directly from your terminal:

### `uv run fcc-server`
Starts the standalone background proxy server and the local Admin Web UI on port `8082`. Leave this running in a background terminal.

### `uv run fcc-claude`
The primary wrapper for the Claude Code CLI. 
*   It automatically detects if your `fcc-server` is running. If it isn't, it seamlessly boots it up in the background.
*   It then instantly drops you into the official Claude Code CLI terminal experience, fully proxied and ready to code!

### `uv run fcc-ide`
For the visual coders! 
*   Detects if you have **VS Code** installed.
*   Starts the local server.
*   Launches VS Code and injects the required Anthropic Base URL and API keys so your local extensions (like *Cline* or the official *Claude Code* extension) instantly connect to the proxy without manual configuration!

### `uv run fcc-desktop`
Want to use the official Anthropic Claude GUI App?
*   Detects your official Windows Store installation of the Claude Desktop app.
*   Starts the server and automatically pops open the app, fully linked to your proxy!

---

## 💡 Troubleshooting VS Code Extensions

If you are using the official **Anthropic Claude Code** extension inside VS Code, it features a hardcoded login screen. To bypass it and connect to your local proxy:

1. Open your VS Code `settings.json`
2. Add these lines:
```json
"claudeCode.disableLoginPrompt": true,
"claudeCode.env": [
    { "name": "ANTHROPIC_BASE_URL", "value": "http://127.0.0.1:8082" },
    { "name": "ANTHROPIC_API_KEY", "value": "freecc" }
]
```
3. Restart VS Code!

*(Alternatively, use the **Cline** extension from the marketplace, which allows you to set the Custom Base URL to `http://127.0.0.1:8082` directly in its UI settings!)*

---
Made with ❤️ for the open-source coding community!
