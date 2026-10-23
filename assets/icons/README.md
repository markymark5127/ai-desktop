# Mutsu OS SVG design assets

Upload your source SVG files **here**. Keep the original vector paths and
transparent backgrounds; don't rasterize to 4K and don't bake a full desktop
screenshot into an icon.

## Suggested filenames

| Filename | Purpose |
| --- | --- |
| `mutsu-logo-symbol.svg` | Approved circular, two-wave Mutsu mark; panel, About screen, Spotlight AI and app icon |
| `mutsu-logo-wordmark.svg` | Full Mutsu OS logo/lettering, if you have a separate vector version |
| `mutsu-ai.svg` | Optional bespoke AI suggestion icon |
| `mutsu-app-grid.svg` | Optional tablet Home / app drawer icon |
| `mutsu-search.svg` | Optional magnifying-glass/search visual |

If your actual SVG filenames are different, they can be renamed on upload.
Only upload assets you own or can redistribute in the Mutsu OS image.

Future integration will use `Gtk.Image.new_from_file(...)` for the app
launcher and/or install a registered GTK/GNOME icon theme under
`/usr/share/icons/Mutsu/`. Avoid loading random SVGs as CSS via network
URLs. Color-appropriate symbolic variants can be added later.

**Status:** The prototype currently uses standard GTK symbolic icons.
Custom SVGs have not yet been uploaded/connected and are not a prerequisite
for the grouped results and wallpaper changes.
