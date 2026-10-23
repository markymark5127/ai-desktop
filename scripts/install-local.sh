#!/usr/bin/env bash
# Installs a user-scoped app launcher only; does not change GNOME shortcuts.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
printf '#!/usr/bin/env bash\nexport PYTHONPATH=%q:"${PYTHONPATH:-}"\nexec python3 -m aidesktop "$@"\n' "$repo_dir/src" > "$HOME/.local/bin/ai-desktop"
chmod +x "$HOME/.local/bin/ai-desktop"
cat > "$HOME/.local/share/applications/io.github.markymark5127.AIDesktop.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Mutsu Search
Comment=Mutsu OS Spotlight-style application, file and AI search
Exec=$HOME/.local/bin/ai-desktop
Icon=system-search-symbolic
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
echo "Installed AI Desktop launcher at $HOME/.local/bin/ai-desktop"
echo "To use Super+Space, configure a custom shortcut in GNOME Settings > Keyboard."
