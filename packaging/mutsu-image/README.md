# Mutsu OS system-image branding (experimental)

This folder is the starting point for replacing **user-facing Bazzite
branding** in a future **Mutsu OS GNOME derivative image**. It is **not**
an instruction to change an existing Bazzite machine's immutable system
partition or blindly uninstall upstream packages.

**Source image:** Bazzite GNOME. Official guidance recommends deriving
through Universal Blue's [image template](https://github.com/ublue-os/image-template),
rather than replacing random logos in a running machine. This proof-of-concept
Containerfile can later be integrated with that build/signing/ISO workflow.

## What this image layer changes

| Surface | Intended Mutsu branding | Status |
| --- | --- | --- |
| Mutsu Search icon in app grid | Original Mutsu mark | Working as user-scoped install once SVG is present; image layer also includes it |
| GNOME Settings → About OS logo | Mutsu circular SVG via icon name in os-release | Image build configured; **not yet boot-tested** |
| Operating system display name | `NAME` / `PRETTY_NAME` set to Mutsu OS | Image build configured; **not yet boot-tested** |
| GDM login/greeter logo | Horizontal Mutsu wordmark via dconf system DB | Image build configured; **not yet boot-tested** |
| Preinstalled wallpapers | Your two 4K Mutsu PNGs | Image build stages them |
| GNOME Shell top-left logo, dock custom app-grid icon | Symbolic Mutsu artwork + future Shell extension/theme | Pending GNOME-version-compatible work |
| Plymouth boot animation/splash | Mutsu mark instead of Bazzite animation | Pending PNG + proper initramfs/testing |
| Installation ISO / first-boot branding | Mutsu identity | Pending custom bootc installer image |
| Full icon theme for third-party apps | Optional dedicated coherent icon theme | Not required for OS branding |

The build **does not** remove existing Bazzite/Fedora files, remove
`bazzite` RPM packages or override the bootloader with untested assets.
It leaves technical `ID`, `ID_LIKE`, `VERSION_ID` and package/update
identifiers untouched to help preserve Bazzite compatibility. Normal
system tools, Steam, KDE Connect, Flatpak and Bazzite updating must continue
to work.

**Attribution:** Source code/licenses and upstream Bazzite/Universal Blue/
Fedora credit should remain available in About/Help, release notes and
repository documentation even if the prominent product logo is Mutsu OS.

## Required artwork (not uploaded under these names yet)

Under `assets/icons/`, put your existing SVGs:

- `mutsu-logo-symbol.svg`: primary two-wave logo
- `mutsu-logo-wordmark.svg`: horizontal Mutsu OS wordmark
- `mutsu-logo-symbolic.svg`: monochrome GNOME top-bar/Quick Settings icon

The image layer requires the first two; the symbolic one is optional
until custom Shell integration. Exact roles for the theme variants and
optional boot/installer PNGs are in
[assets/icons/README.md](../../assets/icons/README.md).

Check status:

```bash
cd ~/ai-desktop
python3 scripts/check-brand-assets.py
```

## Building safely (no automatic switch)

Once the SVG files are ready, on a machine with Podman:

```bash
podman build \
  -f packaging/mutsu-image/Containerfile \
  -t localhost/mutsu-os:dev .
```

The `BASE_IMAGE` build argument defaults to
`ghcr.io/ublue-os/bazzite-gnome:stable`. Before publishing, match
your actual Bazzite GNOME variant/digest and base release, instead of
mixing incompatible images. The build intentionally fails with a
clear error if the core SVG assets are missing.

**Do not use `sudo bootc switch` to this experimental image on your
main Bazzite machine.** First build it through the supported Universal
Blue workflow, validate the exact GNOME version/OS release contents,
boot it in a disposable VM and verify GDM, GNOME About, login, updates,
rollback and app launching. Merely compiling a container is not proof
that a usable installer/bootable OS exists.

## Remaining system components

The Plymouth boot splash is the most important remaining *distinct*
artifact. Your source emblem should be rendered as a transparent
512px/1024px PNG and incorporated into a Plymouth theme, with image-based
boot/initramfs handling for the matching Bazzite release.

The installer/ISO also needs branding appropriate for its actual UI,
separately from GNOME Shell and GDM. The bootloader is intentionally
kept minimal; changing GRUB/EFI branding is not necessary for first
release and is high-risk on atomic systems.

On a currently installed Bazzite VM, the **supported initial test**
is the user-scoped Mutsu OS Search icon:
```bash
bash scripts/install-local.sh
```
No system-wide changes are made by that command.
