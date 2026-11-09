from .canvas import document, frame, text, label, delay, crop_marks
from .scope import oscilloscope
from .theme import FULL_WIDTH, PAPER, GREY, DIM, LINE, SIGNAL, INK

HEIGHT = 590
ROLES = [
    'агентный софт',
    'десктоп: Tauri & Qt',
    'системный код: Rust / C++',
    'тестирование и QA',
    'плагины для Astra',
    'UI: Flutter & Electron',
]
STACK = [
    'Rust',
    'Go',
    'Python',
    'C / C++ / C#',
    'TypeScript',
    'JavaScript',
    'Assembly',
    'Electron / Tauri',
    'Flutter / Qt 5/6',
    'HTML / CSS',
]
MARQUEE = [
    'SPHEREPRIME',
    'LEAD QA',
    'ASTRA',
    'PRIME CLI',
    'TAURI & ELECTRON',
    'QT 5/6 & FLUTTER',
    'RUST & GO',
    'C / C++ / C#',
    'ASSEMBLY',
    'HTML / CSS',
    'AUTOMATION',
]
ROLE_STEP = 2.6
STACK_STEP = 1.3
COLUMNS = (28, 392, 752)


def name():
    return f'''
<clipPath id="name-clip"><rect x="20" y="60" width="840" height="200"/></clipPath>
<g clip-path="url(#name-clip)"><g class="reveal" style="{delay(.1)}">
  <text x="22" y="218" font-size="132" font-weight="800" letter-spacing="-5" fill="{PAPER}">LilKALINOV<tspan fill="{SIGNAL}">.</tspan></text>
</g></g>
<g class="rise" style="{delay(.7)}">{text(28, 270, 'Инструменты для ИИ-агентов, тестирование и открытый код — от CLI до голоса.', 18.5, GREY)}</g>'''


def portrait(avatar):
    mime, data = avatar
    x, y, size = 868, 76, 200
    duotone = f'''<filter id="duotone" color-interpolation-filters="sRGB">
  <feColorMatrix type="matrix" values=".33 .5 .17 0 0 .33 .5 .17 0 0 .33 .5 .17 0 0 0 0 0 1 0"/>
  <feComponentTransfer><feFuncR type="table" tableValues=".055 .93"/><feFuncG type="table" tableValues=".055 .92"/><feFuncB type="table" tableValues=".05 .89"/></feComponentTransfer>
</filter>'''
    css = (f'@keyframes scan{{0%{{transform:translateY(0);opacity:0}}6%{{opacity:1}}88%{{opacity:1}}100%{{transform:translateY({size}px);opacity:0}}}}'
           f'.scan{{animation:scan 5.5s cubic-bezier(.45,0,.55,1) infinite}}')
    body = f'''
<g class="fade" style="{delay(.4)}">
  <clipPath id="photo"><rect x="{x}" y="{y}" width="{size}" height="{size}"/></clipPath>
  <image x="{x}" y="{y}" width="{size}" height="{size}" href="data:{mime};base64,{data}" xlink:href="data:{mime};base64,{data}" clip-path="url(#photo)" preserveAspectRatio="xMidYMid slice" filter="url(#duotone)"/>
  <g clip-path="url(#photo)"><g class="scan"><rect x="{x}" y="{y - 1}" width="{size}" height="2" fill="{SIGNAL}"/><rect x="{x}" y="{y - 40}" width="{size}" height="39" fill="{SIGNAL}" opacity=".08"/></g></g>
  <rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="{LINE}"/>
  <g transform="translate({x - 10} {y - 10})">{crop_marks(size + 20, size + 20, inset=0, size=12, color=GREY)}</g>
  {label(x, y + size + 30, 'fig. 00 — автор')}
</g>'''
    return body, duotone, css


def role_ticker(x):
    baseline, line = 392, 40
    items = ROLES + ROLES[:1]
    words = ''.join(text(x, baseline + i * line, role, 28, PAPER, 700, spacing=-.5) for i, role in enumerate(items))
    steps = len(ROLES)
    frames = [f'{100 * i / steps:.2f}%,{100 * i / steps + 100 / steps * .8:.2f}%{{transform:translateY({-i * line}px)}}' for i in range(steps)]
    frames.append(f'100%{{transform:translateY({-steps * line}px)}}')
    css = f'@keyframes ticker{{{"".join(frames)}}}.ticker{{animation:ticker {ROLE_STEP * steps}s cubic-bezier(.77,0,.18,1) infinite}}'
    body = f'''
{label(x, 344, '01 / делаю')}
{text(x, 364, 'Проектирую и тестирую', 15, GREY)}
<clipPath id="ticker-clip"><rect x="{x - 2}" y="{baseline - 30}" width="330" height="40"/></clipPath>
<g clip-path="url(#ticker-clip)"><g class="ticker">{words}</g></g>
{text(x, 430, 'SpherePrime и нативные UI —', 15, GREY)}
{text(x, 452, 'надежность, архитектура и релизы', 15, GREY)}
{text(x, 474, 'без компромиссов.', 15, GREY)}'''
    return body, css


