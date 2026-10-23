#!/usr/bin/env bash
# User-session installation of the Mutsu OS desktop prototype.
# Intentionally DOES NOT write to /usr, install GNOME extensions or modify
# kernel/system images. It is safe on rpm-ostree/Bazzite GNOME.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
want_shortcut=0
if [[ "${1:-}" == "--with-shortcut" && "${#}" -eq 1 ]]; then
  want_shortcut=1
elif [[ "${#}" -ne 0 ]]; then
  printf 'Usage: bash scripts/install-desktop-experience.sh [--with-shortcut]\n' >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3 is required. Run this from a GNOME Linux desktop.\n' >&2
  exit 1
fi

if ! python3 -c 'import gi; gi.require_version("Gtk","4.0"); gi.require_version("Adw","1"); from gi.repository import Gtk, Adw' >/dev/null 2>&1; then
  printf 'Missing GTK4, libadwaita or PyGObject. Install the GNOME Python bindings before using Mutsu OS Search.\n' >&2
  exit 1
fi

bash "$repo_dir/scripts/install-local.sh"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/ai-desktop"
if (( want_shortcut )); then
  if [[ -f "$state_dir/gnome-shortcut.json" ]]; then
    printf 'Super+Space already configured; preserving the existing binding.\n'
    # Only relabel our own legacy entry. Never overwrite someone else's
    # shortcut, command or custom display name.
    python3 "$repo_dir/scripts/shortcut.py" --refresh-label || printf 'Existing shortcut label was left unchanged.\n'
  else
    python3 "$repo_dir/scripts/shortcut.py" --apply
  fi
fi

cat <<'INSTRUCTIONS'

Mutsu OS Search is installed in your USER session, without changing Bazzite's OS image.

Run or re-open the setup wizard:
  ~/.local/bin/ai-desktop --setup

Optional Spotlight (Super+Space / Mac Command+Space) shortcut:
  python3 scripts/shortcut.py --apply
Restore it:
  python3 scripts/shortcut.py --restore

For a permanent Mac-style dock and hiding the top-left Activities button:
  Open Extension Manager, install/enable Dash to Dock and (optionally) Just Perfection.
  Configure dock position/always visible on the Mutsu OS setup wizard's dock page.
  Hide only the Activities button in Just Perfection; keep the GNOME Overview available.

For optional headless Newelle:
  flatpak install flathub io.github.qwersyk.Newelle
  See docs/NEWELLE_SETUP.md to configure the authenticated localhost API.
  Then: bash scripts/configure-newelle-key.sh
        bash scripts/install-newelle-service.sh

GSConnect/KDE Connect:
  Choose iPhone/Android on the wizard's Phone page, scan the app-store QR,
  and open GSConnect preferences to pair your phone.

The Cyberpunk/Japandi appearance styles the Mutsu Search and setup windows,
not every GNOME/Flatpak application. A custom Bazzite system image remains
a separate build milestone.
INSTRUCTIONS
