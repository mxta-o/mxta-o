"""Contribution data for the room: daily counts from GitHub, plus the streak maths."""
import datetime as dt
import html
import json
import os
import re
import urllib.request
from pathlib import Path

USER = "mxta-o"
FIRST_YEAR = 2022  # the year the account was created
CACHE = Path(__file__).resolve().parent.parent / ".cache" / "days.json"

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def _get(url, body=None, headers=None):
    req = urllib.request.Request(url, data=body, headers={"User-Agent": USER, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def _year_graphql(year, token):
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER, "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"}}).encode()
    out = json.loads(_get("https://api.github.com/graphql", body, {"Authorization": f"bearer {token}"}))
    weeks = out["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def _year_html(year):
    """Fallback without a token: the public calendar fragment, one tooltip per day."""
    page = _get(f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31")
    ids = dict(re.findall(r'data-date="([\d-]+)" id="([\w-]+)"', page))
    tips = {m[0]: html.unescape(m[1]) for m in re.findall(r'<tool-tip[^>]*for="([\w-]+)"[^>]*>([^<]*)</tool-tip>', page)}
    days = {}
    for date, cell in ids.items():
        n = re.match(r"([\d,]+) contribution", tips.get(cell, ""))
        days[date] = int(n.group(1).replace(",", "")) if n else 0
    return days


def load_days(refresh=True):
    """{iso_date: count} for every day from FIRST_YEAR to today."""
    if refresh or not CACHE.exists():
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        days = {}
        for year in range(FIRST_YEAR, dt.date.today().year + 1):
            days.update(_year_graphql(year, token) if token else _year_html(year))
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(days, sort_keys=True))
    today = dt.date.today().isoformat()
    return {d: n for d, n in json.loads(CACHE.read_text()).items() if d <= today}


def stats(days):
    dates = sorted(days)
    today = dt.date.fromisoformat(dates[-1])
    best = run = 0
    for d in dates:
        run = run + 1 if days[d] > 0 else 0
        best = max(best, run)
    # Today doesn't break the streak until it's over
    cursor = today if days[dates[-1]] > 0 else today - dt.timedelta(days=1)
    current = 0
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    year_ago = today.replace(year=today.year - 1).isoformat()
    return {
        "today": today,
        "total": sum(days.values()),
        "last_year": sum(n for d, n in days.items() if d > year_ago),
        "current": current,
        "longest": best,
    }
