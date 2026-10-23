# Mutsu OS development roadmap

## Phase 0: prototype (this commit)
- Native GNOME window, bounded model-driven tool calls, CLI, tests.
- Headless Newelle inference adapter as default (plus built-in, direct Ollama, OpenAI API and Anthropic API), authentication and optional systemd user service.
- Optional, persistent, revocable model-sharing permission (off by default); separately confirmed system-changing actions.

## Phase 1: genuinely helpful desktop assistant
- Offline installed-app and bounded local filename search implemented, grouped with an opt-in AI fallback. Persistent whole-disk/content indexing remains pending.
- Desktop application discovery by friendly name (implemented in search UI; agent tool exposes IDs internally).
- Compact undecorated translucent Spotlight GTK launcher **implemented**: app matches plus visible Ask AI fallback; ordinary Enter asks AI when no match; idle focus-loss closes the launcher; in-flight work retains the hidden window. Full GNOME Shell overlay, native blur and fullscreen focus behavior remain pending. See [Spotlight UI](SPOTLIGHT_UI.md).
- Japandi/Cyberpunk/System theme selector and saved launcher preference implemented; explicit theme selection can apply uploaded Mutsu OS wallpapers with a reversible GNOME backup. Full OS-wide styling is still pending.
- Standard US vs Mac US keyboard profile selector, displayed Super-key shortcut labels, opt-in reversible GNOME XKB source selection (implemented). Next: guided physical-key test and optional shortcut emulation, without globally swapping Ctrl/Cmd.
- **First-run wizard prototype now implemented:** launch on first run/--setup; skippable and reopenable from launcher. Includes app-search exercise, theme, Mac/PC keyboard and live key test, helper, optional Newelle check, GSConnect availability/pairing guidance, Steam detection. See [Onboarding](ONBOARDING.md).
- Reframe the first-run step as **"Your computer comes with a helping hand"**, not "select an AI model"; let users test Super+Space immediately. See [Helper Experience](HELPER_EXPERIENCE.md).
- Three user learning/explanation styles now stored and included in Mutsu OS's prompt; no tool authorization or approval changes from style. Future: rich details UI, verified repair narratives.
- Newelle setup guided by documentation today; next build in-app onboarding, provider status/selection and a privacy-aware first-run wizard.
- Develop a unified **Open / Do / Get help** omnibox with indexed file/settings/game search, deterministic typed tools, multi-step verified troubleshooting and graceful unsupported-action handling.
- Conversation state, explanation of troubleshooting, verifiable fixes and undo.

## Phase 2: safe system agent
- Privilege-separated action service, Polkit, audit log, transactions.
- Model-independent capability registry and per-tool privacy controls.
- Structured provider-native tool calls, redaction, sensitive-data minimization.
- Test suite against real/virtual Linux failure scenarios.

## Adaptive Desktop on convertibles (planned; flagship OS feature)

See [Adaptive Desktop design and implementation specification](ADAPTIVE_DESKTOP.md). This is **not yet implemented** in the assistant, welcome wizard, GNOME extension or Bazzite image.

- Detect real convertible/tablet posture from kernel/libinput tablet switches when supported; distinguish orientation from posture; add manual mode toggle and safe fallback.
- Implement a GNOME Shell-owned touch-first **Home/app grid**, invoked when folded; traditional desktop remains available but secondary.
- Design bottom-edge swipe to Home, hold for multitasking, and app/window navigation without breaking GNOME's existing bottom-edge on-screen keyboard gesture.
- Maximize launched apps by default where appropriate; retain running windows, notifications, OSK, rotation lock and accessible shell controls.
- Add responsive larger icons, text and touch targets with separate touch presets layered over Japandi/Cyberpunk/System; honor accessibility preferences.
- Restore laptop dock/window/scale behavior when unfolding without overwriting changed user settings; handle suspend/resume and unreliable switches.
- Evaluate Touchshell/TouchUp as GNOME-version-pinned prototypes, avoiding conflicting gesture extensions; test on actual Yoga-class hardware rather than assuming VM detection.

## Mutsu OS system-wide branding

- [x] Centralize product name and user-visible Mutsu Search app label
- [x] Install primary Mutsu emblem as a user-scoped app icon when uploaded
- [x] Add read-only SVG inventory and three core icon filename requirements
- [x] Scaffold *experimental, opt-in* Bazzite GNOME-derived image overlay for Mutsu OS name/LOGO, GDM greeter mark and wallpaper assets
- [ ] Upload the approved circular symbol, monochrome symbolic logo, and horizontal wordmark SVGs to `assets/icons/`
- [ ] Boot-test image, GNOME About and GDM login in a disposable VM with upstream-compatible updates/rollback
- [ ] Create and integrate an approved Plymouth boot splash from the existing two-wave mark
- [ ] Brand the installer/ISO, GNOME Shell top bar and tablet Home without breaking the existing session or upstream attribution

See [system-branding build guide](../packaging/mutsu-image/README.md) and [icon inventory](../assets/icons/README.md).

## Mac-familiar desktop experience (cross-cutting milestones)
- Design for Mac-to-Linux migration and Steam/Proton gaming; see [Product vision](PRODUCT_VISION.md).
- Reversible Mac dock configurator now implemented for an already enabled Dash to Dock GNOME extension (Bottom/Left/Right/Top, always-on default, Show Applications/Launchpad grid). The install wizard page is included. See [DOCK.md](DOCK.md).
- Evaluate/automate compatible Dash to Dock and tiling extensions, GNOME Overview, Activities-label hiding via Just Perfection, and Sushi previews, with version-specific Shell testing.
- Provide optional GSConnect device pairing. KDE Connect iOS lacks full background connectivity, iMessage/SMS and system notification mirroring; never advertise AirDrop/Continuity feature parity.
- First-run GTK wizard prototype built with appearance, physical key test, AI connection check, phone/GSConnect guidance and installed Steam check. Still need actual pairing UI, guided local model install, file migration, dock/window tiling configuration, game diagnostics and dedicated Bazzite first-login integration.
- Preserve a standalone GNOME install path; only create a Bazzite-derived image after real UX and native gaming QA.

## Phase 3: app ecosystem
- MCP broker, capability manifests, discovery, permission settings.
- Flatpak storefront integration instead of breaking compatibility with existing apps.
- MPRIS music history via an optional local history collector.
- Gaming integrations for Steam/Proton, controllers, audio, GPU diagnostics.

## Phase 4: distribution
- Signed Bazzite GNOME-derived atomic image, AMD/Intel/NVIDIA variants.
- First-run setup, automatic updates, recovery/rollback guidance.
- iPhone pairing, files and clipboard where iOS supports it; Mac bridge for iMessage.
- Nontechnical user testing and accessibility review.
