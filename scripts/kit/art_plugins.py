import math
from .canvas import text, label, delay, window_keyframes
from .scope import oscilloscope
from .theme import PAPER, GREY, DIM, LINE, SIGNAL, INK, PANEL

STT_CYCLE = 8
TTS_CYCLE = 9
DDG_CYCLE = 8
JOURNEY_CYCLE = 10


def appear(name, start, end, cycle):
    return window_keyframes(name, start, end, fade=3, lift=6) + f'.{name}{{animation:{name} {cycle}s cubic-bezier(.2,.8,.2,1) infinite}}'


def stt(x, y, w, h):
    lx = x + 16
    bw = 136
    rx = x + 188
    rw = w - 204
    cy = y + 86

    # Equalizer bars on the left (audio input)
    bar_heights = [14, 28, 46, 68, 52, 34, 18]
    eq_bars = ''.join(
        f'<rect class="fb eq" style="{delay(-(i * .19) % 1.4)};animation-duration:{.85 + (i % 5) * .15:.2f}s"'
        f' x="{lx + 14 + i * 16}" y="{y + 88 - h_bar / 2:.1f}" width="8" height="{h_bar}" rx="2"'
        f' fill="{SIGNAL if i == 3 else (PAPER if i in (2, 4) else GREY)}"/>'
        for i, h_bar in enumerate(bar_heights)
    )

    bus_path = f'M{lx + bw} {cy}H{rx}'

    css = appear('st1', 2, 94, STT_CYCLE) + appear('st2', 28, 94, STT_CYCLE)

    svg = f'''
<circle cx="{lx + 8}" cy="{y + 20}" r="3" fill="{SIGNAL}"/>
{text(lx + 18, y + 24, 'MIC IN · 48 kHz / 16-BIT PCM', 9, GREY, mono=True)}
{text(x + w - 16, y + 24, 'STREAMING ACTIVE', 9, SIGNAL, 700, mono=True, anchor='end')}
<line x1="{lx}" y1="{y + 32}" x2="{x + w - 16}" y2="{y + 32}" stroke="{LINE}"/>

<rect x="{lx}" y="{y + 40}" width="{bw}" height="96" fill="{INK}" stroke="{LINE}"/>
<rect x="{lx}" y="{y + 40}" width="{bw}" height="20" fill="{PANEL}" stroke="{LINE}"/>
{text(lx + 10, y + 54, 'AUDIO INPUT STREAM', 8, GREY, 700, mono=True)}
{eq_bars}
{text(lx + 10, y + 126, 'VAD: VOICE DETECTED', 8, DIM, mono=True)}

<path d="{bus_path}" stroke="{LINE}" stroke-width="1.6" stroke-dasharray="3 3"/>
<rect x="-3" y="-3" width="6" height="6" fill="{SIGNAL}"><animateMotion dur="1.6s" repeatCount="indefinite" path="{bus_path}"/></rect>
{text(lx + bw + (rx - (lx + bw)) / 2, cy - 8, 'HTTP/2', 7.5, DIM, mono=True, anchor='middle')}

<rect x="{rx}" y="{y + 40}" width="{rw}" height="96" fill="{INK}" stroke="{LINE}"/>
<rect x="{rx}" y="{y + 40}" width="{rw}" height="22" fill="{PANEL}" stroke="{LINE}"/>
{text(rx + 12, y + 55, 'GOOGLE WEB SPEECH', 8.5, SIGNAL, 800, mono=True)}
<rect x="{rx + rw - 76}" y="{y + 45}" width="66" height="12" rx="2" fill="{INK}" stroke="{LINE}"/>
{text(rx + rw - 43, y + 54, 'KEYLESS / FREE', 7.5, GREY, mono=True, anchor='middle')}

{text(rx + 12, y + 78, 'INPUT_STREAM:', 8, DIM, 700, mono=True)}
<g class="st1">
  {text(rx + 12, y + 98, '«открой проект Prime»', 12, PAPER, 700, mono=True)}
  <rect class="pulse" x="{rx + 184}" y="{y + 87}" width="6" height="13" fill="{SIGNAL}"/>
</g>
<g class="st2">
  {text(rx + 12, y + 124, 'status: 200 · conf: 0.99 · 28ms', 8.5, GREY, mono=True)}
</g>

<line x1="{lx}" y1="{y + 148}" x2="{x + w - 16}" y2="{y + 148}" stroke="{LINE}"/>
{text(lx, y + 164, 'ASTRA AUDIO PIPELINE · DIRECT WEBSOCKET / TLS', 8, DIM, mono=True)}
{text(x + w - 16, y + 164, 'ZERO LATENCY', 8, GREY, mono=True, anchor='end')}'''
    return svg, css


