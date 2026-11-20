from __future__ import annotations

"""Render the profile README as a stack of animated, print-inspired SVG cards."""
import base64
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "cards"
DATA = ROOT / "contributions.json"
STATIC = os.getenv("STATIC") == "1"
PAPER = "#F6F5F0"
INK = "#10131A"
BLUE = "#1748D5"
BLUE_DARK = "#0D2D82"
GRID = "#C9D1DE"
PALE_BLUE = "#E2E9F8"
MUTED = "#4C5668"
WHITE = "#FFFFFF"

REPOS = [
    {"slug": "xmum-navigate", "name": "XMUM Navigate", "eyebrow": "FINAL YEAR PROJECT", "description": "A campus companion for navigation, venue recommendations, and canteen information.", "stack": "React · Vite · Node.js · PostgreSQL", "url": "https://github.com/GregoriusFelix/xmum-navigate"},
    {"slug": "project-tracker", "name": "Project Tracker", "eyebrow": "FULL STACK APPLICATION", "description": "A project and task manager with a React interface and an ASP.NET Core API.", "stack": "React · C# · ASP.NET Core · SQL Server", "url": "https://github.com/GregoriusFelix/Project_Tracker"},
    {"slug": "xmum-navigate-mobile", "name": "XMUM Navigate · Mobile", "eyebrow": "MOBILE APP", "description": "A Flutter campus companion with sign in, profiles, and campus content.", "stack": "Flutter · Dart · Firebase", "url": "https://github.com/GregoriusFelix/Mobile-App_XMUM-Navigate"},
    {"slug": "svv-project", "name": "SVV Project", "eyebrow": "REGISTRATION / AUTH", "description": "A travel site with registration, email verification, validation, and bcrypt hashing.", "stack": "Node.js · Express · MySQL", "url": "https://github.com/GregoriusFelix/SVV_Project"},
    {"slug": "pacman-ai-search", "name": "Pac-Man AI Search", "eyebrow": "GAME AI", "description": "A Godot Pac-Man project exploring search and ghost pathfinding.", "stack": "Godot · GDScript · AI Search", "url": "https://github.com/GregoriusFelix/Pac-Man-AI-Search"},
    {"slug": "the-grind", "name": "The Grind", "eyebrow": "WEB DESIGN", "description": "A café website with menu, ordering, gallery, loyalty, and careers pages.", "stack": "HTML · CSS", "url": "https://github.com/GregoriusFelix/The_Grind"},
]
TILES = [
    ("LinkedIn", "LET'S CONNECT", "https://www.linkedin.com/in/gregorius-felix-caton-erawan-751789239/", "CONTACT"),
    ("Résumé", "VIEW PDF", "assets/Gregorius%20Felix%20Caton%20Erawan_Resume.pdf", "EXPERIENCE"),
    ("GitHub", "BROWSE PROJECTS", "https://github.com/GregoriusFelix?tab=repositories", "SOURCE"),
]


