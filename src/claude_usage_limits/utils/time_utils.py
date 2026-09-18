"""Parse the reset timestamps printed by /usage."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

SESSION_WINDOW_SECONDS = 5 * 3600
WEEK_WINDOW_SECONDS = 7 * 24 * 3600
WINDOW_SECONDS = {"session": SESSION_WINDOW_SECONDS, "week": WEEK_WINDOW_SECONDS, "fable": WEEK_WINDOW_SECONDS}

RESET_RE = re.compile(
    r"(?P<mon>[A-Za-z]{3}) (?P<day>\d{1,2}) at "
    r"(?P<hour>\d{1,2})(?::(?P<min>\d{2}))?(?P<ampm>am|pm) \((?P<tz>[^)]+)\)"
)

MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}



def time_to_reset(reset_str, window_seconds, now=None):
    """'Sep 21 at 1pm (America/New_York)' -> ('3d 3h', elapsed_fraction, remaining_seconds)."""
    m = RESET_RE.search(reset_str)
    if not m or m.group("mon") not in MONTHS:
        return None, None, None

    try:
        tz = ZoneInfo(m.group("tz"))
    except Exception:
        return None, None, None

    now = now or datetime.now(tz)
    hour = int(m.group("hour"))
    minute = int(m.group("min") or 0)
    if m.group("ampm") == "pm":
        hour = 12 if hour == 12 else hour + 12
    else:
        hour = 0 if hour == 12 else hour

    reset_dt = datetime(now.year, MONTHS[m.group("mon")], int(m.group("day")), hour, minute, tzinfo=tz)
    if reset_dt < now:
        reset_dt = reset_dt.replace(year=now.year + 1)

    remaining = int((reset_dt - now).total_seconds())
    days, rem = divmod(remaining, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        eta = f"{days}d {hours}h"
    elif hours:
        eta = f"{hours}h {minutes}m"
    else:
        eta = f"{minutes}m"

    elapsed_frac = None
    if window_seconds:
        elapsed_frac = max(0.0, min(1.0, 1 - remaining / window_seconds))

    return eta, elapsed_frac, remaining
