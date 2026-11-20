from __future__ import annotations

"""Render the profile README's animated SVG cards. Requires pyftsubset (fonttools)."""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "cards"
DATA = ROOT / "contributions.json"
STATIC = os.getenv("STATIC") == "1"
INK = "#182F36"
PANEL = "#20434B"
TEAL = "#0F766E"
BLUE = "#245F73"
PALE = "#D9F2EF"
MUTED = "#A7C5C8"
WHITE = "#F4FAF9"

REPOS = [
    {"slug": "xmum-navigate", "name": "XMUM Navigate", "eyebrow": "FINAL YEAR PROJECT", "description": "A campus companion for navigation, venue recommendations, and canteen information.", "stack": "React · Vite · Node.js · PostgreSQL", "url": "https://github.com/GregoriusFelix/xmum-navigate"},
    {"slug": "project-tracker", "name": "Project Tracker", "eyebrow": "FULL STACK", "description": "A project and task manager with a React interface and an ASP.NET Core API.", "stack": "React · C# · ASP.NET Core · SQL Server", "url": "https://github.com/GregoriusFelix/Project_Tracker"},
    {"slug": "xmum-navigate-mobile", "name": "XMUM Navigate · Mobile", "eyebrow": "MOBILE APP", "description": "A Flutter campus companion with sign in, profiles, and campus content.", "stack": "Flutter · Dart · Firebase", "url": "https://github.com/GregoriusFelix/Mobile-App_XMUM-Navigate"},
    {"slug": "svv-project", "name": "SVV Project", "eyebrow": "AUTHENTICATION", "description": "A travel site with registration, email verification, validation, and bcrypt hashing.", "stack": "Node.js · Express · MySQL", "url": "https://github.com/GregoriusFelix/SVV_Project"},
    {"slug": "pacman-ai-search", "name": "Pac-Man AI Search", "eyebrow": "GAME AI", "description": "A Godot Pac-Man project exploring search and ghost pathfinding.", "stack": "Godot · GDScript · AI Search", "url": "https://github.com/GregoriusFelix/Pac-Man-AI-Search"},
    {"slug": "the-grind", "name": "The Grind", "eyebrow": "WEB DESIGN", "description": "A café website with menu, ordering, gallery, loyalty, and careers pages.", "stack": "HTML · CSS", "url": "https://github.com/GregoriusFelix/The_Grind"},
]
TILES = [
    ("LinkedIn", "LET'S CONNECT", "https://www.linkedin.com/in/gregorius-felix-caton-erawan-751789239/", "01 / CONTACT"),
    ("Résumé", "VIEW PDF", "https://github.com/GregoriusFelix/GregoriusFelix/blob/main/assets/Gregorius%20Felix%20Caton%20Erawan_Resume.pdf", "02 / EXPERIENCE"),
    ("GitHub", "BROWSE PROJECTS", "https://github.com/GregoriusFelix?tab=repositories", "03 / SOURCE"),
]


