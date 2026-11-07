"""Spotlight-style instant answers for Mutsu Search.

Everything here is local and side-effect free until the user activates a
row: typing never contacts the network or an AI model.

- calculate():      arithmetic, percentages and common functions
- convert_units():  "5 km in miles", "72 f to c", "2 gb in mb"
- web_action():     open a typed address or search the web (on Enter only)
- search_settings(): GNOME Settings pages ("wifi", "bluetooth", ...)
- UsageStore:       app suggestions from launch frequency and time of day
- content search:   file contents through GNOME's LocalSearch index
"""

from __future__ import annotations

import ast
import json
import math
import operator
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse


# ---- calculator -------------------------------------------------------------

@dataclass(frozen=True)
class Answer:
    """An instant answer row: Enter copies `value` to the clipboard."""
    title: str
    subtitle: str
    value: str


_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {
    "sqrt": math.sqrt, "abs": abs, "round": round, "floor": math.floor,
    "ceil": math.ceil, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log10, "ln": math.log, "exp": math.exp,
}
_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}
_MATHY = re.compile(r"^[\d\s.+\-*/%^()×÷,a-z]+$")


def _evaluate(node, depth=0):
    if depth > 40:
        raise ValueError("too deep")
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, depth + 1)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left = _evaluate(node.left, depth + 1)
        right = _evaluate(node.right, depth + 1)
        if isinstance(node.op, ast.Pow) and (abs(right) > 1000 or abs(left) > 1e6):
            raise ValueError("power too large")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_evaluate(node.operand, depth + 1))
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _FUNCTIONS and len(node.args) == 1 and not node.keywords):
        return _FUNCTIONS[node.func.id](_evaluate(node.args[0], depth + 1))
    raise ValueError("unsupported")


def format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        value = int(value)
    if isinstance(value, int):
        return f"{value:,}"
    text = f"{value:,.10g}"
    return text


_ASK_PREFIX = re.compile(r"^(?:what\s+is|what's|whats|calc(?:ulate)?|=)\s*", re.I)


def calculate(query: str) -> Answer | None:
    text = _ASK_PREFIX.sub("", query.strip().casefold()).rstrip("?=").strip()
    if not text or not _MATHY.match(text) or not re.search(r"\d", text):
        return None
    # "15% of 80" and bare "15%"
    text = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*of\s*", r"(\1/100)*", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", text)
    text = text.replace("×", "*").replace("÷", "/").replace("^", "**").replace(",", "")
    # A lone number is not a calculation.
    if re.fullmatch(r"[\d.\s]+", text):
        return None
    try:
        value = _evaluate(ast.parse(text, mode="eval"))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or math.isnan(value):
        return None
    result = format_number(value)
    return Answer(f"= {result}", f"{query.strip()} · Enter copies the result",
                  result.replace(",", ""))


# ---- unit conversion --------------------------------------------------------

# unit -> (category, factor to the base unit)
_UNITS: dict[str, tuple[str, float]] = {}


def _add(category: str, factor: float, *names: str) -> None:
    for name in names:
        _UNITS[name] = (category, factor)


