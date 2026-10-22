# Product vision: a Mac-familiar gaming desktop

**North star:** A long-time Mac user should be able to install the OS, immediately recognize how to navigate it, connect their phone, launch Steam games, and solve routine problems without learning Linux commands. **Super + Space is the everyday control center, and the helper is Linux training wheels rather than AI hype.** See [Helper Experience](HELPER_EXPERIENCE.md).

This is **not a macOS clone**, a new desktop environment, or an AI chatbot pasted on top of a distro. Build an approachable GNOME desktop experience atop Bazzite, with a fast Spotlight-style launcher, headless Newelle inference, safe system actions, and gaming support.

## Who it is for

- People comfortable with macOS who want access to the Steam/Proton PC gaming catalog.
- People curious about Linux who don't want a terminal-centric troubleshooting burden.
- Existing GNOME users who may want just the portable assistant/desktop experience without installing a new OS.

## Non-negotiable experience principles

1. **Familiar first:** persistent optional bottom dock, clean top bar, natural trackpad gestures, prominent Files, readable app menus, predictable shortcuts.
2. **Search first, AI second:** app and file results return instantly offline; complex requests invoke Newelle only when needed. No unnecessary model cost/latency for a calculator or a file.
3. **Safe repairs:** permissions for consequential actions, user-facing explanation, execution verification, an auditable history, and rollback when technically supported. No unrestricted root shell from a model.
4. **Gaming is already there:** preserve Bazzite's supported Steam, Proton, Gamescope and vendor GPU variant capabilities rather than inventing a gaming stack.
5. **No surprises:** updates should be atomic and recoverable; iPhone limitations are explicitly explained, never disguised as fully functioning Mac Continuity.

## Expected desktop behavior

| Mac expectation | Practical GNOME/Linux implementation | Priority |
| --- | --- | --- |
| Dock, running-app indicators | Evaluate Dash to Dock (GNOME extension), bottom position, optional auto-hide | High |
| Spotlight on Command-Space | AI Desktop Super-Space launcher, app/file search and optional natural language | High |
| Finder with file previews | GNOME Files (Nautilus) and GNOME Sushi Quick Look where supported | High |
| Mission Control/Spaces | GNOME Overview, workspaces, gestures, intentional keyboard mapping | High |
| Easy split windows | Built-in GNOME half snapping; test an extension such as Smart Tiling/Tiling Assistant for quarters and assisted layouts | High |
| macOS keyboard muscle memory | Show a Mac-oriented shortcut guide; use Super for Shell actions. Don't globally rewrite Ctrl vs Command in apps without explicit opt-in | High |
| AirDrop/Continuity sharing | GSConnect on GNOME, KDE Connect on phones; pair-device walkthrough | High |
| Mac-style coherent interface | App-scoped Japandi/Cyberpunk already available; future matching shell/dock/wallpaper/icons | Medium |
| macOS migration | Explain equivalent Linux apps and how to import local files/browser/bookmarks | Medium |
| Gaming | Steam game import, Proton guidance, controller setup and launch experiences | High |
| Troubleshooting help | Newelle via inference only initially, AI Desktop action broker for approved fixes | High |

**Extension caveat:** GNOME extensions must be tested against each GNOME Shell release shipped in the base image. Do not assume an extension that supports GNOME 49 supports GNOME 50; pin/test versions in the future image and give users a no-extension recovery mode.

## Phone integration reality (must be explained during onboarding)

Use [GSConnect](https://github.com/shell-extensions/gsconnect) with GNOME, **not** the regular KDE Connect Linux daemon at the same time. Its iOS peer is [KDE Connect for iOS](https://github.com/KDE/kdeconnect-ios).

On iPhone, prioritize: app-mediated file transfer, link sharing, and optional remote input/limited clipboard sync while the companion is open.

**Do not promise:** ordinary iMessage or SMS integration, system-wide iOS notification mirroring, full Universal Clipboard, or an always-on background iOS pairing service. iOS sandbox/background restrictions make these unavailable via ordinary KDE Connect. Distinguish Android's broader capabilities from iOS. A separate Mac-to-Linux iMessage bridge may be an *optional advanced* project but must not be a dependency of the product.

The device wizard should detect connection problems and present accurate troubleshooting without overstating feature support. Respect users' choice not to pair a phone.

## The first-run wizard (future)

1. Choose light Japandi, dark Cyberpunk, or system look; show a real preview and accessible fallback.
2. Choose a familiar dock/layout style and turn on any GNOME extensions with explicit user control.
3. Explain the **Super** key on PC and **Command** key on Apple keyboards and teach the 5 most useful shortcuts.
4. Introduce **"Your computer comes with a helping hand"**, not an AI feature pitch: demonstrate Super+Space as an instant app/file/settings launcher and a plain-English troubleshooting buddy; allow a real "Try it now" task.
5. Choose an explanation preference: "Just help me fix things", "Help me and briefly explain" (default), or "Teach me as we go". This must never alter permissions or approval rules.
6. Configure headless Newelle as an **optional backend**, with privacy/cost disclosure for cloud use; ensure Spotlight and ordinary navigation still work without it.
7. Optionally pair a phone via GSConnect/KDE Connect; show OS-specific capability chart.
8. Optional Mac migration guide (browser data, documents, music/photos, passwords, app alternatives).
9. Test graphics/controller basics and offer Steam sign-in/gaming mode on supported devices.
10. Show recovery entry points and a clear **Undo/Revert** path for supported changes.

No Apple ID or sensitive credential should be requested by the distro just to perform basic onboarding.

## Measurable prototype acceptance test

In a **Fedora GNOME VM** (for GUI/search/testing) and later **Bazzite GNOME on physical hardware**:

- A Mac user can find Files, Settings, Browser, Steam and a downloaded file in seconds.
- Dock and overview make it clear which app is running and how to move between windows/workspaces.
- Super-Space search is predictable and faster than a language model for ordinary navigation.
- Two or four windows can be tiled with discoverable keyboard/mouse actions.
- Phone pairing is explained, with iPhone limitations visible before setup.
- A mis-selected audio sink can be diagnosed and fixed after user confirmation, then verified.
- A Steam/Proton/controller failure can be explained without pretending repair succeeded.
- Nontechnical testers can revert appearance/shortcut changes without opening the terminal.
- VM success does **not** stand in for GPU/Proton/native gaming reliability.

## Engineering/build packaging decision

**Now:** maintain `ai-desktop` as a GNOME app + optional Shell extension and clearly scoped services (Newelle backend, permission broker).

**Later:** offer a signed Bazzite GNOME-derived image preconfiguring our app, compatible shell extensions, Steam/Gaming Mode, onboarding, and sensible defaults. This can be a recognizable OS product without replacing GNOME or creating an independently maintained distro/kernel.

**Keep the standalone app installable** on unmodified GNOME distributions. Don't couple search, styling or the AI backend to one image.

## Early roadmap order

- Search and window polish: real indexed file search, persistent window behavior, first-run guided UI.
- GSConnect/iOS pairing discovery and status (without promising Mac-level continuity).
- Snap/tiling extension compatibility testing and discoverable layouts.
- Newelle onboarding + per-tool cloud privacy + safe repair flow.
- Mac migration checklist and keyboard onboarding.
- Bazzite GNOME VM then native gaming QA and eventually an OS image.
