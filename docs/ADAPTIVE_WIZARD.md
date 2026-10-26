# Adaptive Desktop wizard page

The first-run setup wizard gains an **Adaptive Desktop** step for 2-in-1 / convertible machines.

## What the page does

- Explains MacBook-like desktop vs iPad-like app-grid Home.
- Offers three modes:
  - **Automatic** — use the hardware tablet-mode signal when available.
  - **Always Desktop** — stay in the normal Mac-like desktop.
  - **Always Tablet** — force tablet mode.
- Writes the choice to `org.gnome.shell.extensions.mutsu-adaptive` via `gsettings` when the extension is installed.
- If the extension is missing, the page explains that and does not fail.

## Implementation

- Helper: `src/aidesktop/adaptive_prefs.py`
- The wizard page itself is added in `setup_wizard.py` (see the PR).

## Notes

- This is a preference only. Real posture detection still depends on the Shell extension and hardware `SW_TABLET_MODE`.
- Gestures remain off unless the user enables the experimental setting in the extension.