def silero(x, y, w, h):
    lx = x + 16
    cy = y + 86
    bw = 144
    cx = x + 198
    rx = x + 236
    rw = w - 252

    bus1 = f'M{lx + bw} {cy}H{cx - 18}'
    bus2 = f'M{cx + 18} {cy}H{rx}'

    chip_dots = []
    for row in range(3):
        for col in range(3):
            dot_color = SIGNAL if (row == 1 and col == 1) or (row + col) % 3 == 0 else (PAPER if (row + col) % 2 == 0 else DIM)
            chip_dots.append(f'<circle cx="{cx - 8 + col * 8}" cy="{cy - 8 + row * 8}" r="2" fill="{dot_color}"/>')

    wave_pts = []
    for px in range(0, int(rw - 24), 3):
        angle = px * 0.14
        h_sin = math.sin(angle) * 16 * math.sin(px * 0.04)
        wave_pts.append(f'{rx + 12 + px:.1f} {y + 90 - h_sin:.1f}')
    wave_path = 'M' + ' L'.join(wave_pts)

    css = appear('sl1', 4, 94, TTS_CYCLE) + appear('sl2', 30, 94, TTS_CYCLE)

    svg = f'''
<circle cx="{lx + 8}" cy="{y + 20}" r="3" fill="{SIGNAL}"/>
{text(lx + 18, y + 24, 'TEXT-TO-SPEECH (RU) · SILERO V4', 9, GREY, mono=True)}
{text(x + w - 16, y + 24, '100% OFFLINE', 9, SIGNAL, 700, mono=True, anchor='end')}
<line x1="{lx}" y1="{y + 32}" x2="{x + w - 16}" y2="{y + 32}" stroke="{LINE}"/>

<rect x="{lx}" y="{y + 40}" width="{bw}" height="96" fill="{INK}" stroke="{LINE}"/>
<rect x="{lx}" y="{y + 40}" width="{bw}" height="20" fill="{PANEL}" stroke="{LINE}"/>
{text(lx + 10, y + 54, 'TEXT BUFFER (RU)', 8, GREY, 700, mono=True)}
{text(lx + 10, y + 78, 'astra.speak(', 8.5, DIM, mono=True)}
<g class="sl1">
  {text(lx + 10, y + 98, '«Ассистент готов»', 11, PAPER, 700, mono=True)}
</g>
{text(lx + 10, y + 116, ')', 8.5, DIM, mono=True)}
{text(lx + 10, y + 128, 'lang: ru · tokens: 3', 7.5, GREY, mono=True)}

<path d="{bus1}" stroke="{LINE}" stroke-width="1.6" stroke-dasharray="2 3"/>
<rect x="-3" y="-3" width="6" height="6" fill="{PAPER}"><animateMotion dur="1.8s" repeatCount="indefinite" path="{bus1}"/></rect>

<rect x="{cx - 18}" y="{cy - 18}" width="36" height="36" fill="{INK}" stroke="{SIGNAL}" stroke-width="1.4"/>
{text(cx, cy - 23, 'NEURAL', 7.5, DIM, 700, mono=True, anchor='middle')}
{"".join(chip_dots)}
{text(cx, cy + 30, 'VOCODER', 7.5, DIM, 700, mono=True, anchor='middle')}

<path d="{bus2}" stroke="{LINE}" stroke-width="1.6" stroke-dasharray="2 3"/>
<rect x="-3" y="-3" width="6" height="6" fill="{SIGNAL}"><animateMotion dur="1.8s" repeatCount="indefinite" path="{bus2}"/></rect>

<rect x="{rx}" y="{y + 40}" width="{rw}" height="96" fill="{INK}" stroke="{LINE}"/>
<rect x="{rx}" y="{y + 40}" width="{rw}" height="20" fill="{PANEL}" stroke="{LINE}"/>
{text(rx + 10, y + 54, 'AUDIO OUT · 24 kHz', 8, SIGNAL, 700, mono=True)}
{text(rx + rw - 10, y + 54, '0ms NETWORK', 7.5, GREY, mono=True, anchor='end')}
<line x1="{rx + 10}" y1="{y + 90}" x2="{rx + rw - 10}" y2="{y + 90}" stroke="{LINE}" stroke-dasharray="2 4"/>
<g class="sl2">
  <path d="{wave_path}" fill="none" stroke="{SIGNAL}" stroke-width="1.8"/>
</g>
{text(rx + 10, y + 126, 'ON-DEVICE · SILERO NEURAL SYNTH', 8, GREY, mono=True)}

<line x1="{lx}" y1="{y + 148}" x2="{x + w - 16}" y2="{y + 148}" stroke="{LINE}"/>
{text(lx, y + 164, 'LOCAL INFERENCE · ZERO CLOUD API · ZERO TELEMETRY', 8, DIM, mono=True)}
{text(x + w - 16, y + 164, 'STATUS: READY', 8, GREY, mono=True, anchor='end')}'''
    return svg, css


