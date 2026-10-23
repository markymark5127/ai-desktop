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
the walkthrough, even after completing/skipping it. The normal Spotlight search field no longer shows a permanent Setup button; choose the small preferences icon (or Ctrl+,), then **Setup & keyboard settings…**. No root account is needed.

For a headless check of locally saved user options:

    bash scripts/run-dev.sh --setup-status

## Wizard pages: what's actually wired

| Page | Currently implemented | Still needs platform/product development |
| --- | --- | --- |
| Welcome | Local installed-app search exercise; explains keyboard-first usage | Full indexed file and Settings search |
| Appearance and keyboard | Full-bleed Japandi/Cyberpunk/System, red/yellow/green buttons left, reversible left-side controls for compatible GNOME apps, PC/Mac shortcuts, real key-event test, optional US XKB source and Restore | Per-device Apple keyboard mapping, OS-wide matched colors for third-party titlebars |
| Mac-style dock | Configure installed/enabled Dash to Dock: four positions, persistent/auto-hide, Show Applications icon, confirmation and Restore | Automatic compatible extension installation; hide Activities automatically; OS-image defaults |
| Your helper | Three persisted teaching preferences used when constructing the assistant prompt | Graphical per-task explanations, general repair verification and rollback |
| AI connection | User-initiated check of authenticated loopback Newelle GUI API; links to setup guide | Automatic installation/provider onboarding with usable provider selection |
| Phone pairing | iPhone/Android/skip choice with **offline app-store QR codes** for KDE Connect; inspect GSConnect availability; open its preferences | Actual in-wizard pairing and phone diagnostics |
| Gaming and desktop | Shows whether Steam is installed; one-click explicit open if found; tiling guidance | Full Bazzite integration, Steam/Proton controller diagnostics and quarter-tiling extensions |
| Adaptive Desktop / tablet posture | **Not implemented** — planned mode choice in future onboarding | Automatic detection, app-grid Home, swipe-to-Home, larger touch UI, maximized apps and safe switch back |

**No promise of full AirDrop, Universal Clipboard, SMS, iMessage, or always-on
iPhone sync.** KDE Connect on iOS is limited by iOS background and sandbox rules.

**No app installs or root commands are performed** by the wizard. Dash to Dock settings are changed only after selecting Apply and confirming, and the previous dock configuration is backed up. Hiding Activities is still manual through a compatible Just Perfection extension. It does not
automatically replace GNOME shortcut bindings, modify the XKB layout, pair a
phone, or initialize Newelle without user input.

## Planned adaptive desktop onboarding

The final distro will detect capable 2-in-1 hardware where the Linux kernel/libinput exposes a real tablet-mode switch, demonstrate touch-first app-grid Home, and offer Automatic / Always Desktop / Always Tablet preferences. If there is no reliable switch, users need a manual mode toggle. It must never force tablet mode just because a touchscreen is present. **This is only a future requirement, not available in today's wizard.** See [ADAPTIVE_DESKTOP.md](ADAPTIVE_DESKTOP.md).

## Installer and recent wizard polish

For a user-level install with a reversible Spotlight shortcut, run
`bash scripts/install-desktop-experience.sh --with-shortcut` from the cloned
repository. More steps for GNOME extensions and Newelle are in
[INSTALL_ON_BAZZITE.md](INSTALL_ON_BAZZITE.md).

Changing setup steps now resets the shared scroll container to the top, both
before and after the animated page transition. The Gtk.Stack uses the active
page's height rather than retaining the tallest step.

The Mac traffic lights are separate fixed-size 13px functional controls. The
Cyberpunk theme has neon outlines, square corners and a retro font treatment;
Japandi's original rounded design is unchanged.

## Window appearance and phone-app QR codes

The wizard and launcher now fill the entire window in Japandi and Cyberpunk, without the prior white margin. Both display left-side red/yellow/green titlebar controls. On the Appearance step, a separately confirmed option changes the user GNOME button arrangement for other compatible applications and preserves a Restore backup. Other apps may retain their own decorations and colors.

The Phone step draws locally bundled QR codes for the official KDE Connect listings in Apple's App Store or Google Play. It does not call an online QR service or transmit phone data. This installs the *phone app*, while GSConnect remains the desktop integration. See [WINDOW_AND_PHONE_SETUP.md](WINDOW_AND_PHONE_SETUP.md).

## Mac-style dock

The wizard now has a separate dock step with Bottom (default), Left, Right or Top, a persistent dock checkbox, check/install guidance, an explicit Apply action, Restore and a link to Just Perfection for optionally hiding Activities. A GNOME Shell extension must already be installed and enabled. See [DOCK.md](DOCK.md) for all settings and VM test requirements.

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