_add("length", 0.001, "mm", "millimeter", "millimeters", "millimetre", "millimetres")
_add("length", 0.01, "cm", "centimeter", "centimeters", "centimetre", "centimetres")
_add("length", 1.0, "m", "meter", "meters", "metre", "metres")
_add("length", 1000.0, "km", "kilometer", "kilometers", "kilometre", "kilometres")
_add("length", 0.0254, "in", "inch", "inches", '"')
_add("length", 0.3048, "ft", "foot", "feet", "'")
_add("length", 0.9144, "yd", "yard", "yards")
_add("length", 1609.344, "mi", "mile", "miles")
_add("mass", 0.001, "g", "gram", "grams")
_add("mass", 1.0, "kg", "kilogram", "kilograms", "kilo", "kilos")
_add("mass", 0.000001, "mg", "milligram", "milligrams")
_add("mass", 0.028349523125, "oz", "ounce", "ounces")
_add("mass", 0.45359237, "lb", "lbs", "pound", "pounds")
_add("mass", 6.35029318, "st", "stone", "stones")
_add("volume", 0.001, "ml", "milliliter", "milliliters", "millilitre", "millilitres")
_add("volume", 1.0, "l", "liter", "liters", "litre", "litres")
_add("volume", 0.00492892159375, "tsp", "teaspoon", "teaspoons")
_add("volume", 0.01478676478125, "tbsp", "tablespoon", "tablespoons")
_add("volume", 0.2365882365, "cup", "cups")
_add("volume", 0.0295735295625, "floz", "fl oz")
_add("volume", 0.473176473, "pt", "pint", "pints")
_add("volume", 0.946352946, "qt", "quart", "quarts")
_add("volume", 3.785411784, "gal", "gallon", "gallons")
_add("data", 1.0, "b", "byte", "bytes")
_add("data", 1e3, "kb", "kilobyte", "kilobytes")
_add("data", 1e6, "mb", "megabyte", "megabytes")
_add("data", 1e9, "gb", "gigabyte", "gigabytes")
_add("data", 1e12, "tb", "terabyte", "terabytes")
_add("data", 1024.0, "kib")
_add("data", 1024.0 ** 2, "mib")
_add("data", 1024.0 ** 3, "gib")
_add("data", 1024.0 ** 4, "tib")
_add("time", 0.001, "ms", "millisecond", "milliseconds")
_add("time", 1.0, "s", "sec", "secs", "second", "seconds")
_add("time", 60.0, "min", "mins", "minute", "minutes")
_add("time", 3600.0, "h", "hr", "hrs", "hour", "hours")
_add("time", 86400.0, "day", "days")
_add("time", 604800.0, "week", "weeks")
_add("speed", 1 / 3.6, "kph", "km/h", "kmh")
_add("speed", 0.44704, "mph")
_add("speed", 1.0, "m/s", "mps")
_TEMPERATURE = {"c": "c", "°c": "c", "celsius": "c", "f": "f", "°f": "f",
                "fahrenheit": "f", "k": "k", "kelvin": "k"}
_CONVERSION = re.compile(
    r"^\s*(-?\d+(?:[.,]\d+)?)\s*([a-z°/\"' ]+?)\s+(?:to|in|as|into|=)\s+([a-z°/\"' ]+?)\s*$")


def _to_celsius(value: float, unit: str) -> float:
    return {"c": value, "f": (value - 32) * 5 / 9, "k": value - 273.15}[unit]


def _from_celsius(value: float, unit: str) -> float:
    return {"c": value, "f": value * 9 / 5 + 32, "k": value + 273.15}[unit]


def convert_units(query: str) -> Answer | None:
    match = _CONVERSION.match(query.casefold())
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    source, target = match.group(2).strip(), match.group(3).strip()
    if source in _TEMPERATURE and target in _TEMPERATURE:
        value = _from_celsius(_to_celsius(amount, _TEMPERATURE[source]), _TEMPERATURE[target])
        unit = "°" + _TEMPERATURE[target].upper() if _TEMPERATURE[target] != "k" else " K"
        result = f"{value:.4g}" if abs(value) < 1e6 else format_number(value)
        return Answer(f"= {result}{unit}", f"{query.strip()} · Enter copies the result", result)
    if source not in _UNITS or target not in _UNITS:
        return None
    (category, from_factor), (other, to_factor) = _UNITS[source], _UNITS[target]
    if category != other:
        return None
    value = amount * from_factor / to_factor
    result = f"{value:.6g}" if abs(value) < 1e9 else format_number(value)
    return Answer(f"= {result} {target}", f"{query.strip()} · Enter copies the result", result)


def instant_answer(query: str) -> Answer | None:
    return convert_units(query) or calculate(query)


