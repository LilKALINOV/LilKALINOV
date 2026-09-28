"""Measure the real contrast of every text run in the generated assets.

Why this exists
---------------
The obvious method - crop the run's nominal ink box, take the mean, compare to
the panel colour - reports 11px mono inside a chip at 3.7:1 when the chip label
is really 13:1 against its own dark surface. The box is taller than the glyphs,
so the mean is dragged down by background, and at 11px the whole run is
antialiasing with no fully covered pixel to read. Both failures push the same
way: they under-report.

So this measures the rendered ink rather than the box:

* the page is rendered at 3x, which gives every stroke enough device pixels
  that its core reaches the authored colour;
* the background is the *median* of the box, which is background for any text
  thin enough to be the minority of its own bounding box, and is immune to the
  wash gradient running through the panel;
* the ink is the extreme value *within the pixels the box marks as ink*, not
  within the whole box - a run that overflows a chip therefore cannot borrow
  the neighbouring panel's brightness.

The result is the contrast a reader actually gets, not the contrast the source
claims. Pillow is required (it is, for the font metrics); nothing else is.
"""

from __future__ import annotations

import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NS = '{http://www.w3.org/2000/svg}'

# README order, which is the order the page stacks them in
ORDER = ['hero.svg', 'intro.svg', 'astra.svg', 'primeproxy.svg',
         'primerouter.svg', 'plugins.svg', 'sphereprime.svg', 'footer.svg']

# Segoe UI for the sans stack, Consolas for the mono stack, exactly as the
# generator's font-family list resolves them on a Windows box
FONT_FILES = {
    ('sans', False): r'C:\Windows\Fonts\segoeui.ttf',
    ('sans', True): r'C:\Windows\Fonts\segoeuib.ttf',
    ('mono', False): r'C:\Windows\Fonts\consola.ttf',
    ('mono', True): r'C:\Windows\Fonts\consolab.ttf',
}
FALLBACK_ADVANCE = {'mono': 0.55, 'sans': 0.52}
SCALE = 3          # must match --force-device-scale-factor
# the fraction of the distance from background to white that a pixel must cross
# to count as ink. The faintest colour used as type is VIOLET at L=0.20 over a
# panel at L=0.007, i.e. 0.194 of the way - so the gate has to sit under that,
# and well over the plate grain, which is opacity .05 blurred and lands near
# L=0.01
INK_FLOOR = 0.12
MIN_AA = 4.5       # WCAG AA for body text
MIN_AA_LARGE = 3.0  # WCAG AA for >=18.66px bold / >=24px

_fonts: dict = {}


def font(family: str, bold: bool):
    from PIL import ImageFont
    key = (family, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_FILES[key], 100)
    return _fonts[key]


def advance(string: str, family: str, size: float, bold: bool) -> float:
    if not string:
        return 0.0
    try:
        return font(family, bold).getlength(string) * size / 100
    except Exception:
        return len(string) * size * FALLBACK_ADVANCE[family]


def rel_lum(rgb) -> float:
    out = []
    for channel in rgb[:3]:
        c = channel / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(a: float, b: float) -> float:
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def runs_of(path: Path):
    """Every <text> run as (label, x, y, size, width, family, bold, fill)."""
    root = ET.parse(path).getroot()
    out = []
    for node in root.iter(f'{NS}text'):
        try:
            x, y = float(node.get('x')), float(node.get('y'))
            size = float(node.get('font-size'))
        except (TypeError, ValueError):
            continue
        label = ''.join(node.itertext())
        family = 'mono' if 'mono' in (node.get('class') or '') else 'sans'
        bold = (node.get('font-weight') or '400') in ('600', '700', '800', '900')
        width = advance(label, family, size, bold)
        if node.get('textLength'):
            width = float(node.get('textLength'))
        width += float(node.get('letter-spacing') or 0) * max(len(label) - 1, 0)
        if node.get('text-anchor') == 'end':
            x -= width
        elif node.get('text-anchor') == 'middle':
            x -= width / 2
        out.append((label, x, y, size, width, family, bold, node.get('fill') or '#fff'))
    return out


def measure(image, x, y, size, width):
    """Background and ink luminance for a run, from the rendered pixels."""
    pad = 2.0
    x0 = int((x - pad) * SCALE)
    x1 = int((x + width + pad) * SCALE) + 1
    y0 = int((y - 0.95 * size - pad) * SCALE)
    y1 = int((y + 0.30 * size + pad) * SCALE) + 1
    box = image.crop((x0, y0, x1, y1))
    if box.width < 2 or box.height < 2:
        return None
    lums = [rel_lum(p) for p in box.getdata()]
    bg = statistics.median(lums)
    # the ink is the extreme furthest from the background in whichever direction
    # the background sits. Testing the background's own level rather than its
    # polarity is the whole trick: this is a dark theme, so every background
    # lands near 0.01 and a naive "is the background light?" test sends every
    # run down the dark-ink branch and reports the grain instead of the text.
    ink = max(lums) if (1.0 - bg) >= bg else min(lums)
    if ink > bg:
        gate = bg + (1.0 - bg) * INK_FLOOR
    else:
        gate = bg * (1.0 - INK_FLOOR)
    cover = sum(1 for l in lums if (l > gate) == (ink > bg))
    return bg, ink, cover / len(lums)


def main() -> int:
    from PIL import Image

    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    shot = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if shot is None:
        print('usage: measure_contrast.py <3x screenshot of _full.html>')
        return 2
    image = Image.open(shot).convert('RGB')

    offset = 0
    fails = []
    total = 0
    for name in ORDER:
        path = ASSETS / name
        height = int(ET.parse(path).getroot().get('height'))
        for label, x, y, size, width, family, bold, fill in runs_of(path):
            total += 1
            got = measure(image, x, y + offset, size, width)
            if got is None:
                continue
            bg, ink, cover = got
            ratio = contrast(ink, bg)
            # AA: 18.66px bold, or 24px regular, and above
            large = size >= 24 or (bold and size >= 18.66)
            floor = MIN_AA_LARGE if large else MIN_AA
            if ratio < floor:
                fails.append((name, label, size, fill, bg, ink, cover, ratio, floor))
        offset += height

    print(f'{total} text runs measured at {SCALE}x\n')
    if not fails:
        print('every run clears WCAG AA against what is actually behind it')
        return 0
    fails.sort(key=lambda f: f[7])
    print(f'{len(fails)} of {total} below AA:\n')
    print(f'{"asset":16} {"size":>5}  {"bg":>7} {"ink":>7}  {"ink%":>5}  '
          f'{"ratio":>6} {"need":>5}  run')
    for name, label, size, fill, bg, ink, cover, ratio, floor in fails:
        snippet = ' '.join(label.split())[:34]
        print(f'{name[:-4]:16} {size:5}  {bg:7.4f} {ink:7.4f}  {cover * 100:4.1f}%  '
              f'{ratio:6.2f} {floor:5.1f}  {fill} {snippet!r}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
