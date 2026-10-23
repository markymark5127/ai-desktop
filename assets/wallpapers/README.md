# Mutsu OS 4K desktop wallpapers

Upload the **actual wallpaper images (no dock, search window, GNOME bar,
or screenshot UI baked in)** to this folder in the repository.

## Required names and dimensions

| Theme | Exact filename | Native resolution | Format |
| --- | --- | --- | --- |
| Calm / Japandi | `mutsu-japandi-4k.png` | **3840 × 2160 (16:9)** | PNG |
| Cyberpunk | `mutsu-cyberpunk-4k.png` | **3840 × 2160 (16:9)** | PNG |

Please keep these filenames lowercase and use hyphens, not spaces. Include
the final approved Mutsu circular two-wave logo in each wallpaper itself if
desired; do not replace it with an older Nagi variant. The calm wallpaper
should match the soft parchment/sage palette; the cyberpunk wallpaper should
match the sharp, dark neon-magenta/cyan palette.

The supplied full-screen Japandi concept screenshot is a **desktop UI
reference**, **not** the wallpaper: otherwise the top bar, Spotlight list and
dock would appear twice once we actually render them.

Optional future extras, not required now: dark/light 16:10 laptop variants
named `mutsu-japandi-16x10.png` and `mutsu-cyberpunk-16x10.png`,
and separately designed lock-screen images.

## Prototype test installation on Bazzite GNOME

Once both assets are uploaded and pulled from GitHub:

```bash
mkdir -p "$HOME/.local/share/backgrounds/mutsu"
cp assets/wallpapers/mutsu-*-4k.png "$HOME/.local/share/backgrounds/mutsu/"

# Apply the warm Japandi image for both light and dark appearance.
uri="file://$HOME/.local/share/backgrounds/mutsu/mutsu-japandi-4k.png"
gsettings set org.gnome.desktop.background picture-uri "$uri"
gsettings set org.gnome.desktop.background picture-uri-dark "$uri"
```

To test Cyberpunk instead:

```bash
uri="file://$HOME/.local/share/backgrounds/mutsu/mutsu-cyberpunk-4k.png"
gsettings set org.gnome.desktop.background picture-uri "$uri"
gsettings set org.gnome.desktop.background picture-uri-dark "$uri"
```

These commands only change **the current user's GNOME wallpaper**, and only
when explicitly run. Theme selection inside AI Desktop does *not* yet
automatically set GNOME backgrounds.

## Planned distribution packaging

The eventual Mutsu OS image will install the images to:

```text
/usr/share/backgrounds/mutsu/mutsu-japandi-4k.png
/usr/share/backgrounds/mutsu/mutsu-cyberpunk-4k.png
```

The GNOME appearance controller should eventually select the appropriate
wallpaper with a user-controlled, reversible desktop theme change. Currently
the project is a Bazzite GNOME prototype, not a rebuilt/bootable OS image.