# ---- web --------------------------------------------------------------------

SEARCH_ENGINES = {
    "duckduckgo": ("DuckDuckGo", "https://duckduckgo.com/?q={}"),
    "google": ("Google", "https://www.google.com/search?q={}"),
    "bing": ("Bing", "https://www.bing.com/search?q={}"),
    "brave": ("Brave Search", "https://search.brave.com/search?q={}"),
    "startpage": ("Startpage", "https://www.startpage.com/do/search?q={}"),
    "ecosia": ("Ecosia", "https://www.ecosia.org/search?q={}"),
}
DEFAULT_ENGINE = "duckduckgo"
_DOMAIN = re.compile(r"^(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,24}(?::\d+)?(?:[/?#]\S*)?$", re.I)


@dataclass(frozen=True)
class WebAction:
    title: str
    subtitle: str
    url: str


def web_actions(query: str, engine: str = DEFAULT_ENGINE) -> list[WebAction]:
    """An "Open site" row for typed addresses, then a web search row."""
    query = query.strip()
    if not query:
        return []
    actions = []
    if " " not in query and _DOMAIN.match(query) and not re.fullmatch(r"[\d.]+", query):
        url = query if re.match(r"^https?://", query, re.I) else f"https://{query}"
        actions.append(WebAction(f"Open {query}", "Website", url))
    name, template = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
    actions.append(WebAction(f"Search the web for “{query[:60]}”", name,
                             template.format(quote_plus(query))))
    return actions


# ---- GNOME Settings pages ---------------------------------------------------

@dataclass(frozen=True)
class SettingsPage:
    title: str
    panel: str
    keywords: tuple[str, ...]


SETTINGS_PAGES = (
    SettingsPage("Wi-Fi", "wifi", ("wifi", "wi-fi", "wireless", "internet", "network")),
    SettingsPage("Network", "network", ("network", "ethernet", "vpn", "proxy")),
    SettingsPage("Bluetooth", "bluetooth", ("bluetooth", "headphones", "pair")),
    SettingsPage("Displays", "display", ("display", "monitor", "screen", "resolution",
                                          "night light", "scale", "refresh rate")),
    SettingsPage("Sound", "sound", ("sound", "volume", "audio", "speaker", "microphone")),
    SettingsPage("Power", "power", ("power", "battery", "sleep", "suspend")),
    SettingsPage("Appearance", "background", ("appearance", "wallpaper", "background",
                                              "dark mode", "theme", "accent")),
    SettingsPage("Notifications", "notifications", ("notifications", "do not disturb")),
    SettingsPage("Search", "search", ("search",)),
    SettingsPage("Apps", "applications", ("apps", "applications", "default apps",
                                          "permissions")),
    SettingsPage("Privacy & Security", "privacy", ("privacy", "security", "location",
                                                   "camera", "lock screen")),
    SettingsPage("Online Accounts", "online-accounts", ("accounts", "google", "microsoft")),
    SettingsPage("Sharing", "sharing", ("sharing", "remote desktop", "file sharing")),
    SettingsPage("Mouse & Touchpad", "mouse", ("mouse", "touchpad", "trackpad", "scroll")),
    SettingsPage("Keyboard", "keyboard", ("keyboard", "shortcuts", "input", "language")),
    SettingsPage("Printers", "printers", ("printer", "printers", "print")),
    SettingsPage("Accessibility", "universal-access", ("accessibility", "zoom",
                                                       "screen reader", "large text")),
    SettingsPage("Users", "user-accounts", ("users", "password", "account", "avatar")),
    SettingsPage("Date & Time", "datetime", ("date", "time", "timezone", "clock")),
    SettingsPage("System", "system", ("about", "system", "updates", "storage", "region")),
    SettingsPage("Wacom Tablet", "wacom", ("pen", "stylus", "wacom", "tablet")),
)


