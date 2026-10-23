# Appearance and theme design

AI Desktop uses **GNOME + libadwaita**, not an independently maintained
desktop environment. The Spotlight-like launcher stays keyboard-first while
its styling can change independently.

## Included looks

| Theme | Background | Main surface | Accent | Character |
| --- | --- | --- | --- | --- |
| Japandi (default) | `#F3EFE7` | `#FFFCF6` | `#516B5C` | Warm paper, charcoal, muted sage |
| Cyberpunk | `#080C16` | `#0A1428` | Neon cyan `#00F5FF`, magenta `#FF36BA` | Sharp square edges, glowing outlines, retro monospace/pixel-inspired typography |
| System | GNOME default | GNOME default | GNOME default | Unmodified libadwaita |

Use the **Appearance** choice inside the Spotlight search field's small preferences popover (or in the setup wizard) to switch. The selected theme
is saved as `~/.config/ai-desktop/appearance.json` (or under
`$XDG_CONFIG_HOME`).

## Two deliberately different visual languages

**Japandi** keeps its existing rounded, soft neutral surfaces and green
accents. **Cyberpunk** now uses rectangular inputs/panels, 0px-radius
controls, neon outlines, brighter hover/focus glows, cyan headings, magenta
selection, and a monospace/typewriter feel. A real bitmap/pixel font is
optional and is **not bundled**; GTK falls back to locally available monospace.
The Linux OS-wide GTK/Qt/GNOME Shell styling is still a separate project.

The full **setup wizard** uses fixed-size, centered **13-pixel Gtk.Buttons** with direct close/minimize/maximize actions. The everyday **Spotlight launcher is intentionally borderless** with no window controls, so it resembles macOS Spotlight instead of a full app.

## Implementation

The colors are defined in `src/aidesktop/themes.py`. The top-level application window now receives the background color, and interior spacing is applied to a nested body, avoiding exposed white edges. The window headerbar uses Mac-style left-side red/yellow/green buttons; system high-contrast accessibility mode suppresses decorative overrides. The CSS rules use the
`.ai-desktop` widget class, so they apply only to our assistant window. They
do NOT change every installed GTK app, GNOME Shell, login screen, wallpaper,
or other users' settings.

Libadwaita selects appropriate light/dark widget behavior when you select
Japandi or Cyberpunk. Selecting System returns to the GNOME theme.

## Mutsu wallpaper upload names

The final 4K desktop wallpapers should be committed under
`assets/wallpapers/`, with exact filenames
`mutsu-japandi-4k.png` and `mutsu-cyberpunk-4k.png`
(**3840 × 2160 PNG**). See
[wallpaper README](../assets/wallpapers/README.md) for testing commands and
future OS-image installation paths. The screenshot showing the dock, bar,
search results and background is a **desktop design reference**, not the
wallpaper file. See [Calm Japandi design](MUTSU_DESKTOP_REFERENCE.md).

The Spotlight results list uses per-theme translucent GTK scroller/viewport/
row styling, including selected state; an unmatched search now produces a full
Ask AI row rather than a collapsed footer. The app closes on normal focus
loss to avoid stale hidden singleton instances, while background model
requests and pending approvals preserve their state. Final appearance still
requires VM/Wayland testing.

## Future OS-wide coherence

Later, the distro image can choose a matching wallpaper, icons, dock behavior,
fonts, app metadata and GNOME Shell extension style. That should happen through
GNOME APIs and maintainable extensions rather than patching GNOME Shell.

Maintain accessible contrast, readable selection states, keyboard navigation
and high-contrast fallback. The theme is subordinate to function and should
never impair a newcomer's ability to troubleshoot their computer.


## Window buttons and phone QR

AI Desktop applies its stoplight CSS only to its own launcher/wizard. The setup wizard can optionally apply a reversible GNOME-wide left-side button placement; applications with independent titlebars may ignore it. Phone pairing now uses offline, scannable official-store QR codes. See [Window and phone setup](WINDOW_AND_PHONE_SETUP.md).


## Minimal translucent Spotlight surface

Spotlight now opens as a small undecorated text field with optional results and AI replies beneath it. Its per-theme CSS provides translucency, distinct Japandi/Cyberpunk treatments and a high-contrast opaque fallback. Settings and provider choices live in a hidden popover (gear icon or Ctrl+,). This does not yet provide system-compositor background blur or exact Mac overlay positioning. See [Spotlight UI](SPOTLIGHT_UI.md).
