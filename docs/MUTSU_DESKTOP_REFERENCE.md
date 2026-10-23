# Mutsu OS — Calm Japandi desktop reference

The user-supplied **Mutsu OS Japandi desktop concept image** in the design
discussion (Oct 23, 2026) is the approved direction for the **overall desktop
experience**, not a screenshot of our implemented GNOME launcher.

## Design target

- Warm textured cream / light stone wallpaper, subtle botanical silhouettes,
  Mutsu round two-wave logo centered in muted sage above a spaced **MUTSU OS**
  wordmark; plenty of clean negative space.
- Light translucent GNOME-like top bar with compact Mutsu app/menu identity
  at the upper left, clock centered and restrained system indicators at right.
- Centered low-profile floating bottom dock, soft rounded rectangle, subtle
  shadow, familiar launcher/file/browser/system icons, understated running
  indicators and magnification restrained for a calm aesthetic.
- Search overlay near the **top third** of screen, centered at about **one
  third of a 16:9 screen width**, with frosted warm-paper chrome and soft
  shadows. No normal application titlebar.
- Search area has a visible search field; when expanded it groups
  **Top Results**, **Files**, **AI Suggestions** with generous ~50–64px
  touch-friendly rows, green-gray hover/selection, small secondary labels
  and simple icons. When the only result is Ask AI, it still looks like a
  full selectable row; never a tiny footer.
- Distinct application, file and AI results. AI prompt suggestions are
  optional; no request is sent during typing. Privacy remains controlled
  by the saved checkbox in Setup/Preferences.

## Implemented vs future

| Area | Status |
| --- | --- |
| Compact translucent Spotlight bar | GTK4 prototype implemented |
| Local installed app search + explicit Ask AI fallback | Implemented |
| Warm Japandi styling of result rows and AI-only state | Implemented in CSS; VM QA pending |
| Popup settings and Newelle inference/consent | Implemented; VM QA pending |
| User 4K wallpaper images committed to repo | Both present |
| Explicit theme selection applies matching GNOME wallpaper | Implemented with backup/restore; VM QA pending |
| OS wallpaper switch, dock icons and full GNOME Shell visual style | Planned |
| Bounded filename/folder results (Documents, Downloads, Pictures etc.) | Implemented locally; depth/budget capped, no content indexing |
| Full persistent file index with modified dates and comprehensive ranking | Planned |
| Two non-network AI prompt chips (Explain / Troubleshoot) | Implemented, prefill only |
| Rich contextual actions and per-file AI suggestion menus | Planned |
| Mac-style top bar/global menu, true GNOME Shell blur and positioning | Planned |
| Actual Bazzite-derived installable image | Planned |

See [wallpaper upload instructions](../assets/wallpapers/README.md) and
[themes](THEMES.md). Do not ship screenshot mockup as actual file results or
claim unimplemented features work.
