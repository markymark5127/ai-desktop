# Mac window controls and KDE Connect phone QR setup

The first-run wizard and AI Desktop launcher now use the **left-side**
Close, Minimize and Maximize headerbar layout and app-scoped red/yellow/green
traffic-light styling. This does not force other applications to adopt our CSS.

## Why GNOME apps still show controls on the right

GNOME controls titlebar button placement using a per-user preference. Run:

    gsettings get org.gnome.desktop.wm.preferences button-layout

The setup wizard's **Appearance & keyboard** page offers:

- **Use left-side buttons in GNOME…** — asks permission, backs up your original
  setting and applies close,minimize,maximize: through GNOME GSettings.
- **Restore original buttons** — restores the saved setting.

The backup is under the XDG state folder:
~/.local/state/ai-desktop/window-buttons-backup.json.
No root privileges or shell command expansion are required.

This setting affects GNOME/GTK applications and window decorations that
respect it. Some Flatpaks, Qt apps, games, Chromium/Electron apps and apps
with custom titlebars may use their own controls. **Colored stoplight buttons
are currently guaranteed only for the AI Desktop launcher and wizard,**
because the custom CSS is scoped to those windows. They are on the left even
if you do not apply the GNOME-wide preference.

An eventual branded Bazzite-derived image can ship a maintained
GTK/Qt/Shell appearance theme and test integrations. Do not globally overwrite
arbitrary GTK CSS files as a quick substitute.

## Edge-to-edge Japandi and Cyberpunk backgrounds

The setup window previously had outside margins on its **root content box**.
Only that inset box received the theme's background, exposing default white
Adwaita background around the edges.

The updated layout paints the toplevel window and the full-bleed root:
- Headerbar reaches the window edges.
- Padding is applied to an inner body box, not outside the root.
- Japandi, Cyberpunk and System appearances remain selectable.
- GNOME high-contrast accessibility settings override decorative colors.

## Pair an iPhone or Android phone by scanning

The **Phone pairing** step displays a scannable QR instead of a download
hyperlink:

- iPhone: the official KDE Connect App Store listing at
  https://apps.apple.com/us/app/kde-connect/id1580245991
- Android: KDE Connect on Google Play at
  https://play.google.com/store/apps/details?id=org.kde.kdeconnect_tp
- Skip: no QR shown

Both QR codes are **bundled and rendered offline** inside the GTK wizard.
They contain only these public store URLs: no QR-code service, network
connection, API key, account data or personal device identifier is involved.

**GSConnect runs on the GNOME desktop; KDE Connect is the phone app.**
The QR only installs the phone app. Actual pairing requires opening KDE Connect
on the phone and GSConnect on the desktop while on the same usable local
network. The wizard's **Open GSConnect preferences** button helps with
the GNOME part.

The QR matrices were independently checked with an image QR decoder and
returned the exact official store destinations. GTK layout changes still need
real VM testing.

## Quick VM validation

    cd ~/ai-desktop
    git pull
    bash scripts/run-dev.sh --setup

1. Verify Japandi fills the window without a white frame/padding gap.
2. Change to Cyberpunk and verify its dark background fills the window.
3. Check red/yellow/green controls on the top left of the wizard and launcher;
   closing, minimizing and maximizing should still work.
4. On Appearance & keyboard click **Use left-side buttons in GNOME…** and
   approve. Open GNOME Files/Settings: controls should move to the left.
5. Click **Restore original buttons** and confirm that GNOME goes back.
6. In Phone pairing choose iPhone and scan the QR; it should open the official
   App Store listing.
7. Choose Android and scan; it should open KDE Connect on Google Play.
8. Choose Skip; no QR should appear.
9. Test GNOME high-contrast mode and confirm controls stay readable.

Apps with independent titlebar implementations need separate QA.
