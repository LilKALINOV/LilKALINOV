from .canvas import text, label, delay, window_keyframes
from .theme import PAPER, GREY, DIM, LINE, SIGNAL, INK, PANEL

CLI_CYCLE = 13
ROUTER_CYCLE = 8
MODELS = ['claude-opus', 'gpt-5', 'local / qwen']
TARGETS = ['Claude', 'GPT', 'Gemini', 'DeepSeek']


def appear(name, start, cycle, end=94):
    return window_keyframes(name, start, end, fade=2.5, lift=4) + f'.{name}{{animation:{name} {cycle}s cubic-bezier(.2,.8,.2,1) infinite}}'


def model_ticker(x, y):
    step = 22
    items = MODELS + MODELS[:1]
    labels = ''.join(text(x, y + i * step, item, 12, SIGNAL, 600, anchor='end', mono=True) for i, item in enumerate(items))
    frames = [f'{100 * i / len(MODELS):.2f}%,{100 * i / len(MODELS) + 26:.2f}%{{transform:translateY({-i * step}px)}}' for i in range(len(MODELS))]
    frames.append(f'100%{{transform:translateY({-len(MODELS) * step}px)}}')
    css = f'@keyframes mtick{{{"".join(frames)}}}.mtick{{animation:mtick 7.5s cubic-bezier(.77,0,.18,1) infinite}}'
    return f'<clipPath id="mclip"><rect x="{x - 140}" y="{y - 14}" width="150" height="19"/></clipPath><g clip-path="url(#mclip)"><g class="mtick">{labels}</g></g>', css


def cli(x, y, w, h):
    prompt = 'добавь авторизацию в API'
    char = 8.4
    widths = ';'.join(f'{i * char:.1f}' for i in range(len(prompt) + 1)) + f';{len(prompt) * char:.1f};0'
    times = ';'.join(f'{.2 * i / len(prompt):.4f}' for i in range(len(prompt) + 1)) + ';.95;1'
    steps = [('read', 'src/api/auth.go', 26), ('lsp', '3 references · AuthService', 36),
             ('mcp', 'github.create_pull_request', 46), ('edit', '+128 −14 · 4 files', 56)]
    css = ''
    rows = []
    for index, (tag, value, start) in enumerate(steps):
        css += appear(f'cl{index}', start, CLI_CYCLE)
        rows.append(f'<g class="cl{index}">{text(x + 24, y + 112 + index * 28, tag.upper(), 11, DIM, 700, mono=True, spacing=1.5)}'
                    f'{text(x + 92, y + 112 + index * 28, value, 13.5, GREY, mono=True)}</g>')
    css += appear('cldone', 68, CLI_CYCLE)
    rows.append(f'<g class="cldone"><rect x="{x + 24}" y="{y + 216}" width="8" height="8" fill="{SIGNAL}"/>'
                f'{text(x + 40, y + 225, "готово за 42s — PR открыт", 13.5, PAPER, 700, mono=True)}</g>')
    ticker, ticker_css = model_ticker(x + w - 20, y + 25)
    css += ticker_css
    svg = f'''
<path d="M{x} {y + 40}H{x + w}" stroke="{LINE}"/>
{label(x + 20, y + 25, 'prime — ~/project', GREY)}
{ticker}
{text(x + 24, y + 74, '›', 16, SIGNAL, 700, mono=True)}
<clipPath id="cli-type"><rect x="{x + 44}" y="{y + 58}" width="0" height="24"><animate attributeName="width" dur="{CLI_CYCLE}s" repeatCount="indefinite" calcMode="discrete" values="{widths}" keyTimes="{times}"/></rect></clipPath>
<g clip-path="url(#cli-type)">{text(x + 44, y + 74, prompt, 14, PAPER, mono=True)}</g>
{"".join(rows)}
<path d="M{x} {y + h - 44}H{x + w}" stroke="{LINE}"/>
{text(x + 24, y + h - 17, '›', 15, GREY, 700, mono=True)}<rect class="blink" x="{x + 42}" y="{y + h - 29}" width="8" height="15" fill="{PAPER}"/>
{label(x + w - 20, y + h - 18, 'ctrl+p palette', DIM, anchor='end', size=10)}'''
    return svg, css


