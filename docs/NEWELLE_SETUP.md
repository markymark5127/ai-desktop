# Bazzite GNOME + headless Newelle

AI Desktop is the only launcher/UI in the intended experience. Newelle runs as
a separately installed Flatpak in headless GUI-API mode, not as a fork.

## One-time setup

1. Install Bazzite GNOME (or test on any GNOME desktop), and install Newelle:

       flatpak install flathub io.github.qwersyk.Newelle

2. Open **Newelle once**. Configure its preferred model (local llama.cpp,
   Ollama, Claude via a supported provider, or OpenAI) and install the GUI-API
   interface requirements when prompted.

3. In **Newelle → Settings → Interfaces → GUI API**, set:
   - Host: **127.0.0.1** (never 0.0.0.0)
   - Port: **8081** (AI Desktop default)
   - API key: create a long random key; do not leave it empty.

   The exact UI labels may differ with Newelle versions.

4. Save that same GUI API key for AI Desktop's client:

       bash scripts/configure-newelle-key.sh

   This creates a file readable only by your user. Alternatively, set
   AIDESKTOP_NEWELLE_API_KEY in the launcher environment. We never put
   your key into the systemd service or commit it to Git.

5. Start Newelle headlessly for a manual check:

       flatpak run io.github.qwersyk.Newelle --interface gui-api

   In another terminal, from the repository:

       bash scripts/run-dev.sh --check-newelle

   Expected output includes "Newelle connected" with the selected model.

6. After confirming that works, stop the manually running backend and install
   the autostarting **user service**, with no root privileges:

       bash scripts/install-newelle-service.sh
       systemctl --user status ai-desktop-newelle.service

   The service runs only within your logged-in user session. To stop it:

       systemctl --user disable --now ai-desktop-newelle.service

7. Start the Spotlight frontend:

       bash scripts/run-dev.sh

   Choose **Newelle (recommended)**, or use an app search without invoking AI.
   For the keyboard shortcut, follow the main README's local installation and
   opt-in Super+Space instructions.

## Safety and trust boundaries

**Currently implemented:** AI Desktop calls only Newelle's
POST /v1/chat/completions (model inference, not autonomous Newelle agent
execution) and GET /v1/models (status). The interface's selected model does
not automatically receive shell/MCP access through AI Desktop.

Our restricted Linux tools and approval UI remain responsible for machine
changes. All tool output is treated as untrusted, and actions are allowlisted.

**Do not expose Newelle's GUI API on a network.** Its API can control far
more than inference and it enables broad CORS. A GUI API key is required in
our client, but you MUST also configure that key on Newelle itself. Even
localhost services can be reached by other processes on your machine.
Do not enable Newelle's terminal automation or unrestricted MCP tools for
this prototype. Its full /api/messages/run-llm and /v2 agent endpoints are
deliberately *not* used.

Cloud-backed models may upload your prompt, system details, and log output,
depending on the model configured inside Newelle. AI Desktop displays a
per-request confirmation in the GUI. CLI prompts do not have this dialog;
avoid sending sensitive information from the CLI. A future onboarding flow
will discover the selected provider and apply finer-grained privacy rules.

## Troubleshooting

- Missing Newelle GUI API key: set a key in Newelle's GUI API settings and
  run configure-newelle-key.sh.
- HTTP 401: the locally stored key does not match Newelle's configured key.
- Connection refused: start the gui-api interface and check host/port.
- API responds but assistant gives invalid JSON: choose a model with reliable
  structured-instruction following or return to built-in tools.
- Port customized: export AIDESKTOP_NEWELLE_PORT before launching AI Desktop.
- Inspect service logs: journalctl --user -u ai-desktop-newelle -n 100 --no-pager

No Bazzite image or self-contained ISO is shipped yet. These steps are for
testing the assistant as part of a GNOME session.
