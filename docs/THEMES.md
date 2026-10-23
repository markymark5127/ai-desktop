# Appearance and theme design

AI Desktop uses **GNOME + libadwaita**, not an independently maintained
desktop environment. The Spotlight-like launcher stays keyboard-first while
its styling can change independently.

## Included looks

| Theme | Background | Main surface | Accent | Character |
| --- | --- | --- | --- | --- |
| Japandi (default) | `#F3EFE7` | `#FFFCF6` | `#516B5C` | Warm paper, charcoal, muted sage |
| Cyberpunk | `#121522` | `#1C2130` | `#B62D7E`, cyan border `#50DCE3` | Dark indigo, magenta and cyan |
| System | GNOME default | GNOME default | GNOME default | Unmodified libadwaita |

Use the **Appearance** dropdown in the title bar to switch. The selected theme
is saved as `~/.config/ai-desktop/appearance.json` (or under
`$XDG_CONFIG_HOME`).

## Implementation

The colors are defined in `src/aidesktop/themes.py`. The top-level application window now receives the background color, and interior spacing is applied to a nested body, avoiding exposed white edges. The window headerbar uses Mac-style left-side red/yellow/green buttons; system high-contrast accessibility mode suppresses decorative overrides. The CSS rules use the
`.ai-desktop` widget class, so they apply only to our assistant window. They
do NOT change every installed GTK app, GNOME Shell, login screen, wallpaper,
or other users' settings.

Libadwaita selects appropriate light/dark widget behavior when you select
Japandi or Cyberpunk. Selecting System returns to the GNOME theme.

## Future OS-wide coherence

Later, the distro image can choose a matching wallpaper, icons, dock behavior,
fonts, app metadata and GNOME Shell extension style. That should happen through
GNOME APIs and maintainable extensions rather than patching GNOME Shell.

Maintain accessible contrast, readable selection states, keyboard navigation
and high-contrast fallback. The theme is subordinate to function and should
never impair a newcomer's ability to troubleshoot their computer.


## Window buttons and phone QR

AI Desktop applies its stoplight CSS only to its own launcher/wizard. The setup wizard can optionally apply a reversible GNOME-wide left-side button placement; applications with independent titlebars may ignore it. Phone pairing now uses offline, scannable official-store QR codes. See [Window and phone setup](WINDOW_AND_PHONE_SETUP.md).
