# Mutsu OS icon assets

Upload **your existing approved Mutsu two-wave SVG artwork** to this
directory, with the exact filenames below. Do not substitute a generic
apple logo, redesign the wave mark or use an old Nagi OS emblem.

## The three core files

| File | Appearance | Used for |
| --- | --- | --- |
| `mutsu-logo-symbol.svg` | Full-color/sage original circular two-wave logo, transparent background | Mutsu Search app icon, system/About icon, source for boot art |
| `mutsu-logo-symbolic.svg` | Single-color **symbolic** wave mark (no fixed white background); must remain legible around 16–24px | GNOME Shell top bar, quick settings and monochrome interface |
| `mutsu-logo-wordmark.svg` | Horizontal Mutsu OS mark+wordmark; designed to be legible at 48px height | GNOME login branding and Welcome/installer artwork |

**Currently:** The project has this README, but the above filenames have
not yet been verified as uploaded. To check after uploading:

```bash
cd ~/ai-desktop
git pull
python3 scripts/check-brand-assets.py
python3 scripts/check-brand-assets.py --strict
```

The check script lists missing and differently named SVG files. It does not
alter the system.

## Theme variants — use the vectors you already made

These are optional until the first full image is working. They should use
the **same approved two-wave shape** with only the theme palette changed:

| Exact filename | Use |
| --- | --- |
| `mutsu-logo-original.svg` | Original black neutral logo |
| `mutsu-logo-japandi.svg` | Calm/Japandi muted sage logo |
| `mutsu-logo-cyberpunk.svg` | Cyberpunk cyan–magenta gradient logo |
| `mutsu-wordmark-japandi.svg` | Calm wordmark |
| `mutsu-wordmark-cyberpunk.svg` | Neon wordmark |
| `mutsu-logo-symbolic-white.svg` | Optional fixed white overlay on dark UI |
| `mutsu-ai.svg` | Optional Mutsu AI suggestion glyph |
| `mutsu-app-grid.svg` | Optional tablet Home app-drawer glyph |

The wallpaper PNGs are already in `assets/wallpapers/`. There is no need
to upload separate raster sizes of the SVG app mark just for GTK: SVG scales
to different icon sizes. **However**, the future boot splash or installer
may require pre-rendered transparent PNG artwork.

## Optional future boot and installer assets

- `assets/branding/boot/mutsu-boot-logo.png`: transparent, suggested
  512×512 or 1024×1024 logo without lettering, used when a tested Plymouth
  theme is packaged.
- `assets/branding/installer/mutsu-installer-banner.png`: wide branded
  image tailored to the selected installer, once known.
- A light/dark version of the wordmark if the GDM/installer background
  uses both dark and light modes.

**Do not create an icon for every app** simply to remove Bazzite branding.
Firefox, Files, Steam and Settings retain their actual identities unless
a complete, separately maintained icon theme is deliberately produced.
Upstream Bazzite logos that appear in apps/services/packages must be
identified by surface, not globally deleted.

## Packaging locations

During user-session prototyping, `bash scripts/install-local.sh`
installs `mutsu-logo-symbol.svg` (if present) as the Mutsu OS Search app
icon in `~/.local/share/icons/hicolor/scalable/apps/`. It never writes to
system folders.

The future custom Bazzite GNOME OCI image uses
[packaging/mutsu-image](../../packaging/mutsu-image/README.md) to install:

- `/usr/share/icons/hicolor/scalable/apps/mutsu-os-logo.svg` for OS About;
- `/usr/share/icons/hicolor/symbolic/apps/mutsu-os-symbolic.svg` for GNOME;
- `/usr/share/pixmaps/mutsu/mutsu-logo-wordmark.svg` for GDM.

The system image build is **experimental**, separate from your current
Bazzite installation. Preserving Fedora/Bazzite attribution and package
identifiers is important for update compatibility.
