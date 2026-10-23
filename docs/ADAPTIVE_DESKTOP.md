# Adaptive Desktop: MacBook when open, iPad-like when folded

**Status: product goal and engineering specification; NOT IMPLEMENTED.**
This is a flagship feature for the Bazzite GNOME-derived distro, designed for
Lenovo Yoga-class 360° convertibles, 2-in-1s with detachable keyboards, and
conventional touch-screen PCs.

## Core promise

An Adaptive Desktop uses the **same applications, account and GNOME session**
in both modes. Laptop posture feels like a MacBook: persistent dock, resizable
windows, Spotlight, GNOME workspaces and predictable mouse/keyboard controls.
Tablet posture feels like a tablet: a **Home screen based on Show Applications**,
large touch targets, an unobtrusive gesture navigation surface, a reliable
on-screen keyboard, and apps that occupy the usable screen.

The desktop is not deleted or a separate session. Users can return to the
desktop at any time and unfolding the keyboard restores the desktop defaults.

## Mode transitions

### Automatic detection

When supported, use the **hardware-reported tablet posture**, not the absence
of keyboard events or a touchscreen alone:

- Kernel switch **EV_SW / SW_TABLET_MODE** is exposed through libinput's
  **LIBINPUT_SWITCH_TABLET_MODE**. libinput handles disabling/re-enabling
  integrated keyboard, touchpad and trackpoint on supported convertibles.
- Plan a small GNOME Shell extension (GJS) with a trusted OS/session bridge
  for detecting this state, because GNOME Shell owns Overview and app grid.
- Use supported orientation facilities (e.g. iio-sensor-proxy through the
  desktop) independently for rotation. Orientation is **not** proof of tablet
  posture. Do not guess posture from a screen rotation or from another keyboard
  being attached.
- Detachable devices may report posture differently; detect trustworthy
  hardware-specific inputs only after testing. If there is no reliable signal,
  expose a manual **Tablet Mode** toggle rather than silently assuming.
- Debounce switch transitions and tolerate suspend/resume, boot in tablet
  posture and rapid hinge changes. Transitions must be idempotent.

**Control:** Settings -> Adaptive Desktop -> Automatic / Always Desktop /
Always Tablet. In Automatic, a manual session-level override is available;
the user can turn off automatic transitions without unplugging devices.
Provide an accessible quick-settings toggle on devices with touch input.

### Laptop -> tablet

1. Detect a confirmed tablet-mode transition.
2. Save only settings the OS is actually about to change (per-user,
   reversible; do not overwrite other modifications).
3. Switch to a touch-target preset and larger effective text/icons.
4. Make the **Show Applications app grid** the main Home screen. On entering
   tablet posture, reveal Home rather than exposing an empty desktop.
5. Present a bottom gesture affordance; respect GNOME's existing on-screen
   keyboard and other reserved edge gestures.
6. Hide or collapse the desktop persistent dock in favor of tablet navigation.
7. For subsequently launched apps, maximize ordinary windows where practical
   (not indiscriminate fullscreen, which can hide access to notification,
   accessibility and system controls).
8. Keep existing app windows and workspaces running; do not force-close them.

### Tablet -> laptop

- Return to the familiar Mac-like desktop, dock, normal touch targets and
  scaling, **restoring pre-tablet values** when appropriate.
- Preserve running windows, app state and documents. Do not try to undo the
  entire session's window history or forcibly unmaximize apps the user
  intentionally changed.
- Restore keyboard and pointing-device access through the normal
  hardware/libinput mechanism.
- Never overwrite user-configured scaling, dock position or accessibility
  settings that changed while tablet mode was active. User settings and
  accessibility accommodations override automatic cosmetics.

## The tablet Home screen

GNOME's **Show Applications** grid is the base, but tablet mode must make it
the **primary entry point**, with larger grid tiles, sufficient spacing,
touch-friendly search, folders and predictable app launching. The GNOME
Overview/workspace switcher remains accessible, but the naked desktop is a
secondary destination.

Navigation design target:

| Interaction | Result |
| --- | --- |
| First fold to tablet | Open Home/app grid |
| One-finger upward swipe from bottom edge | Return to Home/app grid |
| Swipe up and hold | Multitasking / Overview |
| Horizontal multitouch swipe | Navigate open apps/workspaces |
| Tap large application tile | Open/maximize the app |
| Enter desktop option | Show traditional desktop for windowed work |
| External keyboard/trackpad used | Still permit keyboard/mouse navigation; do not automatically exit tablet mode solely because a Bluetooth keyboard is present |

**Important GNOME conflict:** GNOME's existing touchscreen bottom-edge swipe
can invoke the on-screen keyboard; GNOME normally exposes Overview/app grid via
three-finger upward gestures. Do not blindly bind both to the same gesture.
Prototype a compatible GNOME Shell gesture recognizer and test the onscreen
keyboard, edge swipe, full-screen games, notification shade, screen lock,
touch accessibility and navigation bar before calling the gesture supported.

