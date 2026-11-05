#!/usr/bin/env python3
"""Builds README.md from live GitHub API data + pyfiglet ASCII art."""
import os, json, datetime as dt, urllib.request, collections
import pyfiglet

U = "Paraspandey-debugs"
NAME = ["PARAS", "PANDEY"]
TOK = os.environ.get("GITHUB_TOKEN", "")

def call(url, data=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": U}
    if TOK: h["Authorization"] = f"Bearer {TOK}"
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def safe(f, default):
    try: return f()
    except Exception as e:
        print("API fallback:", e); return default

user = safe(lambda: call(f"https://api.github.com/users/{U}"), None)
repos = safe(lambda: call(f"https://api.github.com/users/{U}/repos?per_page=100&sort=pushed"), None)
live = bool(user and repos)

if not live:  # offline snapshot
    user = {"public_repos": 50, "followers": 17, "following": 15, "created_at": "2024-08-13T15:10:24Z"}
    repos = [
        {"name": "Relay", "language": "Go", "stargazers_count": 5, "fork": False, "description": "Terminal-native download manager"},
        {"name": "nn-from-zero", "language": "Jupyter Notebook", "stargazers_count": 1, "fork": False, "description": "Neural net from scratch in NumPy"},
    ]

own = [r for r in repos if not r["fork"]]
stars = sum(r["stargazers_count"] for r in own)
langs = collections.Counter(r["language"] for r in own if r["language"])
tot = sum(langs.values()) or 1

def fig(t, font="ansi_shadow"):
    return "\n".join(l.rstrip() for l in pyfiglet.figlet_format(t, font=font).split("\n")).strip("\n")

banner = "\n\n".join(fig(w) for w in NAME)

# language bars
bars = []
for l, c in langs.most_common(6):
    p = c / tot
    n = round(p * 24)
    bars.append(f"{l:<17} {'█'*n}{'░'*(24-n)} {p*100:5.1f}%")
lang_block = "\n".join(bars)

# repo table
top = sorted(own, key=lambda r: (r["stargazers_count"], r.get("pushed_at", "")), reverse=True)[:6]
rows = []
for r in top:
    d = (r.get("description") or "")[:44]
    rows.append(f"║ {r['name'][:20]:<20} ║ {(r['language'] or '-')[:16]:<16} ║ ★ {r['stargazers_count']:<3} ║ {d:<44} ║")
W = (22, 18, 7, 46)
line = lambda a, b, c: a + b.join("═" * w for w in W) + c
table = "\n".join([line("╔", "╦", "╗"),
    f"║ {'REPO':<20} ║ {'LANG':<16} ║ {'STAR':<5} ║ {'ABOUT':<44} ║",
    line("╠", "╬", "╣"), *rows, line("╚", "╩", "╝")])

# ASCII contribution heatmap (needs token for GraphQL)
heat = ""
if TOK:
    q = {"query": '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount weekday}}}}}}' % U}
    g = safe(lambda: call("https://api.github.com/graphql", json.dumps(q).encode()), None)
    try:
        cal = g["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        grid = [[" "] * len(cal["weeks"]) for _ in range(7)]
        mx = max(d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]) or 1
        for i, w in enumerate(cal["weeks"]):
            for d in w["contributionDays"]:
                c = d["contributionCount"]
                grid[d["weekday"]][i] = "·" if c == 0 else "░▒▓█"[min(3, int(c / mx * 3.99))]
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        heat = f"{cal['totalContributions']} contributions in the last year\n\n" + "\n".join(f"{days[i]} {''.join(r)}" for i, r in enumerate(grid))
    except Exception as e:
        print("heatmap skipped:", e)

since = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
yrs = (dt.datetime.now(dt.timezone.utc) - since).days / 365
now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def row(a, b):
    return f"│ {a:<18}│ {b:<18}│"
stats = "\n".join([
    "┌" + "─"*19 + "┬" + "─"*19 + "┐",
    row(f"repos       {user['public_repos']}", f"followers   {user['followers']}"),
    row(f"stars       {stars}", f"following   {user['following']}"),
    row(f"on GitHub   {yrs:.1f}y", f"updated  {now[5:10]}"),
    "└" + "─"*19 + "┴" + "─"*19 + "┘"])

lang_section = f"### `$ github --languages`\n\n```text\n{lang_block}\n```\n\n" if live else ""

md = f"""<div align="center">

```
{banner}
```

**B.Tech · IIIT Allahabad** &nbsp;|&nbsp; algorithms · systems · ML

[![LinkedIn](https://img.shields.io/badge/LinkedIn-paraspandeydev-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://in.linkedin.com/in/paraspandeydev)
![Followers](https://img.shields.io/github/followers/{U}?style=flat-square&logo=github&label=followers)
![Views](https://komarev.com/ghpvc/?username={U}&style=flat-square&color=00ff9f&label=views)

</div>

```text
$ whoami
paras_pandey

$ cat about.txt
┌────────────────────────────────────────────────────────┐
│ studying   : 3rd-year B.Tech, IIIT Allahabad           │
│ role       : Placement Representative                  │
│ into       : DSA, competitive programming, CS core     │
│ building   : CLI tools, ML from scratch                │
│ contribute : open source                               │
└────────────────────────────────────────────────────────┘
```

### `$ github --stats`

```text
{stats}
```

{lang_section}### `$ github --top-repos`

```text
{table}
```
"""
if heat:
    md += f"\n### `$ github --activity`\n\n```text\n{heat}\n```\n"
md += f"""
### `$ contact`

```text
[in]  linkedin.com/in/paraspandeydev
[gh]  github.com/{U}
```

<sub>auto-generated from the GitHub API · {now}</sub>
"""
open("README.md", "w").write(md)
print("live data" if live else "OFFLINE snapshot", "-> README.md written")
