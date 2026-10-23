# Testing AI Desktop inside Windows (VMware + Fedora GNOME)

This is the recommended **development** environment. It lets you validate
the launcher, keyboard shortcut, themes, Newelle integration, and basic Linux
diagnostics without repartitioning your Windows computer or changing Bazzite
on any existing gaming hardware. It is NOT a valid GPU/gaming performance test.

## 1. Host and guest

- Windows host: install [VMware Workstation Pro](https://knowledge.broadcom.com/external/article/368667/download-and-license-free-vmware-desktop.html).
  Workstation Pro 26H1 is free and available through Broadcom's portal.
- Linux guest: download [Fedora Workstation 44 (x86_64)](https://fedoraproject.org/workstation/download/).
- Create a new Linux/Fedora 64-bit virtual machine with the ISO attached.
- Use **UEFI**, **4 vCPUs**, **8 GB RAM**, **80 GB virtual disk** (growable),
  **NAT** networking and **3D acceleration** to start. On a Windows machine
  with only 16 GB RAM, allocate 4–6 GB to the VM instead.
- Take a VM snapshot named `clean-fedora` immediately after setup.
- If GNOME graphical rendering is corrupted or sluggish, try adjusting the
  virtual display/3D setting. VMware's virtual GPU is *not* your host GPU.

Fedora rather than Bazzite is recommended at first because its GNOME
dependencies are straightforward and you can focus on the launcher and AI
features. Repeat the test with a Bazzite GNOME guest or physical install later
to catch Flatpak/atomic-system differences.

## 2. Install desktop development requirements

Inside the Fedora guest, open Terminal:

```bash
sudo dnf upgrade --refresh -y
sudo dnf install -y git python3-gobject gtk4 libadwaita open-vm-tools-desktop
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); from gi.repository import Gtk, Adw; print('GNOME libraries ready')"
```

This VM setup uses host-installed GTK/GObject rather than trying to pip-install
PyGObject on Windows.

## 3. Pull AI Desktop and exercise it offline

```bash
git clone https://github.com/markymark5127/ai-desktop.git
cd ai-desktop
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash scripts/run-dev.sh --search steam
bash scripts/run-dev.sh --ask "system info" --provider builtin
bash scripts/run-dev.sh
# Reopen the welcome guide at any time
bash scripts/run-dev.sh --setup
bash scripts/run-dev.sh --setup-status
```

The **first launch automatically opens the skippable welcome wizard**.
Work through the theme, keyboard, helper, Newelle status, GSConnect and Steam
steps. To re-open it later, press Ctrl+, in the search bar (or click the small preferences icon) and choose **Setup & keyboard settings…**. See
[ONBOARDING.md](ONBOARDING.md) for the regression checklist and exact privacy
boundaries.

- Launch the regular AI Desktop window and verify it is **only a translucent search field**, not a large chat app, with no permanent titlebar or transcript. See [SPOTLIGHT_UI.md](SPOTLIGHT_UI.md).
- Search for a GNOME application by name. Type a few letters; matches expand below the field; press Enter and verify the app starts and Spotlight closes.
- Open preferences (gear / Ctrl+,), select **Built-in (offline)**, and try "my sound is not working" with Ctrl+Enter; verify the result appears below the field only on request.
- Change the appearance between **Japandi**, **Cyberpunk**, and **System**, using Spotlight preferences or the setup wizard. Check that the bar remains compact/translucent; Japandi should retain rounded edges and Cyberpunk should have angular neon outlines. Cyberpunk should show square neon-outlined controls; Japandi should retain its original soft rounded controls.
- Scroll to the bottom of a long wizard page, select **Continue**, then **Back**; each new page should start at the top (including after the slide transition).
- Check that the colored Mac titlebar controls are **small true circles** and that close, minimize and maximize work.
- Verify left-side colored stoplight controls on both setup and launcher; apply/revert the GNOME-wide button-layout option and inspect Files/Settings.
- In the Phone step select iPhone and Android and scan the local QR codes; verify the official KDE Connect store listings. Choosing Later hides the QR; see [Window and phone setup](WINDOW_AND_PHONE_SETUP.md).
- In the Mac-style dock step, check for Dash to Dock. If present and enabled, apply Bottom + Always show, verify dock visibility and the Show Applications grid, test the Left/Right/Top positions, then Restore; see [DOCK.md](DOCK.md).
- Restart the window and confirm that your choice was saved.
- Select **Mac US · ⌘ Command**, then **Apply layout to GNOME** and verify it offers the English (Macintosh) source without removing other languages.
- Press **Restore layout** and verify the previous input-source list returns. See [Keyboard Profiles](KEYBOARD_PROFILES.md).

For application launching, only installed desktop applications should appear
and no model call should be needed.

## 4. Install the Spotlight shortcut (optional)

```bash
bash scripts/install-local.sh
python3 scripts/shortcut.py --apply
```

Press **Super+Space** (Win+Space on a PC keyboard, ⌘+Space on most Apple keyboards). The window should appear without opening Newelle's UI. On a Windows-hosted VM, physical Mac modifier behavior can be intercepted by the host/hypervisor; verify on actual Apple hardware later.
This replaces GNOME's usual Super+Space input-source action while enabled.

To restore the original shortcut:

```bash
python3 scripts/shortcut.py --restore
```

Take another snapshot named `desktop-search-working`.

## 5. Add headless Newelle

Install Newelle and follow
[NEWELLE_SETUP.md](NEWELLE_SETUP.md) to select a model and configure its
localhost GUI API **with a key**. Then:

```bash
bash scripts/configure-newelle-key.sh
bash scripts/install-newelle-service.sh
bash scripts/run-dev.sh --check-newelle
bash scripts/run-dev.sh
```

The API model is configured inside Newelle, but AI Desktop remains the only
window for normal use. Enable AI Desktop's Newelle provider and ask a
non-sensitive question, for example "What audio devices are available?"

If Newelle uses a model on the host computer, networking and API exposure
need a separate security design; the current AI Desktop adapter **only**
accepts loopback inside the VM. Do not weaken the bind address to expose its
privileged GUI API over the LAN.

## 6. Regression checklist

- [ ] Fedora and GNOME boot reliably; mouse/keyboard shortcuts work
- [ ] App search results appear immediately without starting a model
- [ ] Enter opens an app; Ctrl+Enter uses the selected AI backend
- [ ] Both design themes display readable text and useful selection contrast
- [ ] Super+Space activates the window and can be reverted
- [ ] Clicking another app/desktop closes an idle Spotlight, and the next shortcut opens a fresh working launcher; an in-flight AI request hides without losing its response
- [ ] Japandi installed-app and AI-only results have no white list/viewport; AI-only appears as a full-sized row without a tiny footer
- [ ] Filename search shows only real local Documents/Downloads/Pictures hits under Files, and opens selected files via GNOME default handler
- [ ] Two AI suggestion chips prefill a prompt without sending anything until Enter
- [ ] Selecting Japandi or Cyberpunk uses the uploaded Mutsu 4K wallpaper, while selecting System restores the previous user wallpaper (if not manually edited)
- [ ] Reopening Spotlight or the wizard repeatedly does not stack stale CSS providers or recolor results
- [ ] Enter on unmatched query asks AI; Enter on app result launches; nothing is sent while typing
- [ ] Model sharing defaults OFF for a new user and older configurations, blocking Newelle/Ollama/cloud inference without a popup
- [ ] Set model-sharing checkbox in setup or Settings, ask several questions without any per-query privacy popup, revoke and verify later AI calls are blocked
- [ ] Revoking model sharing does not affect installed app searches or built-in offline diagnostics
- [ ] Newelle --check-newelle and --test-newelle distinguish API availability from working inference (test requires opt-in)
- [ ] Offline diagnostics work when Newelle is stopped
- [ ] `bash scripts/restart-dev.sh` stops any old hidden AI Desktop Python instance without stopping Newelle, then launches the latest code
- [ ] Spotlight gear → Setup & keyboard settings activates the GNOME app action and opens the full wizard
- [ ] `bash scripts/run-dev.sh --setup` opens the wizard even while the updated Spotlight process is already running
- [ ] Closing setup via window close or Finish returns to the same Spotlight launcher
- [ ] Changing model-sharing permission in setup is reflected in Spotlight preferences after return
- [ ] An intentional wizard construction error surfaces a visible message and traceback instead of disappearing
- [ ] Newelle headless user service reconnects after VM reboot
- [ ] Approved action requires an actual click; declining makes no change
- [ ] `--history` records approved actions but not prompts or secrets
- [ ] Model-unavailable and wrong-key errors are understandable

## 7. When a VM is not enough

Test on physical AMD, Intel and NVIDIA PCs for: graphics drivers, sleep,
controller recognition, Steam Input, Proton compatibility, gaming performance,
Bluetooth, battery/power management, and real-world audio devices.

A Bazzite-derived image and bootable installer should come only after the
GNOME user experience survives these initial tests.
