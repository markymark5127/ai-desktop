#!/usr/bin/env bash
# Store a matching Newelle GUI API key privately, without typing it as an argument.
set -euo pipefail
if [[ ! -t 0 ]]; then
  echo "Run interactively in a terminal to enter the GUI API token." >&2
  exit 1
fi
umask 077
config_root="$HOME/.config"
if [[ -n "$XDG_CONFIG_HOME" ]]; then config_root="$XDG_CONFIG_HOME"; fi
target_dir="$config_root/ai-desktop"
mkdir -p -m 700 "$target_dir"
chmod 700 "$target_dir"
read -r -s -p "Enter the key already configured in Newelle's GUI API: " api_key
printf '\n'
if [[ -z "$api_key" ]] || [[ "$api_key" == *$'\n'* ]]; then
  echo "The key must be nonempty and single-line." >&2
  exit 1
fi
tmp="$(mktemp "$target_dir/.newelle-token.XXXXXXXX")"
trap 'rm -f "$tmp"' EXIT
printf '%s\n' "$api_key" > "$tmp"
chmod 600 "$tmp"
mv -f "$tmp" "$target_dir/newelle-token"
trap - EXIT
unset api_key
echo "Token stored in $target_dir/newelle-token (permissions 0600)."
echo "This does not change Newelle's own API key; the two settings must match."
