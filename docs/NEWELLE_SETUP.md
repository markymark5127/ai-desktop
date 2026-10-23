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

   Expected output includes "Newelle connected" with the selected model. This **only checks API availability**, not working inference. To send model requests, enable the optional sharing checkbox in the AI Desktop wizard's AI connection page or Spotlight Settings. It defaults to off. Verify the selected model really answers by running:

       bash scripts/run-dev.sh --test-newelle

   You can also use Spotlight's settings (gear icon) → **Test Newelle connection + reply**. This sends only a generic non-personal test prompt; Newelle may pass it to a configured cloud model.

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
depending on the model configured inside Newelle. The wizard and Spotlight
Settings have an **unchecked-by-default, revocable model-sharing permission**.
Once checked, Spotlight no longer interrupts each request with a popup; CLI
agent requests also respect the saved setting. The optional end-to-end Newelle
inference test requires this permission, while the model-list connection check
does not. Disabling sharing prevents future requests but cannot retract data
already sent. Avoid sending sensitive information from the CLI. A future onboarding flow
will discover the selected provider and apply finer-grained privacy rules.

## Troubleshooting

- Missing Newelle GUI API key: set a key in Newelle's GUI API settings and
  run configure-newelle-key.sh.
- HTTP 401: the locally stored key does not match Newelle's configured key.
- Connection refused: start the gui-api interface and check host/port.
- Ordinary Newelle text replies now appear as an informational answer. Malformed JSON tool/action plans remain rejected.
- HTTP 400/422: check Newelle's selected model and provider; HTTP 404: check the GUI API interface and port.
- If Spotlight shows **Built-in (offline)** instead of Newelle, change its provider in the gear-icon preferences.
- Port customized: export AIDESKTOP_NEWELLE_PORT before launching AI Desktop.
- Inspect service logs: journalctl --user -u ai-desktop-newelle -n 100 --no-pager

No Bazzite image or self-contained ISO is shipped yet. These steps are for
testing the assistant as part of a GNOME session.

### Quick check when Spotlight cannot talk to Newelle

Run these commands in the same Linux session as AI Desktop:

    bash scripts/run-dev.sh --check-newelle
    bash scripts/run-dev.sh --test-newelle

If only the first works, Newelle's HTTP server is present but the model cannot generate replies. Try a normal message inside Newelle itself and inspect its service: `systemctl --user status ai-desktop-newelle.service` and `journalctl --user -u ai-desktop-newelle -n 60 --no-pager`. Don't paste your API key into logs or chat.