def esc(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def subset_fonts():
    exe = shutil.which("pyftsubset")
    if not exe:
        raise SystemExit("pyftsubset not found. Install fonttools: python -m pip install fonttools")
    chars = "0123456789/·↗é’&.,:!?-+()" + "Gregorius Felix Caton ErawanSoftware Engineering student building web and mobile applicationsLinkedIn LET'S CONNECTRésumé VIEW PDFGitHub BROWSE PROJECTSXMUM NavigateProject TrackerMobileSVV ProjectPac-Man AI SearchThe GrindFINAL YEAR PROJECT FULL STACK MOBILE APP REGISTRATION AUTH GAME AI WEB DESIGNCONTRIBUTIONS LAST 12 MONTHS ACTIVITY PAST YEAR STREAK ACTIVE DAYS BUSIEST DAY CLASS OF"
    fonts = {}
    for key, filename in (("editorial", "Dico.ttf"), ("label", "impact.ttf")):
        source = ROOT / "assets" / "fonts" / filename
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / f"{key}.woff"
            subprocess.run([exe, str(source), f"--output-file={target}", "--flavor=woff", f"--text={chars}"], check=True, stdout=subprocess.DEVNULL)
            fonts[key] = base64.b64encode(target.read_bytes()).decode("ascii")
    return fonts


def svg_start(title: str, desc: str, width: int, height: int, fonts: dict[str, str], delay: float = 0) -> str:
    entrance = "animation:none" if STATIC else f"animation:print-in .9s cubic-bezier(.16,1,.3,1) {delay:.2f}s both"
    title_motion = "animation:none" if STATIC else "animation:ink-reveal .85s cubic-bezier(.16,1,.3,1) .15s both"
    style = f'''<style>
@font-face{{font-family:DicoEditorial;src:url(data:font/woff;base64,{fonts['editorial']}) format('woff')}}
@font-face{{font-family:FelixLabel;src:url(data:font/woff;base64,{fonts['label']}) format('woff')}}
*{{box-sizing:border-box}}.enter{{transform-box:fill-box;transform-origin:center;{entrance}}}
.headline{{{title_motion}}}
@keyframes print-in{{from{{opacity:0;transform:translate(18px,12px) rotate(.7deg)}}to{{opacity:1;transform:translate(0) rotate(0)}}}}
@keyframes ink-reveal{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 0 0 0)}}}}
.paper-grid{{fill:url(#paper-grid)}}.sm-motion{{display:inline}}.sm-final{{display:none}}
@media(prefers-reduced-motion:reduce){{.enter,.headline{{animation:none}}.sm-motion{{display:none}}.sm-final{{display:inline}}}}
</style>'''
    defs = f'<defs><pattern id="paper-grid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="{GRID}" stroke-width="1"/></pattern><pattern id="halftone" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{INK}" opacity=".52"/></pattern></defs>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{esc(title)}</title><desc id="desc">{esc(desc)}</desc>{style}{defs}')


def paper(width: int, height: int) -> str:
    return (f'<rect width="{width}" height="{height}" fill="{PAPER}"/>'
            f'<rect width="{width}" height="{height}" class="paper-grid" opacity=".68"/>')


def save(name: str, svg: str):
    (OUTPUT / name).write_text(svg + "</svg>\n", encoding="utf-8", newline="\n")


def optional_portrait() -> str | None:
    for name, mime in (("profile.png", "image/png"), ("profile.jpg", "image/jpeg"), ("profile.jpeg", "image/jpeg"), ("profile.webp", "image/webp")):
        path = ROOT / "assets" / name
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f'data:{mime};base64,{encoded}'
    return None


def contribution_data():
    if not DATA.exists():
        raise SystemExit("contributions.json is missing. Run the scheduled workflow once to fetch it.")
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    calendar = raw.get("data", {}).get("user", {}).get("contributionsCollection", {}).get("contributionCalendar")
    if calendar:
        days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
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
    recent = days[-365:]
    positive = {day for day, value in recent if value > 0}
    today = date.today()
    cursor = today if today in positive else today - timedelta(days=1)
    streak = 0
    while cursor in positive:
        streak += 1
        cursor -= timedelta(days=1)
    busiest, count = max(recent, key=lambda item: (item[1], item[0]))
    active = sum(1 for _, value in recent if value > 0)
    return by_month, streak, active, busiest, count


def heatmap(days, x: int, y: int, cell: int, gap: int, limit: int = 53, animate: bool = True) -> str:
    first = days[0][0]
    padded = [(None, 0)] * ((first.weekday() + 1) % 7) + days
    weeks = [padded[index:index + 7] for index in range(0, len(padded), 7)]
    while len(weeks[-1]) < 7:
        weeks[-1].append((None, 0))
    output = []
    for week_index, week in enumerate(weeks[:limit]):
        for row, (day, value) in enumerate(week):
            if day is None:
                continue
            left, top = x + week_index * (cell + gap), y + row * (cell + gap)
            opacity = .12 if value == 0 else .36 if value < 2 else .66 if value < 5 else 1
            if animate and not STATIC:
                output.append(f'<rect class="sm-motion" x="{left}" y="{top}" width="{cell}" height="{cell}" fill="{BLUE}" opacity="{opacity}"><animate attributeName="opacity" values="0;{opacity}" dur=".55s" begin="{1.1+week_index*.012:.2f}s" fill="freeze"/></rect>')
                output.append(f'<rect class="sm-final" x="{left}" y="{top}" width="{cell}" height="{cell}" fill="{BLUE}" opacity="{opacity}"/>')
            else:
                output.append(f'<rect x="{left}" y="{top}" width="{cell}" height="{cell}" fill="{BLUE}" opacity="{opacity}"/>')
    return ''.join(output)


