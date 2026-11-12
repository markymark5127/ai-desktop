"""Small, app-scoped presentation themes for AI Desktop.

This module deliberately has no GTK dependency so it can be tested headlessly.
Themes affect only the AI Desktop window, not every GNOME application.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


THEME_LABELS = [
    ("Japandi", "japandi"),
    ("Cyberpunk", "cyberpunk"),
    ("System", "system"),
]

# GTK4 CSS, scoped entirely to the root class added by ui.py.
# Fonts fall back to the user's configured GNOME typeface.
COMMON = """
.ai-desktop {
  padding: 0;
}
.ai-desktop entry {
  min-height: 46px;
  border-radius: 12px;
  padding-left: 12px;
  padding-right: 12px;
}
.ai-desktop scrolledwindow {
  border-radius: 12px;
}
.ai-desktop list {
  border-radius: 12px;
}
.ai-desktop list row {
  border-radius: 8px;
}
.ai-desktop button {
  min-height: 32px;
  border-radius: 9px;
}
"""

# We intentionally scope colored title buttons to AI Desktop windows. Applying
# left-side controls OS-wide is a separate, reversible GNOME user preference;
# Qt/Electron apps can provide their own decorations.
WINDOW_BUTTONS = """
/* These are our own non-stretching 13px GTK Buttons, not GNOME's tall
   windowcontrols buttons; keep normal headerbar controls fully separate. */