def stack(x):
    rows = 5
    col_width = 162
    positions = [(x + (i // rows) * col_width, 376 + (i % rows) * 23) for i in range(len(STACK))]
    items = ''.join(f'<g class="rise" style="{delay(.8 + i * .05)}">{text(px + 14, py, f"{i + 1:02d}", 10, DIM, mono=True)}{text(px + 36, py, item, 12.5, PAPER, mono=True)}</g>'
                    for i, (item, (px, py)) in enumerate(zip(STACK, positions)))
    frames = []
    count = len(STACK)
    for i, (px, py) in enumerate(positions):
        start = 100 * i / count
        frames.append(f'{start:.2f}%,{start + 100 / count * .7:.2f}%{{transform:translate({px - x}px,{py - positions[0][1]}px)}}')
    frames.append(f'100%{{transform:translate(0,0)}}')
    css = f'@keyframes picker{{{"".join(frames)}}}.picker{{animation:picker {STACK_STEP * count}s cubic-bezier(.77,0,.18,1) infinite}}'
    body = f'''
{label(x, 344, '02 / стек')}
{items}
<g class="picker"><rect x="{x}" y="{positions[0][1] - 9}" width="7" height="7" fill="{SIGNAL}"/></g>'''
    return body, css


def signal(x):
    width, top, height = 320, 368, 84
    command = '$ prime test --coverage --all'
    char = 8.4
    widths = ';'.join(f'{i * char:.1f}' for i in range(len(command) + 1)) + f';{len(command) * char:.1f};0'
    times = ';'.join(f'{.4 * i / len(command):.4f}' for i in range(len(command) + 1)) + ';.96;1'
    ticks = ''.join(f'<path d="M{x + k * 20} {top + height}v-5" stroke="{DIM}"/>' for k in range(17))
    body = f'''
{label(x, 344, '03 / сигнал')}
{label(x + width, 344, 'QA / PASS', anchor='end', fill=SIGNAL)}
<rect x="{x}" y="{top}" width="{width}" height="{height}" fill="{INK}" stroke="{LINE}"/>
<path d="M{x} {top + height / 2}H{x + width}" stroke="{DIM}" stroke-dasharray="2 4"/>
{ticks}
{oscilloscope(x + 6, top + height / 2, width - 12, 30, SIGNAL, duration=4.2, stroke=1.6)}
<clipPath id="cmd-clip"><rect x="{x}" y="{top + height + 16}" width="0" height="26"><animate attributeName="width" dur="10s" repeatCount="indefinite" calcMode="discrete" values="{widths}" keyTimes="{times}"/></rect></clipPath>
<g clip-path="url(#cmd-clip)">{text(x, top + height + 34, command, 14, PAPER, mono=True)}</g>'''
    return body, ''


def marquee():
    content = '   —   '.join(MARQUEE) + '   —   '
    size, spacing = 12, 2.4
    width = len(content) * (size * .6 + spacing)
    line = ''.join(text(i * width, 0, content, size, GREY, 600, mono=True, spacing=spacing,
                        extra=f'textLength="{width:.1f}" lengthAdjust="spacing"') for i in range(2))
    css = f'.marquee{{--shift:-{width:.1f}px;animation:marquee 40s linear infinite}}'
    body = f'''
<path d="M28 {HEIGHT - 62}H{FULL_WIDTH - 28}" stroke="{LINE}"/>
<clipPath id="mq"><rect x="28" y="{HEIGHT - 50}" width="{FULL_WIDTH - 56}" height="24"/></clipPath>
<g clip-path="url(#mq)"><g transform="translate(28 {HEIGHT - 33})"><g class="marquee">{line}</g></g></g>'''
    return body, css


def build(avatar):
    photo, duotone, photo_css = portrait(avatar)
    ticker, ticker_css = role_ticker(COLUMNS[0])
    picker, picker_css = stack(COLUMNS[1])
    scope, _ = signal(COLUMNS[2])
    tape, tape_css = marquee()
    dividers = ''.join(f'<path d="M{cx - 26} 330V{HEIGHT - 86}" stroke="{LINE}"/>' for cx in COLUMNS[1:])
    body = (frame(FULL_WIDTH, HEIGHT, 'lilkalinov / readme', 'co-founder · lead qa · agent tooling — rev. 11.2026', phase=0)
            + name() + photo
            + f'<rect class="fbl grow" style="{delay(.5)}" x="28" y="308" width="{FULL_WIDTH - 56}" height="1" fill="{GREY}"/>'
            + dividers + ticker + picker + scope + tape)
    title = 'LilKALINOV — со-основатель SpherePrime, Lead QA Astra: инструменты для ИИ-агентов, тестирование и плагины.'
    return document(FULL_WIDTH, HEIGHT, body, title, css=photo_css + ticker_css + picker_css + tape_css, extra_defs=duotone)