def router(x, y, w, h):
    cy = y + h / 2
    sx, rx, tx = x + 56, x + 214, x + w - 124
    box_w = 108
    ys = [cy - 54, cy - 18, cy + 18, cy + 54]
    css, paths, boxes, pulses = '', [], [], []
    feed = f'M{sx + 28} {cy}H{rx - 30}'
    for index, (target, ty) in enumerate(zip(TARGETS, ys)):
        route = f'M{rx + 30} {cy}H{rx + 60}V{ty}H{tx}'
        start = index / len(TARGETS)
        end = start + .12
        hit = 100 * end
        leave = hit + 11
        s0 = max(hit - .4, 0)
        s1 = hit
        e0 = leave
        e1 = min(leave + .4, 100)
        css += (f'@keyframes rtb{index}{{0%,{s0:.1f}%{{stroke:{DIM};fill:{INK};stroke-width:1px}}{s1:.1f}%,{e0:.1f}%{{stroke:{SIGNAL};fill:#381a0b;stroke-width:2px}}{e1:.1f}%,100%{{stroke:{DIM};fill:{INK};stroke-width:1px}}}}'
                f'.rtb{index}{{stroke:{DIM};fill:{INK};stroke-width:1px;animation:rtb{index} {ROUTER_CYCLE}s linear infinite}}'
                f'@keyframes rtt{index}{{0%,{s0:.1f}%{{fill:{GREY};font-weight:400}}{s1:.1f}%,{e0:.1f}%{{fill:#ffffff;font-weight:800}}{e1:.1f}%,100%{{fill:{GREY};font-weight:400}}}}'
                f'.rtt{index}{{fill:{GREY};font-weight:400;animation:rtt{index} {ROUTER_CYCLE}s linear infinite}}'
                f'@keyframes rtd{index}{{0%,{s0:.1f}%{{fill:{DIM};opacity:.3}}{s1:.1f}%,{e0:.1f}%{{fill:{SIGNAL};opacity:1}}{e1:.1f}%,100%{{fill:{DIM};opacity:.3}}}}'
                f'.rtd{index}{{fill:{DIM};opacity:.3;animation:rtd{index} {ROUTER_CYCLE}s linear infinite}}')
        paths.append(f'<path d="{route}" fill="none" stroke="{DIM}"/>')
        pulses.append(f'<rect x="-4" y="-4" width="8" height="8" fill="{SIGNAL}" opacity="0"><animateMotion dur="{ROUTER_CYCLE}s" repeatCount="indefinite" path="{route}" keyPoints="0;0;1;1" keyTimes="0;{start:.3f};{end:.3f};1" calcMode="linear"/>'
                      f'<animate attributeName="opacity" dur="{ROUTER_CYCLE}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="0;{max(start - .001, 0):.3f};{start + .001:.3f};{end:.3f};{end + .002:.3f};1"/></rect>')
        boxes.append(f'<rect class="rtb{index}" x="{tx}" y="{ty - 13}" width="{box_w}" height="26" rx="3"/>'
                     f'<circle class="rtd{index}" cx="{tx + 12}" cy="{ty}" r="3"/>'
                     f'<text class="rtt{index} mono" x="{tx + 22}" y="{ty + 4.5}" font-size="12">{target}</text>')
    svg = f'''
{"".join(paths)}
<path d="{feed}" fill="none" stroke="{GREY}"/>
<rect x="-3" y="-3" width="6" height="6" fill="{PAPER}"><animateMotion dur="1.6s" repeatCount="indefinite" path="{feed}"/></rect>
<rect x="{sx - 28}" y="{cy - 20}" width="56" height="40" fill="{INK}" stroke="{PAPER}"/>
{text(sx, cy + 4.5, 'Astra', 12.5, PAPER, 700, anchor='middle')}
<g transform="rotate(45 {rx} {cy})"><rect x="{rx - 26}" y="{cy - 26}" width="52" height="52" fill="{INK}" stroke="{PAPER}" stroke-width="1.4"/></g>
<g class="fb spin"><g transform="rotate(45 {rx} {cy})"><rect x="{rx - 36}" y="{cy - 36}" width="72" height="72" fill="none" stroke="{DIM}" stroke-dasharray="3 5"/></g></g>
{text(rx, cy + 4, 'ROUTER', 10.5, PAPER, 700, anchor='middle', mono=True, spacing=1)}
{"".join(boxes)}
{"".join(pulses)}'''
    return svg, css


