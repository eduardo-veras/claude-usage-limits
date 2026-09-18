"""Dashboard panels."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from claude_usage_limits.terminal.themes import glyphs
from claude_usage_limits.ui.progress_bars import FACTOR_BAR_WIDTH, render_bar

LIMIT_ROWS = [
    ("session", "Session"),
    ("week", "Week (all models)"),
    ("fable", "Week (Fable)"),
]


def row_label(glyph, label):
    return f"{glyphs[glyph]} {label}".strip()


def build_limits_panel(data):
    table = Table.grid(padding=(0, 1))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True, overflow="fold")

    for key, label in LIMIT_ROWS:
        info = data.get(key)
        if info is None:
            table.add_row(row_label(key, label), render_bar(None), Text("no data", style="muted"))
            continue
        eta = info["eta"]
        reset_text = f"resets in {eta}" if eta else f"resets {info['resets']}"
        table.add_row(row_label(key, label), render_bar(info["pct"]), Text(reset_text, style="muted"))

    # Time-elapsed bars for the two underlying clocks (session=5h, week=7d;
    # "week" and "fable" share the same weekly clock so one row covers both).
    session_info = data.get("session")
    if session_info and session_info["elapsed_frac"] is not None:
        pct = round(session_info["elapsed_frac"] * 100)
        table.add_row(row_label("clock", "Session window"), render_bar(pct, style="elapsed"), Text("elapsed", style="muted"))
    else:
        table.add_row(row_label("clock", "Session window"), render_bar(None), Text("no data", style="muted"))

    week_info = data.get("week")
    if week_info and week_info["elapsed_frac"] is not None:
        pct = round(week_info["elapsed_frac"] * 100)
        table.add_row(row_label("clock", "Weekly window"), render_bar(pct, style="elapsed"), Text("elapsed", style="muted"))
    else:
        table.add_row(row_label("clock", "Weekly window"), render_bar(None), Text("no data", style="muted"))

    return Panel(
        table,
        title="[bold]Account-Wide Limits[/bold] [muted](from claude.ai, via /usage)[/muted]",
        border_style="border",
        padding=(1, 1),
        box=glyphs["box"],
    )


def render_toggle_hint(active, interactive=False):
    hint = Text()
    for key, label in (("24h", "Last 24h"), ("7d", "Last 7d")):
        style = "tab.bold" if key == active else "muted"
        hint.append(f" {label} ", style=style)
        hint.append(" ")
    hint.append("(press Tab to switch)" if interactive else "(choose with --view)", style="muted.italic")
    return hint


def build_contrib_panel(data, active, interactive=False):
    contrib = data.get("contrib") or {}
    block = contrib.get(active)

    body = [render_toggle_hint(active, interactive), Text("")]

    if not block:
        if any(contrib.values()):
            # /usage omits a window entirely when it has no activity.
            body.append(Text(f"No activity in the last {active}.", style="muted"))
        elif data.get("breakdown"):
            # Unrecognised format: show claude's own text rather than nothing.
            body.append(Text(data["breakdown"], style="muted"))
        else:
            body.append(Text("No usage breakdown available yet.", style="muted"))
        return Panel(Group(*body), title="[bold]What's Contributing[/bold]", border_style="border2", padding=(1, 1), box=glyphs["box"])

    body.append(Text(f"{block['requests']} requests {glyphs['sep']} {block['sessions']} sessions", style="bold"))
    body.append(Text(""))

    for pct, desc in block["factors"]:
        row = Text()
        row.append(render_bar(pct, width=FACTOR_BAR_WIDTH, style="factor"))
        row.append(f"  {desc}")
        body.append(row)

    for category, items in block["tops"]:
        if not items:
            continue
        body.append(Text(""))
        body.append(Text(f"Top {category}:", style="muted.bold"))
        for name, pct in items:
            row = Text("  ")
            row.append(render_bar(pct, width=FACTOR_BAR_WIDTH, style="top"))
            row.append(f"  {name}")
            body.append(row)

    return Panel(Group(*body), title="[bold]What's Contributing[/bold]", border_style="border2", padding=(1, 1), box=glyphs["box"])
