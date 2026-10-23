# AI Desktop roadmap

## Phase 0: prototype (this commit)
- Native GNOME window, bounded model-driven tool calls, CLI, tests.
- Headless Newelle inference adapter as default (plus built-in, direct Ollama, OpenAI API and Anthropic API), authentication and optional systemd user service.
- Explicit per-request cloud consent; explicit change approval.

## Phase 1: genuinely helpful desktop assistant
- Offline instant app search and natural-language queries (app search implemented; indexed file search pending).
- Desktop application discovery by friendly name (implemented in search UI; agent tool exposes IDs internally).
- Compact undecorated, translucent Spotlight GTK launcher **implemented** (conditional app results and AI answers; preferences hidden). Exact GNOME Shell overlay positioning, native blur, fullscreen behavior and robust desktop-keybinding focus integration are still pending; reversible Super+Space shortcut already implemented. See [Spotlight UI](SPOTLIGHT_UI.md).
- Japandi/Cyberpunk/System theme selector and saved launcher preference implemented; OS-wide styling still pending.
- Standard US vs Mac US keyboard profile selector, displayed Super-key shortcut labels, opt-in reversible GNOME XKB source selection (implemented). Next: guided physical-key test and optional shortcut emulation, without globally swapping Ctrl/Cmd.
- **First-run wizard prototype now implemented:** launch on first run/--setup; skippable and reopenable from launcher. Includes app-search exercise, theme, Mac/PC keyboard and live key test, helper, optional Newelle check, GSConnect availability/pairing guidance, Steam detection. See [Onboarding](ONBOARDING.md).
- Reframe the first-run step as **"Your computer comes with a helping hand"**, not "select an AI model"; let users test Super+Space immediately. See [Helper Experience](HELPER_EXPERIENCE.md).
- Three user learning/explanation styles now stored and included in AI Desktop's prompt; no tool authorization or approval changes from style. Future: rich details UI, verified repair narratives.
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
