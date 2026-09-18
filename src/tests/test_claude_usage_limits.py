from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from rich.console import Console

from claude_usage_limits.core import parser
from claude_usage_limits.terminal import themes
from claude_usage_limits.ui import components, layouts, progress_bars
from claude_usage_limits.utils import time_utils

SAMPLE = """\
Current session: 42% used · resets Sep 18 at 9pm (America/New_York)
Current week (all models): 81% used · resets Sep 21 at 1pm (America/New_York)
Current week (Fable): 7% used · resets Sep 21 at 1pm (America/New_York)

What's contributing to your limits usage?

Last 24h · 120 requests · 4 sessions
60% of your usage came from long conversations
Top models: fable 70%, opus 30%

Last 7d · 900 requests · 25 sessions
35% of your usage came from subagents
Top projects: repo-a 55%, repo-b 45%
"""

NY = ZoneInfo("America/New_York")


def test_parse_usage_headers():
    data = parser.parse_usage(SAMPLE)
    assert data["session"]["pct"] == 42
    assert data["week"]["pct"] == 81
    assert data["fable"]["pct"] == 7
    assert data["week"]["resets"] == "Sep 21 at 1pm (America/New_York)"


def test_parse_usage_contrib_blocks_stay_separate():
    contrib = parser.parse_usage(SAMPLE)["contrib"]
    assert contrib["24h"] == {
        "requests": 120,
        "sessions": 4,
        "factors": [(60, "came from long conversations")],
        "tops": [("models", [("fable", 70), ("opus", 30)])],
    }
    assert contrib["7d"]["requests"] == 900
    assert contrib["7d"]["tops"] == [("projects", [("repo-a", 55), ("repo-b", 45)])]


def test_parse_usage_garbage():
    data = parser.parse_usage("not logged in")
    assert data["session"] is None and data["week"] is None and data["breakdown"] == ""


def test_time_to_reset():
    now = datetime(2026, 9, 18, 18, 30, tzinfo=NY)
    eta, frac, remaining = time_utils.time_to_reset("Sep 18 at 9pm (America/New_York)", time_utils.SESSION_WINDOW_SECONDS, now)
    assert (eta, remaining) == ("2h 30m", 9000)
    assert frac == pytest.approx(0.5)

    eta, _, _ = time_utils.time_to_reset("Sep 21 at 1:15pm (America/New_York)", time_utils.WEEK_WINDOW_SECONDS, now)
    assert eta == "2d 18h"


@pytest.mark.parametrize("text,hour", [("12am", 0), ("12pm", 12), ("1am", 1), ("11pm", 23)])
def test_time_to_reset_12_hour_clock(text, hour):
    now = datetime(2026, 9, 18, 0, 0, tzinfo=NY)
    _, _, remaining = time_utils.time_to_reset(f"Sep 19 at {text} (America/New_York)", None, now)
    assert remaining == 86400 + hour * 3600


def test_time_to_reset_year_rollover_and_bad_input():
    now = datetime(2026, 12, 31, 23, 0, tzinfo=NY)
    assert time_utils.time_to_reset("Jan 1 at 1am (America/New_York)", None, now)[0] == "2h 0m"
    assert time_utils.time_to_reset("soon", None) == (None, None, None)
    assert time_utils.time_to_reset("Sep 18 at 9pm (Not/AZone)", None) == (None, None, None)


@pytest.mark.parametrize(
    "colorfgbg,theme",
    [("15;0", "dark"), ("0;15", "light"), ("0;7", "light"), ("12;8", "dark"), ("0;default;15", "light"), ("junk", "classic")],
)
def test_detect_theme(colorfgbg, theme):
    assert themes.detect_theme({"COLORFGBG": colorfgbg}) == theme
    assert themes.detect_theme({}) == "classic"


def test_render_bar():
    assert progress_bars.render_bar(50, width=10).plain == "[█████░░░░░]  50%"
    assert progress_bars.render_bar(250, width=10).plain == "[██████████] 250%"
    assert progress_bars.render_bar(None, width=4).plain == "[░░░░]  --"
    assert [progress_bars.threshold_style(p) for p in (0, 49, 50, 79, 80)] == ["ok", "ok", "warn", "warn", "crit"]


@pytest.mark.parametrize("theme", themes.THEMES)
def test_dashboard_renders_in_every_theme(theme):
    # Catches a style name used in the code but missing from a theme.
    assert set(themes.THEMES[theme]) == set(themes.THEMES["classic"])
    console = Console(theme=themes.build_theme(theme), width=100, record=True, force_terminal=True)
    data = parser.parse_usage(SAMPLE)
    for view in ("24h", "7d"):
        console.print(layouts.build_dashboard(data, None, countdown=5, view=view))
    console.print(layouts.build_dashboard({}, "boom"))
    out = console.export_text()
    assert "Account-Wide Limits" in out and "repo-a" in out and "boom" in out


def test_ascii_glyphs(monkeypatch):
    for key, value in themes.ASCII_GLYPHS.items():
        monkeypatch.setitem(themes.glyphs, key, value)
    console = Console(theme=themes.build_theme("classic"), width=100, record=True)
    console.print(layouts.build_dashboard(parser.parse_usage(SAMPLE), None, countdown=5))
    assert console.export_text().isascii()


def test_missing_window_does_not_dump_raw_text():
    data = parser.parse_usage(SAMPLE.replace("Last 24h", "Last 99h"))
    console = Console(theme=themes.build_theme("classic"), width=100, record=True)
    console.print(components.build_contrib_panel(data, "24h"))
    out = console.export_text()
    assert "No activity in the last 24h" in out and "repo-a" not in out


def test_bold_variants_are_actually_styled():
    # rich silently drops unparseable styles like "bold accent"; check the ANSI output.
    console = Console(theme=themes.build_theme("classic"), width=100, record=True, force_terminal=True, color_system="standard")
    console.print(layouts.build_dashboard(parser.parse_usage(SAMPLE), None))
    out = console.export_text(styles=True)
    assert "\x1b[1;36mCLAUDE ACCOUNT USAGE MONITOR" in out  # bold cyan title
    assert "\x1b[1;31m 81%" in out  # bold red percentage
    assert "\x1b[1;7m Last 24h " in out  # bold reverse active tab
