# Architecture and security constraints

## Design

GNOME/libadwaita GUI (Japandi/Cyberpunk/System themes) -> provider-independent Agent -> explicit tool registry -> OS.

The prototype is a GNOME **application** with a future Shell extension. The proposed [Adaptive Desktop](ADAPTIVE_DESKTOP.md) is a **GNOME Shell integration** layered on the same session; it will respond to reliable libinput tablet posture events to show app-grid Home, touch navigation, maximize-on-launch and reversible appearance presets, without creating a separate window manager or app launcher. It is not a custom GNOME fork or a new desktop environment. A customized signed Bazzite GNOME OS image may be built later for distribution, preserving the reusable desktop assistant as a standalone app.
Inference providers: **headless Newelle GUI API** (default), built-in routing, optional direct local Ollama, OpenAI API and Anthropic API. Newelle is separately installed and managed via a systemd user service (optional).

## Current prototype

- Read-only diagnostics: system snapshot, audio, NetworkManager state, user warning logs, Flatpak application list.
- Approved actions: launch a desktop application, change an existing default PulseAudio/PipeWire sink.
- Four maximum agent planning steps per query; no free-form terminal commands.
- GTK operations only on the GTK thread; inference runs on worker threads.
- Newelle and cloud model selections ask for confirmation for each request; configured Newelle models may be local or cloud.
- Newelle adapter accepts only loopback 127.0.0.1 on a validated port and requires a configured API token. Only /v1/models and /v1/chat/completions are called. The full Newelle agent API is not used.

## Security limitations / TODO

- Cloud providers receive prompts and tool output, including potentially sensitive log lines, with one per-request consent. A production edition needs per-tool data-sharing decisions and redaction.
- Direct providers currently rely on environment variables instead of GNOME Secret Service/Keyring. Newelle key is stored in a user-private config file or environment. A shared localhost service can still pose a security risk.
- Actions are restricted, but no general permission broker or audit log exists yet.
- Approved AI-driven actions are now logged (timestamp, tool name and status only) to a user-private JSONL history file, with no prompts or tool outputs. Automatic rollback is not yet implemented.
- No MCP application adapters, polkit helper, rollback, App Store, distro image or iPhone companion yet.
- No arbitrary shell tool should be exposed to models.
- Do not run this prototype as root. Test first in a disposable VM.

## Next milestones

1. GNOME Shell keybinding/overlay integration and app/file indexed search.
2. Structured tool calling instead of prompting for JSON action plans.
3. Durable per-tool permissions, audit trail, change validation, rollback support.
4. MCP broker with trusted application capability manifests.
5. GNOME keyring credentials, supported account-auth flows and redaction.
6. Gaming tools and Bazzite GNOME image customization.
7. Phone continuity integration where iOS allows it.
8. Adaptive Desktop hardware posture bridge and GNOME Shell touch-first Home, with manual override, accessibility preservation, reversible desktop state and physical convertible QA.
