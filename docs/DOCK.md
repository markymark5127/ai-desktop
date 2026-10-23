# Mac-style dock on Bazzite GNOME

## What the finished desktop should do

The default desktop should feel familiar to macOS users, rather than hiding
installed/running apps inside GNOME's Activities overview.

- A **persistent** dock is visible on the desktop by default.
- Dock position is user-configurable: **Bottom** (default), **Left**, **Right** or **Top**.
- Auto-hide is an optional user choice, **off by default**.
- One dock button opens **Show Applications**, GNOME's full app grid (Launchpad-style).
- Other dock icons pin/open Files, browser, Steam, and frequently used applications.
- **Super+Space / ⌘+Space** independently opens AI Desktop's Spotlight/search.
- The top-left **Activities** button should be absent in the final distro. GNOME
  Overview/workspaces remain accessible by gestures or the Super key, so the
  user never *needs* to open the overview just to get to the dock.
- The top bar remains useful for the clock, connectivity, battery and sound.

This is a separate user-facing dock feature, not a new desktop environment.

## What's implemented in ai-desktop today

The GTK first-run wizard now includes a **Mac-style dock** page. It configures
**already installed and enabled** Dash to Dock GNOME Shell extensions through
their documented GSettings keys, after explicit user confirmation.

1. Install and enable a Dash to Dock extension compatible with the GNOME
   version on this machine. Open GNOME's **Extension Manager** to inspect what's
   already installed. [Dash to Dock](https://extensions.gnome.org/extension/307/dash-to-dock/)
   is the upstream project. Ubuntu Dock variants are also detected.
2. Open AI Desktop: \`bash scripts/run-dev.sh --setup\`.
3. On the **Mac-style dock** page, select the dock edge and optionally disable
   **Always show dock** if you prefer auto-hide.
4. Click **Check dock extension**, then **Apply Mac-style dock…**, and confirm.
5. The dock becomes persistent with an Applications grid button; the extension
   should make the dock available outside the overview.
6. **Restore original dock settings** returns the previous GSettings values
   using the per-user backup created when first applying.

No root privileges, package layering or OS image modifications are required to
configure an existing extension. No extension installation is automated.

GNOME extensions are version-sensitive. Bazzite [warns about compatibility and
Shell crashes](https://docs.bazzite.gg/General/Desktop_Environment_Tweaks/).
Recent Dash to Dock versions have user reports of GNOME/Bazzite graphical issues,
so **test in your VM and keep an enabled recovery path before shipping**.

## Hiding the top-left Activities label

The upper-left Activities text is *not* a traditional Windows Start menu; it
opens GNOME Overview/workspace switching. Once a persistent dock is working,
use an additional compatible GNOME Shell extension such as
[Just Perfection](https://extensions.gnome.org/extension/3843/just-perfection/)
and disable **Activities Button visibility** in its preferences.

This part remains **manual**, not yet programmatically set by the wizard:
compatibility varies across GNOME Shell versions, so we should not install
or change another extension without testing the target Bazzite image.

Do not hide the **Overview** itself. Mac users can still switch workspaces with
gestures and Super, just as with Mission Control.

## Technical settings

The typed settings are restricted to the Dash to Dock schema
\`org.gnome.shell.extensions.dash-to-dock\`.

| Key | Default Mac-like preset |
| --- | --- |
| \`dock-position\` | \`BOTTOM\` |
| \`dock-fixed\` | \`true\` |
| \`autohide\` | \`false\` |
| \`intellihide\` | \`false\` |
| \`manualhide\` | \`false\` |
| \`show-show-apps-button\` | \`true\` |
| \`show-apps-at-top\` | \`true\` |
| \`extend-height\` | \`false\` |

Applying a new preference never overwrites the first backup. It lives at
\`$XDG_STATE_HOME/ai-desktop/dock-backup.json\`, or
\`~/.local/state/ai-desktop/dock-backup.json\`. Restore replays each saved value
and removes the backup once successful. The code supports extensions whose
schemas live under ~/.local/share/gnome-shell/extensions.

The application *does not* implement a custom dock. It configures a
maintained GNOME Shell extension. More OS-level polish, icon styling,
position presets, and automatic installation will arrive only after a pinned
GNOME + Bazzite image is tested.

## VM test checklist

- [ ] In a normal GNOME session, enable Dash to Dock from Extension Manager.
- [ ] Run the first-run wizard and apply the Bottom + Always visible preset.
- [ ] Verify the dock appears **without entering Activities/Overview**.
- [ ] Click the Show Applications icon; confirm the GNOME app grid opens.
- [ ] Change position to Left, Right, Top, then back to Bottom.
- [ ] Verify pinned Files/Steam apps launch without opening the overview.
- [ ] Test full-screen application/game behavior and multi-monitor placement.
- [ ] Click Restore and confirm original settings return.
- [ ] Optional: use Just Perfection to hide only the Activities button.
- [ ] Verify workspaces/Overview still open with Super/gestures.
- [ ] Disable extension temporarily and verify desktop still works.

The first branded Bazzite image should pin extension versions, use user-scoped
defaults, and provide an obvious "Restore standard GNOME desktop" action.