def proxy(x, y, w, h):
    cy = y + h / 2 + 6
    lx, rx = x + 54, x + w - 54
    t0, t1 = lx + 44, rx - 44
    rings = ''.join(f'<rect x="{t0 + (t1 - t0) * i / 9 - 1:.1f}" y="{cy - (32 - abs(i - 4.5) * 3):.1f}" width="2" height="{2 * (32 - abs(i - 4.5) * 3):.1f}" fill="{DIM}" class="pulse" style="{delay(-i * .25)}"/>' for i in range(10))
    span = t1 - t0
    css = (f'@keyframes pkt{{from{{transform:translateX(0);opacity:0}}10%,90%{{opacity:1}}to{{transform:translateX({span:.0f}px);opacity:0}}}}.pkt{{animation:pkt 2.6s linear infinite}}'
           f'@keyframes pktr{{from{{transform:translateX(0);opacity:0}}10%,90%{{opacity:1}}to{{transform:translateX(-{span:.0f}px);opacity:0}}}}.pktr{{animation:pktr 3.2s linear infinite}}')
    packets = ''.join(f'<rect class="pkt" style="{delay(-i * .65)}" x="{t0}" y="{cy - 9}" width="16" height="6" fill="{SIGNAL}"/>' for i in range(4))
    packets += ''.join(f'<rect class="pktr" style="{delay(-i * .8)}" x="{t1 - 12}" y="{cy + 4}" width="12" height="5" fill="{PAPER}"/>' for i in range(4))
    lock_x, lock_y = (t0 + t1) / 2, y + 30
    svg = f'''
<path d="M{t0} {cy - 34}H{t1}M{t0} {cy + 34}H{t1}" stroke="{LINE}"/>
{rings}{packets}
<rect x="{lx - 28}" y="{cy - 28}" width="56" height="56" fill="{INK}" stroke="{PAPER}"/>
<path d="M{lx - 13} {cy}L{lx + 12} {cy - 10}L{lx + 6} {cy + 13}L{lx - 1} {cy + 5}Z" fill="none" stroke="{PAPER}" stroke-width="1.6" stroke-linejoin="round"/>
<rect x="{rx - 28}" y="{cy - 28}" width="56" height="56" fill="{INK}" stroke="{PAPER}"/>
{"".join(f'<path d="M{rx - 15} {cy - 12 + k * 12}H{rx + 9}" stroke="{GREY}"/><rect class="pulse" style="{delay(-k * .7)}" x="{rx + 11}" y="{cy - 14 + k * 12}" width="4" height="4" fill="{SIGNAL}"/>' for k in range(3))}
<rect x="{lock_x - 12}" y="{lock_y}" width="24" height="18" fill="none" stroke="{PAPER}" stroke-width="1.5"/>
<path d="M{lock_x - 7} {lock_y}V{lock_y - 6}A7 7 0 0 1 {lock_x + 7} {lock_y - 6}V{lock_y}" fill="none" stroke="{PAPER}" stroke-width="1.5"/>
<rect x="{lock_x - 2}" y="{lock_y + 6}" width="4" height="6" fill="{SIGNAL}"/>
{label(lock_x, cy + 58, 'mtproto ⇄ websocket', GREY, anchor='middle', size=10)}
{label(lx, cy + 46, 'tg', DIM, anchor='middle', size=9)}{label(rx, cy + 46, 'dc', DIM, anchor='middle', size=9)}'''
    return svg, css


DESK_CYCLE = 12
PROJECTS = ['PrimeBoost', 'astra-tg', 'Prime CLI', 'portfolio']