def emit_hero(fonts, days):
    width, height = 1200, 570
    svg = svg_start("Gregorius Felix Caton Erawan", "Software Engineering student building web and mobile applications.", width, height, fonts, 0)
    svg += paper(width, height)
    svg += '<path d="M822 0h378v570H988l-229-271z" fill="#1748D5"/><path d="M985 0h215v570h-120L850 272z" fill="url(#halftone)"/>'
    svg += f'<g class="enter"><text x="58" y="68" fill="{INK}" font-family="FelixLabel,Impact,sans-serif" font-size="16" letter-spacing="2">SOFTWARE ENGINEERING  /  XMUM</text><text x="58" y="94" fill="{MUTED}" font-family="Arial,sans-serif" font-size="14">MALAYSIA · CLASS OF 2027</text></g>'
    svg += f'<g class="headline" fill="{INK}" font-family="DicoEditorial,Georgia,serif"><text x="48" y="219" font-size="77">Gregorius</text><text x="35" y="329" fill="{BLUE}" font-size="130">Felix</text><text x="55" y="387" font-size="50">Caton Erawan</text></g>'
    svg += f'<path d="M66 416h320" stroke="{INK}" stroke-width="1.5"/><text x="65" y="461" fill="{INK}" font-family="Arial,sans-serif" font-size="14">Software Engineering student building web and mobile applications.</text>'
    # The contribution field acts as a data-led print plate in the collage.
    svg += '<path d="M456 166l641-91 59 283-658 96z" fill="#102D83" opacity=".18"/>'
    svg += '<g transform="rotate(-5 790 260)"><g class="enter"><rect x="448" y="118" width="665" height="298" fill="#FCFCFA" stroke="#11141A" stroke-width="2"/><text x="478" y="160" fill="#10131A" font-family="FelixLabel,Impact,sans-serif" font-size="15" letter-spacing="2">FIELD NOTES / SOFTWARE</text><text x="1080" y="160" text-anchor="end" fill="#4C5668" font-family="Arial,sans-serif" font-size="13">XMUM · MALAYSIA</text><path d="M478 178h606" stroke="#10131A" stroke-width="1"/>'
    svg += f'<rect x="478" y="188" width="606" height="197" fill="{BLUE}"/><rect x="478" y="188" width="606" height="197" fill="url(#halftone)" opacity=".28"/>'
    svg += heatmap(days, 496, 216, 10, 5, limit=37)
    svg += f'<text x="478" y="404" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">Final-year project · currently in development</text></g></g>'
    portrait = optional_portrait()
    if portrait:
        svg += f'<g transform="rotate(7 1070 107)"><g class="enter"><rect x="966" y="34" width="208" height="146" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/><image href="{portrait}" x="975" y="43" width="190" height="128" preserveAspectRatio="xMidYMid slice"/></g></g>'
    # A smaller paper proof overlaps the activity panel, like a print laid over a contact sheet.
    svg += f'<g transform="rotate(6 540 442)"><g class="enter"><rect x="414" y="385" width="308" height="132" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/><rect x="423" y="394" width="290" height="114" fill="url(#paper-grid)" opacity=".6"/><text x="442" y="427" fill="{BLUE}" font-family="FelixLabel,Impact,sans-serif" font-size="13" letter-spacing="2">IN PROGRESS</text><text x="440" y="466" fill="{INK}" font-family="DicoEditorial,Georgia,serif" font-size="27">XMUM Navigate</text><text x="442" y="491" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">Campus companion · web and mobile</text></g></g>'
    # Thin registration marks and the folio number carry the poster's print language.
    svg += f'<path d="M387 117c26-16 37-41 40-74 3 33 16 58 43 74-27 13-40 35-43 67-4-32-16-54-40-67zM1113 459c16-11 24-26 26-47 2 21 10 36 27 47-17 9-25 22-27 43-2-21-10-34-26-43z" fill="none" stroke="{BLUE}" stroke-width="1.4"/><text x="1122" y="536" fill="{WHITE}" font-family="FelixLabel,Impact,sans-serif" font-size="64">06</text>'
    save("hero.svg", svg)


