<div align="center">
  <img src="https://img.shields.io/badge/Claude--Code-Integration-7B61FF?style=for-the-badge&logo=anthropic" alt="Claude Code" />
  <img src="https://img.shields.io/badge/OpenRouter-API-black?style=for-the-badge&logo=ai" alt="OpenRouter API" />
  <img src="https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  
  <h1>🚀 Free Claude Code (FCC)</h1>
  <p><b>The Ultimate Local Gateway & OpenRouter Key Manager</b></p>
  
  <p>Superpower your <b>Claude Code CLI</b>, <b>Claude Desktop</b>, and <b>VS Code</b> with automatic multi-key rotation, zero-latency failover, and a premium web dashboard.</p>

  <p>
    <a href="https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation/stargazers"><img src="https://img.shields.io/github/stars/jassu-Workspace/Claude-code-Openrouter-free-rotation?style=flat-square&color=yellow" alt="Stars" /></a>
    <a href="https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation/network/members"><img src="https://img.shields.io/github/forks/jassu-Workspace/Claude-code-Openrouter-free-rotation?style=flat-square&color=blue" alt="Forks" /></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License" /></a>
  </p>
</div>

<br/>

> **Tired of hitting rate limits?** Ever been deep in the zone, only to be interrupted by a `429 Too Many Requests` or an empty API balance? **Free Claude Code (FCC)** is a smart, local proxy server that manages a pool of OpenRouter API keys. The millisecond one key fails, FCC silently rotates to the next one—meaning your coding sessions are never interrupted again.

---

## ✨ Stellar Features

*   🔄 **Automatic Key Rotation:** Add an unlimited number of OpenRouter keys. The engine load-balances and instantly fails over when limits are hit!
*   🎛️ **Gorgeous Local Dashboard:** A premium, glassmorphic Web UI (running at `localhost:8082/admin`) to effortlessly manage your keys, test provider latency, and tweak settings.
*   🔌 **Zero-Config IDE Launchers:** Native terminal commands that instantly boot your server and launch your favorite tools with the proxy environment variables automatically injected.
*   🧠 **Universal Provider Support:** Not just OpenRouter! Connect local models via LM Studio, Ollama, llama.cpp, DeepSeek, and more.
*   ⚡ **Lightning Fast Architecture:** Built on modern Python (3.14) using FastAPI and Uvicorn for true async performance.

---

## 🚀 Step 1: Installation & Setup

We recommend using `uv`, the insanely fast Python package manager, for the cleanest installation.