def desktop(x, y, w, h):
    side = 128
    cx = x + side
    css = ''
    rows = []
    for index, name in enumerate(PROJECTS):
        rows.append(text(x + 30, y + 78 + index * 26, name, 12.5, PAPER if index == 2 else GREY, mono=True))
    frames = [f'{100 * i / len(PROJECTS):.1f}%,{100 * i / len(PROJECTS) + 20:.1f}%{{transform:translateY({i * 26}px)}}' for i in range(len(PROJECTS))]
    frames.append('100%{transform:translateY(0)}')
    css += f'@keyframes dpick{{{"".join(frames)}}}.dpick{{animation:dpick 9s cubic-bezier(.77,0,.18,1) infinite}}'
    activity = [('read', 'src/app/router.ts', 8), ('lsp', 'diagnostics · 0 errors', 16),
                ('edit', 'src/app/auth.ts', 24), ('diff', '+128 -14 · 4 files', 32)]
    lines = []
    for index, (tag, value, start) in enumerate(activity):
        css += appear(f'da{index}', start, DESK_CYCLE)
        lines.append(f'<g class="da{index}">{text(cx + 18, y + 104 + index * 24, tag.upper(), 9.5, DIM, 700, mono=True, spacing=1.2)}'
                     f'{text(cx + 66, y + 104 + index * 24, value, 12, GREY, mono=True)}</g>')
    css += appear('dapprove', 38, DESK_CYCLE)
    css += f'@keyframes dclick{{0%,52%{{fill:{INK}}}54%,100%{{fill:{SIGNAL}}}}}.dclick{{animation:dclick {DESK_CYCLE}s steps(1,end) infinite}}'
    css += f'@keyframes dtext{{0%,52%{{fill:{SIGNAL}}}54%,100%{{fill:{INK}}}}}.dtext{{animation:dtext {DESK_CYCLE}s steps(1,end) infinite}}'
    css += appear('ddiff', 56, DESK_CYCLE)
    diff_x = x + w - 140
    diff = ''.join(
        f'<rect x="{diff_x + 14}" y="{y + 70 + k * 16}" width="{[90, 70, 104, 56, 84, 96, 62][k]}" height="6" fill="{SIGNAL if k in (2, 4) else (DIM if k == 3 else GREY)}" opacity="{1 if k in (2, 4) else .7}"/>'
        + (text(diff_x + 4, y + 77 + k * 16, '+' if k in (2, 4) else ('−' if k == 3 else ' '), 10, SIGNAL if k in (2, 4) else DIM, 700, mono=True))
        for k in range(7))
    bottom_y = y + h - 54
    bar_h = 34
    bar_y = bottom_y - bar_h - 10
    bar_w = diff_x - cx - 24
    btn_w = 72
    btn_h = 20
    btn_x = diff_x - 12 - 8 - btn_w
    btn_y = bar_y + 7
    svg = f'''
<path d="M{x} {y + 34}H{x + w}M{cx} {y + 34}V{y + h}M{diff_x} {y + 34}V{bottom_y}" stroke="{LINE}"/>
{label(x + 18, y + 22, 'prime desktop', PAPER, size=10.5)}
{label(x + w - 18, y + 22, 'tauri · react · go engine', DIM, anchor='end', size=9.5)}
{label(x + 18, y + 54, 'проекты', DIM, size=9.5)}
<g class="dpick"><rect x="{x + 18}" y="{y + 70}" width="4" height="12" fill="{SIGNAL}"/></g>
{"".join(rows)}
{label(x + 18, y + h - 22, 'ssh · automations', DIM, size=9)}
<rect x="{cx + 16}" y="{y + 50}" width="{diff_x - cx - 32}" height="28" fill="{PANEL}" stroke="{LINE}"/>
{text(cx + 28, y + 68.5, 'добавь вход через Telegram', 12, PAPER)}
{"".join(lines)}
<g class="dapprove">
  <rect x="{cx + 12}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3" fill="{INK}" stroke="{SIGNAL}" stroke-width="1.2"/>
  <circle cx="{cx + 24}" cy="{bar_y + 17}" r="2.5" fill="{SIGNAL}"/>
  {text(cx + 32, bar_y + 20.5, 'Применить правки', 10.5, PAPER, 700)}
  <rect class="dclick" x="{btn_x}" y="{btn_y}" width="{btn_w}" height="{btn_h}" rx="2" fill="{INK}" stroke="{SIGNAL}"/>
  {text(btn_x + btn_w / 2, btn_y + 13.5, 'разрешить ↵', 9, SIGNAL, 700, anchor='middle', mono=True, cls='dtext')}
</g>
{label(diff_x + 14, y + 54, 'diff', DIM, size=9.5)}
<g class="ddiff">{diff}</g>
<path d="M{cx} {bottom_y}H{x + w}" stroke="{LINE}"/>
{text(cx + 20, y + h - 22, '›', 15, GREY, 700, mono=True)}
<rect class="blink" x="{cx + 38}" y="{y + h - 34}" width="8" height="15" fill="{PAPER}"/>
<rect x="{x + w - 46}" y="{y + h - 40}" width="28" height="28" fill="none" stroke="{PAPER}"/>
<rect x="{x + w - 35}" y="{y + h - 34}" width="6" height="11" rx="3" fill="none" stroke="{PAPER}" stroke-width="1.4"/>
<path d="M{x + w - 39} {y + h - 26}A7 7 0 0 1 {x + w - 25} {y + h - 26}M{x + w - 32} {y + h - 19}V{y + h - 16}" fill="none" stroke="{PAPER}" stroke-width="1.4"/>
{"".join(f'<rect class="fbb eq" style="{delay(-(k * .23) % 1.5)};animation-duration:{1 + (k % 4) * .2:.1f}s" x="{x + w - 150 + k * 6}" y="{y + h - 34}" width="3" height="16" fill="{SIGNAL}"/>' for k in range(16))}'''
    return svg, css