def search_settings(query: str, limit: int = 2) -> list[SettingsPage]:
    q = query.strip().casefold()
    if len(q) < 3:
        return []
    scored = []
    for page in SETTINGS_PAGES:
        names = (page.title.casefold(), *page.keywords)
        if any(name == q for name in names):
            scored.append((0, page))
        elif any(name.startswith(q) for name in names):
            scored.append((1, page))
        elif len(q) >= 4 and any(q in name for name in names):
            scored.append((2, page))
    scored.sort(key=lambda item: item[0])
    return [page for _rank, page in scored[:limit]]


# ---- app suggestions (frequency + time of day) ------------------------------

def usage_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(base) / "mutsu-search" / "usage.json"


class UsageStore:
    """Local launch history for suggestions. Never leaves the computer."""

    HALF_LIFE_DAYS = 10
    MAX_EVENTS = 40

    def __init__(self, path: Path | None = None):
        self.path = path or usage_path()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.events = {k: [float(t) for t in v][-self.MAX_EVENTS:]
                           for k, v in data.get("launches", {}).items()
                           if isinstance(k, str) and isinstance(v, list)}
        except (OSError, ValueError, TypeError, AttributeError):
            self.events = {}

    def record(self, desktop_id: str, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self.events.setdefault(desktop_id, []).append(now)
        self.events[desktop_id] = self.events[desktop_id][-self.MAX_EVENTS:]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"version": 1, "launches": self.events}), encoding="utf-8")
            os.chmod(tmp, 0o600)
            tmp.replace(self.path)
        except OSError:
            pass

    def score(self, desktop_id: str, now: float | None = None) -> float:
        now = time.time() if now is None else now
        hour = time.localtime(now).tm_hour + time.localtime(now).tm_min / 60
        total = 0.0
        for stamp in self.events.get(desktop_id, ()):
            age_days = max(0.0, (now - stamp) / 86400)
            weight = 0.5 ** (age_days / self.HALF_LIFE_DAYS)
            launched = time.localtime(stamp)
            diff = abs(hour - (launched.tm_hour + launched.tm_min / 60))
            if min(diff, 24 - diff) <= 1.5:
                weight *= 1.6  # you tend to use this app around now
            total += weight
        return total

    def suggestions(self, desktop_ids: list[str], limit: int = 6,
                    now: float | None = None) -> list[str]:
        scored = [(self.score(d, now), d) for d in desktop_ids if d in self.events]
        scored.sort(key=lambda item: -item[0])
        return [d for score, d in scored[:limit] if score > 0.05]


# ---- file contents (GNOME LocalSearch) --------------------------------------

def content_search_command(query: str, limit: int = 6) -> list[str] | None:
    for tool in ("localsearch", "tracker3"):
        if shutil.which(tool):
            return [tool, "search", "-l", str(limit), query]
    return None


def parse_content_results(output: str, home: Path, limit: int = 6) -> list[Path]:
    """Paths from LocalSearch/Tracker output, kept to visible files in home."""
    paths: list[Path] = []
    for match in re.finditer(r"file://(\S+)", output):
        path = Path(unquote(urlparse("file://" + match.group(1)).path))
        try:
            relative = path.relative_to(home)
        except ValueError:
            continue
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path not in paths and path.is_file():
            paths.append(path)
        if len(paths) >= limit:
            break
    return paths


def search_file_contents(query: str, home: Path | None = None, *, limit: int = 6,
                         timeout: float = 2.0) -> list[Path]:
    """Files whose text matches, via GNOME's existing index. Blocking: call
    from a worker thread. Returns [] if LocalSearch is not installed."""
    query = query.strip()
    if len(query) < 3:
        return []
    command = content_search_command(query, limit * 2)
    if command is None:
        return []
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, check=False,
                                env={**os.environ, "NO_COLOR": "1"})
    except (OSError, subprocess.TimeoutExpired):
        return []
    return parse_content_results(result.stdout, home or Path.home(), limit)
