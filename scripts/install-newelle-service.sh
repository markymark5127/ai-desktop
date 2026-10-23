#!/usr/bin/env bash
# Installs headless Newelle as a user service on a GNOME/Flatpak system.
# Only run after configuring a matching GUI-API key in Newelle itself.
set -euo pipefail

if ! command -v flatpak >/dev/null || ! command -v systemctl >/dev/null; then
  echo "This installer requires Flatpak and systemd --user." >&2
  exit 1
fi
if ! flatpak info io.github.qwersyk.Newelle >/dev/null 2>&1; then
  echo "Install Newelle first: flatpak install flathub io.github.qwersyk.Newelle" >&2
  exit 1
fi
config_root="$HOME/.config"
if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then config_root="$XDG_CONFIG_HOME"; fi
config_dir="$config_root/ai-desktop"
if [[ ! -s "$config_dir/newelle-token" ]]; then
  echo "Missing $config_dir/newelle-token." >&2
  echo "Set the same API key under Newelle > Settings > Interfaces > GUI API," >&2
  echo "then run: bash scripts/configure-newelle-key.sh" >&2
  exit 1
fi

unit_dir="$config_root/systemd/user"
mkdir -p "$unit_dir"
unit="$unit_dir/ai-desktop-newelle.service"
if [[ -e "$unit" ]]; then
  echo "Existing unit at $unit; refusing to overwrite custom configuration." >&2
  exit 1
fi
cat > "$unit" <<'EOF'
[Unit]
Description=Headless Newelle backend for Mutsu OS
Documentation=https://newelle.qsk.me/docs/Creating-Interfaces
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/flatpak run io.github.qwersyk.Newelle --interface gui-api
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now ai-desktop-newelle.service
echo "Installed and started user-scoped Newelle backend."
echo "Check: systemctl --user status ai-desktop-newelle.service"
echo "Test API: bash scripts/run-dev.sh --check-newelle"
echo "The backend host, port and key must be configured in Newelle's GUI API settings."
