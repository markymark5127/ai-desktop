#!/usr/bin/env bash
# Installs a user-scoped app launcher only; does not change GNOME shortcuts.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
printf '#!/usr/bin/env bash\nexport PYTHONPATH=%q:"${PYTHONPATH:-}"\nexec python3 -m aidesktop "$@"\n' "$repo_dir/src" > "$HOME/.local/bin/ai-desktop"
chmod +x "$HOME/.local/bin/ai-desktop"
# Install the owner's Mutsu logo as a user-scoped app icon once uploaded.
# Do not overwrite or uninstall upstream Bazzite/Fedora icons and packages.
icon_name="io.github.markymark5127.AIDesktop"
icon_source="$repo_dir/assets/icons/mutsu-logo-symbol.svg"
icon_value="system-search-symbolic"
if [[ -s "$icon_source" ]]; then
  icon_dir="$HOME/.local/share/icons/hicolor/scalable/apps"
  mkdir -p "$icon_dir"
  cp "$icon_source" "$icon_dir/$icon_name.svg"
  icon_value="$icon_name"
  printf 'Installed Mutsu OS Search icon from %s\n' "$icon_source"
else
  printf 'Mutsu SVG not uploaded yet; keeping the generic search icon.\n'
fi
cat > "$HOME/.local/share/applications/io.github.markymark5127.AIDesktop.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Mutsu OS Search
GenericName=Application, File and AI Search
Comment=Search Mutsu OS applications, local files and the selected AI
Keywords=Mutsu;Mutsu OS;Spotlight;Search;AI;Files;
Exec=$HOME/.local/bin/ai-desktop
Icon=$icon_value
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
echo "Installed Mutsu OS Search launcher at $HOME/.local/bin/ai-desktop"
echo "To use Super+Space, configure a custom shortcut in GNOME Settings > Keyboard."