def ddg(x, y, w, h):
    cy = y + h / 2
    lx = x + 24
    sweep_x, sweep_y = x + w - 80, cy

    css = appear('dd1', 4, 94, DDG_CYCLE) + appear('dd2', 30, 94, DDG_CYCLE)
    css += '@keyframes ddgradar{to{transform:rotate(360deg)}}.ddgradar{transform-origin:center;animation:ddgradar 6s linear infinite}'

    svg = f'''
{label(lx, y + 20, 'DDG: REAL-TIME SEARCH', SIGNAL, size=9.5)}
<rect x="{lx}" y="{y + 28}" width="260" height="34" fill="{INK}" stroke="{PAPER}"/>
{text(lx + 12, y + 50, '$ astra search prime', 13, PAPER, mono=True)}
<rect class="pulse" x="{lx + 205}" y="{y + 38}" width="7" height="14" fill="{SIGNAL}"/>
<g class="dd1">
  <rect x="{lx}" y="{y + 72}" width="260" height="48" fill="{INK}" stroke="{LINE}"/>
  {text(lx + 12, y + 90, 'RESULT 01: github.com/SpherePrime', 12, PAPER, 700)}
  {text(lx + 12, y + 107, 'HTTP 200 · no ratelimit · instant parse', 11, GREY, mono=True)}
</g>
<g class="dd2">
  <rect x="{lx}" y="{y + 128}" width="260" height="34" fill="{INK}" stroke="{LINE}"/>
  {text(lx + 12, y + 150, 'RESULT 02: docs & architecture', 12, PAPER, 700)}
</g>
<circle cx="{sweep_x}" cy="{sweep_y}" r="44" fill="{INK}" stroke="{LINE}"/>
<circle cx="{sweep_x}" cy="{sweep_y}" r="28" fill="none" stroke="{LINE}" stroke-dasharray="2 4"/>
<circle cx="{sweep_x}" cy="{sweep_y}" r="4" fill="{SIGNAL}"/>
<g class="ddgradar" style="transform-box:fill-box;transform-origin:{sweep_x}px {sweep_y}px">
  <line x1="{sweep_x}" y1="{sweep_y}" x2="{sweep_x + 44}" y2="{sweep_y}" stroke="{SIGNAL}" stroke-width="1.8"/>
</g>
{label(sweep_x, sweep_y + 58, 'DDG RADAR', GREY, anchor='middle', size=9.5)}'''
    return svg, css


def journey(x, y, w, h):
    cy = y + h / 2
    nodes = [
        ('STELLA', 'Голосовой мод', '2024 · Старт', x + 76),
        ('ASTRA', 'Lead QA & Тесты', '2025 · KNICE', x + w / 2),
        ('SPHEREPRIME', 'Со-основатель', '2026 · Prime', x + w - 76)
    ]
    path = f'M{nodes[0][3]} {cy}H{nodes[2][3]}'
    svg_nodes = []
    for i, (title, sub, year, nx) in enumerate(nodes):
        is_last = (i == 2)
        color = SIGNAL if is_last else PAPER
        svg_nodes.append(f'''
<circle cx="{nx}" cy="{cy}" r="16" fill="{INK}" stroke="{color}" stroke-width="2"/>
<circle cx="{nx}" cy="{cy}" r="6" fill="{color}"/>
{label(nx, cy - 26, title, color, anchor='middle', size=11)}
{text(nx, cy + 34, sub, 13.5, PAPER if is_last else GREY, 700 if is_last else 400, anchor='middle')}
{text(nx, cy + 52, year, 11, DIM, anchor='middle', mono=True)}''')

    css = '@keyframes journeywave{0%{stroke-dashoffset:40}100%{stroke-dashoffset:0}}'
    svg = f'''
<path d="{path}" fill="none" stroke="{LINE}" stroke-width="2"/>
<rect x="-4" y="-4" width="8" height="8" fill="{SIGNAL}"><animateMotion dur="4s" repeatCount="indefinite" path="{path}"/></rect>
{"".join(svg_nodes)}'''
    return svg, css
