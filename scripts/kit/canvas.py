from html import escape

from .theme import STYLE, PANEL, PAPER, GREY, DIM, LINE, SIGNAL, REGISTER_CYCLE

RADIUS = 6


def text_width(content, size, mono=False, weight=400, spacing=0.0):
    if mono:
        return len(content) * (size * 0.6 + spacing)
    total = 0.0
    for char in content:
        if char == ' ':
            total += 0.28
        elif char in 'il.,:;|!\'':
            total += 0.26
        elif char in 'fjrt()[]-':
            total += 0.36
        elif char.isdigit():
            total += 0.56
        elif char.isupper():
            total += 0.66
        elif 'Ѐ' <= char <= 'ӿ':
            total += 0.6
        else:
            total += 0.54
    total *= size * (1.06 if weight >= 600 else 1)
    return total + spacing * len(content)


def text(x, y, content, size=16, fill=PAPER, weight=400, anchor='start', mono=False,
         spacing=0.0, cls='', style='', opacity=None, extra=''):
    attrs = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight != 400:
        attrs.append(f'font-weight="{weight}"')
    if anchor != 'start':
        attrs.append(f'text-anchor="{anchor}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    classes = ' '.join(part for part in ('mono' if mono else '', cls) if part)
    if classes:
        attrs.append(f'class="{classes}"')
    if style:
        attrs.append(f'style="{style}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)}>{escape(content)}</text>'


def label(x, y, content, fill=GREY, anchor='start', size=11):
    return text(x, y, content.upper(), size, fill, 600, anchor=anchor, mono=True, spacing=1.6)


def delay(seconds):
    return f'animation-delay:{seconds:.2f}s'


def window_keyframes(name, start, end, fade=4, lift=6):
    s0, s1 = max(start, 0), min(start + fade, 99)
    e0, e1 = max(end - fade, s1), min(end, 100)
    return (f'@keyframes {name}{{0%,{s0}%{{opacity:0;transform:translateY({lift}px)}}'
            f'{s1}%,{e0}%{{opacity:1;transform:none}}{e1}%,100%{{opacity:0;transform:none}}}}')


def reveal(uid, x, y, size, content, start=0.0, width=1000, **options):
    top = y - size * 1.02
    height = size * 1.3
    return (f'<clipPath id="rv-{uid}"><rect x="{x - 4:.1f}" y="{top:.1f}" width="{width}" height="{height:.1f}"/></clipPath>'
            f'<g clip-path="url(#rv-{uid})"><g class="reveal" style="{delay(start)}">{text(x, y, content, size, **options)}</g></g>')


def document(width, height, body, title, css='', extra_defs=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">{escape(title)}</title>
<defs>
 <clipPath id="clip"><rect width="{width}" height="{height}" rx="{RADIUS}"/></clipPath>
 <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M0 .5H2M.5 0V2" stroke="{PAPER}" stroke-opacity=".14"/></pattern>
 {extra_defs}
</defs>
<style>{STYLE}{css}</style>
{body}
</svg>'''


def crop_marks(width, height, inset=12, size=10, color=DIM):
    marks = []
    for x, sx in ((inset, 1), (width - inset, -1)):
        for y, sy in ((inset, 1), (height - inset, -1)):
            marks.append(f'M{x} {y + sy * size}V{y}H{x + sx * size}')
    return f'<path d="{"".join(marks)}" fill="none" stroke="{color}" stroke-width="1.2"/>'


def frame(width, height, left='', right='', phase=0.0, grid=True, strip=True):
    layers = [f'<rect width="{width}" height="{height}" rx="{RADIUS}" fill="{PANEL}"/>']
    if grid:
        layers.append(f'<rect width="{width}" height="{height}" fill="url(#grid)" clip-path="url(#clip)"/>')
    layers.append(crop_marks(width, height))
    if strip:
        run = width - 2 * 28 - 56
        layers.append(f'<path d="M28 50H{width - 28}" stroke="{LINE}"/>')
        layers.append(f'<g style="--run:{run}px"><rect class="register" style="{delay(-(phase % REGISTER_CYCLE))}" x="28" y="49" width="56" height="2" fill="{SIGNAL}"/></g>')
        if left:
            layers.append(label(28, 36, left))
        if right:
            layers.append(label(width - 28, 36, right, anchor='end'))
    layers.append(f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{RADIUS}" fill="none" stroke="{LINE}"/>')
    return ''.join(layers)


def tags(x, y, items, size=12):
    out, cursor = [], x
    for index, item in enumerate(items):
        if index:
            out.append(text(cursor, y, '/', size, SIGNAL, mono=True))
            cursor += size * .6 + 10
        out.append(text(cursor, y, item, size, GREY, mono=True))
        cursor += text_width(item, size, mono=True) + 10
    return f'<g class="fade" style="{delay(.6)}">{"".join(out)}</g>'


def arrow(cx, cy, size=10, color=PAPER, width=1.6):
    return (f'<path d="M{cx - size} {cy + size}L{cx + size} {cy - size}M{cx - size * .4} {cy - size}H{cx + size}V{cy + size * .4}" '
            f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="square"/>')
