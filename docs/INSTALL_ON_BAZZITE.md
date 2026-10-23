# Install the Mutsu OS desktop prototype on Bazzite GNOME

This is a **user-level prototype install**, not yet a separately installable
Bazzite-derived OS image. Everything in the repository that has an actual
working integration can be enabled on an existing Bazzite GNOME machine or
Fedora GNOME VM. No rebase, package layering, root access or custom ISO is
required to install the launcher.

## 1. Install Mutsu OS and its keyboard shortcut

Run inside a GNOME session:

    cd ~/ai-desktop
    git pull
    bash scripts/install-desktop-experience.sh --with-shortcut

If you have not cloned the repo:

    cd ~
    git clone https://github.com/markymark5127/ai-desktop.git
    cd ai-desktop
    bash scripts/install-desktop-experience.sh --with-shortcut

The installer checks GTK4/PyGObject/libadwaita, creates an **Mutsu OS**
app-menu entry and user launcher under ~/.local/bin, then binds Super+Space
(opt-in, because it replaces GNOME's input-source switching shortcut).
Do not delete or relocate the cloned repository: the launcher points at
its Python source tree. To install the app without changing shortcuts, omit
--with-shortcut.

Launch the wizard:

    ~/.local/bin/ai-desktop --setup

On a Mac keyboard, physical Command normally sends Linux Super, so Spotlight
is Command+Space. On a PC keyboard it is Win+Space.

Restore the original keybinding at any time:

    python3 scripts/shortcut.py --restore

## 2. Appearance and Mac window controls

In **Appearance & keyboard**:

- Choose **Japandi**, **Cyberpunk**, or **System**. Japandi stays soft/rounded.
  Cyberpunk uses angular neon cyan/magenta outlines, darker pixel/terminal
  styling and a monospace fallback. Its optional pixel font is not bundled.
- Mutsu OS's own upper-left window controls are 13px circles and do not
  depend on changing GNOME's global style.
- If you want other *compatible GNOME apps* to move their window buttons to
  the left, click **Use left-side buttons in GNOME…** and approve. Use
  **Restore original buttons** to undo.

Not every GNOME/Qt/Flatpak/game window will have red/yellow/green circular
buttons: external apps have their own titlebar implementations. Our two GTK
windows are styled; the entire Bazzite desktop is **not yet themed**.

## 3. Persistent Mac-style dock and Launchpad app grid

Open **Extension Manager** in Bazzite GNOME (or install it from Flathub
if it is absent):

    flatpak install flathub com.mattjakeman.ExtensionManager

From Extension Manager, install and enable **Dash to Dock** (verify your
GNOME Shell version). In the setup wizard's **Mac-style dock** step:

- Set position to Bottom (default) or Left, Right, Top.
- Leave **Always show dock** enabled.
- Click **Check dock extension** and **Apply Mac-style dock…**.
- Verify the **Show Applications** dock icon opens the GNOME app grid,
  analogous to Launchpad.
- Use **Restore original dock settings** to revert.

To remove the top-left Activities label without destroying workspaces,
install compatible **Just Perfection** through Extension Manager and disable
**Activities Button** in its settings. GNOME's overview/gesture switching
continues to work.

**Extension stability:** some recent Dash to Dock releases have caused GNOME
Shell/Bazzite regressions. Take a VM snapshot, check extension compatibility,
and test before installing on your primary machine.

## 4. Phone integration

GSConnect is the *GNOME-side* KDE Connect integration. In the wizard's Phone
step, select iPhone or Android and **scan the offline QR** to get KDE Connect
from the official store on your phone. Then click **Open GSConnect preferences**
in the wizard, and follow pairing prompts on both devices while connected to
a compatible network.

iOS does not provide full AirDrop, iMessage/SMS or always-on background
Continuity; phone integration is optional.

## 5. Optional AI troubleshooting buddy (Newelle)

Installed-app search and built-in diagnostics work without Newelle. For more
advanced requests, install Newelle:

    flatpak install flathub io.github.qwersyk.Newelle

Open Newelle once; select a model and configure an authenticated **127.0.0.1**
GUI API on port **8081**, following [NEWELLE_SETUP.md](NEWELLE_SETUP.md).
Then from ~/ai-desktop:

    bash scripts/configure-newelle-key.sh
    bash scripts/install-newelle-service.sh
    bash scripts/run-dev.sh --check-newelle

Do **not** grant Newelle unrestricted terminal, D-Bus or home-directory access
just to make the prototype work. Mutsu OS uses model inference only and
retains its own system-action approvals.

## 6. Update, test, or remove

To get ongoing changes:

    cd ~/ai-desktop
    git pull
    bash scripts/run-dev.sh --setup

Run offline/headless tests:

    PYTHONPATH=src python3 -m unittest discover -s tests -v

To remove the launcher (not your saved appearance/learning preferences):

    rm -f ~/.local/share/applications/io.github.markymark5127.AIDesktop.desktop
    rm -f ~/.local/bin/ai-desktop

Restore the Spotlight shortcut **before removing the repo** with
`python3 scripts/shortcut.py --restore`; if you applied dock/button changes,
use their respective **Restore** buttons in the wizard.

## Still not included in the install

This user-scoped installer does *not* yet deliver a standalone distro,
OS-wide Japandi/Cyberpunk styling, custom GNOME Shell app-grid visuals,
automated compatible extension installation, full phone pairing, indexed
file/Settings/Steam game search, general AI repair automation, or a finished
Bazzite installer. Those need their own integration and testing before we can
truthfully claim that the full Mac-to-Linux distribution is installed.
