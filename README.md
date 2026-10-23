# Mutsu OS

**A Mac-familiar, adaptive Linux gaming OS in development.** The current repository implements its GNOME desktop prototype; it is not yet a separately installable distribution image.

A Mac-inspired search window that lets people describe what they want in everyday language. It can inspect common Linux problems, explain findings, and request confirmation before making a supported change. The intended future base is Bazzite GNOME for gaming, but this first milestone runs as a normal GNOME application.

See the [official naming guide](docs/BRANDING.md). Our [Calm Japandi desktop reference](docs/MUTSU_DESKTOP_REFERENCE.md) describes the visual direction and the [4K wallpaper upload folder](assets/wallpapers/README.md) specifies the approved asset names. Our [Adaptive Desktop vision](docs/ADAPTIVE_DESKTOP.md) adds automatic MacBook-to-iPad-like transitions on supported convertible laptops, with tablet-first app-grid Home and an explicit manual override (planned, not implemented). Our [troubleshooting-buddy / universal Spotlight design](docs/HELPER_EXPERIENCE.md) makes the helper into optional Linux training wheels and supports user-adjustable explanation levels (planned, not yet built). Our [product vision](docs/PRODUCT_VISION.md) is to help Mac users feel at home on a Bazzite-based gaming PC: Spotlight-style search with headless Newelle, GNOME dock/gestures/window snapping, honest phone continuity through GSConnect/KDE Connect, approachable game support and safe system repair. Mac-like *behavior* comes before cosmetic imitation.

## Working in this first version

- **Compact translucent Spotlight-style search bar** with no permanent titlebar/chat pane. App matches and replies expand only as needed; appearance/provider/setup live in a small preferences popover. See [Spotlight UI](docs/SPOTLIGHT_UI.md).
- GTK4 / libadwaita first-run wizard with switchable Japandi, Cyberpunk or System appearance, edge-to-edge styling and optional Mac controls.
- Mac-style red/yellow/green window controls on the **upper left** of Mutsu OS, plus a reversible, optional left-side window-button setting for other compatible GNOME apps.
- Offline, scannable **KDE Connect iPhone/Android QR codes** in the phone-pairing step, using official app-store destinations.
- Reversible **Mac-style GNOME dock configuration** through an already enabled Dash to Dock extension: always-on bottom dock by default, four positions, Launchpad-like Show Applications grid button; optional Activities-button hiding guidance.
- **Standard English US / Mac English US keyboard profiles**, with Win+Space versus ⌘+Space labels, explicit GNOME layout application, and reversible input-source backup.
- Instant offline application search by friendly name, description, or desktop ID, with keyboard navigation; plus bounded local-only filename and folder search in familiar home directories. Spotlight groups real results under Top Results, Files and AI Suggestions.
- Enter opens a matching app, or **asks the selected AI by default** if there is no local match. Every nonempty search also offers a visible Ask AI option. No special AI shortcut is needed; clicking elsewhere closes an idle Spotlight (in-flight requests remain alive). Ctrl+, or Command+, opens preferences.
- Built-in read-only diagnostics, even without an AI model.
- **One-time, optional model-sharing permission** in setup wizard and Spotlight Settings. Off by default; when approved, Enter asks Newelle/other configured models without repeated privacy popups. Disabling it prevents future model requests; system-changing actions still need approval.
- **Headless Newelle (default)** for local or cloud models configured once in Newelle; legacy direct Ollama, OpenAI API and Anthropic API adapters remain optional.
- A model can request only allowlisted tools, never arbitrary shell commands.
- Every application launch or default audio-output change requires an explicit click to approve.
- Network requests run in background workers instead of freezing the window.
- Private history of approved AI-driven actions (no chat transcripts or diagnostic output).
- CLI mode for development and unit tests.

**Not yet implemented:** convertible/tablet posture detection, touch-first app-grid Home or swipe-up tablet navigation, automated device pairing/AI provider onboarding in the welcome wizard, complete OS-wide visual theming (currently the launcher/wizard and explicit GNOME wallpaper selection), automatic Newelle onboarding and provider switching UI, GNOME Shell overlay (Super+Space is now available through an opt-in setup script), full persistent file-content indexing, MCP, account-based ChatGPT/Claude login, GNOME Keyring configuration, distro ISO, app store, gaming-repair workflows, iPhone continuity, audit logs, rollback, or generalized troubleshooting. This is a prototype, not a reliable automated repair utility.

## New: working first-run welcome wizard (prototype)

