"""Layout guard for the generated SVG assets.

Catches the failures that are invisible in code review but obvious on screen:
text overflowing the canvas, text colliding with other text, and text running
into reserved art zones (the hero orbit, the card illustrations).

Pillow is used for real font metrics when available; without it the checker
falls back to a per-character advance estimate so it still runs stdlib-only.
"""

from __future__ import annotations

import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NS = '{http://www.w3.org/2000/svg}'
# the only assets that draw illustration in the right-hand corridor
CAP = 0.35          # cap height as a fraction of the em
CSS_KEYWORDS = {'none', 'initial', 'inherit', 'unset', 'running', 'paused'}
ART_ASSETS = {'astra.svg', 'primeproxy.svg', 'primerouter.svg'}

# single source of truth: the checker reads the grid straight off the generator,
# so a moved axis can never leave the two files disagreeing
sys.path.insert(0, str(ROOT / 'scripts'))
from build_assets import (AXIS, DIV, HEAD_EYEBROW, HEAD_SIZE, HEAD_SUB,  # noqa: E402
                          HEAD_TITLE, RIGHT, SPINE_X, TEXT)

FONT_FILES = {
    ('sans', False): r'C:\Windows\Fonts\segoeui.ttf',
    ('sans', True): r'C:\Windows\Fonts\segoeuib.ttf',
    ('mono', False): r'C:\Windows\Fonts\consola.ttf',
    ('mono', True): r'C:\Windows\Fonts\consolab.ttf',
}
# conservative per-character advance as a fraction of font-size
FALLBACK_ADVANCE = {'mono': 0.55, 'sans': 0.52}

_font_cache: dict = {}


def measure(text: str, family: str, size: float, bold: bool) -> float:
    """Advance width of `text` at `size` px, in user units."""
    try:
        from PIL import ImageFont
    except ImportError:
        return len(text) * size * FALLBACK_ADVANCE[family]
    key = (family, bold, round(size))
    if key not in _font_cache:
        path = FONT_FILES[(family, bold)]
        _font_cache[key] = ImageFont.truetype(path, int(round(size)))
    font = _font_cache[key]
    try:
        return font.getlength(text)
    except Exception:
        return len(text) * size * FALLBACK_ADVANCE[family]


