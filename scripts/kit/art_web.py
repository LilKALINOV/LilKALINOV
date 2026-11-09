import math

from .canvas import text, label, delay, window_keyframes
from .solid import (icosahedron, fibonacci_sphere, meridian, parallel, rotate, angles,
                    animated_edges, animated_points, polyline_frames, static_polyline, depth_opacity)
from .theme import PAPER, GREY, DIM, LINE, SIGNAL, INK

GLOBE_STEP = 3
CLICK_CYCLE = 7
CALLOUTS = [('next.js', -150, -96, -60, -40), ('three.js', 140, -110, 58, -50), ('react', -170, 96, -70, 44), ('gsap', 150, 104, 66, 40)]


def callout(cx, cy, name, lx, ly, px, py, index):
    anchor = 'end' if lx < 0 else 'start'
    shift = -6 if lx < 0 else 6
    elbow = cx + lx + (24 if lx < 0 else -24)
    return (f'<g class="fade" style="{delay(1 + index * .2)}">'
            f'<path d="M{cx + px} {cy + py}L{elbow} {cy + ly}H{cx + lx}" fill="none" stroke="{GREY}" stroke-width=".9"/>'
            f'<rect x="{cx + px - 3}" y="{cy + py - 3}" width="6" height="6" fill="{SIGNAL}"/>'
            + label(cx + lx + shift, cy + ly + 4, name, PAPER, anchor=anchor, size=11) + '</g>')


def portfolio(x, y, w, h):
    cx, cy = x + w / 2, y + h / 2 + 4
    vertices, edges = icosahedron()
    pitch = .42
    wire = animated_edges(vertices, edges, cx, cy, 92, pitch, 26, PAPER, 1.2)
    corners = animated_points(vertices, cx, cy, 92, pitch, 26, PAPER, radius=2.6)
    cloud = animated_points(fibonacci_sphere(64), cx, cy, 136, pitch, 40, GREY, radius=1.4, yaw_offset=.3)
    orbit = f'M{cx - 180} {cy}A180 40 0 1 1 {cx + 180} {cy}A180 40 0 1 1 {cx - 180} {cy}'
    svg = f'''
<path d="M{cx} {y + 12}V{y + h - 12}M{x + 12} {cy}H{x + w - 12}" stroke="{LINE}" stroke-dasharray="2 6"/>
{cloud}
<g transform="rotate(-12 {cx} {cy})"><path d="{orbit}" fill="none" stroke="{DIM}" stroke-dasharray="3 5"/>
<rect x="-4" y="-4" width="8" height="8" fill="{SIGNAL}"><animateMotion dur="7s" repeatCount="indefinite" path="{orbit}"/></rect></g>
{wire}{corners}
{"".join(callout(cx, cy, *item, index) for index, item in enumerate(CALLOUTS))}
{label(x + 14, y + h - 14, 'icosahedron · 26s / rev', DIM, size=10)}'''
    return svg, ''