On first graphical launch, Mutsu OS opens a skippable **Mac-to-Linux welcome wizard**. In the compact Spotlight launcher, click the small preferences icon or press Ctrl+, and choose **Setup & keyboard settings…** to reopen it:

    bash scripts/run-dev.sh --setup
    bash scripts/run-dev.sh --setup-status

The wizard offers Japandi/Cyberpunk appearance, Mac or PC US keyboard selection with a real modifier-key test, a separately approved/reversible GNOME keymap option, a live installed-app search exercise, the **Linux troubleshooting buddy** explanation mode, a Newelle connection check, GSConnect/iPhone/Android guidance, and Steam detection.

It does **not** yet automatically install Newelle, pair a phone, configure a Mac-like dock/advanced tiling, index files, or make Bazzite installation images. Those are separate milestones.

See [First-run onboarding](docs/ONBOARDING.md) for the implemented steps, privacy boundaries, and VM test checklist. For the latest theme, titlebar and QR-code details see [Window and phone setup](docs/WINDOW_AND_PHONE_SETUP.md).

## Install on Bazzite GNOME (user session)

If you already cloned the project on a Bazzite GNOME machine or Fedora GNOME VM:

    cd ~/ai-desktop
    git pull
    bash scripts/install-desktop-experience.sh --with-shortcut
    ~/.local/bin/ai-desktop --setup

This installs the desktop application entry and reversible Super+Space binding
for your **user account**, without modifying Bazzite's atomic base image.
See [Full Bazzite installation steps](docs/INSTALL_ON_BAZZITE.md) to enable
the existing GNOME dock, GSConnect pairing and optional Newelle backend.
**It is not a whole-OS theme or a finished custom distribution yet.**

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

The script is opt-in; inspect it first if you prefer. This is still a standalone window, not a custom GNOME Shell overlay. If you already use Super+Space to switch languages, expect that behavior to change while Mutsu OS is bound.

**During active development**, Git pulls do not replace an already-running,
hidden GNOME application instance. To make sure new UI code is actually
running, use `bash scripts/restart-dev.sh`, which stops only your current
user's Mutsu OS Python module process, then launches the updated source.
It does not stop Newelle. The **Setup & keyboard settings…** item uses an
application action, and `bash scripts/run-dev.sh --setup` is forwarded
correctly to the existing primary instance (after restarting old instances
at least once to load the updated handler).

### Recommended: headless Newelle on Bazzite GNOME

Newelle manages your model configuration while Mutsu OS owns the Spotlight
UI, system tools and approvals. **No fork is needed.**

Follow **[Headless Newelle setup](docs/NEWELLE_SETUP.md)** to install the Flatpak,
set a localhost-only GUI API with authentication, connect the Mutsu OS client,
and optionally enable an automatic systemd **user service**. With it running,
select **Newelle (recommended)** in Spotlight's preferences popover (gear icon / Ctrl+,).

This integration intentionally uses only the non-agent model endpoint:
Newelle does **not** get to run system commands or MCP tools behind our
permission interface. Mutsu OS validates requests, proposes changes and asks
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

Select the desired provider in Spotlight Settings. Before using any AI model, optionally check **Allow questions and diagnostics to be sent to the AI model** in the setup wizard or Settings. It is **off by default** and replaces repeated per-query popups. If enabled, prompts and diagnostic results may leave the device through cloud providers, including Newelle if configured to use a cloud model. You can turn it off anytime; already transmitted requests cannot be recalled. Do not share confidential diagnostics.

**Important:** This MVP uses separately billed API keys, NOT your ChatGPT or Claude subscription sign-in. Subscription/OAuth-style provider flows are future integrations, subject to each provider's terms and eligibility.

### Run tests

    PYTHONPATH=src python3 -m unittest discover -s tests -v

## Repository layout

- src/aidesktop/ui.py — compact translucent Spotlight window, conditional app/results and approval dialogs
- src/aidesktop/themes.py — original Japandi and new neon/squared Cyberpunk styles
- src/aidesktop/mac_stoplights.py — compact Mac-style accessible window action buttons
- src/aidesktop/keyboard_profiles.py — Mac/PC US profile settings and optional reversible GNOME layout
- src/aidesktop/onboarding.py — secure per-user first-run status, phone choice and learning style
- src/aidesktop/setup_wizard.py — GTK welcome, dock, keyboard test, Newelle check, GSConnect guidance and Steam overview
- src/aidesktop/dock.py — safe, reversible dock configuration for an enabled GNOME Dash to Dock extension
- src/aidesktop/window_controls.py — reversible GNOME user window-button placement
- src/aidesktop/phone_download.py — bundled offline KDE Connect app-store QR matrices
- src/aidesktop/search.py — freedesktop application catalog and instant ranked search
- src/aidesktop/search_routing.py — local-first matching and safe focus-loss logic
- src/aidesktop/file_search.py — bounded background filename-only search under user-facing home folders
- src/aidesktop/wallpaper.py — explicit, reversible GNOME wallpaper switching to uploaded Mutsu assets
- src/aidesktop/history.py — timestamped, private audit trail for approved actions
- src/aidesktop/agent.py — bounded AI planner and confirmation handling
- src/aidesktop/providers.py — model provider adapters
- src/aidesktop/newelle_client.py — authenticated loopback-only Newelle model adapter
- src/aidesktop/tools.py — restricted Linux diagnostics/actions
- tests/ — headless tests (also run via GitHub Actions)
- scripts/ — dev launcher, GNOME user-session installer, desktop integration and optional Newelle systemd user service
- docs/ARCHITECTURE.md — trust boundaries and future security work