def emit_tile(fonts, index, tile):
    title, subtitle, url, eyebrow = tile
    width, height = 390, 126
    delay = .8 + index * .14
    svg = svg_start(title, subtitle, width, height, fonts, delay)
    svg += paper(width, height)
    svg += f'<g class="enter"><path d="M1 1h388v124H1z" fill="none" stroke="{INK}" stroke-width="1"/><text x="22" y="31" fill="{BLUE}" font-family="FelixLabel,Impact,sans-serif" font-size="12" letter-spacing="2">{eyebrow}</text><text x="20" y="79" fill="{INK}" font-family="DicoEditorial,Georgia,serif" font-size="34">{esc(title)}</text><text x="22" y="105" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12" letter-spacing="1">{esc(subtitle)}</text><path d="M344 82h22m-8-8 8 8-8 8" fill="none" stroke="{BLUE}" stroke-width="2"/></g>'
    save(f"tile-{index+1}.svg", svg)


def emit_months(fonts, days):
    by_month, streak, active, busiest, count = contribution_stats(days)
    months = sorted(by_month)[-12:]
    width, height = 1200, 330
    svg = svg_start("Contribution activity by month", "Monthly GitHub contributions, current streak, active days, and busiest day.", width, height, fonts, 1.45)
    svg += paper(width, height)
    svg += f'<text x="46" y="61" fill="{INK}" font-family="DicoEditorial,Georgia,serif" font-size="34">Work, month by month</text><text x="1153" y="56" text-anchor="end" fill="{BLUE}" font-family="FelixLabel,Impact,sans-serif" font-size="13" letter-spacing="2">CONTRIBUTIONS / 12 MONTHS</text>'
    metrics = [("CURRENT STREAK", f"{streak} days"), ("ACTIVE DAYS", str(active)), ("BUSIEST DAY", f"{busiest.strftime('%b %d')} · {count}")]
    for index, (label, value) in enumerate(metrics):
        x = 48 + index * 375
        svg += f'<g class="enter"><path d="M{x} 82v59" stroke="{GRID}" stroke-width="1"/><text x="{x+16}" y="99" fill="{MUTED}" font-family="FelixLabel,Impact,sans-serif" font-size="12" letter-spacing="1.5">{label}</text><text x="{x+14}" y="134" fill="{INK}" font-family="DicoEditorial,Georgia,serif" font-size="28">{esc(value)}</text></g>'
    chart_x, chart_y, chart_w, chart_h, gap = 50, 179, 1100, 103, 14
    max_value = max([by_month[month] for month in months] or [1]) or 1
    bar_w = (chart_w - gap * (len(months)-1)) / len(months)
    for index, month in enumerate(months):
        value = by_month[month]
        bar_h = max(3, chart_h * value / max_value)
        x = chart_x + index * (bar_w + gap)
        y = chart_y + chart_h - bar_h
        animated_class = ' class="sm-motion"' if not STATIC else ""
        svg += f'<rect{animated_class} x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{BLUE}" opacity=".92">'
        if not STATIC:
            svg += f'<animate attributeName="height" values="0;{bar_h:.1f}" dur=".72s" begin="{1.75+index*.045:.2f}s" fill="freeze"/><animate attributeName="y" values="{chart_y+chart_h};{y:.1f}" dur=".72s" begin="{1.75+index*.045:.2f}s" fill="freeze"/>'
        svg += '</rect>'
        if not STATIC:
            svg += f'<rect class="sm-final" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{BLUE}" opacity=".92"/>'
        svg += f'<text x="{x+bar_w/2:.1f}" y="{max(chart_y+12,y-6):.1f}" text-anchor="middle" fill="{INK}" font-family="Arial,sans-serif" font-size="11">{value}</text>'
        svg += f'<text x="{x+bar_w/2:.1f}" y="{chart_y+chart_h+20}" text-anchor="middle" fill="{MUTED}" font-family="FelixLabel,Impact,sans-serif" font-size="11">{date.fromisoformat(month+"-01").strftime("%b").upper()}</text>'
    save("contributions-monthly.svg", svg)


