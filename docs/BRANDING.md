# Mutsu OS — official product name

**Mutsu OS** is the public-facing name of the planned Bazzite-based Linux
distribution. It is inspired by the Mutsu apple and uses the approved circular
two-wave symbol. The calm/Japandi and Cyberpunk themes are both Mutsu OS,
not separate operating systems.

## Names shown to users

| Surface | Label |
| --- | --- |
| Operating system / distribution | **Mutsu OS** |
| First-run welcome | **Welcome to Mutsu OS** |
| Search / application-menu launcher | **Mutsu OS Search** |
| Assistant result in search | **Mutsu AI** |
| GNOME keyboard shortcut description | **Mutsu OS Search** |
| Wallpapers | `mutsu-japandi-4k.png`, `mutsu-cyberpunk-4k.png` |
| Icon artwork | `mutsu-logo-symbol.svg`, `mutsu-logo-wordmark.svg` |

Brand wording is centralized for the Python UI in
`src/aidesktop/branding.py`. The desktop entry and GNOME shortcut script
use the same public wording. The logo should use the original approved
Mutsu two-wave mark, not a generic apple silhouette or old Nagi variant.

## Why some internal paths are still `ai-desktop`

The current repository is still named `ai-desktop`, the Python module is
`aidesktop`, and GNOME's app identifier remains
`io.github.markymark5127.AIDesktop`. These are **implementation details**,
not the name shown to people. For compatibility we have deliberately not
renamed:

- `~/ai-desktop` clone and installed `~/.local/bin/ai-desktop` command.
- GNOME `.desktop` filename and D-Bus application identifier.
- `~/.config/ai-desktop` saved settings and Newelle API keys.
- `~/.local/state/ai-desktop` user settings/shortcut backups.
- `ai-desktop-newelle.service` background service.
- Existing shortcut's internal GSettings keybinding path.

Changing these now would require a tested migration for GNOME single-instance
application registration, startup shortcuts, Newelle credentials, user data,
and rollback. **Do not** rename the GitHub repository or service IDs merely
to update a label.

## Upgrading a Bazzite development session

To refresh the application's user-visible name in GNOME's app grid, re-run
the non-privileged installer:

```bash
cd ~/ai-desktop
git pull
bash scripts/install-local.sh
```

If you previously bound Super+Space, refresh **just its label** without
replacing the saved binding or undo state:

```bash
python3 scripts/shortcut.py --refresh-label
```

Then start the new source through `bash scripts/restart-dev.sh`. When the
actual Mutsu OS derivative image is built, we can perform an explicit
versioned migration to new technical identifiers if needed.

## Scope today

This repository implements a GNOME application prototype and optional
user-session configuration. Calling it **Mutsu OS** is product branding;
it does **not** mean that the repo already builds a bootable Mutsu OS image,
owns GNOME Shell's top bar, or provides an OS-wide icon theme. See
[product vision](PRODUCT_VISION.md) and
[desktop reference](MUTSU_DESKTOP_REFERENCE.md).