An iPad-like Home is a **shell integration**, not opening the AI Desktop GTK
Spotlight app in a fullscreen window. Spotlight remains available via
touch search and keyboard.

## Touch-first visual scaling

Define a separate tablet appearance dimension on top of Japandi/Cyberpunk:
both looks must adapt without losing their character.

- Min target size approximately 44-48 logical pixels for primary touch
  actions, subject to real accessibility and GNOME scaling tests.
- Increase launch-grid icon sizes, labels, spacing, navigation and Settings
  controls; ensure controls remain reachable in portrait and landscape.
- Increase readable text size without destroying preexisting accessibility
  overrides; treat system text scaling as a user preference requiring careful
  save/restore semantics.
- The on-screen keyboard should appear for editable fields when in touch mode,
  and should not cover the field or consent dialog.
- Support auto-rotation where supported and sensible; allow rotation lock.
- GNOME/GTK adaptive/libadwaita apps should reflow with narrower screens.
  Don't claim every third-party Flatpak, Qt or game becomes genuinely
  touch-native or scales its text. Provide honest fallbacks.

## Architecture

Suggested separations:

1. **Posture signal adapter**: detect trustworthy kernel/libinput tablet
   switch, plus verified device-specific inputs and manual override.
2. **Session state controller**: Normal / Tablet / Transitioning, ownership
   of reversible user-level settings, and safety on crashes/resume.
3. **GNOME Shell integration**: Home app grid, navigation gestures, dock mode,
   workspace switching, Overview, new-app maximize behavior and touch chrome.
4. **Appearance adapter**: touch presets layered onto current
   Japandi/Cyberpunk/System. A responsive font-size scale does not require
   duplicating every theme asset.
5. **Settings/first-run wizard**: explain automatic switching, test it, and
   offer Manual / Automatic / Always Desktop / Always Tablet choices.

The system should never modify privileged keyboard settings, disable input
manually, create fake tablet posture events or force screen rotation simply
because the user taps the tablet-mode switch.

### Existing projects to evaluate, not blindly depend on

- **GNOME/libinput** already supports switch events and multitouch
  navigation (see reference links below).
- **Touchshell** is a GNOME 49/50 Wayland extension (as currently
  documented) with Auto/Always/Off support for tablet posture, improved edge
  gestures, fullscreen app mode and bottom navigation. Evaluate the design,
  compatibility and GPL license before reusing code or bundling it.
- **TouchUp** offers a tablet-style nav bar, touch gestures, on-screen
  keyboard additions and related options on supported GNOME versions.
- These extensions may conflict with Dash to Dock, Just Perfection,
  Gesture Improvements or each other. Choose one clear integration
  strategy and test it against the pinned Bazzite/GNOME release.

## Manual override, safety and accessibility

- Reliable **manual toggle** must work even without sensor/switch hardware,
  and should be available from the login session or quick settings.
- GNOME a11y settings, screen readers, large text settings and user preference
  must take precedence over automatic visual scaling.
- A mistaken hinge detection must never leave the user unable to type/click.
  GNOME's normal input and the standard desktop remain recoverable.
- Disable/suspend automatic UI transitions during certain gameplay or remote
  sessions if testing shows lost focus/surfaces; user override is primary.
- Do not intercept lock-screen gestures or system security confirmations.
- Bluetooth and USB keyboards are not direct evidence of laptop posture.

## Definition of done

Use **a real Lenovo Yoga convertible** and a second touch/2-in-1 hardware model,
along with Fedora GNOME VM for UI-only tests:

1. Start OS in laptop posture, confirm dock/window controls/Spotlight.
2. Fold keyboard back: hardware switch reliably triggers Home/app grid,
   larger touch controls and touch-friendly app windows.
3. Swipe up from bottom: Home, not merely a hidden desktop. Swipe-and-hold
   reveals multitasking, without stealing on-screen keyboard activation.
4. Open Files, Firefox, Settings, Steam and multiple windows. No documents
   close; apps remain usable in portrait and landscape.
5. Unfold: restore desktop dock/text defaults without sacrificing open apps.
6. Rapidly fold/unfold, suspend/resume, unplug keyboards, test tablet boot.
7. Disable auto-detection and manually switch in both directions.
8. Test screen reader/high contrast/large fonts; no regression.
9. Test Wayland GNOME and supported Bazzite device variants. Do not infer
   sensor and touch availability from a virtual machine.

## Sources

- libinput hardware switch documentation: https://wayland.freedesktop.org/libinput/doc/1.27.1/switches.html
- GNOME built-in touchscreen gestures: https://help.gnome.org/gnome-help/touchscreen-gestures.html
- Touchshell project: https://github.com/keithvassallomt/touchshell
- TouchUp GNOME extension: https://extensions.gnome.org/extension/8102/touchup/
