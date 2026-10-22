# Helper Experience: Linux training wheels, not an AI chatbot

## Product promise

AI Desktop is the built-in troubleshooting buddy that helps someone move from macOS to Linux gaming without memorizing Linux terminology or terminal commands. The assistant is optional, permission-aware, and educational. It is not a process that silently changes the system.

**Super + Space** is the universal entry point. It opens apps, finds files, navigates settings, carries out supported actions, and helps troubleshoot problems.

### Example requests and expected routing

| User types | Intended behavior |
| --- | --- |
| Steam | Instant installed-app result; open with Enter, no AI call |
| Downloads | Show files/folders; open the selected item |
| Bluetooth | Show the Bluetooth settings panel; open immediately |
| Turn up volume | Execute a trusted local desktop operation |
| Install VLC | Show verified app/source and request approval before install |
| My Xbox controller isn't working in Black Mesa | Check permitted system/Steam Input diagnostics, propose and verify safe repair |
| What's a Flatpak? | Explain simply, optionally comparing it to Mac apps |

**These are product targets.** Currently implemented are app search, limited diagnostics/actions and headless Newelle model inference; file search, most actions, full repair/verification, and first-run onboarding are not yet implemented.

## Onboarding: "Your computer comes with a helping hand"

Do not open with an AI provider-selection screen. Begin with:

> Linux is easier when you're not on your own.
>
> Search for apps and files, tell your computer what you'd like to do, or ask for help when something goes wrong.
>
> Press Super + Space anytime.

Provide a live "Try it now" box with real, detected installed apps and available system capabilities. Never pretend to detect hardware or applications.

### Learning styles (changeable any time)

1. **Just help me fix things.** Short diagnosis, approval and result.
2. **Help me and briefly explain (default).** One or two sentences about the cause and action, plus outcome.
3. **Teach me as we go.** Optional longer explanation with macOS analogies, exact supported tool actions, and links to learn more.

Learning style influences verbosity and educational detail, **not** permissions, privileges or which system tools can run. Save the choice per-user; it is never a reason to auto-approve changes.

### AI setup is optional and secondary

- Desktop search and built-in diagnostics must work even when Newelle is offline.
- Default to authenticated loopback-only headless Newelle for complex interpretation and planning.
- Newelle may use a local or cloud model; make costs and privacy implications clear.
- Do not enable Newelle's unrestricted agent, shell, or MCP execution behind the desktop's back.
- Share diagnostic content with a cloud provider only with specific user consent.
- If the AI cannot act, offer normal GNOME controls and clear instructions, not a dead end.

## Unified omnibox architecture

One input, three kinds of result: **Open**, **Do**, **Get Help**.

1. **Search/index:** installed desktop applications, accessible indexed user files, Settings panels, common folders, Steam games, and registered system/application capabilities.
2. **Local-first routing:** app/file/settings launch and typed simple actions are deterministic, quick, and do not require an LLM.
3. **AI fallback:** send complex requests to Newelle as an inference/planning model only. An independent allowlisted broker validates requested tools and permissions.
4. **Action preview:** show exactly what will change; request approval for persistent settings, installs, sensitive access, sharing data, privilege changes.
5. **Execute and verify:** perform typed, bounded actions; read the relevant state afterward; indicate success or uncertainty honestly.
6. **Teach and recover:** summarize what happened at the user's preferred level, offer "Show details" and "Undo" only when genuinely possible.

### Search UI layout

- **Open:** app, file, folder, system settings or Steam game; Enter/click is an explicit user launch request.
- **Do:** supported action like change audio output, adjust volume or install a verified Flatpak; confirm when necessary.
- **Get help:** diagnose an issue, show evidence, recommend a fix, obtain approval, execute, verify and explain.

Example illustrative response:

> My Xbox controller stopped working.
>
> Possible cause: Steam is using another controller as Player 1.
>
> Suggested next step: open Steam Input's controller order.
>
> [Open controller settings] [Explain why] [Show details]

This diagnosis must appear only if supported by real system evidence.

### Permission model

| Category | Examples | Expected behavior |
| --- | --- | --- |
| Read-only navigation | app/file search, list installed apps | Immediate results with OS permissions |
| Read-only diagnostics | audio sinks, network state, Steam Input state | Show output and any privacy limitations |
| Transient control | volume, brightness | Run a typed allowed tool, reversible when supported |
| Persistent modification | default audio sink, install an app, configuration change | Preview, explicit user approval, verification, action log |
| Privileged, destructive, sensitive | root access, disk formatting, deleting data, credential changes | Dedicated trusted policy and stronger approval, or unsupported |

"Do anything from Spotlight" means provide a **single discoverable entry point** to whatever the system can safely support, not arbitrary unrestricted execution. If an action is unsupported, explain what to do and open the appropriate settings panel where possible.

## Build order

1. Deterministic local omnibox: existing app search, add Settings pages, indexed files and Steam titles.
2. Keyboard UI separating Open, Do and Get help; quick results without model latency.
3. Safe, verified troubleshooting of one recurring problem (wrong audio output), with action history and undo if supported.
4. Learning style preference and optional explanations, independent from action permissions.
5. First-run buddy tour with a real Super+Space exercise and privacy-aware Newelle setup.
6. Additional trusted capabilities via D-Bus/desktop portals/MCP and gaming support.

## Test with beginners

- Without Newelle, can someone open a file, launch an app and find a setting?
- When the user describes an issue, does the helper investigate and say when it is uncertain?
- Does every consequential change get the right approval even in "just fix it" mode?
- Does "Teach me" explain without dumping unexplained commands?
- Can the user see what happened and recover from failure?
- Can someone finish onboarding without ever seeing the terms D-Bus, Polkit, MCP, or API key?