def emit_repo(fonts, repo, index):
    heights = [278, 238, 220, 220, 202, 202]
    width, height = 1200, heights[index]
    delay = 2.2 + index * .16
    svg = svg_start(repo["name"], repo["description"], width, height, fonts, delay)
    svg += paper(width, height)
    svg += f'<g class="enter">'
    if index in (0, 3, 5):
        svg += f'<path d="M0 0h132v{height}H0z" fill="{BLUE}"/><text x="28" y="{height//2+22}" fill="{WHITE}" font-family="FelixLabel,Impact,sans-serif" font-size="42">{index+1:02d}</text><path d="M132 0v{height}" stroke="{INK}" stroke-width="1"/>'
        left = 177
    else:
        svg += f'<path d="M0 {height-7}h1200v7H0z" fill="{BLUE}"/>'
        svg += f'<text x="1142" y="{height//2+14}" text-anchor="end" fill="{BLUE}" font-family="FelixLabel,Impact,sans-serif" font-size="43">{index+1:02d}</text>'
        left = 48
    svg += f'<text x="{left}" y="48" fill="{BLUE}" font-family="FelixLabel,Impact,sans-serif" font-size="13" letter-spacing="2">{esc(repo["eyebrow"])}</text>'
    title_size = 42 if index < 2 else 35
    title_y = 104 if index < 2 else 98
    svg += f'<text x="{left-3}" y="{title_y}" fill="{INK}" font-family="DicoEditorial,Georgia,serif" font-size="{title_size}">{esc(repo["name"])}</text>'
    desc_y = title_y + 38
    svg += f'<text x="{left}" y="{desc_y}" fill="{INK}" font-family="Arial,sans-serif" font-size="17">{esc(repo["description"])}</text>'
    stack_y = height - 26
    svg += f'<text x="{left}" y="{stack_y}" fill="{MUTED}" font-family="FelixLabel,Impact,sans-serif" font-size="13" letter-spacing="1">{esc(repo["stack"])}</text>'
    svg += '</g>'
    save(f"repo-{repo['slug']}.svg", svg)


def emit_graph(fonts, days):
    width, height = 1200, 260
    svg = svg_start("GitHub contribution graph", "A year of daily GitHub activity in cobalt blue.", width, height, fonts, 3.3)
    svg += f'<rect width="{width}" height="{height}" fill="{BLUE}"/><rect width="{width}" height="{height}" fill="url(#halftone)" opacity=".2"/>'
    svg += f'<g class="enter"><text x="40" y="51" fill="{WHITE}" font-family="DicoEditorial,Georgia,serif" font-size="31">A year of showing up</text><text x="1153" y="49" text-anchor="end" fill="{WHITE}" font-family="FelixLabel,Impact,sans-serif" font-size="13" letter-spacing="2">GITHUB / PAST YEAR</text><path d="M40 68h1110" stroke="{WHITE}" stroke-width="1" opacity=".55"/>'
    svg += heatmap(days, 42, 93, 14, 5, limit=53)
    svg += f'<text x="1150" y="232" text-anchor="end" fill="{WHITE}" font-family="FelixLabel,Impact,sans-serif" font-size="12" letter-spacing="1">LESS   ·   ·   ·   ·   MORE</text></g>'
    save("contributions-graph.svg", svg)


def main():
    OUTPUT.mkdir(exist_ok=True)
    fonts = subset_fonts()
    days = contribution_data()
    emit_hero(fonts, days)
    for index, tile in enumerate(TILES):
        emit_tile(fonts, index, tile)
    emit_months(fonts, days)
    for index, repo in enumerate(REPOS):
        emit_repo(fonts, repo, index)
    emit_graph(fonts, days)
    print(f"Rendered 12 SVG cards in {OUTPUT.relative_to(ROOT)} (STATIC={int(STATIC)}).")


if __name__ == "__main__":
    main()
