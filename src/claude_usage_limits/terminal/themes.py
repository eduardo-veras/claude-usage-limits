"""Colour themes, glyph sets and light/dark background detection."""

import os

from rich import box
from rich.theme import Theme

# Foreground colours only; the terminal background is never touched. "classic"
# sticks to the 16 ANSI colours, which every terminal palette (Solarized,
# Dracula, ...) already tunes for its own background, so it is the safe default.
THEMES = {
    "classic": {
        "ok": "green", "warn": "yellow", "crit": "red", "accent": "cyan", "muted": "dim",
        "elapsed": "blue", "factor": "magenta", "top": "cyan", "border": "bright_blue",
        "border2": "dim", "tab": "reverse",
    },
    "dark": {
        "ok": "color(118)", "warn": "color(214)", "crit": "color(203)", "accent": "color(117)",
        "muted": "color(245)", "elapsed": "color(111)", "factor": "color(177)", "top": "color(117)",
        "border": "color(111)", "border2": "color(245)", "tab": "black on color(117)",
    },
    "light": {
        "ok": "color(22)", "warn": "color(166)", "crit": "color(124)", "accent": "color(19)",
        "muted": "color(243)", "elapsed": "color(19)", "factor": "color(90)", "top": "color(24)",
        "border": "color(19)", "border2": "color(243)", "tab": "white on color(19)",
    },
}

UNICODE_GLYPHS = {
    "full": "█", "empty": "░", "sep": "·", "warn": "⚠", "deco": "✦ ✧ ✦ ✧ ✦",
    "session": "💻", "week": "📅", "fable": "✨", "clock": "⏳", "box": box.ROUNDED,
}
ASCII_GLYPHS = {
    "full": "#", "empty": "-", "sep": "-", "warn": "!", "deco": "* * *",
    "session": "", "week": "", "fable": "", "clock": "", "box": box.ASCII,
}
glyphs = dict(UNICODE_GLYPHS)  # main() swaps in ASCII_GLYPHS for --ascii


def build_theme(name):
    """Rich Theme with `<style>.bold` / `<style>.italic` variants of every style.

    Rich cannot parse "bold accent" when `accent` is a theme name (it silently
    renders unstyled), so the variants have to be real theme entries.
    """
    styles = dict(THEMES[name])
    for key, value in THEMES[name].items():
        styles[f"{key}.bold"] = f"bold {value}"
        styles[f"{key}.italic"] = f"italic {value}"
    return Theme(styles)


def detect_theme(env=None):
    """COLORFGBG is "fg;bg" with bg an ANSI colour index; unset -> classic."""
    # ponytail: env var only. Upstream also does an OSC 11 terminal query; add
    # that if users on terminals without COLORFGBG ask for real auto-detection.
    env = os.environ if env is None else env
    try:
        bg = int(env.get("COLORFGBG", "").split(";")[-1])
    except ValueError:
        return "classic"
    return "light" if bg == 7 or bg >= 9 else "dark"
