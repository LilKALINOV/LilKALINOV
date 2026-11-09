from .canvas import document, frame, text, label, delay, text_width
from .theme import FULL_WIDTH, PAPER, GREY, DIM, LINE, SIGNAL

HEIGHT = 326
DIGIT = 46
LINE_HEIGHT = 86
BASELINE = 156


def odometer(x, value, index):
    out = []
    for position, digit in enumerate(str(value)):
        column = list(range(10)) + list(range(int(digit) + 1))
        shift = (len(column) - 1) * LINE_HEIGHT
        cells = ''.join(text(x + position * DIGIT + DIGIT / 2, BASELINE + k * LINE_HEIGHT, str(n), 80, PAPER, 800, anchor='middle')
                        for k, n in enumerate(column))
        name = f'odo{index}{position}'
        out.append(f'<style>@keyframes {name}{{to{{transform:translateY(-{shift}px)}}}}'
                   f'.{name}{{animation:{name} {2.2 + position * .5:.1f}s cubic-bezier(.16,1,.3,1) {.2 + index * .15:.2f}s both}}</style>'
                   f'<clipPath id="c{name}"><rect x="{x + position * DIGIT}" y="{BASELINE - 66}" width="{DIGIT}" height="{LINE_HEIGHT}"/></clipPath>'
                   f'<g clip-path="url(#c{name})"><g class="{name}">{cells}</g></g>')
    return ''.join(out), len(str(value)) * DIGIT


def counters(items):
    out = []
    column = (FULL_WIDTH - 56) / len(items)
    for index, (value, suffix, caption, note) in enumerate(items):
        x = 28 + index * column
        digits, width = odometer(x, value, index)
        out.append(digits)
        if suffix:
            out.append(f'<g class="fade" style="{delay(2)}">{text(x + width + 2, BASELINE, suffix, 60, SIGNAL, 800)}</g>')
        out.append(label(x + 2, BASELINE + 32, caption, PAPER, size=12))
        out.append(text(x + 2, BASELINE + 52, note, 12, DIM, mono=True))
        if index:
            out.append(f'<path d="M{x - 16:.1f} 82V{BASELINE + 56}" stroke="{LINE}"/>')
    return ''.join(out)


def barcode(rows, total):
    left, right, top, height = 28, FULL_WIDTH - 28, 246, 30
    step = (right - left) / total
    bars, legend = [], []
    index = 0
    legend_x = left
    for name, count, color in rows:
        for _ in range(count):
            bars.append(f'<rect class="fbb eq-once" style="{delay(.6 + index * .018)}" x="{left + index * step:.1f}" y="{top}" width="{step - 3:.1f}" height="{height}" fill="{color}"/>')
            index += 1
        caption = f'{name} {count}'
        legend.append(f'<rect x="{legend_x}" y="{top + height + 17}" width="9" height="9" fill="{color}"/>'
                      + text(legend_x + 16, top + height + 26, caption.upper(), 11, GREY, 600, mono=True, spacing=1))
        legend_x += text_width(caption, 11, mono=True, spacing=1) + 44
    css = '@keyframes once{from{transform:scaleY(0)}to{transform:scaleY(1)}}.eq-once{animation:once .5s cubic-bezier(.19,1,.22,1) both}'
    return ''.join(bars) + ''.join(legend), css


def build(repo_total, language_rows, highlights, meta):
    items = [(repo_total, '+', 'репозитория', 'SpherePrime / LilKALINOV')] + highlights
    total = sum(count for _, count, _ in language_rows)
    code, css = barcode(language_rows, total)
    body = (frame(FULL_WIDTH, HEIGHT, 'index / в цифрах', meta, phase=3)
            + counters(items)
            + f'<path d="M28 214H{FULL_WIDTH - 28}" stroke="{LINE}"/>'
            + label(28, 234, 'каждая полоса — репозиторий, цвет — язык', DIM, size=10)
            + code)
    title = f'{repo_total}+ репозитория с SpherePrime / LilKALINOV. ' + '. '.join(f'{v} {c}' for v, _, c, _ in highlights) + '. Языки: ' + ', '.join(f'{n} {c}' for n, c, _ in language_rows)
    return document(FULL_WIDTH, HEIGHT, body, title, css=css)
