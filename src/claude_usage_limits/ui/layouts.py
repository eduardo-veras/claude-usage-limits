"""Top-level dashboard layout."""

from datetime import datetime

from rich.align import Align
from rich.console import Group
from rich.text import Text

from claude_usage_limits.terminal.themes import glyphs
from claude_usage_limits.ui.components import build_contrib_panel, build_limits_panel


def build_dashboard(data, error, countdown=None, view="24h", fetched_at=None):
    lines = []

    title = Text(justify="center")
    title.append(f"{glyphs['deco']}  ", style="muted")
    title.append("CLAUDE ACCOUNT USAGE MONITOR", style="accent.bold")
    title.append(f"  {glyphs['deco']}", style="muted")
    lines.append(Align.center(title))
    lines.append(Text(""))

    if error:
        lines.append(Text(f"{glyphs['warn']} {error}", style="crit.bold"))
        return Group(*lines)

    lines.append(build_limits_panel(data))
    lines.append(build_contrib_panel(data, view))

    stamp = (fetched_at or datetime.now()).strftime("%H:%M:%S")
    footer = Text(f"Last updated {stamp}", style="muted")
    if countdown is not None:
        sep = glyphs["sep"]
        footer.append(f"  {sep}  refreshing in {countdown}s  {sep}  Ctrl+C to exit")
    lines.append(footer)

    return Group(*lines)
