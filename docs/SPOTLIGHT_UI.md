# Mutsu OS Search — Spotlight-style overlay (prototype)

The everyday launcher is now a **compact, undecorated GTK4 window** instead
of a full-size AI chat application. The intended interaction is deliberately
familiar to someone coming from macOS Spotlight.

## Behavior now implemented

- Open the launcher with its GNOME shortcut: **Super+Space** (usually
  Command+Space on a Mac keyboard), or select Mutsu OS from the app menu.
- An empty search is just a **single translucent input field**—no titlebar,
  permanent chat transcript, provider selector, dock settings or onboarding
  buttons are visible.
- Type an installed app name to see a small list of up to **five** matching
  applications under the field. **Enter** opens the selected app, closes the
  launcher after the desktop reports the launch request, and does not call AI.
- If there is no matching application, **Ask AI** appears as a full-sized selected row (not a tiny footer) and ordinary **Enter** invokes the chosen assistant. An Ask AI option is also available underneath app matches. Nothing is sent while typing. Answers expand below the field only on request. A special Ctrl+Enter shortcut is no longer needed.
- **One-time opt-in:** the AI connection step of setup and Spotlight Settings
  offer a checkbox to allow questions/diagnostics to be sent to the chosen
  model. This permission defaults OFF and can be revoked at any time. Once
  enabled there is **no per-query privacy popup**. Unchecked means no model
  requests, including to a locally configured model; offline search still works.
- AI-proposed changes still show **Apply change / Decline** controls, even
  when model permission has been approved. Actions remain bounded by
  the project's approved tool catalog.
- **Escape** closes Spotlight. Clicking another application or the desktop **closes an idle launcher** so later Super+Space launches a fresh process; an in-flight AI request or pending approval hides temporarily instead of being abandoned. The settings popover is exempt. Arrow keys select app or AI results, and a new search collapses the previous answer.
- A subtle settings icon inside the bar (or **Ctrl+,** / **Command+,**) opens provider and
  appearance choices plus a **Setup & keyboard settings…** entry. The full
  original setup wizard remains a separate window via `--setup`.

The search results no longer render an opaque default Gtk.ListBox, GtkViewport or scroll container; Japandi selection uses soft sage, while Cyberpunk uses an angular magenta/cyan highlight. This style change also removes old window-level CSS providers on close, preventing stacked-outdated themes after re-opening the wizard or launcher. These changes require VM validation.

### Translucency and placement limitations

The background uses alpha-composited GTK4 CSS rather than an opaque top-level
window. Japandi remains warm and rounded; Cyberpunk uses a dark angular
panel with cyan neon outlines; System uses a neutral dark translucent bar.
GNOME high-contrast settings instead get a readable opaque fallback. The
Japandi background can now follow the theme selection using the uploaded
Mutsu wallpaper; System restores the prior GNOME background when possible.

**This is not yet a true GNOME Shell Spotlight overlay.** A normal GTK4 app
cannot guarantee the Mac's precise centered/top-third placement, compositor
background blur, focus behavior over fullscreen games, or being present on
every workspace. GTK4 transparency and undecorated windows are supported,
but compositor decisions can vary in VMware, VirtualBox, Wayland, and X11.

A future GNOME Shell extension should own positioning, focus, activation
and compositor integration, while the same Python application handles
the trusted search/AI backend. Never claim blur is already implemented.

### App search versus AI scope

Spotlight now searches real installed applications **and filenames** in a
bounded local scan of Documents, Downloads, Desktop, Pictures, Videos and
Music. The scan runs in a worker thread and searches only metadata/filenames:
no file contents, symlinks, hidden directories, arbitrary mounted drives or
cloud results are indexed. File hits open with their registered GNOME
application. Full GNOME Tracker integration, metadata dates, file contents,
Steam game search and settings actions are future milestones. Newelle model inference is optional, and an installed-app
search remains usable when it is offline.

