# AI Desktop roadmap

## Phase 0: prototype (this commit)
- Native GNOME window, bounded model-driven tool calls, CLI, tests.
- Headless Newelle inference adapter as default (plus built-in, direct Ollama, OpenAI API and Anthropic API), authentication and optional systemd user service.
- Explicit per-request cloud consent; explicit change approval.

## Phase 1: genuinely helpful desktop assistant
- Offline instant app search and natural-language queries (app search implemented; indexed file search pending).
- Desktop application discovery by friendly name (implemented in search UI; agent tool exposes IDs internally).
- GNOME Shell overlay still pending; opt-in, reversible Super+Space GSettings binding implemented.
- Japandi/Cyberpunk/System theme selector and saved launcher preference implemented; OS-wide styling still pending.
- Standard US vs Mac US keyboard profile selector, displayed Super-key shortcut labels, opt-in reversible GNOME XKB source selection (implemented). Next: guided physical-key test and optional shortcut emulation, without globally swapping Ctrl/Cmd.
- Reframe the first-run step as **"Your computer comes with a helping hand"**, not "select an AI model"; let users test Super+Space immediately. See [Helper Experience](HELPER_EXPERIENCE.md).
- Add three optional learning/explanation styles; never change action approval policy based on style.
- Newelle setup guided by documentation today; next build in-app onboarding, provider status/selection and a privacy-aware first-run wizard.
- Develop a unified **Open / Do / Get help** omnibox with indexed file/settings/game search, deterministic typed tools, multi-step verified troubleshooting and graceful unsupported-action handling.
- Conversation state, explanation of troubleshooting, verifiable fixes and undo.

## Phase 2: safe system agent
- Privilege-separated action service, Polkit, audit log, transactions.
- Model-independent capability registry and per-tool privacy controls.
- Structured provider-native tool calls, redaction, sensitive-data minimization.
- Test suite against real/virtual Linux failure scenarios.

## Mac-familiar desktop experience (cross-cutting milestones)
- Design for Mac-to-Linux migration and Steam/Proton gaming; see [Product vision](PRODUCT_VISION.md).
- Evaluate compatible Dash to Dock and tiling extensions, GNOME Overview and Sushi file previews, with version-specific Shell testing.
- Provide optional GSConnect device pairing. KDE Connect iOS lacks full background connectivity, iMessage/SMS and system notification mirroring; never advertise AirDrop/Continuity feature parity.
- Build first-run wizard with appearance/layout, shortcuts, AI/privacy settings, optional phone pairing, Mac files/app migration and basic Steam setup.
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
