"""Regenerate the intro banners. Install dependencies from scripts/requirements.txt first."""
from pathlib import Path
import base64

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
PHRASES = ["Hello, my name is Felix!", "Software Engineering Student", "I build Web & Mobile Apps."]


def headline(font, phrase, font_size=64, letter_spacing=0):
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    pen = SVGPathPen(glyphs)
    advance = 0
    positions = [0]
    for index, char in enumerate(phrase):
        glyph_name = cmap[ord(char)]
        glyphs[glyph_name].draw(TransformPen(pen, (1, 0, 0, 1, advance, 0)))
        advance += font['hmtx'][glyph_name][0]
        if index < len(phrase) - 1:
            advance += letter_spacing * font['head'].unitsPerEm / font_size
        positions.append(advance)
    scale = min(font_size / font['head'].unitsPerEm, 1040 / advance)
    return pen.getCommands(), advance * scale, scale, [x * scale for x in positions]


CYCLE_SECONDS = 24


def animate(attribute, frames):
    """Use one shared clock so every letter, cursor, and selection loops together."""
    states = dict(frames)
    states.setdefault(0, frames[0][1])
    states.setdefault(CYCLE_SECONDS, frames[-1][1])
    ordered = sorted(states.items())
    times = ';'.join(f'{time / CYCLE_SECONDS:.7f}' for time, _ in ordered)
    values = ';'.join(f'{value:.4f}' for _, value in ordered)
    return (f'<animate attributeName="{attribute}" values="{values}" '
            f'keyTimes="{times}" calcMode="discrete" dur="{CYCLE_SECONDS}s" '
            'repeatCount="indefinite"/>')


def letters(positions, start, end, erase=False):
    steps = list(reversed(positions)) if erase else positions
    return [(start + (end - start) * i / (len(steps) - 1), value)
            for i, value in enumerate(steps)]


def clipped_outline(identifier, outline, left, scale, frames, color):
    return (f'<defs><clipPath id="{identifier}"><rect x="{left}" y="140" '
            f'width="0" height="100">{animate("width", frames)}</rect></clipPath></defs>'
            f'<g clip-path="url(#{identifier})"><path d="{outline}" '
            f'transform="translate({left} 220) scale({scale} {-scale})" fill="{color}"/></g>')


def cursor(frames, accent, visible):
    return (f'<g opacity="0">{animate("opacity", visible)}'
            f'<rect x="{frames[0][1]}" y="155" width="3" height="72" fill="{accent}">'
            f'{animate("x", frames)}'
            '<animate attributeName="opacity" values="1;1;0;0" '
            'keyTimes="0;.48;.5;1" dur=".9s" repeatCount="indefinite"/>'
            '</rect></g>')


def greeting(font, support_font, color, accent):
    phrase = PHRASES[0]
    # Keep ordinary typing available if the greeting is later changed to omit Felix.
    if 'Felix' not in phrase:
        return typed_phrase(font, phrase, 0, 12, 'greeting', color, accent)
    split = phrase.index('Felix')
    prefix, name = phrase[:split], phrase[split:]
    _, width, scale, positions = headline(font, phrase)
    left = (1200 - width) / 2
    prefix_outline, _, _, prefix_positions = headline(font, prefix)
    prefix_width = positions[split]
    name_left = left + prefix_width
    # Preserve the original greeting's scale and origin while only the name changes.
    size = scale * font['head'].unitsPerEm
    prefix_outline, _, prefix_scale, prefix_positions = headline(font, prefix, size)
    original, original_width, original_scale, original_positions = headline(font, name, size)
    midar_font = TTFont(ROOT / 'assets' / 'fonts' / 'Midar.ttf')
    midar, midar_width, midar_scale, midar_positions = headline(midar_font, name, size)
    impact, impact_width, impact_scale, impact_positions = headline(support_font, name, size)
    prefix_done = .2 + 1.6 * split / len(phrase)
    prefix_frames = ([(0, 0)] + letters(prefix_positions, .2, prefix_done)
                     + letters(prefix_positions, 11.35, 11.8, erase=True))
    original_frames = ([(0, 0)] + letters(original_positions, prefix_done, 1.8)
                       + letters(original_positions, 2.9, 3.5, erase=True)
                       + letters(original_positions, 8.45, 9.2)
                       + letters(original_positions, 11.2, 11.35, erase=True))
    midar_frames = [(0, 0)] + letters(midar_positions, 3.8, 4.55) + [(6.1, 0)]
    impact_frames = ([(0, 0), (6.1, impact_width)]
                     + letters(impact_positions, 7.6, 8.2, erase=True))
    cursor_frames = ([(0, left + 7)]
                     + [(t, left + x + 7) for t, x in letters(prefix_positions, .2, prefix_done)]
                     + [(t, name_left + x + 7) for t, x in original_frames if t > 0 and t < 3.8]
                     + [(t, name_left + x + 7) for t, x in midar_frames if 3.8 <= t < 6.1]
                     + [(6.1, name_left + impact_width + 7)]
                     + [(t, name_left + x + 7) for t, x in letters(impact_positions, 7.6, 8.2, erase=True)]
                     + [(t, name_left + x + 7) for t, x in original_frames if t >= 8.45]
                     + [(t, left + x + 7) for t, x in letters(prefix_positions, 11.35, 11.8, erase=True)])
    selection = (f'<rect x="{name_left - 5}" y="151" width="{midar_width + 10}" '
                 'height="80" fill="#60a5fa" opacity="0">'
                 f'{animate("opacity", [(0, 0), (5.6, .4), (6.1, 0)])}</rect>')
    return ('<g class="typing-line" data-sequence="font-audition">'
            + clipped_outline('greeting-prefix', prefix_outline, left, prefix_scale, prefix_frames, color)
            + selection
            + clipped_outline('name-born2bsporty', original, name_left, original_scale, original_frames, color)
            + clipped_outline('name-midar', midar, name_left, midar_scale, midar_frames, color)
            + clipped_outline('name-impact', impact, name_left, impact_scale, impact_frames, color)
            + cursor(cursor_frames, accent, [(0, 1), (5.6, 0), (6.1, 1), (11.8, 0)])
            + '</g>')