### Test in a GNOME VM

    cd ~/ai-desktop
    git pull
    bash scripts/run-dev.sh

Or reopen the wizard separately:

    bash scripts/run-dev.sh --setup

1. Open Spotlight: verify a single compact, translucent text field appears,
   without titlebar or permanent answer panel.
2. Type `files`; verify installed app matches appear below and arrow keys
   change selection.
3. Press Enter on a real installed application: it should launch and the
   Spotlight window should close.
4. Reopen, type a question and press **Enter**; verify that the AI fallback is selected. For offline tests, choose **Built-in (offline)** in Preferences before asking about audio, disk space or network status.
5. Search `mutsu` or an actual filename under Documents/Downloads/Pictures.
   Verify `Top Results`, `Files` and `AI Suggestions` headings appear
   only when there are matching real entries. Enter on a file should open it.
   Try `Explain this` or `Troubleshoot`: the chip must only prefill the
   search box; Enter is required for model inference.
6. Check that the answer and any approval buttons appear **only when needed**.
6. Type a new search: the prior response should collapse.
7. Open Preferences with the gear icon or Ctrl+, change theme, and verify
   Japandi/Cyberpunk translucent styling. Full setup should still open.
8. Open the gear icon and click **Setup & keyboard settings…**:
   Spotlight should hide only after the full wizard is visible. Close the
   wizard's red button or Finish: Spotlight should reappear and the new
   privacy/keyboard choices should still be saved.
9. Press Escape: launcher closes. Test Ctrl+, and Esc with the popover open.
9. Enable GNOME high-contrast mode: input, result rows and responses remain
   readable.
10. In your graphics-troubled VM, try:
       GSK_RENDERER=cairo LIBGL_ALWAYS_SOFTWARE=1 bash scripts/run-dev.sh
    Transparency/blur are compositor-dependent and may look different in a VM.

## Implementation files

- `src/aidesktop/ui.py` — compact field, conditional result/answer sections,
  privacy/approval flow, small settings popover and keyboard handling.
- `src/aidesktop/themes.py` — per-theme semi-transparent launcher CSS;
  existing setup wizard and Mac-style titlebar styling remain separate.
- `src/aidesktop/setup_wizard.py` — full setup experience unchanged.

The GNOME user-session launcher and Super+Space installer scripts are unchanged.

## Test Newelle end-to-end

Enable model sharing via Spotlight Settings, then click the gear icon →
**Test Newelle connection + reply**. This performs both a read-only model listing and a harmless short inference request via the configured Newelle GUI API. It sends no personal diagnostics, but can use a cloud model if you selected one in Newelle. From Terminal, the equivalent command is:

    bash scripts/run-dev.sh --test-newelle

If this fails, follow [NEWELLE_SETUP.md](NEWELLE_SETUP.md). Normal plain-text model replies are displayed as explanations; only validated structured action plans can invoke allowed tools with approvals.

### When Setup & keyboard settings doesn't open

GTK/Adwaita is a **single-instance app**. A hidden, still-running Spotlight
can retain earlier Python code after `git pull`; executing `run-dev.sh` by
itself may simply reactivate that old instance. Use the dev-only safe restart:

    cd ~/ai-desktop
    git pull
    bash scripts/restart-dev.sh

Then use the gear menu → **Setup & keyboard settings…**. The menu now
activates the `app.open-setup` GNOME application action, with an idempotent
`clicked` fallback. Setup is presented before Spotlight hides.

For a second independent test, while the newly restarted app is running,
open another terminal and execute:

    bash scripts/run-dev.sh --setup

Unlike the old local-only `force_setup` flag, `--setup` is now forwarded via
GApplication command-line handling to the **existing** process, so it opens the
full wizard even when Spotlight is already running.

A wizard-construction error is reported inline in Spotlight as
`Couldn't open Setup & keyboard settings`, and a Python traceback is printed
to the terminal. If either navigation path still fails, please report the
terminal traceback, excluding all API keys.
