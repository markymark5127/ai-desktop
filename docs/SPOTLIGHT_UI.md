# Spotlight-style search overlay (prototype)

The everyday launcher is now a **compact, undecorated GTK4 window** instead
of a full-size AI chat application. The intended interaction is deliberately
familiar to someone coming from macOS Spotlight.

## Behavior now implemented

- Open the launcher with its GNOME shortcut: **Super+Space** (usually
  Command+Space on a Mac keyboard), or select AI Desktop from the app menu.
- An empty search is just a **single translucent input field**—no titlebar,
  permanent chat transcript, provider selector, dock settings or onboarding
  buttons are visible.
- Type an installed app name to see a small list of up to **five** matching
  applications under the field. **Enter** opens the selected app, closes the
  launcher after the desktop reports the launch request, and does not call AI.
- If you type a question, press **Enter** with no app match, or use
  **Ctrl+Enter** to explicitly ask the AI. The result appears in an expandable,
  height-limited answer section below the search field.
- AI-proposed changes still show **Apply change / Decline** controls, and
  cloud-capable providers still require privacy consent per request. Actions
  remain bounded by the project's approved tool catalog.
- **Escape** closes Spotlight. Arrow keys select application results.
- A subtle settings icon inside the bar (or **Ctrl+,**) opens provider and
  appearance choices plus a **Setup & keyboard settings…** entry. The full
  original setup wizard remains a separate window via `--setup`.

### Translucency and placement limitations

The background uses alpha-composited GTK4 CSS rather than an opaque top-level
window. Japandi remains warm and rounded; Cyberpunk uses a dark angular
panel with cyan neon outlines; System uses a neutral dark translucent bar.
GNOME high-contrast settings instead get a readable opaque fallback.

**This is not yet a true GNOME Shell Spotlight overlay.** A normal GTK4 app
cannot guarantee the Mac's precise centered/top-third placement, compositor
background blur, focus behavior over fullscreen games, or being present on
every workspace. GTK4 transparency and undecorated windows are supported,
but compositor decisions can vary in VMware, VirtualBox, Wayland, and X11.

A future GNOME Shell extension should own positioning, focus, activation
and compositor integration, while the same Python application handles
the trusted search/AI backend. Never claim blur is already implemented.

### App search versus AI scope

The current fast index covers **installed applications only**. Files,
Settings pages, Steam games, and general desktop actions remain future
search features. Newelle model inference is optional, and an installed-app
search remains usable when it is offline.

### Test in a GNOME VM

    cd ~/ai-desktop
    git pull
    bash scripts/run-dev.sh

Or reopen the wizard separately:

    bash scripts/run-dev.sh --setup

1. Open Spotlight: verify a single compact, translucent text field appears,
   without titlebar or permanent answer panel.
2. Type `files`; verify installed app matches appear below and arrow keys
   change selection.
3. Press Enter on a real installed application: it should launch and the
   Spotlight window should close.
4. Reopen, type a question and press Ctrl+Enter. For offline tests, open
   Preferences and select **Built-in (offline)** before asking about audio,
   disk space or network status.
5. Check that the answer and any approval buttons appear **only when needed**.
6. Type a new search: the prior response should collapse.
7. Open Preferences with the gear icon or Ctrl+, change theme, and verify
   Japandi/Cyberpunk translucent styling. Full setup should still open.
8. Press Escape: launcher closes. Test Ctrl+, and Esc with the popover open.
9. Enable GNOME high-contrast mode: input, result rows and responses remain
   readable.
10. In your graphics-troubled VM, try:
       GSK_RENDERER=cairo LIBGL_ALWAYS_SOFTWARE=1 bash scripts/run-dev.sh
    Transparency/blur are compositor-dependent and may look different in a VM.

## Implementation files

- `src/aidesktop/ui.py` — compact field, conditional result/answer sections,
  privacy/approval flow, small settings popover and keyboard handling.
- `src/aidesktop/themes.py` — per-theme semi-transparent launcher CSS;
  existing setup wizard and Mac-style titlebar styling remain separate.
- `src/aidesktop/setup_wizard.py` — full setup experience unchanged.

The GNOME user-session launcher and Super+Space installer scripts are unchanged.