window.ai-desktop-window headerbar .mac-stoplights {
  background: transparent;
  border: none;
  box-shadow: none;
}
window.ai-desktop-window headerbar button.mac-stoplight {
  min-width: 13px;
  min-height: 13px;
  padding: 0;
  margin: 0;
  border-radius: 999px;
  background-image: none;
  box-shadow: inset 0 1px rgba(255,255,255,0.22);
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-close {
  background-color: #ff5f57;
  border: 1px solid #df514e;
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-minimize {
  background-color: #febc2e;
  border: 1px solid #dba224;
}
window.ai-desktop-window headerbar button.mac-stoplight.mac-maximize {
  background-color: #28c840;
  border: 1px solid #1fae37;
}
window.ai-desktop-window headerbar button.mac-stoplight:hover {
  box-shadow: 0 0 0 2px rgba(180,180,180,0.40);
}
window.ai-desktop-window headerbar button.mac-stoplight:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
"""

JAPANDI = """
/* Shoji Glass: warm paper, milky glass rows with a bright rim, and the
   liquid teal-to-violet only on the one action that matters. */
.ai-desktop.japandi,
window.ai-desktop-window.japandi {
  background-color: #f5f0e7;
  background-image: linear-gradient(180deg, #fbf8f2, #efe7da);
  color: #2B2F2C;
}
window.ai-desktop-window.japandi headerbar {
  background-color: transparent;
  background-image: none;
  color: #2B2F2C;
  box-shadow: none;
}
.ai-desktop.japandi entry {
  background-color: rgba(255, 255, 255, 0.70);
  color: #2B2F2C;
  border: 1px solid rgba(43, 47, 44, 0.12);
  border-radius: 14px;
  box-shadow: inset 0 1px 2px rgba(43, 36, 28, 0.05);
}
.ai-desktop.japandi entry:focus-within {
  border-color: #7466C2;
}
.ai-desktop.japandi list,
.ai-desktop.japandi list.boxed-list {
  background-color: rgba(255, 255, 255, 0.58);
  color: #2B2F2C;
  border: 1px solid rgba(255, 255, 255, 0.90);
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(43, 36, 28, 0.07);
}
.ai-desktop.japandi list row:selected {
  background-color: rgba(116, 102, 194, 0.12);
  color: #2B2F2C;
}
.ai-desktop.japandi list.welcome-overview row {
  border-radius: 0;
}
.ai-desktop.japandi list.welcome-overview row:hover {
  background-color: rgba(255, 255, 255, 0.55);
}
.ai-desktop.japandi .welcome-row-icon {
  min-width: 34px;
  min-height: 34px;
  border-radius: 11px;
  color: #3F5F86;
  background-color: rgba(255, 255, 255, 0.80);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 1px 3px rgba(43, 36, 28, 0.10);
}
.ai-desktop.japandi button {
  border-radius: 12px;
}
.ai-desktop.japandi button.pill {
  border-radius: 999px;
}
.ai-desktop.japandi textview,
.ai-desktop.japandi textview text {
  background-color: #fffcf6;
  color: #33302c;
}
.ai-desktop.japandi button.suggested-action {
  background-color: #5879AD;
  background-image: linear-gradient(90deg, #3D8C99, #7466C2);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.40);
  box-shadow: 0 4px 12px rgba(88, 121, 173, 0.28);
}
.ai-desktop.japandi button.suggested-action:hover {
  background-image: linear-gradient(90deg, #46979F, #7E71CB);
}
.ai-desktop.japandi button.suggested-action:active {
  background-image: linear-gradient(90deg, #357D89, #6658B1);
}
"""

CYBERPUNK = """
/* Deliberately distinct from Adwaita Dark: angular retro-terminal panels,
   cyan/magenta borders, thin neon glow and monospace/pixel-font fallback. */
window.ai-desktop-window.cyberpunk,
.ai-desktop.cyberpunk,
window.ai-desktop-window.cyberpunk toolbarview {
  background-color: #080c16;
  color: #ebfdff;
}
window.ai-desktop-window.cyberpunk headerbar {
  background-color: #111125;
  color: #00f5ff;
  font-family: "Press Start 2P", "Pixeloid Sans", monospace;
  font-weight: 700;
  border-bottom: 2px solid #00f5ff;
  box-shadow: 0 3px 12px rgba(0,245,255,0.35);
  border-radius: 0;
}
window.ai-desktop-window.cyberpunk headerbar button:not(.mac-stoplight),
window.ai-desktop-window.cyberpunk headerbar dropdown > button {
  color: #ecfcff;
  background-color: #1c1737;
  background-image: none;
  border: 1px solid #ff36ba;
  border-radius: 0;
  box-shadow: 0 0 6px rgba(255,54,186,0.36);
}
.ai-desktop.cyberpunk {
  font-family: "Pixeloid Sans", "DejaVu Sans Mono", monospace;
}
.ai-desktop.cyberpunk .title-1 {
  font-family: "Press Start 2P", "Pixeloid Sans", monospace;
  font-weight: 800;
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0,245,255,0.6);
}
.ai-desktop.cyberpunk .dim-label {
  color: #9ab5d0;
}
.ai-desktop.cyberpunk entry,
.ai-desktop.cyberpunk textview,
.ai-desktop.cyberpunk textview text {
  color: #e9fdff;
  background-color: #0a1428;
  background-image: none;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: inset 0 0 0 1px rgba(0,245,255,0.16),
              0 0 10px rgba(0,245,255,0.30);
  font-family: monospace;
}
.ai-desktop.cyberpunk entry:focus-within {
  border-color: #ff36ba;
  box-shadow: 0 0 12px rgba(255,54,186,0.55);
}
.ai-desktop.cyberpunk scrolledwindow,
.ai-desktop.cyberpunk list,
.ai-desktop.cyberpunk box,
.ai-desktop.cyberpunk stack {
  border-radius: 0;
}
.ai-desktop.cyberpunk list {
  color: #e9fdff;
  background-color: #0c1427;
  border: 1px solid #00f5ff;
  box-shadow: 0 0 10px rgba(0,245,255,0.18);
}
.ai-desktop.cyberpunk list row {
  border-radius: 0;
  border-bottom: 1px solid rgba(0,245,255,0.20);
}
.ai-desktop.cyberpunk list row:selected {
  background-color: #2e1440;
  color: #ffffff;
  border-left: 3px solid #ff36ba;
}
.ai-desktop.cyberpunk button,
.ai-desktop.cyberpunk dropdown > button {
  color: #e9fdff;
  background-color: #15182e;
  background-image: none;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 8px rgba(0,245,255,0.20);
  font-family: monospace;
  font-weight: 700;
}
.ai-desktop.cyberpunk button:hover,
.ai-desktop.cyberpunk dropdown > button:hover {
  background-color: #261b47;
  border-color: #ff36ba;
  box-shadow: 0 0 12px rgba(255,54,186,0.45);
}
.ai-desktop.cyberpunk button.suggested-action {
  color: #080c16;
  background-color: #00f5ff;
  border: 2px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 16px rgba(0,245,255,0.60);
}
.ai-desktop.cyberpunk button.suggested-action:hover {
  color: #ffffff;
  background-color: #7c135e;
  border-color: #ff36ba;
  box-shadow: 0 0 17px rgba(255,54,186,0.72);
}
.ai-desktop.cyberpunk checkbutton check {
  background-color: #0a1428;
  border: 1px solid #ff36ba;
  border-radius: 0;
}
.ai-desktop.cyberpunk checkbutton check:checked {
  background-color: #ff36ba;
}
.ai-desktop.cyberpunk progressbar trough {
  background-color: #15182e;
  border: 1px solid #00f5ff;
  border-radius: 0;
}
.ai-desktop.cyberpunk progressbar progress {
  background-color: #ff36ba;
  border-radius: 0;
}
"""

STYLES = {
    "system": WINDOW_BUTTONS,
    "japandi": COMMON + WINDOW_BUTTONS + JAPANDI,
    "cyberpunk": COMMON + WINDOW_BUTTONS + CYBERPUNK,
}

# Spotlight is a separate, deliberately small surface. These rules apply ONLY
# to the launcher window, after the normal app-scoped theme. Translucency is
# CSS alpha; GNOME/Wayland does not provide a portable app-controlled blur.
SPOTLIGHT_COMMON = """
window.ai-desktop-window.spotlight-window {
  background-color: transparent;
  background-image: none;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell {
  margin: 30px;
  padding: 10px 12px;
  border-radius: 18px;
}
window.spotlight-window .spotlight-searchbar .spotlight-hint {
  margin: 0 8px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  opacity: 0.72;
}
/* The empty launcher: a grid of apps under the field. */
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-launchpad {
  padding: 12px 2px 4px;
}
window.spotlight-window .ai-desktop.spotlight-shell flowbox.spotlight-grid {
  background: transparent;
}
window.spotlight-window .ai-desktop.spotlight-shell flowboxchild.spotlight-tile {
  padding: 10px 2px 8px;
  border-radius: 18px;
  background: transparent;
  transition: background-color 160ms ease-out;
}
window.spotlight-window .ai-desktop.spotlight-shell flowboxchild.spotlight-tile:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: -2px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-tile-label {
  font-size: 12px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-all-apps .spotlight-tile-icon {
  padding: 10px;
  border-radius: 14px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry {
  min-height: 52px;
  padding: 2px 8px;
  border: none;
  background: transparent;
  background-image: none;
  box-shadow: none;
  font-size: 17px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry:focus,
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry:focus-within {
  outline: none;
  box-shadow: none;
}
/* Nothing but the card paints: no window outline or shade around it. */
window.ai-desktop-window.spotlight-window,
window.ai-desktop-window.spotlight-window > widget {
  outline: none;
  background: transparent;
  box-shadow: none;
}
window.spotlight-window .spotlight-searchbar menubutton.spotlight-settings-button > button {
  min-width: 30px;
  min-height: 30px;
  margin: 0 3px;
  padding: 1px;
  border: none;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}
window.spotlight-window .spotlight-searchbar menubutton.spotlight-settings-button > button:hover {
  background-color: rgba(127, 127, 127, 0.16);
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-results,
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-response {
  padding-bottom: 4px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-approval {
  padding: 2px 12px 9px;
}
/* GTK4's ListBox, its implicit viewport, and rows can each paint a
   separate Adwaita surface. Reset ALL layers so the results inherit the
   themed translucent Spotlight panel instead of forming a white rectangle. */
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.spotlight-scroll,
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.spotlight-scroll > viewport,
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list,
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row {
  background: transparent;
  background-image: none;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list {
  padding: 2px 1px 9px;
}
/* A calm native spotlight grouping rhythm. Section headers are not rows
   that can be activated, and never draw a highlighted selection. */
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row.spotlight-section-row {
  background: transparent;
  background-image: none;
  border: none;
  box-shadow: none;
  padding: 2px 0 0;
  min-height: 26px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-section-heading {
  font-weight: 600;
  font-size: 12px;
  opacity: 0.72;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-result-subtitle {
  font-size: 12px;
  opacity: 0.76;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row.spotlight-result-row {
  min-height: 55px;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row.spotlight-ask-row {
  min-height: 61px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-results {
  border-radius: 12px;
  background: transparent;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row {
  margin: 2px 0;
  min-height: 46px;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row.spotlight-ask-row {
  min-height: 70px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-ai-only {
  padding-top: 0;
  padding-bottom: 0;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-ask-title {
  font-weight: 600;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-ask-subtitle {
  font-size: 12px;
}
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-chips {
  background: transparent;
  border: none;
}
window.spotlight-window .ai-desktop.spotlight-shell button.spotlight-chip {
  min-height: 29px;
  min-width: 0;
  padding: 4px 11px;
  font-size: 12px;
  background-image: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: -2px;
}
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output text {
  background: transparent;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell separator {
  min-height: 1px;
}
/* Chat with Mutsu Mechanic: the search window becomes a conversation. */
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-header {
  padding: 6px 2px 2px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-title {
  font-weight: 600;
  font-size: 15px;
}
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.mechanic-scroll,
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.mechanic-scroll > viewport {
  background: transparent;
  border: none;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-messages {
  padding: 4px 4px 8px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble {
  padding: 8px 12px;
  border-radius: 16px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble.from-user {
  margin-left: 64px;
  border-bottom-right-radius: 5px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble.from-mechanic {
  margin-right: 48px;
  border-bottom-left-radius: 5px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble.thinking {
  opacity: 0.7;
  font-style: italic;
}
window.spotlight-window .ai-desktop.spotlight-shell.chatting .spotlight-searchbar {
  margin-top: 4px;
  border-radius: 14px;
}
window.spotlight-window .ai-desktop.spotlight-shell.chatting entry.spotlight-entry {
  min-height: 44px;
  font-size: 15px;
}
"""

SPOTLIGHT_STYLES = {
    "system": SPOTLIGHT_COMMON + """
window.spotlight-window .ai-desktop.spotlight-shell {
  background-color: rgba(38, 42, 51, 0.90);
  color: #f8f9fc;
  border: 1px solid rgba(233, 237, 246, 0.20);
  box-shadow: 0 9px 28px rgba(0, 0, 0, 0.28);
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output {
  color: #ffffff;
}
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.spotlight-scroll,
window.spotlight-window .ai-desktop.spotlight-shell scrolledwindow.spotlight-scroll > viewport,
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list,
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row:not(:selected) {
  background: transparent;
  color: #f8f9fc;
}
window.spotlight-window .ai-desktop.spotlight-shell list.spotlight-list row:selected {
  background-color: rgba(255,255,255,0.18);
  border-radius: 10px;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble.from-mechanic {
  background-color: rgba(255, 255, 255, 0.10);
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble.from-user {
  background-color: rgba(120, 160, 255, 0.35);
}
window.spotlight-window .ai-desktop.spotlight-shell.chatting .spotlight-searchbar {
  background-color: rgba(255, 255, 255, 0.08);
}
window.spotlight-window .ai-desktop.spotlight-shell flowboxchild.spotlight-tile:hover,
window.spotlight-window .ai-desktop.spotlight-shell flowboxchild.spotlight-tile:focus-visible {
  background-color: rgba(255, 255, 255, 0.12);
}
window.spotlight-window .spotlight-searchbar .spotlight-hint,
window.spotlight-window .ai-desktop.spotlight-shell .spotlight-all-apps .spotlight-tile-icon {
  background-color: rgba(255, 255, 255, 0.10);
}
""",
    "japandi": SPOTLIGHT_COMMON + """
/* Shoji Glass: milky paper with a bright rim, liquid colour only for
   the active moment (selection, your messages). */
window.spotlight-window .ai-desktop.spotlight-shell.japandi {
  background-color: rgba(250, 246, 238, 0.86);
  background-image: linear-gradient(180deg, rgba(255, 253, 248, 0.90), rgba(244, 237, 224, 0.80));
  color: #2B2F2C;
  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 28px;
  box-shadow: 0 8px 22px rgba(43, 36, 28, 0.22), inset 0 1px rgba(255, 255, 255, 0.90);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-searchbar {
  background-color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.80);
  border-radius: 20px;
  box-shadow: inset 0 1px 2px rgba(43, 36, 28, 0.06);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-searchbar:focus-within {
  border-color: rgba(116, 102, 194, 0.45);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-hint {
  background-color: rgba(43, 47, 44, 0.06);
  border: 1px solid rgba(43, 47, 44, 0.08);
  color: #4A4E49;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi flowboxchild.spotlight-tile:hover {
  background-color: rgba(255, 255, 255, 0.55);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi flowboxchild.spotlight-tile:focus-visible {
  background-color: rgba(255, 255, 255, 0.70);
  outline-color: #7466C2;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-tile-label {
  color: #2B2F2C;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-all-apps .spotlight-tile-icon {
  background-color: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.90);
  color: #2B2F2C;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell.japandi textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell.japandi textview.spotlight-output text {
  background: transparent;
  border: none;
  color: #33302c;
  box-shadow: none;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi scrolledwindow.spotlight-scroll,
window.spotlight-window .ai-desktop.spotlight-shell.japandi scrolledwindow.spotlight-scroll > viewport,
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list,
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row:not(:selected) {
  background: transparent;
  background-image: none;
  border: none;
  color: #33302c;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row {
  border-radius: 12px;
  color: #33302c;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row:hover:not(:selected) {
  background: rgba(255, 255, 255, 0.50);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row:selected {
  background-color: #5879AD;
  background-image: linear-gradient(90deg, #3D8C99, #7466C2);
  color: #FFFFFF;
  border-radius: 14px;
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.35);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row:selected label,
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row:selected image {
  color: #FFFFFF;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .spotlight-section-heading {
  color: #6B6459;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi button.spotlight-chip {
  background-color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 999px;
  color: #2B2F2C;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi button.spotlight-chip:hover {
  background-color: rgba(255, 255, 255, 0.80);
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi list.spotlight-list row.spotlight-section-row {
  border-radius: 0;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .mechanic-bubble.from-mechanic {
  background-color: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.85);
  color: #2B2F2C;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .mechanic-bubble.from-user {
  background-color: #5879AD;
  background-image: linear-gradient(135deg, #3D8C99, #7466C2);
  color: #FFFCF6;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi .mechanic-bubble.from-user label {
  color: #FFFCF6;
}
window.spotlight-window .ai-desktop.spotlight-shell.japandi.chatting .spotlight-searchbar {
  background-color: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.85);
}
""",
    "cyberpunk": SPOTLIGHT_COMMON + """
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk {
  background-color: rgba(8, 12, 22, 0.90);
  color: #ebfdff;
  border: 1px solid #00f5ff;
  border-radius: 0;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.32);
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk textview.spotlight-output text {
  background: transparent;
  border: 0;
  border-radius: 0;
  color: #ebfdff;
  box-shadow: none;
  font-family: monospace;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk scrolledwindow.spotlight-scroll,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk scrolledwindow.spotlight-scroll > viewport,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk list.spotlight-list,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk list.spotlight-list row:not(:selected) {
  background: transparent;
  border: none;
  color: #ebfdff;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk list.spotlight-list row {
  border-radius: 0;
  color: #ebfdff;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk list.spotlight-list row:hover:not(:selected) {
  background-color: rgba(0, 245, 255, 0.10);
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk list.spotlight-list row:selected {
  background-color: rgba(255, 54, 186, 0.25);
  border-left: 3px solid #ff36ba;
  border-radius: 0;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .spotlight-section-heading {
  color: #00f5ff;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-family: monospace;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk button.spotlight-chip {
  background-color: rgba(0, 245, 255, 0.04);
  border: 1px solid #00f5ff;
  border-radius: 0;
  color: #00f5ff;
  font-family: monospace;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk button.spotlight-chip:hover {
  border-color: #ff36ba;
  color: #ff36ba;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .mechanic-bubble {
  border-radius: 0;
  font-family: monospace;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .mechanic-bubble.from-mechanic {
  background-color: rgba(0, 245, 255, 0.06);
  border-left: 2px solid #00f5ff;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .mechanic-bubble.from-user {
  background-color: rgba(255, 54, 186, 0.16);
  border-right: 2px solid #ff36ba;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk.chatting .spotlight-searchbar {
  border: 1px solid rgba(0, 245, 255, 0.5);
  border-radius: 0;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk flowboxchild.spotlight-tile {
  border-radius: 0;
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk flowboxchild.spotlight-tile:hover,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk flowboxchild.spotlight-tile:focus-visible {
  background-color: rgba(0, 245, 255, 0.12);
}
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .spotlight-hint,
window.spotlight-window .ai-desktop.spotlight-shell.cyberpunk .spotlight-all-apps .spotlight-tile-icon {
  border: 1px solid rgba(0, 245, 255, 0.35);
  border-radius: 0;
  color: #00f5ff;
}
""",
}

SPOTLIGHT_HIGH_CONTRAST = """
window.ai-desktop-window.spotlight-window {
  background-color: transparent;
}
window.spotlight-window .ai-desktop.spotlight-shell {
  padding: 8px;
  background-color: #101010;
  color: #ffffff;
  border: 2px solid #ffffff;
  border-radius: 8px;
}
window.spotlight-window .ai-desktop.spotlight-shell entry.spotlight-entry,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output,
window.spotlight-window .ai-desktop.spotlight-shell textview.spotlight-output text {
  background: #101010;
  color: #ffffff;
}
window.spotlight-window .ai-desktop.spotlight-shell .mechanic-bubble {
  padding: 8px 12px;
  border: 2px solid #ffffff;
  border-radius: 6px;
}
"""

SCHEMES = {"system": "default", "japandi": "light", "cyberpunk": "dark"}


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "ai-desktop" / "appearance.json"


def validate_theme(name: str) -> str:
    if name not in STYLES:
        raise ValueError("Unknown theme")
    return name


def load_theme() -> str:
    try:
        with config_path().open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return "japandi"
    if not isinstance(value, dict):
        return "japandi"
    # Desktop extension writes "appearance"; this app writes "theme".
    name = value.get("theme") or value.get("appearance")
    if name not in STYLES:
        return "japandi"
    return name


def save_theme(name: str) -> None:
    name = validate_theme(name)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".appearance-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"theme": name, "appearance": name}, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
