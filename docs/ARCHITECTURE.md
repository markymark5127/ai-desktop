# Architecture and security constraints

## Design

GNOME/libadwaita GUI -> provider-independent Agent -> explicit tool registry -> OS.
Inference providers: built-in routing, local Ollama, OpenAI API, Anthropic API.

## Current prototype

- Read-only diagnostics: system snapshot, audio, NetworkManager state, user warning logs, Flatpak application list.
- Approved actions: launch a desktop application, change an existing default PulseAudio/PipeWire sink.
- Four maximum agent planning steps per query; no free-form terminal commands.
- GTK operations only on the GTK thread; inference runs on worker threads.
- Cloud model selection asks for confirmation for each request.

## Security limitations / TODO

- Cloud providers receive prompts and tool output, including potentially sensitive log lines, with one per-request consent. A production edition needs per-tool data-sharing decisions and redaction.
- Providers currently rely on environment variables instead of GNOME Secret Service/Keyring.
- Actions are restricted, but no general permission broker or audit log exists yet.
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
