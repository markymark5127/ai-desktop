# First-run setup: Mac-familiar GNOME + Linux troubleshooting buddy

The first-run wizard is now part of AI Desktop's GTK4/libadwaita app. It is
**not** the Linux disk-partitioning/installation screen. It launches the first
time a user opens AI Desktop and can be skipped or reopened later.

## Run it

On Fedora GNOME or Bazzite GNOME with the GTK4/PyGObject dependencies installed:

    git pull
    bash scripts/run-dev.sh --setup

To open the desktop app normally:

    bash scripts/run-dev.sh

If no setup preference exists, the wizard opens automatically. Press **Skip
setup** to keep using the launcher. In the launcher, click **Setup** to reopen
the walkthrough, even after completing/skipping it. No root account is needed.

For a headless check of locally saved user options:

    bash scripts/run-dev.sh --setup-status

## Wizard pages: what's actually wired

| Page | Currently implemented | Still needs platform/product development |
| --- | --- | --- |
| Welcome | Local installed-app search exercise; explains keyboard-first usage | Full indexed file and Settings search |
| Appearance and keyboard | Japandi/Cyberpunk/System, PC/Mac shortcut label, real key-event test, optional confirmed US XKB source application and Restore | Per-device Apple keyboard mapping, installed custom desktop dock |
| Your helper | Three persisted teaching preferences used when constructing the assistant prompt | Graphical per-task explanations, general repair verification and rollback |
| AI connection | User-initiated check of authenticated loopback Newelle GUI API; links to setup guide | Automatic installation/provider onboarding with usable provider selection |
| Phone pairing | iPhone/Android/skip choice; inspect GSConnect availability; explicit button to open its preferences | In-wizard pairing UI and functional phone diagnostics |
| Gaming and desktop | Shows whether Steam is installed; one-click explicit open if found; tiling guidance | Full Bazzite integration, Steam/Proton controller diagnostics and quarter-tiling extensions |

**No promise of full AirDrop, Universal Clipboard, SMS, iMessage, or always-on
iPhone sync.** KDE Connect on iOS is limited by iOS background and sandbox rules.

**No app installs or root commands are performed** by the wizard. It does not
automatically replace GNOME shortcut bindings, modify the XKB layout, pair a
phone, or initialize Newelle without user input.

## Keyboard profiles

- **Standard English US**: Windows/Super key; Spotlight appears as **Win+Space**.
- **Mac English US**: physical Command key normally reports **Super** on Linux,
  so Spotlight appears as **⌘+Space**. The wizard has a live key test, but some
  keyboards and Windows VMs intercept/remap modifiers.
- Selecting the profile only changes our shortcut labels and saved preference.
  Click **Apply selected layout to GNOME…** (and then approve) to prepend the
  XKB English US or Macintosh US layout while retaining all other sources.
  **Restore prior layout** restores the captured source list.
- App-level Command+C/V emulation is **not** implemented. Terminals and
  games retain their normal key behavior.

More detail in [KEYBOARD_PROFILES.md](KEYBOARD_PROFILES.md).

## Helper learning styles

The wizard stores one of:

- **Just help me fix things** — terse.
- **Help me and briefly explain** — default.
- **Teach me as we go** — Mac analogies and more context.

The model prompt reads this preference for explanations only. It **does not**
change tool allowlists, permissions, actions needing user approval, or privileged
access. Existing actions still require explicit consent. Newelle continues to
serve inference through the limited /v1/chat/completions endpoint.

## Persistence and privacy

User preferences are stored at:
- \`$XDG_CONFIG_HOME/ai-desktop/onboarding.json\` (fallback ~/.config),
- \`$XDG_CONFIG_HOME/ai-desktop/keyboard.json\`,
- \`$XDG_CONFIG_HOME/ai-desktop/appearance.json\`.

The first file contains only the setup status, teaching preference, and chosen
phone type. All are created as user-private files with atomic writes.
The optional XKB input-source backup is in
\`$XDG_STATE_HOME/ai-desktop/keyboard-sources-backup.json\` (fallback ~/.local/state).

A skipped setup is marked **skipped** (so it does not nag every launch) and
the wizard remains manually reopenable. The OS does not request an Apple ID.

## Test checklist for your Windows VM

1. In a clean Fedora GNOME guest, launch AI Desktop; the first-run wizard opens.
2. Search for Files/Settings in Welcome; results are immediate with no model.
3. Choose Cyberpunk, restart and verify the saved appearance.
4. Select Mac keyboard; press Command (if available) in the key-test field.
   In a Windows VM the hypervisor may intercept it; the result should explain.
5. Apply a US layout only if you wish, then Restore; verify that other language
   input sources are not lost.
6. Choose "Teach me as we go"; finish and run a model request to test verbosity.
7. Check Newelle when not running; setup should continue without it.
8. Check GSConnect availability; opening preferences is explicit. Pairing
   requires the user to complete GSConnect/KDE Connect steps themselves.
9. Open Steam if installed (Fedora test VM may not have it).
10. Finish, reopen Setup from the launcher, then test Skip and --setup-status.
11. Run the headless unit suite and test with high-contrast GNOME appearance.

No passing VM test replaces a real Bazzite GNOME hardware test for Apple keys,
Steam Input, graphics, iPhone Wi-Fi discovery, sound or suspend/resume.

## Later installer design

The eventual separately branded Bazzite-derived image should launch this wizard
on **first login**, not during the underlying disk-install phase. It can reuse
this GTK app without tying the assistant to a custom kernel, window manager or
entirely new desktop environment.
