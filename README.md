# Claude Code OpenRouter Free Rotation

[![Python](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-black?style=for-the-badge&logo=ai)](https://openrouter.ai/)
[![Claude Code](https://img.shields.io/badge/Claude--Code-Integration-7B61FF?style=for-the-badge&logo=anthropic)](https://claude.ai/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/jassu-Workspace/Claude-code-Openrouter-free-rotation?style=for-the-badge)](https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation/stargazers)
[![Forks](https://img.shields.io/github/forks/jassu-Workspace/Claude-code-Openrouter-free-rotation?style=for-the-badge)](https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation/network/members)

**One-command OpenRouter gateway for Claude Code with automatic API key rotation, web management dashboard, diagnostics, and multi-key failover.**

---

## 🚀 Feature Highlights

| Feature | Description |
| :--- | :--- |
| **✓ OpenRouter Multi-Key Rotation** | Seamlessly rotate between dozens of OpenRouter API keys to bypass rate limits. |
| **✓ Automatic Retry Logic** | Intelligent retry mechanism with exponential backoff for transient failures. |
| **✓ Intelligent Key Exhaustion Detection** | Automatically identifies and skips keys with insufficient balance or invalid status. |
| **✓ One Command Startup** | Start the entire rotation gateway and dashboard with a single `fcc-start`. |
| **✓ One Command Installation** | Effortless setup using `uv tool` or `pip` directly from GitHub. |
| **✓ Web-Based Key Management** | Modern, intuitive dashboard to manage keys and monitor provider health. |
| **✓ Dashboard Monitoring** | Real-time status tracking for OpenRouter, Ollama, LM Studio, and Llama.cpp. |
| **✓ Live Rotation Statistics** | Instant visibility into key pool health and exhaustion events. |
| **✓ Claude Code Integration** | Drop-in replacement for the Anthropic API within the Claude Code CLI. |
| **✓ OpenRouter Failover** | Instant automatic failover to the next healthy key on rate limits or errors. |
| **✓ Environment Diagnostics** | Comprehensive `fcc-doctor` tool to verify environment readiness. |
| **✓ Auto Configuration** | Automated setup of local endpoints and provider routing. |
| **✓ No Manual .env Editing** | Manage all environment variables and secrets through the web UI. |
| **✓ Token Usage Tracking** | SQLite-backed per-session and per-model token tracking with daily aggregates. |
| **✓ Cross Platform Support** | Fully optimized for Windows, macOS (Intel/M-series), and Linux. |

---

## 🏗️ Architecture

```text
       User Interaction (Terminal)
                  │
                  ▼
          Claude Code (CLI)
                  │
                  ▼
     FCC Gateway (FastAPI Proxy Server)
                  │
                  ├───────────────────────────────┐
                  │                               │
       ┌──────────┴──────────┐          ┌─────────┴─────────┐
       │ Key Rotation Engine │          │ Provider Registry │
       └──────────┬──────────┘          └─────────┬─────────┘
                  │                               │
                  ▼                               ▼
          OpenRouter API                  Local LLM Providers
        (Multi-Key Pool)               (Ollama, LM Studio, etc.)
                  │
                  ▼
              AI Models
       (Claude 3.5 Sonnet, etc.)
```

---

## 🔄 OpenRouter Rotation Engine

Maximize your uptime and model access with our sophisticated rotation logic.

### How it Works
- **Key Loading:** Keys are loaded from `api_keys.txt` or through the dashboard.
- **3-State Health System:** Each key transitions through `healthy → cooldown → exhausted`.
  - **429 Rate Limit:** Key enters cooldown (60s), auto-recovers after expiry.
  - **402 Insufficient Balance:** Key enters cooldown, retries after expiry.
  - **401 Unauthorized:** Key is rotated out immediately.
  - **Malformed/Empty Response:** Treated as validation failure — key rotated, next key tried.
- **Automatic Failover:** On any failure, engine picks next healthy key and retries transparently.
- **Response Validation:** Every HTTP 200 response is checked — JSON bodies and non-SSE content are rejected as invalid (prevents Claude Code "malformed response" errors).
- **All Keys Exhausted:** Raises clear error instead of silent hang.

---

## 🖥️ Management Dashboard

The FCC Dashboard provides a central hub for controlling your local and remote AI infrastructure.

- **Dashboard Overview:** Real-time summary of the gateway status and active model.
- **OpenRouter Manager:** Securely add, test, and manage your OpenRouter key pool.
- **Provider Monitoring:** One-click health checks for Ollama, LM Studio, and Llama.cpp.
- **Claude Launcher:** Integrated launcher to start Claude Code with correct environment overrides.
- **Diagnostics & Logs:** Live log tailing and system health reports via `fcc-doctor`.
- **Analytics:** Basic tracking of key usage and rotation frequency.

---

## 🛠️ CLI Commands

| Command | Description |
| :--- | :--- |
| `fcc-install` | Verify installation, check prerequisites, and initialize environment. |
| `fcc-start` | Start the gateway server and open the web dashboard. |
| `fcc-status` | Show current server status and active configuration. |
| `fcc-doctor` | Run deep diagnostics on connectivity, keys, and local providers. |
| `fcc-update` | Pull the latest changes from GitHub and update dependencies. |
| `fcc-server` | Manually start the FastAPI gateway server. |
| `fcc-claude` | Launch Claude Code pre-configured to use the FCC gateway. |

---

## 📦 Installation

### Method 1: UV Tool (Recommended)
Fastest installation with isolated environment management.
```bash
uv tool install git+https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation.git
```

### Method 2: PIP
Standard installation into your Python environment.
```bash
pip install git+https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation.git
```

### Method 3: Local Development
For contributing or customizing the source.
```bash
git clone https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation.git
cd Claude-code-Openrouter-free-rotation
uv venv
uv sync
```

---

## ⚡ Quick Start

1. **Install** using Method 1 or 2 above.
2. **Verify Installation:**
   ```bash
   fcc-install
   ```
3. **Start the Engine:**
   ```bash
   fcc-start
   ```
4. **Configure Keys:** Open the dashboard (usually `http://localhost:8082/admin`) and paste your OpenRouter keys.
5. **Launch Claude:**
   ```bash
   fcc-claude
   ```
6. **Chat Away!** Claude Code is now powered by your rotated OpenRouter key pool.

---

## 🖼️ Screenshots

> **Main Dashboard**
![Dashboard Overview](docs/images/dashboard.png)

> **Key Rotation Manager**
![OpenRouter Manager](docs/images/openrouter-manager.png)

> **Real-time Analytics**
![Analytics](docs/images/analytics.png)

> **System Diagnostics**
![Diagnostics](docs/images/diagnostics.png)

---

## ❓ FAQ

**Q: How many keys can I add?**  
A: There is no limit. You can add hundreds of keys to ensure near-infinite rate limits for high-volume coding sessions.

**Q: Does rotation happen automatically?**  
A: Yes. The gateway intercepts failures and rotates keys without you ever noticing in the terminal.

**Q: Can I use free OpenRouter keys?**  
A: Yes! This project was specifically designed to make multiple free/limited keys behave like a single high-tier account.

**Q: Does it support local models?**  
A: Yes, via Ollama, LM Studio, and Llama.cpp integration. You can switch providers instantly in the dashboard.

**Q: How are exhausted keys handled?**  
A: They are marked as exhausted and skipped. You can reset them in the dashboard once you've topped up or when their daily limits reset.

---

## 🗺️ Roadmap

### Current (v1.4.0)
- [x] OpenRouter Multi-Key Rotation with 3-state health system (healthy → cooldown → exhausted)
- [x] Automatic key recovery after cooldown expiry (60s default)
- [x] SSE response validation — detects and rejects malformed/empty HTTP 200 responses
- [x] Graceful lifespan startup/shutdown with failure reporting (no more server hangs)
- [x] SQLite-based token usage tracking per session and model
- [x] Web Dashboard for Config & Monitoring
- [x] Comprehensive CLI Diagnostics (`fcc-doctor`)
- [x] Failover for 401/402/429/empty-response errors
- [x] Cross-platform install scripts with SQLite verification

### Upcoming (v1.5.0+)
- [ ] **Multi-Provider Routing:** Native support for Groq, Gemini, and DeepSeek.
- [ ] **Ollama/LM Studio Load Balancing:** Distribute local inference across multiple machines.
- [ ] **Team Support:** Role-based access for shared key pools.

---

## 🛠️ Troubleshooting

If you encounter issues, follow these steps:

1. **Run `fcc-doctor`:** This is your first line of defense. It checks for common configuration errors, key validity, and connectivity issues.
2. **Check the Logs:** View real-time logs in the dashboard or check `logs/openrouter_rotation.log` for rotation-specific events.
3. **Common Issues:**
   - **Port Conflict:** If `8082` is in use, you can change the `PORT` in the dashboard or `.env` file.
   - **Model Mismatch:** Ensure the model you are requesting in Claude Code is supported by your active provider.
   - **Key Exhaustion:** If all keys are exhausted, rotation will stop. Add more keys or check your OpenRouter balance.

Still having trouble? Open an issue on [GitHub](https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation/issues).

---

## 🤝 Contribution

Contributions are welcome! Whether it's a bug fix, new provider support, or dashboard improvement.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🌟 Acknowledgements

- **Original Project:** [free-claude-code](https://github.com/Alishahryar1/free-claude-code) by Alishahryar1.
- **Providers:** Special thanks to OpenRouter, NVIDIA NIM, and the local LLM community (Ollama/LM Studio).

**Project Repository:** [https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation](https://github.com/jassu-Workspace/Claude-code-Openrouter-free-rotation)
