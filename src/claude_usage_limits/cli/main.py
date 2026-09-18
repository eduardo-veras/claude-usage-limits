"""Argument parsing and entry point."""

import argparse
import json
import sys
from datetime import datetime

from rich.console import Console

import claude_usage_limits
from claude_usage_limits.core.fetcher import fetch_usage_text
from claude_usage_limits.core.parser import parse_usage
from claude_usage_limits.monitoring.live import run_loop
from claude_usage_limits.terminal.themes import (
    ASCII_GLYPHS,
    THEMES,
    build_theme,
    detect_theme,
    glyphs,
)
from claude_usage_limits.ui.layouts import build_dashboard


def run_once(as_json, console, view):
    text, error = fetch_usage_text()
    if error:
        console.print(f"[crit.bold]error:[/crit.bold] {error}")
        sys.exit(1)
    data = parse_usage(text)
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        console.print(build_dashboard(data, None, view=view, fetched_at=datetime.now()))



def main():
    parser = argparse.ArgumentParser(description=claude_usage_limits.__doc__)
    parser.add_argument("--once", action="store_true", help="Print once and exit (no loop).")
    parser.add_argument("--json", action="store_true", help="Print parsed data as JSON instead of a dashboard.")
    parser.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds (default: 60).")
    parser.add_argument(
        "--view",
        choices=["24h", "7d"],
        default="7d",
        help="Window shown in the What's Contributing panel (default: 7d). Tab switches it live on macOS/Linux.",
    )
    parser.add_argument(
        "--theme",
        choices=["auto", *THEMES],
        default="auto",
        help="Colour theme. auto picks light/dark from $COLORFGBG, else classic (default: auto).",
    )
    parser.add_argument("--ascii", action="store_true", help="No emoji or block characters (plain ASCII bars).")
    args = parser.parse_args()

    if args.ascii or "utf" not in (sys.stdout.encoding or "").lower():
        glyphs.update(ASCII_GLYPHS)
    theme = detect_theme() if args.theme == "auto" else args.theme
    console = Console(theme=build_theme(theme))

    if args.once or args.json:
        run_once(args.json, console, args.view)
        return

    run_loop(args.interval, console, args.view)
