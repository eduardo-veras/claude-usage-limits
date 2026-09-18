"""Percentage bars."""

from rich.text import Text

from claude_usage_limits.terminal.themes import glyphs

BAR_WIDTH = 30
FACTOR_BAR_WIDTH = 16



def threshold_style(pct):
    if pct >= 80:
        return "crit"
    if pct >= 50:
        return "warn"
    return "ok"


def render_bar(pct, width=BAR_WIDTH, style=None):
    bar = Text()
    bar.append("[", style="muted")
    if pct is None:
        bar.append(glyphs["empty"] * width, style="muted")
        bar.append("] ", style="muted")
        bar.append(" --", style="muted")
        return bar
    filled = max(0, min(width, int(width * pct / 100)))
    style = style or threshold_style(pct)
    bar.append(glyphs["full"] * filled, style=style)
    bar.append(glyphs["empty"] * (width - filled), style="muted")
    bar.append("] ", style="muted")
    bar.append(f"{pct:3d}%", style=f"{style}.bold")
    return bar
