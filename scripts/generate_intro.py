"""Regenerate the animated SVG introductions using only the Python standard library."""
from pathlib import Path
from html import escape
import math
import random

ROOT = Path(__file__).resolve().parents[1]
PHRASES = ["Hi, I'm Felix.", "Software Engineering Student", "I build web & mobile apps."]


def banner(dark=False):
    bg, fg, muted, accent = ("#0d1117", "#f0f6fc", "#9aaab7", "#67d7ca") if dark else ("#ffffff", "#182f36", "#526872", "#0f766e")
    rng = random.Random(27)
    points = [(rng.randint(-35, 1235), rng.randint(-25, 425)) for _ in range(85)]
    lines, dots = [], []
    for i, (x, y) in enumerate(points):
        dots.append(f'<circle cx="{x}" cy="{y}" r="{rng.choice([1.4, 1.8, 2.2])}" fill="{muted}" opacity=".45"/>')
        for nx, ny in points[i + 1:]:
            distance = math.hypot(x - nx, y - ny)
            if distance < 145:
                opacity = .18 * (1 - distance / 180)
                lines.append(f'<line x1="{x}" y1="{y}" x2="{nx}" y2="{ny}" stroke="{muted}" stroke-width=".8" opacity="{opacity:.3f}"/>')
    text = []
    for i, phrase in enumerate(PHRASES):
        width = len(phrase) * 28.8
        left = (1200 - width) / 2
        count = len(phrase)
        times = [0] + [(.025 + .10 * n / count) for n in range(1, count + 1)] + [.27, .32, 1]
        widths = [0] + [width * n / count for n in range(1, count + 1)] + [width, 0, 0]
        keys = ';'.join(f'{t:.5f}' for t in times)
        values = ';'.join(f'{w:.2f}' for w in widths)
        cursor_values = ';'.join(f'{left + w + 7:.2f}' for w in widths)
        timing = f'begin="{i * 6}s" dur="18s" repeatCount="indefinite"'
        text.append(f"""<defs><clipPath id="type-{i}"><rect x="{left}" y="160" width="0" height="72"><animate attributeName="width" values="{values}" keyTimes="{keys}" calcMode="discrete" {timing}/></rect></clipPath></defs>
<g class="typing-line" opacity="0"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.32;.321;1" {timing}/>
<text x="{left}" y="216" font-family="'Courier New',monospace" font-size="48" font-weight="700" textLength="{width}" lengthAdjust="spacingAndGlyphs" clip-path="url(#type-{i})" fill="{fg}">{escape(phrase)}</text>
<rect x="{left + 7}" y="170" width="3" height="52" fill="{accent}"><animate attributeName="x" values="{cursor_values}" keyTimes="{keys}" calcMode="discrete" {timing}/><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.48;.5;1" dur=".9s" repeatCount="indefinite"/></rect></g>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400" role="img" aria-labelledby="title description">
<title id="title">Hi, I'm Felix. Software Engineering Student.</title>
<desc id="description">An animated typing introduction for Gregorius Felix Caton Erawan, with a moving network of dots and connecting lines.</desc>
<style>.static-text{{display:none}}@media(prefers-reduced-motion:reduce){{.typing-line{{display:none}}.static-text{{display:block}}.network-motion{{display:none}}}}</style>
<rect width="1200" height="400" fill="{bg}"/>
<g class="network-motion">{''.join(lines)}{''.join(dots)}<animateTransform attributeName="transform" type="translate" values="-8,-5;8,5;-8,-5" dur="20s" repeatCount="indefinite"/></g>
<rect x="100" y="122" width="1000" height="155" rx="24" fill="{bg}" opacity=".9"/>
<text x="600" y="132" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="14" letter-spacing="3" fill="{accent}">GREGORIUS FELIX CATON ERAWAN</text>
{''.join(text)}
<text class="static-text" x="600" y="216" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="52" font-weight="700" fill="{fg}">Hi, I'm Felix.</text>
<text x="600" y="276" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="17" fill="{muted}">Software Engineering &#183; Web &amp; Mobile Development</text>
</svg>
"""


if __name__ == '__main__':
    for dark in [False, True]:
        destination = ROOT / 'assets' / ('intro-dark.svg' if dark else 'intro.svg')
        destination.write_text(banner(dark), encoding='utf-8', newline='\n')
        print(f'Generated {destination.relative_to(ROOT)}')