## Safety boundaries

No free-form command executor is available to the model. AI-proposed changes need an approval click; selecting an app search result counts as an explicit launch request. Installed apps are validated against visible desktop entries. The app is not intended to run as root. The Newelle connection has been tested with a simulated local HTTP service; the full GUI + Newelle service has NOT been tested on real hardware in this repository, and its diagnosis cannot be relied on. Use a VM or spare machine first. See docs/ARCHITECTURE.md for limitations.

## Mac-style dock configuration

A new **Mac-style dock** page in the Setup wizard configures an existing,
enabled Dash to Dock GNOME Shell extension without reinstalling or modifying
the underlying Bazzite OS. Choose Bottom (default), Left, Right or Top and
**Always show dock** (default). It enables the Show Applications icon, which
opens GNOME's Launchpad-like app grid. There is a separately confirmed Apply
step and Restore original dock settings action.

The extension must be installed and enabled in GNOME Extension Manager first.
The top-left Activities label can be hidden using a compatible Just Perfection
extension; that particular operation is guidance only, not automated in the
current prototype. See [Mac-style dock requirements and setup](docs/DOCK.md).
Our Spotlight launcher remains available using Super+Space, independently
from the Applications grid and workspace overview.

## Keyboard setup

Choose **Standard US · Win** or **Mac US · ⌘ Command** in Mutsu OS's Keyboard selector. On typical Apple keyboards, ⌘ Command already sends the Linux **Super** modifier. The Spotlight shortcut is always the same Super+Space binding; it appears as Win+Space or ⌘+Space depending on the physical keyboard.

The **Apply layout to GNOME** button is an optional, separately confirmed system change. It prefers `us` or `us+mac` while preserving other input languages and saving a reversible backup. **Restore layout** restores the prior list. Switching profiles by itself changes only Mutsu OS's labels and preference, not your OS keymap. It does not globally remap Command+C/V to Ctrl+C/V.

Full detail: [Keyboard setup / physical Command key behavior](docs/KEYBOARD_PROFILES.md). The first-login setup wizard will include this choice.

## Appearance

Select **Japandi**, **Cyberpunk** or **System** from the small settings icon inside Spotlight (or the setup wizard). Japandi remains the first-run default with its original rounded corners and soft neutral palette. **Cyberpunk** now has deliberately squared panels, neon cyan/magenta outlines, glow effects and monospace/pixel-font fallback. Both Mutsu OS windows have dedicated **13px circular red/yellow/green** functional titlebar controls, rather than resized GNOME buttons. Colors remain app-scoped, not OS-wide. See [Theme design](docs/THEMES.md).

## Keyboard usage

Type an installed app name and press Enter to open it. If there is no local match, a visible **Ask AI** result is selected, so Enter uses the chosen assistant when model sharing has been enabled; no hotkey is needed. Arrow keys can select Ask AI even when app matches exist. Nothing is sent during typing. Clicking another app or the desktop hides Spotlight while retaining any in-flight answer. Escape dismisses it; the gear icon or Ctrl+, opens provider/appearance/setup. Built-in mode can also resolve `open Steam` to the installed desktop application.

**Limitation:** The app catalog loads when the launcher opens; restart the window after installing software. No search results are sent to a model until you explicitly ask the assistant. Native GNOME shortcut binding and full Spotlight overlay remain future milestones.

## Repair history (first version)

User-approved AI actions are recorded under `~/.local/state/ai-desktop/actions.jsonl` (or `$XDG_STATE_HOME/ai-desktop/actions.jsonl`). Events include only the action name, timestamp and success/failure—not chat prompts, secrets, arguments or diagnostic results. Run `bash scripts/run-dev.sh --history` to inspect recent events. This is a primitive audit trail, **not** a rollback system. App launches initiated directly from search results are not recorded as AI repair actions.
