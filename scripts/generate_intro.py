"""Regenerate the intro banners. Install dependencies from scripts/requirements.txt first."""
from pathlib import Path
import base64

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
PHRASES = ["Hi, I'm Felix.", "Software Engineering Student", "I build web & mobile apps."]


def headline(font, phrase):
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    pen = SVGPathPen(glyphs)
    advance = 0
    positions = [0]
    for char in phrase:
        glyph_name = cmap[ord(char)]
        glyphs[glyph_name].draw(TransformPen(pen, (1, 0, 0, 1, advance, 0)))
        advance += font['hmtx'][glyph_name][0]
        positions.append(advance)
    scale = min(64 / font['head'].unitsPerEm, 1040 / advance)
    return pen.getCommands(), advance * scale, scale, [x * scale for x in positions]


def banner(font):
    bg, fg, muted, accent = "#020617", "#ffffff", "#dbeafe", "#bfdbfe"
    background = base64.b64encode((ROOT / 'assets' / 'intro-background.jpg').read_bytes()).decode('ascii')
    text = []
    for i, phrase in enumerate(PHRASES):
        outline, width, scale, positions = headline(font, phrase)
        left = (1200 - width) / 2
        count = len(phrase)
        times = [0] + [(.025 + .10 * n / count) for n in range(1, count + 1)] + [.27, .32, 1]
        widths = positions + [width, 0, 0]
        keys = ';'.join(f'{t:.5f}' for t in times)
        values = ';'.join(f'{w:.2f}' for w in widths)
        cursor_values = ';'.join(f'{left + w + 7:.2f}' for w in widths)
        timing = f'begin="{i * 6}s" dur="18s" repeatCount="indefinite"'
        text.append(f"""<defs><clipPath id="type-{i}"><rect x="{left}" y="140" width="0" height="100"><animate attributeName="width" values="{values}" keyTimes="{keys}" calcMode="discrete" {timing}/></rect></clipPath></defs>
<g class="typing-line" opacity="0"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.32;.321;1" {timing}/>
<g clip-path="url(#type-{i})"><path d="{outline}" transform="translate({left} 220) scale({scale} {-scale})" fill="{fg}"/></g>
<rect x="{left + 7}" y="155" width="3" height="72" fill="{accent}"><animate attributeName="x" values="{cursor_values}" keyTimes="{keys}" calcMode="discrete" {timing}/><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.48;.5;1" dur=".9s" repeatCount="indefinite"/></rect></g>""")
    static_outline, static_width, static_scale, _ = headline(font, PHRASES[0])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400" role="img" aria-labelledby="title description">
<title id="title">Hi, I'm Felix. Software Engineering Student.</title>
<desc id="description">An animated typing introduction for Gregorius Felix Caton Erawan, over a blue and black grid background.</desc>
<style>.static-text{{display:none}}@media(prefers-reduced-motion:reduce){{.typing-line{{display:none}}.static-text{{display:block}}}}</style>
<rect width="1200" height="400" fill="{bg}"/>
<image href="data:image/jpeg;base64,{background}" x="0" y="0" width="1200" height="400" preserveAspectRatio="xMidYMid slice"/>
<rect width="1200" height="400" fill="{bg}" opacity=".22"/>
<text x="600" y="132" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="14" letter-spacing="3" fill="{accent}">GREGORIUS FELIX CATON ERAWAN</text>
{''.join(text)}
<path class="static-text" d="{static_outline}" transform="translate({(1200 - static_width) / 2} 220) scale({static_scale} {-static_scale})" fill="{fg}"/>
<text x="600" y="276" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="17" fill="{muted}">Software Engineering &#183; Web &amp; Mobile Development</text>
</svg>
"""


if __name__ == '__main__':
    font = TTFont(ROOT / 'assets' / 'fonts' / 'Midar.ttf')
    for dark in [False, True]:
        destination = ROOT / 'assets' / ('intro-dark.svg' if dark else 'intro.svg')
        destination.write_text(banner(font), encoding='utf-8', newline='\n')
        print(f'Generated {destination.relative_to(ROOT)}')
