# AI Desktop

**Experimental GNOME assistant for Linux beginners, not yet a Linux distribution.**

A Mac-inspired search window that lets people describe what they want in everyday language. It can inspect common Linux problems, explain findings, and request confirmation before making a supported change. The intended future base is Bazzite GNOME for gaming, but this first milestone runs as a normal GNOME application.

## Working in this first version

- GTK4 / libadwaita search-first application window with **switchable Japandi, Cyberpunk or System appearance**.
- Instant offline application search by friendly name, description, or desktop ID, with keyboard navigation.
- Enter launches the selected app; Ctrl+Enter sends text to the agent; Esc closes the window.
- Built-in read-only diagnostics, even without an AI model.
- **Headless Newelle (default)** for local or cloud models configured once in Newelle; legacy direct Ollama, OpenAI API and Anthropic API adapters remain optional.
- A model can request only allowlisted tools, never arbitrary shell commands.
- Every application launch or default audio-output change requires an explicit click to approve.
- Network requests run in background workers instead of freezing the window.
- Private history of approved AI-driven actions (no chat transcripts or diagnostic output).
- CLI mode for development and unit tests.

**Not yet implemented:** OS-wide visual theming (current appearance affects only our launcher), automatic Newelle onboarding and provider switching UI, GNOME Shell overlay (Super+Space is now available through an opt-in setup script), indexed *file* search, MCP, account-based ChatGPT/Claude login, GNOME Keyring configuration, distro ISO, app store, gaming-repair workflows, iPhone continuity, audit logs, rollback, or generalized troubleshooting. This is a prototype, not a reliable automated repair utility.

## Test on Windows before installing Linux

Follow [Windows VM testing](docs/VM_TESTING.md) for the recommended VMware Workstation Pro + Fedora Workstation GNOME workflow, snapshot strategy, and graphical/AI test checklist. The first VM test validates **desktop behavior**, not native GPU performance.

## Quick start on GNOME Linux

Requires Python 3.11+, GTK4, libadwaita, PyGObject (Python gi), and a working graphical GNOME session. Verify the graphical dependencies with:

    python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print('GNOME libraries ready')"

For a read-only test without GNOME:

    git clone https://github.com/markymark5127/ai-desktop.git
    cd ai-desktop
    bash scripts/run-dev.sh --ask "system info"
    bash scripts/run-dev.sh --search steam
    bash scripts/run-dev.sh --history
    bash scripts/run-dev.sh --check-newelle

To open the graphical launcher on a GNOME machine:

    bash scripts/run-dev.sh

To add a desktop launcher (installs only under your home directory):

    bash scripts/install-local.sh

To enable the GNOME **Super+Space** shortcut after running the local installer:

    python3 scripts/shortcut.py --apply

This changes GNOME's input-source shortcut if it conflicts. The installer saves the previous settings under $XDG_STATE_HOME/ai-desktop/gnome-shortcut.json (or ~/.local/state/ai-desktop/gnome-shortcut.json). To restore the original shortcuts:

    python3 scripts/shortcut.py --restore

The script is opt-in; inspect it first if you prefer. This is still a standalone window, not a custom GNOME Shell overlay. If you already use Super+Space to switch languages, expect that behavior to change while AI Desktop is bound.

### Recommended: headless Newelle on Bazzite GNOME

Newelle manages your model configuration while AI Desktop owns the Spotlight
UI, system tools and approvals. **No fork is needed.**

Follow **[Headless Newelle setup](docs/NEWELLE_SETUP.md)** to install the Flatpak,
set a localhost-only GUI API with authentication, connect the AI Desktop client,
and optionally enable an automatic systemd **user service**. With it running,
select **Newelle (recommended)** (the new default) in the launcher.

This integration intentionally uses only the non-agent model endpoint:
Newelle does **not** get to run system commands or MCP tools behind our
permission interface. AI Desktop validates requests, proposes changes and asks
permission before modifying settings. The full Newelle agent/MCP pipeline is
not connected yet.

### Optional: direct local AI without Newelle

Install Ollama separately, ensure its local server is running, and pull a small model. For example:

    ollama pull qwen2.5:3b

Choose Local Ollama in the model selector. Override the model ID via AIDESKTOP_LOCAL_MODEL if desired. The built-in mode requires no model and no network access.

### Using OpenAI or Claude

Export your own API credentials before starting the app:

    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...
    bash scripts/run-dev.sh

Select the desired provider in the window. Each cloud request requires a privacy confirmation because the prompt and any tool results can be sent off-device, including log snippets and host details. Do not share confidential diagnostics.

**Important:** This MVP uses separately billed API keys, NOT your ChatGPT or Claude subscription sign-in. Subscription/OAuth-style provider flows are future integrations, subject to each provider's terms and eligibility.

### Run tests

    PYTHONPATH=src python3 -m unittest discover -s tests -v

## Repository layout

- src/aidesktop/ui.py — GNOME keyboard-first window, app suggestions, approval dialogs
- src/aidesktop/themes.py — reusable, app-scoped Japandi and Cyberpunk styles
- src/aidesktop/search.py — freedesktop application catalog and instant ranked search
- src/aidesktop/history.py — timestamped, private audit trail for approved actions
- src/aidesktop/agent.py — bounded AI planner and confirmation handling
- src/aidesktop/providers.py — model provider adapters
- src/aidesktop/newelle_client.py — authenticated loopback-only Newelle model adapter
- src/aidesktop/tools.py — restricted Linux diagnostics/actions
- tests/ — headless tests (also run via GitHub Actions)
- scripts/ — dev launcher, GNOME desktop integration, and optional Newelle systemd user service
- docs/ARCHITECTURE.md — trust boundaries and future security work

## Safety boundaries

No free-form command executor is available to the model. AI-proposed changes need an approval click; selecting an app search result counts as an explicit launch request. Installed apps are validated against visible desktop entries. The app is not intended to run as root. The Newelle connection has been tested with a simulated local HTTP service; the full GUI + Newelle service has NOT been tested on real hardware in this repository, and its diagnosis cannot be relied on. Use a VM or spare machine first. See docs/ARCHITECTURE.md for limitations.

## Appearance

Select **Japandi**, **Cyberpunk** or **System** in the launcher's title bar. Japandi is the first-run default. The selected look persists across launches, and changing it does not alter the OS or other applications. See [Theme design](docs/THEMES.md).

## Keyboard usage

Type part of an installed app name and press Enter to open it. Arrow keys change the selected match. For natural-language help, use the **Ask assistant** button or press Ctrl+Enter (or prefix the request with `ask `). Esc closes the window. Built-in mode can also resolve `open Steam` to the installed desktop application.

**Limitation:** The app catalog loads when the launcher opens; restart the window after installing software. No search results are sent to a model until you explicitly ask the assistant. Native GNOME shortcut binding and full Spotlight overlay remain future milestones.

## Repair history (first version)

User-approved AI actions are recorded under `~/.local/state/ai-desktop/actions.jsonl` (or `$XDG_STATE_HOME/ai-desktop/actions.jsonl`). Events include only the action name, timestamp and success/failure—not chat prompts, secrets, arguments or diagnostic results. Run `bash scripts/run-dev.sh --history` to inspect recent events. This is a primitive audit trail, **not** a rollback system. App launches initiated directly from search results are not recorded as AI repair actions.