def esc(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def subset_fonts():
    exe = shutil.which("pyftsubset")
    if not exe:
        raise SystemExit("pyftsubset not found. Install fonttools: python -m pip install fonttools")
    chars = "0123456789/·↗é’&.,:!?-" + "Gregorius Felix Caton ErawanSoftware Engineering student building web and mobile applicationsLinkedIn LET'S CONNECTRésumé VIEW PDFGitHub BROWSE PROJECTSXMUM NavigateProject TrackerMobileSVV ProjectPac-Man AI SearchThe GrindFINAL YEAR PROJECT FULL STACK MOBILE APP AUTHENTICATION GAME AI WEB DESIGN"
    fonts = {}
    for key, filename in (("display", "born2bsporty-fs.otf"), ("body", "impact.ttf")):
        source = ROOT / "assets" / "fonts" / filename
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / f"{key}.woff"
            subprocess.run([exe, str(source), f"--output-file={target}", "--flavor=woff", f"--text={chars}"], check=True, stdout=subprocess.DEVNULL)
            fonts[key] = base64.b64encode(target.read_bytes()).decode("ascii")
    return fonts


def svg_start(title: str, desc: str, width: int, height: int, fonts: dict[str, str], delay: float = 0) -> str:
    enter_motion = "animation:none" if STATIC else f"animation:rise .72s cubic-bezier(.2,.75,.25,1) {delay:.2f}s both"
    style = f'''<style>
@font-face{{font-family:FelixDisplay;src:url(data:font/woff;base64,{fonts['display']}) format('woff')}}
@font-face{{font-family:FelixBody;src:url(data:font/woff;base64,{fonts['body']}) format('woff')}}
*{{box-sizing:border-box}}.enter{{transform-box:fill-box;transform-origin:center;{enter_motion}}}
@keyframes rise{{from{{opacity:0;transform:translateY(15px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:.72}}50%{{opacity:1}}}}
.sm-motion{{display:inline}}.sm-final{{display:none}}
@media(prefers-reduced-motion:reduce){{.enter{{animation:none}}.sm-motion{{display:none}}.sm-final{{display:inline}}}}
</style>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">{esc(desc)}</desc>{style}'


def card_bg(width: int, height: int, label: str = "PROFILE / 01") -> str:
    return (f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="22" fill="{INK}" stroke="{BLUE}" stroke-width="2"/>'
            f'<path d="M22 2h{width-44}" stroke="{TEAL}" stroke-width="4" stroke-linecap="round"/>'
            f'<text x="34" y="38" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="13" letter-spacing="2">{esc(label)}</text>')


def save(name: str, svg: str):
    (OUTPUT / name).write_text(svg + "</svg>\n", encoding="utf-8", newline="\n")


def contribution_data():
    if not DATA.exists():
        raise SystemExit("contributions.json is missing. Run the scheduled workflow once to fetch it.")
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    # Accept the raw GitHub GraphQL response written by the workflow, or a flat {days: [...]} fixture.
    calendar = raw.get("data", {}).get("user", {}).get("contributionsCollection", {}).get("contributionCalendar")
    if calendar:
        days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
    else:
        days = raw.get("days", [])
    start, end = date.today() - timedelta(days=364), date.today()
    parsed = [(date.fromisoformat(day["date"]), int(day["contributionCount"])) for day in days
              if start <= date.fromisoformat(day["date"]) <= end]
    if not parsed:
        raise SystemExit("contributions.json has no contribution days.")
    return sorted(parsed)


def contribution_stats(days):
    by_month = defaultdict(int)
    for day, count in days:
        by_month[day.strftime("%Y-%m")] += count
    recent = days[-366:]
    today = date.today()
    positive = {d for d, n in recent if n > 0}
    cursor = today if today in positive else today - timedelta(days=1)
    streak = 0
    while cursor in positive:
        streak += 1
        cursor -= timedelta(days=1)
    busiest, count = max(recent, key=lambda item: (item[1], item[0]))
    active = sum(1 for _, n in recent if n > 0)
    return by_month, streak, active, busiest, count


def emit_hero(fonts):
    width, height = 1200, 310
    svg = svg_start("Gregorius Felix Caton Erawan", "Software Engineering student building web and mobile applications.", width, height, fonts, 0)
    svg += card_bg(width, height, "GREGORIUS FELIX  /  SOFTWARE ENGINEERING")
    portrait = next((ROOT / "assets" / name for name in ("profile.png", "profile.jpg", "profile.jpeg", "profile.webp") if (ROOT / "assets" / name).exists()), None)
    if portrait:
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[portrait.suffix.lower()]
        encoded = base64.b64encode(portrait.read_bytes()).decode("ascii")
        svg += f'<defs><clipPath id="portrait-clip"><circle cx="1050" cy="158" r="78"/></clipPath></defs><image href="data:{mime};base64,{encoded}" x="972" y="80" width="156" height="156" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait-clip)"/>'
    else:
        svg += '<circle cx="1050" cy="158" r="96" fill="#245F73" opacity=".45"/><circle cx="1050" cy="158" r="72" fill="#0F766E" opacity=".35"/><path d="M1006 170l29 27 61-72" fill="none" stroke="#D9F2EF" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" opacity=".8"/>'
    svg += f'<g class="enter"><text x="54" y="142" fill="{WHITE}" font-family="FelixDisplay,Arial,sans-serif" font-size="49">Gregorius Felix Caton Erawan</text><text x="58" y="192" fill="{PALE}" font-family="FelixBody,Arial,sans-serif" font-size="23">Software Engineering student building web and mobile applications.</text><rect x="58" y="231" width="230" height="38" rx="19" fill="{TEAL}"/><text x="77" y="256" fill="{WHITE}" font-family="FelixBody,Arial,sans-serif" font-size="14" letter-spacing="1">XMUM · CLASS OF 2027</text></g>'
    save("hero.svg", svg)


def emit_tile(fonts, index, tile):
    title, subtitle, url, eyebrow = tile
    width, height = 390, 118
    svg = svg_start(title, subtitle, width, height, fonts, (index + 1) * .12)
    svg += f'<a href="{esc(url)}" target="_blank"><g class="enter">{card_bg(width, height, eyebrow)}<text x="30" y="78" fill="{WHITE}" font-family="FelixDisplay,Arial,sans-serif" font-size="28">{esc(title)}</text><text x="{width-28}" y="78" text-anchor="end" fill="{PALE}" font-family="FelixBody,Arial,sans-serif" font-size="12" letter-spacing="1">{esc(subtitle)} ↗</text></g></a>'
    save(f"tile-{index+1}.svg", svg)


def emit_months(fonts, days):
    by_month, streak, active, busiest, count = contribution_stats(days)
    months = sorted(by_month)[-12:]
    width, height = 1200, 310
    svg = svg_start("Contribution activity by month", "Monthly GitHub contributions with current streak, active days, and busiest day.", width, height, fonts, .3)
    svg += card_bg(width, height, "CONTRIBUTIONS  /  LAST 12 MONTHS")
    metrics = [("STREAK", f"{streak} days"), ("ACTIVE DAYS", str(active)), ("BUSIEST DAY", f"{busiest.strftime('%b %d')} · {count}")]
    for i, (label, value) in enumerate(metrics):
        x = 36 + i * 370
        svg += f'<g class="enter"><text x="{x}" y="83" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="13" letter-spacing="2">{label}</text><text x="{x}" y="127" fill="{WHITE}" font-family="FelixDisplay,Arial,sans-serif" font-size="34">{esc(value)}</text></g>'
    chart_x, chart_y, chart_w, chart_h = 52, 174, 1096, 92
    max_value = max([by_month[m] for m in months] or [1]) or 1
    gap = 14
    bar_w = (chart_w - gap * (len(months)-1)) / len(months)
    for i, month in enumerate(months):
        value = by_month[month]
        bh = max(3, chart_h * value / max_value)
        x = chart_x + i * (bar_w + gap)
        y = chart_y + chart_h - bh
        cls = "sm-motion" if not STATIC else ""
        animation = "" if STATIC else f'<animate attributeName="height" values="0;{bh:.1f}" dur=".8s" begin="{.6+i*.035:.2f}s" fill="freeze"/><animate attributeName="y" values="{chart_y+chart_h};{y:.1f}" dur=".8s" begin="{.6+i*.035:.2f}s" fill="freeze"/>'
        svg += f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="6" fill="{TEAL}" opacity=".9">{animation}</rect>'
        if not STATIC:
            svg += f'<rect class="sm-final" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="6" fill="{TEAL}" opacity=".9"/>'
        svg += f'<text x="{x+bar_w/2:.1f}" y="{max(chart_y+13, y-7):.1f}" text-anchor="middle" fill="{WHITE}" font-family="FelixBody,Arial,sans-serif" font-size="11">{value}</text>'
        svg += f'<text x="{x+bar_w/2:.1f}" y="289" text-anchor="middle" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="12">{date.fromisoformat(month+"-01").strftime("%b")}</text>'
    save("contributions-monthly.svg", svg)


def emit_repo(fonts, repo, index):
    width, height = 1200, 250
    svg = svg_start(repo["name"], repo["description"], width, height, fonts, .45 + index * .12)
    svg += f'<a href="{esc(repo["url"])}" target="_blank"><g class="enter">{card_bg(width, height, "FEATURED REPOSITORY  /  " + repo["eyebrow"])}'
    svg += f'<text x="40" y="112" fill="{WHITE}" font-family="FelixDisplay,Arial,sans-serif" font-size="42">{esc(repo["name"])}</text><text x="42" y="155" fill="{PALE}" font-family="FelixBody,Arial,sans-serif" font-size="18">{esc(repo["description"])}</text><text x="42" y="204" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="14" letter-spacing="1">{esc(repo["stack"])}</text><circle cx="1110" cy="122" r="34" fill="{TEAL}"/><path d="M1097 122h26m-12-12 12 12-12 12" stroke="{WHITE}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g></a>'
    save(f"repo-{repo['slug']}.svg", svg)


def emit_graph(fonts, days):
    # Keep the graph's original calendar columns and recolor them with the profile teal.
    width, height = 1200, 240
    svg = svg_start("GitHub contribution graph", "Daily contributions over the past year shown in Gregorius Felix's teal brand colour.", width, height, fonts, 1.15)
    svg += card_bg(width, height, "GITHUB ACTIVITY  /  PAST YEAR")
    svg += f'<text x="38" y="77" fill="{WHITE}" font-family="FelixDisplay,Arial,sans-serif" font-size="27">A year of showing up</text>'
    start_x, start_y, size, gap = 42, 101, 13, 5
    # Left pad to a Sunday so weekday rows stay aligned.
    first = days[0][0]
    padded = [(None, 0)] * first.weekday() + days
    weeks = [padded[i:i+7] for i in range(0, len(padded), 7)]
    while len(weeks[-1]) < 7:
        weeks[-1].append((None, 0))
    months_seen = set()
    for wi, week in enumerate(weeks[:53]):
        for weekday, (day, value) in enumerate(week):
            if day is None:
                continue
            x, y = start_x + wi * (size + gap), start_y + weekday * (size + gap)
            alpha = .18 if value == 0 else .42 if value < 2 else .68 if value < 5 else 1
            motion = "sm-motion" if not STATIC else ""
            anim = "" if STATIC else f'<animate attributeName="opacity" values="0;{alpha}" dur=".6s" begin="{1.2+wi*.012:.2f}s" fill="freeze"/>'
            svg += f'<rect class="{motion}" x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="{TEAL}" opacity="{alpha}">{anim}</rect>'
            if not STATIC:
                svg += f'<rect class="sm-final" x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="{TEAL}" opacity="{alpha}"/>'
        if week and week[0][0] and week[0][0].strftime("%b") not in months_seen:
            months_seen.add(week[0][0].strftime("%b"))
            svg += f'<text x="{start_x+wi*(size+gap)}" y="220" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="11">{week[0][0].strftime("%b")}</text>'
    svg += f'<text x="1105" y="220" text-anchor="end" fill="{MUTED}" font-family="FelixBody,Arial,sans-serif" font-size="12">LESS  <tspan fill="{TEAL}">■ ■ ■ ■</tspan>  MORE</text>'
    save("contributions-graph.svg", svg)


def main():
    OUTPUT.mkdir(exist_ok=True)
    fonts = subset_fonts()
    days = contribution_data()
    emit_hero(fonts)
    for i, tile in enumerate(TILES):
        emit_tile(fonts, i, tile)
    emit_months(fonts, days)
    for i, repo in enumerate(REPOS):
        emit_repo(fonts, repo, i)
    emit_graph(fonts, days)
    print(f"Rendered 12 SVG cards in {OUTPUT.relative_to(ROOT)} (STATIC={int(STATIC)}).")


if __name__ == "__main__":
    main()