def typed_phrase(font, phrase, start, end, identifier, color, accent):
    outline, width, scale, positions = headline(font, phrase)
    left = (1200 - width) / 2
    frames = ([(0, 0)] + letters(positions, start + .2, start + 1.8)
              + letters(positions, end - .8, end - .2, erase=True))
    return ('<g class="typing-line">'
            + clipped_outline(identifier, outline, left, scale, frames, color)
            + cursor([(t, left + x + 7) for t, x in frames], accent,
                     [(0, 0), (start, 1), (end - .2, 0)])
            + '</g>')


def banner(font, support_font):
    bg, fg, muted, accent = "#020617", "#ffffff", "#ffffff", "#ffffff"
    background = base64.b64encode((ROOT / 'assets' / 'intro-background.jpg').read_bytes()).decode('ascii')
    text = [greeting(font, support_font, fg, accent)]
    for i, phrase in enumerate(PHRASES[1:]):
        start = 12 + i * 6
        text.append(typed_phrase(font, phrase, start, start + 6, f'phrase-{i}', fg, accent))
    static_outline, static_width, static_scale, _ = headline(font, PHRASES[0])
    name_outline, name_width, name_scale, _ = headline(support_font, 'GREGORIUS FELIX CATON ERAWAN', font_size=22, letter_spacing=2)
    subtitle_outline, subtitle_width, subtitle_scale, _ = headline(support_font, 'Software Engineering \u00b7 Web & Mobile Development', font_size=24)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400" role="img" aria-labelledby="title description">
<title id="title">Hello, my name is Felix! Software Engineering Student.</title>
<desc id="description">An animated typing introduction for Gregorius Felix Caton Erawan, over a blue and black grid background.</desc>
<style>.static-text{{display:none}}@media(prefers-reduced-motion:reduce){{.typing-line{{display:none}}.static-text{{display:block}}}}</style>
<rect width="1200" height="400" fill="{bg}"/>
<image href="data:image/jpeg;base64,{background}" x="0" y="0" width="1200" height="400" preserveAspectRatio="xMidYMid slice"/>
<rect width="1200" height="400" fill="{bg}" opacity=".22"/>
<path aria-label="Gregorius Felix Caton Erawan" d="{name_outline}" transform="translate({(1200 - name_width) / 2} 132) scale({name_scale} {-name_scale})" fill="{accent}"/>
{''.join(text)}
<path class="static-text" d="{static_outline}" transform="translate({(1200 - static_width) / 2} 220) scale({static_scale} {-static_scale})" fill="{fg}"/>
<path aria-label="Software Engineering and Web and Mobile Development" d="{subtitle_outline}" transform="translate({(1200 - subtitle_width) / 2} 276) scale({subtitle_scale} {-subtitle_scale})" fill="{muted}"/>
</svg>
"""


if __name__ == '__main__':
    font = TTFont(ROOT / 'assets' / 'fonts' / 'born2bsporty-fs.otf')
    support_font = TTFont(ROOT / 'assets' / 'fonts' / 'impact.ttf')
    for dark in [False, True]:
        destination = ROOT / 'assets' / ('intro-dark.svg' if dark else 'intro.svg')
        destination.write_text(banner(font, support_font), encoding='utf-8', newline='\n')
        print(f'Generated {destination.relative_to(ROOT)}')
