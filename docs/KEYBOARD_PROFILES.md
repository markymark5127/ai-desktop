# Keyboard choices: standard English (US) and Mac English (US)

The finished first-run wizard asks which **physical keyboard** the user has.
AI Desktop's launcher has an early implementation of the same choice now.

| Option | Keyboard labeling | Spotlight shortcut | GNOME layout option |
| --- | --- | --- | --- |
| Standard English (US) | Windows / Super | **Win + Space** | English (US), XKB us |
| Apple / Mac English (US) | ⌘ Command / Super | **⌘ + Space** | English (Macintosh), XKB us+mac |

**Important:** On a typical Apple keyboard connected to Linux, pressing
**⌘ Command already produces Super**. GNOME recognizes the Apple keyboard's
Command key as the usual Super key. The Mac English (US) XKB symbols variant
adjusts the key-symbol layout, but it is **not** a guaranteed physical modifier
remap. If a VM or unusual keyboard sends Alt for Command, choosing a profile
alone cannot force that hardware/host-level mapping. Verify on actual hardware
before shipping a keyboard remap.

## Current implementation

- The keyboard selector is in the AI Desktop launcher. Changing it saves a
  user-scoped preference and adjusts shortcut labels. It does **not** silently
  change system-wide input settings.
- Click **Apply layout to GNOME** to opt into the English US/Mac variant.
  A confirmation warns about the change. Existing keyboard languages and
  input sources are **preserved**, and the selected variant moves to the first
  slot. GNOME may require switching to the selected source if another is active.
- Click **Restore layout** to put your previous list of GNOME input sources
  back. The first application stores a backup in the user's XDG state folder,
  and subsequent selections do not overwrite that initial backup.
- The choice never globally changes **Ctrl+C/Ctrl+V**, terminal signals, or
  per-application shortcuts. Those are deliberate GNOME/Linux conventions.
  Optional Mac-style *application shortcut emulation* is a separate future
  feature with per-app testing and an explicit opt-in.

The persisted profile lives at
\`~/.config/ai-desktop/keyboard.json\` (or \`$XDG_CONFIG_HOME\`).
The reversible GNOME source backup lives at
\`~/.local/state/ai-desktop/keyboard-sources-backup.json\` (or \`$XDG_STATE_HOME\`).

These are private per-user files, and no root privileges are involved.

## Spotlight binding

After installing AI Desktop, the opt-in shortcut script binds **Super+Space**
to the launcher. That means **Win+Space** on a standard PC keyboard or
**⌘+Space** on a Mac keyboard whose Command key is already mapped to Super.

    bash scripts/install-local.sh
    python3 scripts/shortcut.py --apply

To restore GNOME's prior shortcuts:

    python3 scripts/shortcut.py --restore

This intentionally takes over GNOME's default input-source switch shortcut.
If you use several languages, select an alternate input-source shortcut in
GNOME Settings. Switching the AI Desktop keyboard profile does not change
that binding: only the displayed name of the physical Super key changes.

## VM testing

Test *both* selections in Fedora GNOME or Bazzite GNOME:

- Press Win+Space inside a Windows-hosted VM.
- Test a real Apple keyboard with ⌘+Space if possible. The Windows host or
  hypervisor may intercept/remap the physical Command key before Linux sees it.
- Check that another input language stays available after applying US Mac.
- Use Restore, and verify the exact previous input-source list returns.
- Check Terminal: Ctrl+C still interrupts; Ctrl+V still works in usual apps.
- Confirm that choosing Mac does not swap left Alt and Command unexpectedly.

If an actual Apple keyboard fails to send Super, offer a **separately
confirmed modifier-mapping repair**, with per-device troubleshooting. Do not
force an XKB Alt/Win swap merely because the user selected a Mac keyboard.

## Future onboarding

1. Show clear images/labels for **Windows/Super** and **⌘ Command** keys.
2. Ask **Mac keyboard or standard English (US) keyboard?**
3. Let the user test the desired shortcut before applying any keymap changes.
4. Apply the matching GNOME input layout only after permission, preserving
   existing languages.
5. Teach the user how GNOME app shortcuts differ from macOS. Later offer
   optional, compatible application-level Mac-shortcut remaps without breaking
   games, Steam Input or shells.