def nova(x, y, w, h):
    ground = y + h - 14
    towers = [(14, 54, 66), (74, 50, 98), (130, 62, 78), (198, 76, 140), (280, 54, 110), (340, 46, 86), (392, 62, 112), (460, 40, 70)]
    shapes, windows = [], []
    for index, (bx, bw, bh) in enumerate(towers):
        if bx + bw > w - 8:
            continue
        left, top = x + bx, ground - bh
        shapes.append(f'<rect x="{left}" y="{top}" width="{bw}" height="{bh}" fill="{INK}" stroke="{PAPER if bh > 130 else GREY}" stroke-width="1"/>')
        cols, rows = int((bw - 12) // 10), int((bh - 14) // 13)
        for r in range(rows):
            for c in range(cols):
                k = index * 97 + r * 13 + c * 7
                wx, wy = left + 7 + c * 10, top + 9 + r * 13
                if k % 3:
                    color = SIGNAL if k % 5 == 0 else PAPER
                    windows.append(f'<rect class="flicker" style="{delay(-(k * .37) % 7)};animation-duration:{5 + k % 7}s" x="{wx}" y="{wy}" width="5" height="7" fill="{color}"/>')
                else:
                    windows.append(f'<rect x="{wx}" y="{wy}" width="5" height="7" fill="{DIM}" opacity=".5"/>')
    tx, tip = x + 236, ground - 140
    mx, my = x + w - 64, y + 34
    svg = f'''
<circle cx="{mx}" cy="{my}" r="14" fill="none" stroke="{PAPER}"/>
<path d="M{mx - 14} {my}H{mx - 30}M{mx + 14} {my}H{mx + 30}" stroke="{DIM}"/>
{"".join(shapes)}
<path d="M{tx} {tip}V{tip - 22}" stroke="{PAPER}"/>
<rect class="blink" style="animation-duration:1.8s" x="{tx - 3}" y="{tip - 27}" width="6" height="6" fill="{SIGNAL}"/>
{"".join(windows)}
<path d="M{x} {ground}H{x + w}" stroke="{PAPER}"/>
{"".join(f'<path d="M{x + k * 24} {ground}l-8 10" stroke="{DIM}"/>' for k in range(1, int(w // 24) + 1))}'''
    return svg, ''


def globe(x, y, w, h):
    cx, cy, radius = x + 130, y + h / 2, min(h / 2 - 16, 70)
    pitch = .4
    turns = 1 / 12
    lines = []
    for latitude in (-60, -30, 0, 30, 60):
        ring = parallel(math.radians(latitude))
        lines.append(f'<path d="{static_polyline(ring, cx, cy, radius, pitch, front_only=False)}" fill="none" stroke="{DIM}" stroke-opacity=".5"/>')
        lines.append(f'<path d="{static_polyline(ring, cx, cy, radius, pitch)}" fill="none" stroke="{GREY}"/>')
    for k in range(12):
        longitude = math.radians(k * 30)
        frames = polyline_frames(meridian(longitude), cx, cy, radius, pitch, turns)
        opacity = [f'{.15 + .85 * depth_opacity(rotate((math.sin(longitude), 0, math.cos(longitude)), yaw, pitch)[2], 1, 0):.2f}' for yaw in angles(turns)]
        lines.append(f'<path d="{frames[0]}" fill="none" stroke="{PAPER}" stroke-width=".9" opacity="{opacity[0]}">'
                     f'<animate attributeName="d" dur="{GLOBE_STEP}s" repeatCount="indefinite" values="{";".join(frames)}"/>'
                     f'<animate attributeName="opacity" dur="{GLOBE_STEP}s" repeatCount="indefinite" values="{";".join(opacity)}"/></path>')
    nodes = animated_points(fibonacci_sphere(16), cx, cy, radius, pitch, GLOBE_STEP * 12, SIGNAL, radius=3)
    sx, sy = x + w - 120, y + 52
    shield = f'M{sx} {sy - 30}L{sx + 26} {sy - 20}V{sy + 2}C{sx + 26} {sy + 20} {sx + 14} {sy + 30} {sx} {sy + 36}C{sx - 14} {sy + 30} {sx - 26} {sy + 20} {sx - 26} {sy + 2}V{sy - 20}Z'
    css = '@keyframes check{0%,12%{stroke-dashoffset:100}32%,86%{stroke-dashoffset:0}100%{stroke-dashoffset:-100}}.check{stroke-dasharray:100;animation:check 4.5s cubic-bezier(.65,0,.35,1) infinite}'
    svg = f'''
<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{INK}" stroke="{PAPER}"/>
{"".join(lines)}
{nodes}
<path d="{shield}" fill="none" stroke="{PAPER}" stroke-width="1.4" stroke-linejoin="round"/>
<path class="check" pathLength="100" d="M{sx - 11} {sy + 3}L{sx - 3} {sy + 11}L{sx + 12} {sy - 7}" fill="none" stroke="{SIGNAL}" stroke-width="2.6" stroke-linecap="square"/>
<rect class="blink" style="animation-duration:1.6s" x="{sx - 52}" y="{sy + 58}" width="8" height="8" fill="{SIGNAL}"/>
{label(sx - 38, sy + 66, 'connected', PAPER, size=11)}
{label(sx - 52, sy + 88, 'ping 24 ms · ams', DIM, size=10)}'''
    return svg, css


def timeline(x, y, w, h):
    period = 480
    left = x + 14
    tracks = [(y + 40, [(10, 96, 'intro.mov'), (136, 150, 'b-roll'), (316, 128, 'drop')]),
              (y + 74, [(0, 172, 'main_cam.mp4'), (186, 116, 'cutaway'), (316, 150, 'slowmo')])]
    content = []
    for shift in (0, period):
        for row, (top, clips) in enumerate(tracks):
            for index, (start, length, name) in enumerate(clips):
                x0 = left + shift + start
                accent = row == 1 and index == 1
                content.append(f'<rect x="{x0}" y="{top}" width="{length}" height="26" fill="{"#2a160c" if accent else INK}" stroke="{SIGNAL if accent else GREY}"/>'
                               + text(x0 + 8, top + 17, name, 10.5, PAPER, mono=True))
        for k in range(0, period, 4):
            amplitude = 2 + 10 * abs(math.sin(k * .05) * math.cos(k * .013 + .6))
            content.append(f'<rect x="{left + shift + k}" y="{y + 126 - amplitude:.1f}" width="2" height="{amplitude * 2:.1f}" fill="{DIM}"/>')
        for k in range(0, period, 12):
            tall = k % 96 == 0
            content.append(f'<path d="M{left + shift + k} {y + 30}V{y + (20 if tall else 25)}" stroke="{GREY if tall else DIM}"/>')
            if tall:
                content.append(text(left + shift + k + 4, y + 22, f'00:{(k // 96) * 4 + 8:02d}', 9, DIM, mono=True))
    css = f'.tl{{--shift:-{period}px;animation:marquee 16s linear infinite}}'
    head = x + w * .58
    svg = f'''
<g class="tl">{"".join(content)}</g>
<path d="M{head} {y + 12}V{y + h - 8}" stroke="{SIGNAL}" stroke-width="1.6"/>
<path d="M{head - 6} {y + 6}H{head + 6}V{y + 12}L{head} {y + 18}L{head - 6} {y + 12}Z" fill="{SIGNAL}"/>
<rect x="{head + 10}" y="{y + 4}" width="92" height="18" fill="{INK}" stroke="{SIGNAL}"/>
{text(head + 56, y + 17, '00:01:24:12', 10.5, PAPER, 600, anchor='middle', mono=True)}'''
    return svg, css


def landing(x, y, w, h):
    bx, by, bw, bh = x + 22, y + 16, 290, h - 16
    bxr, byr = bx + 24, by + 98
    target_x, target_y = bxr + 80, byr + 16
    css = (f'@keyframes cursor{{0%{{transform:translate(170px,60px);opacity:0}}8%{{opacity:1}}36%{{transform:translate(0,0)}}40%{{transform:translate(0,0) scale(.82)}}44%,82%{{transform:translate(0,0);opacity:1}}94%,100%{{transform:translate(170px,60px);opacity:0}}}}'
           f'.cursor{{animation:cursor {CLICK_CYCLE}s cubic-bezier(.65,0,.35,1) infinite}}'
           f'@keyframes press{{0%,38%,46%,100%{{transform:scale(1)}}41%{{transform:scale(.94)}}}}.press{{animation:press {CLICK_CYCLE}s ease infinite}}'
           + window_keyframes('toast', 48, 90, fade=5, lift=-10) + f'.toast{{animation:toast {CLICK_CYCLE}s cubic-bezier(.2,.8,.2,1) infinite}}')
    tx, ty = x + w - 196, y + 70
    svg = f'''
<rect x="{bx}" y="{by}" width="{bw}" height="{bh + 20}" fill="{INK}" stroke="{GREY}"/>
<path d="M{bx} {by + 24}H{bx + bw}" stroke="{LINE}"/>
{label(bx + 12, by + 16, 'heyksusha.ru/intensive', DIM, size=9.5)}
{label(bx + 24, by + 46, 'интенсив', SIGNAL, size=10)}
{text(bx + 24, by + 76, 'Hey, Ksusha', 24, PAPER, 800, spacing=-.5)}
<rect x="{bx + 24}" y="{by + 84}" width="150" height="3" fill="{DIM}"/>
<g class="fb press"><rect x="{bxr}" y="{byr}" width="124" height="32" fill="{SIGNAL}"/>
{text(bxr + 62, byr + 21, 'Записаться', 13, INK, 700, anchor='middle')}</g>
<circle cx="{bx + 236}" cy="{by + 72}" r="30" fill="none" stroke="{PAPER}"/>
<circle cx="{bx + 236}" cy="{by + 64}" r="9" fill="none" stroke="{PAPER}"/>
<path d="M{bx + 220} {by + 92}C{bx + 222} {by + 78} {bx + 250} {by + 78} {bx + 252} {by + 92}" fill="none" stroke="{PAPER}"/>
<g class="toast"><rect x="{tx}" y="{ty}" width="176" height="44" fill="{INK}" stroke="{PAPER}"/>
<rect x="{tx}" y="{ty}" width="4" height="44" fill="{SIGNAL}"/>
{text(tx + 16, ty + 19, 'Оплата прошла', 13, PAPER, 700)}{label(tx + 16, ty + 35, 'место забронировано', GREY, size=9.5)}</g>
<g transform="translate({target_x} {target_y})"><g class="cursor"><path d="M0 0L0 19L5 14L9 23L12.5 21.5L8.5 13L15 13Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round"/></g></g>'''
    return svg, css