def vmetrics(family: str, size: float, bold: bool) -> tuple[float, float]:
    try:
        from PIL import ImageFont
    except ImportError:
        return size * 0.8, size * 0.2
    key = (family, bold, round(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_FILES[(family, bold)], int(round(size)))
    ascent, descent = _font_cache[key].getmetrics()
    return ascent, descent


def ink_height(text: str, family: str, size: float, bold: bool) -> tuple[float, float]:
    """Vertical extent of a text run relative to its baseline.

    Real glyph ink, not the font's nominal ascent/descent: the difference is
    what stops a 112px headline from being reported as touching the caption
    above it. Falls back to cap-height/descender heuristics without Pillow.
    """
    try:
        from PIL import ImageFont
    except ImportError:
        has_desc = any(ch in 'gjpqyдцщGJQРб()' for ch in text)
        top = -0.73 * size
        return top, (0.22 * size if has_desc else 0.06 * size)
    key = (family, bold, round(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_FILES[(family, bold)], int(round(size)))
    font = _font_cache[key]
    ascent, _ = font.getmetrics()
    box = font.getbbox(text)  # measured from the ascender line
    return box[1] - ascent, box[3] - ascent


def parse_transform(node, parents):
    """Accumulated (angle_deg, ox, oy) rotation from the ancestor chain."""
    angle, ox, oy = 0.0, 0.0, 0.0
    chain = []
    cursor = parents.get(node)
    while cursor is not None:
        raw = cursor.get('transform')
        if raw:
            chain.append(raw)
        cursor = parents.get(cursor)
    for raw in reversed(chain):
        m = re.match(r'rotate\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?(?:[\s,]+(-?[\d.]+))?\s*\)', raw.strip())
        if m:
            angle += float(m.group(1))
            ox = float(m.group(2) or 0)
            oy = float(m.group(3) or 0)
    return angle, ox, oy


def rotate_box(box, angle, ox, oy):
    if not angle:
        return box
    rad = math.radians(angle)
    ca, sa = math.cos(rad), math.sin(rad)
    x0, y0, x1, y1 = box
    pts = []
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        dx, dy = x - ox, y - oy
        pts.append((ox + dx * ca - dy * sa, oy + dx * sa + dy * ca))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def split_lines(node):
    """Break a <text> into rendered lines, honouring <br/>.

    Without this a two-line paragraph measured as one run and reported a bogus
    overflow, because ''.join(itertext()) silently drops the line break.
    """
    lines, cur = [], node.text or ''

    def walk(el):
        nonlocal cur
        for child in el:
            tag = child.tag.split('}')[-1]
            if tag == 'br':
                lines.append(cur)
                cur = child.tail or ''
                continue
            walk(child)
            if child.tail:
                cur += child.tail

    walk(node)
    lines.append(cur)
    return [ln for ln in lines if ln.strip()] or ['']


def text_boxes(root):
    boxes = []
    for node in root.iter(f'{NS}text'):
        size = float(node.get('font-size', 16))
        family = 'mono' if 'mono' in (node.get('class') or '') else 'sans'
        weight = int(node.get('font-weight', 400))
        tracking = float(node.get('letter-spacing', 0) or 0)
        x, y = float(node.get('x', 0)), float(node.get('y', 0))
        anchor = node.get('text-anchor', 'start')
        lines = split_lines(node)
        for i, content in enumerate(lines):
            baseline = y + i * size * 1.2  # SVG default line-height
            # a textLength pin is authoritative: the browser fits the run to it,
            # so the font's natural advance no longer describes what gets painted
            pinned = node.get('textLength')
            if pinned:
                width = float(pinned)
            else:
                width = measure(content, family, size, weight >= 600) + tracking * len(content)
            left = x
            if anchor == 'end':
                left -= width
            elif anchor == 'middle':
                left -= width / 2
            top, bottom = ink_height(content, family, size, weight >= 600)
            label = content if len(lines) == 1 else f'{content} (line {i + 1})'
            boxes.append({'label': label, 'box': (left, baseline + top, left + width, baseline + bottom),
                          'size': size, 'family': family})
    return boxes


def has_mask(node, parents):
    """True when an ancestor clips its subtree through a <mask>.

    The hero wordmark sheen is a plain rect confined to the glyphs by a mask, so
    its raw bbox overlaps type that is never actually painted over.
    """
    cursor = node
    while cursor is not None:
        if cursor.get('mask'):
            return True
        cursor = parents.get(cursor)
    return False


def shape_boxes(root, tags=(f'{NS}rect', f'{NS}circle', f'{NS}ellipse')):
    parents = {child: parent for parent in root.iter() for child in parent}
    boxes = []
    for node in root.iter():
        if node.tag not in tags:
            continue
        if node.get('filter') or node.get('clip-path'):
            continue
        cls = node.get('class') or ''
        style = node.get('style') or ''
        if 'grain' in (node.get('filter') or ''):
            continue
        if has_mask(node, parents):
            continue  # mask-confined: its bbox is not where it paints
        if node.tag == f'{NS}rect':
            x, y = float(node.get('x', 0)), float(node.get('y', 0))
            box = (x, y, x + float(node.get('width', 0)), y + float(node.get('height', 0)))
        elif node.tag == f'{NS}circle':
            cx, cy, r = float(node.get('cx', 0)), float(node.get('cy', 0)), float(node.get('r', 0))
            box = (cx - r, cy - r, cx + r, cy + r)
        else:
            cx, cy = float(node.get('cx', 0)), float(node.get('cy', 0))
            rx, ry = float(node.get('rx', 0)), float(node.get('ry', 0))
            box = (cx - rx, cy - ry, cx + rx, cy + ry)
        if 'fill="none"' in ET.tostring(node, encoding='unicode'):
            continue  # strokes / guides: not solid art
        fill = node.get('fill') or ''
        if fill.startswith('url(#au'):
            continue  # soft aurora backdrops are meant to sit under text
        if 'url(#sheen)' in fill or 'gws' in cls:
            continue  # the traveling sheen sweep: a light overlay, not a surface
        box = rotate_box(box, *parse_transform(node, parents))
        boxes.append({'label': node.tag.split('}')[1] + (f'.{cls}' if cls else ''), 'box': box,
                      'style': style, 'fill': fill})
    return boxes


def overlap(a, b, pad=0.0):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return (ax0 < bx1 - pad and bx0 < ax1 - pad
            and ay0 < by1 - pad and by0 < ay1 - pad)


def check(path: Path, reserved=()):
    root = ET.fromstring(path.read_text(encoding='utf-8'))
    w, h = float(root.get('width')), float(root.get('height'))
    texts = text_boxes(root)
    issues = []

    for t in texts:
        x0, y0, x1, y1 = t['box']
        if x0 < -1 or y0 < -1 or x1 > w + 1 or y1 > h + 1:
            issues.append(
                f"overflow: {t['label']!r} box=({n_(x0)},{n_(y0)})-({n_(x1)},{n_(y1)}) "
                f"outside 0,0-{n_(w)},{n_(h)}")

    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if not overlap(a['box'], b['box'], pad=1.0):
                continue
            # ghost numerals are drawn twice on purpose: a faint base stroke and
            # a dashed bright one travelling over it, at identical coordinates
            same = (a['label'] == b['label']
                    and all(abs(p - q) < 0.5 for p, q in zip(a['box'], b['box'])))
            if not same:
                issues.append(f"text/text collide: {a['label']!r} x {b['label']!r}")

    for name, box in reserved:
        for t in texts:
            if overlap(t['box'], box, pad=0.0):
                issues.append(
                    f"text in reserved zone {name}: {t['label']!r} "
                    f"box=({n_(t['box'][0])},{n_(t['box'][1])})-({n_(t['box'][2])},{n_(t['box'][3])}) "
                    f"vs {tuple(n_(v) for v in box)}")

    shapes = shape_boxes(root)
    for s in shapes:
        x0, y0, x1, y1 = s['box']
        if x1 - x0 >= w - 2 or y1 - y0 >= h - 2:
            continue  # full-bleed background layers
        if x0 < -2 or y0 < -2 or x1 > w + 2 or y1 > h + 2:
            issues.append(
                f"shape clipped: {s['label']} box=({n_(x0)},{n_(y0)})-({n_(x1)},{n_(y1)}) "
                f"outside 0,0-{n_(w)},{n_(h)}")

    for t in texts:
        for s in shapes:
            sb = s['box']
            if sb[2] - sb[0] >= 600:
                continue  # full-bleed panels
            if not overlap(t['box'], sb, pad=0.5):
                continue
            # a shape that fully contains the text is a deliberate surface
            # (pill, badge, button); only a straddling edge is a real problem
            contained = (sb[0] <= t['box'][0] and sb[1] <= t['box'][1]
                         and sb[2] >= t['box'][2] and sb[3] >= t['box'][3])
            if not contained:
                issues.append(
                    f"text/shape straddle: {t['label']!r} x {s['label']} "
                    f"text={tuple(n_(v) for v in t['box'])} shape={tuple(n_(v) for v in sb)}")
    return issues, texts


def n_(v):
    return round(v, 1)


def hero_reserved():
    """The left arc of the hero orbit: reserved so the headline never crosses it.

    Extents come from the rotated-ellipse half-width/half-height, not guesses.
    """
    cx, cy = 868, 236
    rings = [(170, 71, -24), (148, 61, 20)]
    half_w = min(math.hypot(rx * math.cos(math.radians(t)), ry * math.sin(math.radians(t)))
                 for rx, ry, t in rings)
    half_h = max(math.hypot(rx * math.sin(math.radians(t)), ry * math.cos(math.radians(t)))
                 for rx, ry, t in rings)
    return [('orbit-left-arc', (cx - half_w - 6, cy - half_h - 4, 820, cy + half_h + 6))]


def grid_issues(root, name=''):
    """Structural shapes must anchor to an axis, not merely land near one.

    The failure this guards against is subtle: a pill outline drawn at TEXT
    instead of AXIS looks perfectly fine on its own panel, but the moment the
    panels stack in the README the left edge of that row jogs 22px against the
    row below it. So every pill row must be anchored to an edge — its first pill
    starts on AXIS, or its last pill ends flush on RIGHT — and continuation pills
    are free to fall wherever the row's total width puts them.
    """
    issues = []
    rows = {}
    for node in root.iter(f'{NS}rect'):
        try:
            x, w = float(node.get('x')), float(node.get('width'))
            y, h = float(node.get('y')), float(node.get('height'))
        except (TypeError, ValueError):
            continue
        if w > 300:                          # panel border
            continue
        # only the three cards carry illustration in the right-hand corridor;
        # scoping the exclusion by asset keeps the section plates' own
        # right-flushed tag rows inside the check
        if name in ART_ASSETS and x >= DIV:
            continue
        # the left accent spine is classified by shape: a thin tall rect parked
        # at SPINE_X (the margin, clear of the pills on AXIS and copy on TEXT).
        # It carries no stroke, so shape is the only tell. Both the base bar and
        # its clipPath rect match, so expect both at SPINE_X.
        if w <= 6 and h > 80:
            if abs(x - SPINE_X) > 0.5:
                issues.append(f'accent spine starts at x={n_(x)}, expected SPINE_X {SPINE_X}')
        elif h < 60 and node.get('stroke'):  # pill outline
            rows.setdefault(round(y, 1), []).append((x, x + w))
    for y, pills in sorted(rows.items()):
        left = min(p[0] for p in pills)
        right = max(p[1] for p in pills)
        if abs(left - AXIS) > 0.5 and abs(right - RIGHT) > 0.5:
            issues.append(f'pill row at y={n_(y)} spans {n_(left)}..{n_(right)} '
                          f'but is anchored to neither AXIS nor RIGHT')
    issues += centring_issues(root, name)
    return issues


def centring_issues(root, name=''):
    """A label must sit on its container's centre line, measured on cap height.

    Two ways this drifts silently: a baseline hardcoded to "about right", and a
    label drawn at a different tracking than the width its pill was sized from.
    Both land the text a few pixels low, which is invisible in markup and
    obvious in a column of tags.
    """
    issues = []
    rects = []
    for node in root.iter(f'{NS}rect'):
        if not node.get('stroke'):
            continue
        g = lambda k: float(node.get(k) or 0)
        x, w, y, h = g('x'), g('width'), g('y'), g('height')
        if not (20 < w < 300) or not (20 <= h < 60):
            continue
        if name in ART_ASSETS and x >= DIV:
            continue
        rects.append((x, w, y, h))

    for node in root.iter(f'{NS}text'):
        if node.get('text-anchor'):
            continue                       # renderer resolves the anchor itself
        g = lambda k: float(node.get(k) or 0)
        tx, ty, size = g('x'), g('y'), g('font-size')
        for x, w, y, h in rects:
            if not (x - 2 <= tx <= x + w + 2 and y - 2 <= ty <= y + h + 2):
                continue
            skew = (ty - CAP * size) - (y + h / 2)
            if abs(skew) > 0.6:
                label = ''.join(node.itertext())[:18]
                issues.append(f'pill label {label!r} sits {skew:+.1f}px off the '
                              f'pill centre line')
    return issues


def heading_issues(root, name=''):
    """Every panel heading must land on the same line as every other one.

    The panels stack into a single column on the README, so a heading that sits
    a few pixels lower than its neighbours is read as the whole card being off
    level. Each panel is built by a different function, so the shared baseline
    has to be asserted rather than assumed.
    """
    issues = []
    heads = []
    baselines = {float(node.get('y', 0)) for node in root.iter(f'{NS}text')
                 if not node.get('text-anchor')}
    if abs(HEAD_EYEBROW) not in baselines:
        return issues        # hero and footer are their own composition, not a panel head
    for node in root.iter(f'{NS}text'):
        if node.get('text-anchor'):
            continue
        size = float(node.get('font-size', 16))
        if size < 30:                       # only the panel-title size qualifies
            continue
        heads.append((float(node.get('y', 0)), size, ''.join(node.itertext())[:18]))
    if not heads:
        return issues
    for y, size, label in heads:
        if abs(y - HEAD_TITLE) > 0.5:
            issues.append(f'heading {label!r} baselines at {n_(y)}, '
                          f'but every panel heading sits at {n_(HEAD_TITLE)}')
        if abs(size - HEAD_SIZE) > 0.5:
            issues.append(f'heading {label!r} is {n_(size)}px, but every panel '
                          f'heading is {n_(HEAD_SIZE)}px')
    subs = {float(node.get('y', 0)) for node in root.iter(f'{NS}text')
            if not node.get('text-anchor') and 15 <= float(node.get('font-size', 99)) <= 19}
    if subs and HEAD_SUB not in subs:
        issues.append(f'subtitle baselines at {n_(sorted(subs)[0])}, '
                      f'but every panel subtitle sits at {n_(HEAD_SUB)}')
    return issues


def style_issues(src, name=''):
    """Lint the embedded stylesheet: the two things that break silently.

    A universal selector with !important outranks a presentation attribute, so a
    blanket `opacity:1` in the reduced-motion block does not restore what the
    animation took away - it overwrites the opacity every tint in the file was
    authored with, and the design renders with solid blocks where dim washes
    were meant to be. And a class that never matches an element just quietly
    stops animating.
    """
    issues = []
    m = re.search(r'@media\s*\(prefers-reduced-motion\s*:\s*reduce\)\s*\{(.*?)\}\s*$',
                  src, re.S | re.M)
    if not m:
        issues.append('no prefers-reduced-motion block')
    elif re.search(r'opacity\s*:', m.group(1)):
        issues.append('the reduced-motion block resets opacity, which outranks '
                      'every opacity presentation attribute in the file')
    elif not re.search(r'animation\s*:\s*none', m.group(1)):
        issues.append('the reduced-motion block does not cancel animation')

    for cls in sorted(set(re.findall(r'class="([\w -]+)"', src))):
        for name_ in cls.split():
            if f'.{name_}' not in src:
                issues.append(f'class {name_!r} is used but never defined')
    for anim in set(re.findall(r'animation:\s*([\w-]+)', src)):
        if anim in CSS_KEYWORDS:
            continue
        if f'@keyframes {anim}' not in src:
            issues.append(f'animation {anim!r} has no @keyframes')
    for kf, body in re.findall(r'@keyframes\s+([\w-]+)\s*\{from\{([^}]*)\}', src):
        op = re.search(r'opacity:\s*([\d.]+)', body)
        if op and float(op.group(1)) < 0.62:
            issues.append(f'@keyframes {kf} starts at {op.group(1)} opacity, '
                          f'below the 0.62 legibility floor')
    return issues


def line_break_issues(src, name=''):
    """No element inside <text> may be relied on to break a line.

    SVG has no <br/>. The break element belongs to HTML, and a renderer meets
    one inside <text> with nothing to do: the line break never happens and
    every word after it silently vanishes. This is invisible in the source
    review, invisible in the geometry checks - each half still measures as a
    perfectly well-formed run at a perfectly well-formed baseline - and only
    shows up as blank space where a sentence should be. The intro's three
    column descriptions all shipped that way, with the card dividers extended
    to 330 to make room for a second line that no browser ever drew.

    A <tspan> is the one legitimate child: it recolours a fragment of a run.
    """
    issues = []
    for inner in re.findall(r'<text\b[^>]*>((?:(?!</text>).)*)</text>', src, re.S):
        for tag in re.findall(r'<(?!/)(?!\?)(?!tspan\b)([a-zA-Z][\w-]*)', inner):
            issues.append(f'<{tag}> inside <text> cannot break a line - SVG has no '
                          f'line-break element, so the rest of the run is lost')
    return issues


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    art_zone = (DIV, 20, 1080, 200)   # card illustration corridor
    # zones that must stay clear of type, keyed by asset
    zones = {
        'hero.svg': hero_reserved(),
        'astra.svg': [('art', art_zone)],
        'primeproxy.svg': [('art', art_zone)],
        'primerouter.svg': [('art', art_zone)],
        'intro.svg': [],                 # the 3 focus columns own the lower half
        'plugins.svg': [],               # ghost numeral is a text run, checked as text
        'sphereprime.svg': [],
        # gap between the left copy and the CTA button: the button's own label
        # legitimately lives inside the pill, so the zone guards the gutter only
        'footer.svg': [('cta-gutter', (520, 14, 700, 82))],
    }

    failed = 0
    for path in sorted(ASSETS.glob('*.svg')):
        src = path.read_text(encoding='utf-8')
        issues, texts = check(path, zones.get(path.name, []))
        issues += grid_issues(ET.fromstring(src), path.name)
        issues += heading_issues(ET.fromstring(src), path.name)
        issues += style_issues(src, path.name)
        issues += line_break_issues(src, path.name)
        status = 'OK' if not issues else f'{len(issues)} issue(s)'
        print(f'{path.name:20} {len(texts):2} text runs - {status}')
        for issue in issues:
            print(f'    - {issue}')
        failed += bool(issues)

    if failed:
        print(f'\n{failed} asset(s) need layout fixes.')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
