# AI Desktop roadmap

## Phase 0: prototype (this commit)
- Native GNOME window, bounded model-driven tool calls, CLI, tests.
- Built-in, Ollama, OpenAI API, Anthropic API.
- Explicit per-request cloud consent; explicit change approval.

## Phase 1: genuinely helpful desktop assistant
- Offline instant app search and natural-language queries (app search implemented; indexed file search pending).
- Desktop application discovery by friendly name (implemented in search UI; agent tool exposes IDs internally).
- GNOME Shell overlay still pending; opt-in, reversible Super+Space GSettings binding implemented.
- Conversation state, explanation of troubleshooting, verifiable fixes and undo.

## Phase 2: safe system agent
- Privilege-separated action service, Polkit, audit log, transactions.
- Model-independent capability registry and per-tool privacy controls.
- Structured provider-native tool calls, redaction, sensitive-data minimization.
- Test suite against real/virtual Linux failure scenarios.

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
