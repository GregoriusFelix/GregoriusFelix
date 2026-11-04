"""Regenerate the intro banners. Install dependencies from scripts/requirements.txt first."""
from pathlib import Path
import base64
import hashlib
import re

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


GREETING_SECONDS = 9
FONT_VARIANT_SECONDS = .8
FONT_SELECTION_SECONDS = .2
CYCLE_SECONDS = GREETING_SECONDS + 6 * (len(PHRASES) - 1)


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


def greeting(font, color, accent):
    phrase = PHRASES[0]
    if 'Felix' not in phrase:
        return typed_phrase(font, phrase, 0, GREETING_SECONDS, 'greeting', color, accent)
    split = phrase.index('Felix')
    prefix, name = phrase[:split], phrase[split:]
    switch_start = 3.0
    variant_fonts = [
        ('dico', 'Dico.ttf'),
        ('minecraft', 'Minecraft.ttf'),
        ('ari-w9500', 'ari-w9500-condensed-display.ttf'),
        ('determination', 'determination.ttf'),
    ]
    switch_end = round(switch_start + len(variant_fonts) * FONT_VARIANT_SECONDS, 3)
    _, width, scale, positions = headline(font, phrase)
    left = (1200 - width) / 2
    name_left = left + positions[split]
    size = scale * font['head'].unitsPerEm
    prefix_outline, _, prefix_scale, prefix_positions = headline(font, prefix, size)
    original, original_width, original_scale, original_positions = headline(font, name, size)
    prefix_done = .2 + 1.6 * split / len(phrase)
    finish = GREETING_SECONDS - .2
    erase_start = finish - .8
    name_erased = erase_start + .8 * len(name) / len(phrase)
    prefix_erase = letters(prefix_positions, name_erased, finish, erase=True)
    name_erase = letters(original_positions, erase_start, name_erased, erase=True)
    prefix_frames = [(0, 0)] + letters(prefix_positions, .2, prefix_done) + prefix_erase
    original_frames = ([(0, 0)] + letters(original_positions, prefix_done, 1.8)
                       + [(switch_start, 0), (switch_end, original_width)] + name_erase)
    cursor_frames = ([(0, left + 7)]
                     + [(t, left + x + 7) for t, x in letters(prefix_positions, .2, prefix_done)]
                     + [(t, name_left + x + 7) for t, x in letters(original_positions, prefix_done, 1.8)])
    cursor_visibility = [(0, 1)]
    outlines = [clipped_outline('greeting-prefix', prefix_outline, left, prefix_scale, prefix_frames, color),
                clipped_outline('name-born2bsporty', original, name_left, original_scale, original_frames, color)]
    selections = []

    def select_name(selected_width, switch_time):
        selections.append(f'<rect x="{name_left - 5}" y="151" width="{selected_width + 10}" '
                          'height="80" fill="#60a5fa" opacity="0">'
                          f'{animate("opacity", [(0, 0), (switch_time - FONT_SELECTION_SECONDS, .4), (switch_time, 0)])}</rect>')
        cursor_visibility.extend([(switch_time - FONT_SELECTION_SECONDS, 0), (switch_time, 1)])

    select_name(original_width, switch_start)
    # Each selected name changes font in place; its letters never disappear individually.
    for index, (identifier, filename) in enumerate(variant_fonts):
        start = round(switch_start + index * FONT_VARIANT_SECONDS, 3)
        end = round(start + FONT_VARIANT_SECONDS, 3)
        trial_font = TTFont(ROOT / 'assets' / 'fonts' / filename)
        outline, trial_width, trial_scale, _ = headline(trial_font, name, size)
        frames = [(0, 0), (start, trial_width), (end, 0)]
        cursor_frames.append((start, name_left + trial_width + 7))
        select_name(trial_width, end)
        outlines.append(clipped_outline(f'name-{identifier}', outline, name_left, trial_scale, frames, color))
    cursor_frames.append((switch_end, name_left + original_width + 7))
    cursor_frames += [(t, name_left + x + 7) for t, x in name_erase]
    cursor_frames += [(t, left + x + 7) for t, x in prefix_erase]
    cursor_visibility.append((finish, 0))
    return ('<g class="typing-line" data-sequence="font-audition">'
            + ''.join(selections) + ''.join(outlines)
            + cursor(cursor_frames, accent, cursor_visibility) + '</g>')


def typed_phrase(font, phrase, start, end, identifier, color, accent):
    outline, width, scale, positions = headline(font, phrase)
    left = (1200 - width) / 2
    frames = ([(0, 0)] + letters(positions, start + .2, start + 1.8)
              + letters(positions, end - 1, end - .2, erase=True))
    return ('<g class="typing-line">'
            + clipped_outline(identifier, outline, left, scale, frames, color)
            + cursor([(t, left + x + 7) for t, x in frames], accent,
                     [(0, 0), (start, 1), (end - .2, 0)])
            + '</g>')


def banner(font, support_font):
    bg, fg, muted, accent = "#020617", "#ffffff", "#ffffff", "#ffffff"
    background = base64.b64encode((ROOT / 'assets' / 'intro-background.jpg').read_bytes()).decode('ascii')
    text = [greeting(font, fg, accent)]
    for i, phrase in enumerate(PHRASES[1:]):
        start = GREETING_SECONDS + i * 6
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
    readme = ROOT / 'README.md'
    contents = readme.read_text(encoding='utf-8')
    current_versions = set()
    for filename in ['intro.svg', 'intro-dark.svg']:
        asset = ROOT / 'assets' / filename
        version = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        versioned = asset.with_name(f'{asset.stem}-{version}.svg')
        versioned.write_bytes(asset.read_bytes())
        current_versions.add(versioned.name)
        pattern = (r'assets/' + re.escape(asset.stem)
                   + r'(?:-[0-9a-f]{12})?\.svg(?:\?v=[A-Za-z0-9_-]+)?(?=")')
        contents = re.sub(pattern, f'assets/{versioned.name}', contents)
    readme.write_text(contents, encoding='utf-8', newline='\n')
    # Remove only outdated files generated by this content-versioning scheme.
    for previous in (ROOT / 'assets').glob('intro-*.svg'):
        if (re.fullmatch(r'intro(?:-dark)?-[0-9a-f]{12}\.svg', previous.name)
                and previous.name not in current_versions):
            previous.unlink()
    print('Updated README to content-versioned image filenames.')