**1. Install UV (if you don't have it):**
```bash
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Clone and Sync the Repository:**
```bash
git clone https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation.git
cd Claude-code-Openrouter-free-rotation
uv sync
```

---

## ⚙️ Step 2: Configure Your Keys via the Dashboard

Forget messing with `.env` files. FCC comes with a breathtaking local web dashboard!

1. **Start the engine:**
   ```bash
   uv run fcc-server
   ```
2. **Open your browser** and go to: **[http://127.0.0.1:8082/admin](http://127.0.0.1:8082/admin)**
3. In the sidebar, click on **Providers**.
4. Scroll down to the **OpenRouter API Key(s)** input box.
5. **Paste your keys!** You can paste as many as you want, exactly **one key per line**. 
6. Click the **Save** button. The engine is now armed and ready.

---

## 🎯 Step 3: Connect Your Favorite Apps

FCC acts as a drop-in replacement for the Anthropic API. Here are the exact, step-by-step instructions to connect it to your favorite tools:

### 📱 A. Integrating with Claude Desktop (The Official App)

You can connect the official Anthropic Claude Desktop app to your local FCC proxy. 

**Method 1: The Automated Launcher (Recommended)**
Simply open your terminal inside the project folder and run:
```bash
uv run fcc-desktop
```
*This command verifies your server is running, locates your Windows App installation of Claude, and injects the proxy settings perfectly.*

**Method 2: Manual Configuration in Claude Desktop**
If you prefer to configure it manually inside the app:
1. Open the Claude Desktop application.
2. At the top left, click **File** -> **Settings** (or press `Ctrl + ,`).
3. On the left sidebar of the settings menu, look for the **Developer** tab. 
   *(Note: If you don't see the Developer tab, you may need to click on "Appearance" or "Account" and type the Konami code or check Anthropic's docs for enabling developer mode, but usually, it is visible in the latest builds).*
4. In the Developer section, enable **Custom Gateway**.
5. Set the **Gateway Base URL** to exactly: `http://127.0.0.1:8082`
6. Set the **Gateway API key** to: `freecc` *(This is FCC's internal auth token).*
7. **Crucial Step:** Toggle **OFF** "Model Discovery".
8. Manually type the model you want to use (e.g., `anthropic/claude-3.5-sonnet:beta`).

### 💻 B. Integrating with VS Code (Cline / Roo / Claude Code)

Visual Studio Code extensions that use Anthropic's API can easily be rerouted through FCC.

**Method 1: The Automated Launcher (Recommended)**
```bash
uv run fcc-ide
```
*This command starts FCC and launches VS Code with `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY` injected straight into the process.*

**Method 2: Manual Configuration for "Cline" or "Roo Code" extensions**
1. Open your VS Code and open the **Cline** or **Roo** extension sidebar.
2. Click the **Settings** (Gear icon) for the extension.
3. Under **API Provider**, select **Anthropic** (or OpenAI Compatible).
4. Look for the **Custom Base URL** input box.
5. Enter: `http://127.0.0.1:8082`
6. In the **API Key** input box, enter: `freecc`
7. Click Save. You are now proxying through OpenRouter!

**Method 3: Bypassing the official Anthropic Claude Code Extension Login**
If you use Anthropic's official VS Code extension, it has a hardcoded login screen. To bypass it:
1. Open VS Code.
2. Press `Ctrl + Shift + P` and type `Open User Settings (JSON)`.
3. Add the following lines to your `settings.json`:
   ```json
   "claudeCode.disableLoginPrompt": true,
   "claudeCode.env": [
       { "name": "ANTHROPIC_BASE_URL", "value": "http://127.0.0.1:8082" },
       { "name": "ANTHROPIC_API_KEY", "value": "freecc" }
   ]
   ```
4. Restart VS Code!

### 🧑‍💻 C. Integrating with the Claude Code CLI Terminal

Want to use Anthropic's official terminal tool? It's easier than ever.
Just run:
```bash
uv run fcc-claude
```
*This automatically boots the proxy in the background and drops you into the official Claude Code CLI terminal experience, fully proxied and ready to code!*

---

## 🛠️ The Ultimate Command Reference

We've bundled incredibly smart terminal commands to make your workflow absolutely frictionless. Run these using `uv run <command>`:

| Command | What it does |
| :--- | :--- |
| `fcc-server` | Starts the standalone background proxy server and the local Admin Web UI on port `8082`. |
| `fcc-desktop` | Checks your server, starts it silently if needed, and launches the **Claude Desktop App** perfectly synced with your proxy. |
| `fcc-ide` | Auto-detects **VS Code** (or Cursor/Windsurf). Starts your proxy, injects the credentials, and opens your IDE. |
| `fcc-claude` | Starts the server and launches the **Claude Code CLI** terminal client. |
| `fcc-doctor` | Runs deep diagnostics to ensure your networking, proxy, and extensions are working flawlessly. |
| `fcc-status` | Prints live health metrics, uptime, and active keys to the terminal. |

<br/>

<details>
<summary><b>🤔 How does the architecture actually work? (Click to expand)</b></summary>
<br/>

When your application (like VS Code or Claude Desktop) sends an AI prompt, it hits our local FastAPI Proxy (`127.0.0.1:8082`) instead of Anthropic's servers.

1. Our Proxy checks the `KeyManager` and grabs the next available OpenRouter key from the pool you pasted into the dashboard.
2. It forwards your exact prompt to OpenRouter.
3. If OpenRouter returns a `429 Rate Limit` or `402 Insufficient Balance`, our Proxy traps that error instantly.
4. It throws away the dead key, grabs a fresh one, and tries again under the hood—meaning your Claude app never disconnects or fails!

</details>

---

## 🤝 Open Source & Contributions

This project is built for the community!
- We have integrated GitHub Actions for seamless Continuous Integration (`tests.yml`) ensuring code quality.
- Continuous Deployment (`release.yml`) automatically builds and publishes releases.

Fork it, star it, and make it viral! Contributions are always welcome. Just open a Pull Request!

<div align="center">
  <p>Built with ❤️ by the open-source AI community.</p>
</div>
