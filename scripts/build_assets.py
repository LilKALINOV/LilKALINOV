"""Generate the LilKALINOV profile README visuals: self-contained animated SVGs.

The README carries no prose at all — every word on the page is drawn here, so
this module is the whole design system, not a set of pictures.

Grid
----
AXIS (52) is for structure: rules, accent bars, pill outlines, marker gutters.
TEXT (74) is for every run of type, in every asset. RIGHT (1048) is the content
edge. Assets are stacked as separate <img> elements, so per-panel optical
nudging would read as a broken column — the axes are absolute.

Motion
------
GitHub serves SVG through camo, which keeps <style> but drops <script>, so CSS
keyframes are the only portable animation channel. The set shares one stylesheet
across all eight assets: four drifting mesh washes, orbital spin, three stroke-
travel effects, the wordmark sheen and its tracking settle, the morphing core
ring, light running the frame edge, voice ripples, packets riding the network
routes, the equaliser, the accent scan, status pulse, drifting grain, and a
staggered entrance. All of them are neutralised under prefers-reduced-motion.

Three effects are chosen for how they fail, not just how they look. The morph
starts from the plain circle it replaced. The wordmark settle ends on the exact
tracking the layout was measured at. Every travelling dot rests at the start of
its own path. In each case a renderer that applies the animation rule but never
ticks the clock lands on a finished-looking frame.

Entrances are the one effect that can hide content, because fill-mode: both
holds the keyframe's start state during the delay. Any renderer that applies the
animation rule but never ticks the clock - headless captures, link previews,
archiving, print - freezes on that start state, so the start state has to look
finished. No entrance may begin below 62% opacity, and the hero, which is the
only load-bearing copy on the page, begins at 80%. Travel does the rest of the
work: a 9-10px rise reads as a cascade even when the fade is shallow.

Blending is real mesh, not stacked alpha: the washes and the light sources behind
the illustrations composite with `screen`, inside a frame group that is
isolation:isolate so the blend cannot reach the page behind the <img>.

The reduced-motion block cancels animation and transform only. It must not also
force opacity back to 1: the universal selector with !important outranks the
opacity presentation attribute, so that would blow every deliberate tint in the
set to full strength — the card sheen at .018 would become a solid white band
across the top of each card. Cancelling the animation is enough on its own, since
an element only ever animates away from the opacity it was authored with.

Standard library only.  Run:  python scripts/build_assets.py
"""

from __future__ import annotations

import base64
import hashlib
import re
from html import escape
from math import cos, hypot, pi, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'

# --------------------------------------------------------------------------- #
# canvas + grid
# --------------------------------------------------------------------------- #
W = 1100
HERO_H = 436
INTRO_H = 364
CARD_H = 220
FOOTER_H = 150
HERO_R = 22
CARD_R = 18

AXIS = 52       # structure: rules, accent bars, pill outlines, marker gutters
TEXT = 74       # every run of type, in every asset
RIGHT = 1048    # content right edge
COL_GAP = 22

HEAD_EYEBROW = 58
HEAD_TITLE = 102
HEAD_SUB = 134
HEAD_SIZE = 38
HEAD_RULE = 158
ROW_H = 66

# cap height as a fraction of the em, so anything that has to sit on the optical
# centre of a line — a dot in a gutter, a label in a pill — can be placed by
# arithmetic instead of by eye
CAP = 0.35
TOPBAR_H = 58

# card content block, shared by the accent bar and the tag pills so the bar
# always brackets the copy it belongs to
CARD_BAR_Y = 44
CARD_TAG_Y = 166
CARD_TAG_H = 25

# the left accent spine, one shared element drawn in all eight assets. The old
# per-card bar sat on AXIS=52 and swallowed the left edge of the first tag pill
# (pills outline at 52, the bar at 52..56 down to y=191), so it both covered
# type and existed in only three of the eight panels. Parked in the margin at
# x=26 the spine is clear of pills (52) and copy (74), and drawing it the same
# way in every asset is what makes the set read as even.
SPINE_X = 26
SPINE_W = 4
SPINE_TOP = 66       # below the 58px top bar in hero/card, so it never crosses it
SPINE_BOT = 32       # same inset off the bottom edge in every asset
SPINE_SEG = 34       # a traveling light segment, two per spine

# the footer has no top bar, so its spine may run much longer without
# crossing anything: the same left rule, just filling the short panel
SPINE_TOP_SHORT = 20
SPINE_BOT_SHORT = 20

# the standalone link buttons: one row with two big pills, each its own
# Markdown <a>-wrapped <img> in the README - that is the only thing GitHub
# makes actually clickable (anything drawn inside a panel SVG is not).
LINKS_H = 96
BTN_W = 540          # each button is half a strip: two sit side by side
LINK_PILL_W = 400
LINK_PILL_H = 76

# the avatar: the ico.jpg shipped with the repo, inlined as a data URI so the
# SVG stays a single self-contained file behind camo. It fills the orbital core
# where the "K." mark used to be, clipped to a circle inside the 58px ring.
AVR_R = 46

# --- card illustration corridor ------------------------------------------- #
# The rule the layout was missing: the vertical rule that splits the card's copy
# from its illustration is a grid line with a real gutter on each side, and the
# illustration is bounded on the right by the same RIGHT axis the type uses.
#
# It used to sit at 826 with the nearest art element 16px away - two bars
# standing in each other's pockets, stranded next to a 311px hole, because the
# copy only ever reaches x=570. The hole belonged on the copy's side of the
# rule, and the 80px of unused corridor belonged to the art.
#
# ART_X0 mirrors AXIS: the illustration gets the same 52px margin off the rule
# that the copy gets off the frame, so the rule reads as a hinge rather than as
# a wall the art is pressed against.
DIV = 706        # the copy | illustration rule
ART_X0 = 758     # DIV + AXIS: earliest an illustration element may appear
ART_X1 = RIGHT   # nothing in the illustration may cross the type's right edge
ART_Y0 = 44      # = CARD_BAR_Y
ART_Y1 = 191     # = CARD_TAG_Y + CARD_TAG_H, the block's optical floor
ART_CX = (ART_X0 + ART_X1) / 2   # 903: illustrations centre here
# the open-badge chrome in the top-right corner is NOT corridor, but it is the
# one thing the art has to steer around, so it gets a name instead of a rumour
BADGE_CX, BADGE_CY, BADGE_R = 1052, 44, 17

# hero signature mark
ORB_CX, ORB_CY = 868, 236
NAME_SIZE = 110
NAME_Y = 208
CORE_R = 58
SETTLE_TRACK = -6      # the wordmark's final tracking; the entrance opens wider
SETTLE_FROM = -1.4     # and eases into it, so the name is set rather than just placed


def ring_d(cx: float, cy: float, r: float, handle: float) -> str:
    """A closed ring as `M` plus exactly four cubics, one per quadrant.

    CSS only interpolates `d` between paths that share a command sequence, so
    the circle and the squircle are both built here from the same four segments
    and differ only in where the handles sit. `handle` is how far a control
    point steps along the tangent at its end of the arc: 0.5523*r is the
    classic circle fit, and r is the squircle fit, which is what makes the shape
    sit flat against each axis instead of bulging away the way a circle does.

    Each quadrant's c1 steps forward from the segment's start along the tangent
    there, and c2 steps back from the segment's end along that end's tangent, so
    the ring is smooth all the way round for any handle value.
    """
    k = handle
    #            c1                      c2                      end
    quads = [
        ((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r)),
        ((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy)),
        ((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r)),
        ((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy)),
    ]
    d = f'M{n(cx + r)} {n(cy)}'
    for c1, c2, end in quads:
        d += f'C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(end[0])} {n(end[1])}'
    return d + 'Z'


CIRCLE_K = 0.5523     # a cubic quadrant's control-point distance for a true circle


# --------------------------------------------------------------------------- #
# palette
# --------------------------------------------------------------------------- #
BASE = '#080b12'
PANEL_TOP = '#141c2b'
PANEL_BOT = '#0a0f19'
HAIRLINE = '#1b2333'
STROKE = '#222c3f'
GLOW_EDGE = '#ffffff14'

CHIP = '#0b1018'       # the tag chip's own surface
# Near-opaque on purpose. These chips sit in the brightest corner of every
# panel, and `screen` blending roughly triples the luminance there, so a
# translucent chip lets the mesh decide the label's contrast - measured as low
# as 2.3:1. At this fill the chip sets its own contrast instead, whatever is
# behind it, and the accent edge plus the translucency still read as glass.
CHIP_FILL = .88
CHIP_EDGE = .42

INK = '#f3f5f9'
INK_SOFT = '#c5cddd'
INK_MUTE = '#8b95ab'
# the 11px orbit caption is the smallest type here, so this must clear WCAG AA
# (4.5:1) against BOTH ends of the panel gradient; #5f6a80 only reached 3.1:1.
INK_FAINT = '#7e8899'

# The orbit caption lands where two aurora blobs overlap at full strength, so
# its real background measures L=0.048 - eight times the panel floor - and 11px
# grey type drops to 3.2:1. The blobs cannot be pulled back without hollowing
# out the hero, and the caption cannot be brightened without competing with the
# name, so it gets the answer the tag pills already got: its own dark surface.
# Nearly opaque, because here the wash underneath is three times brighter than
# anything behind a pill, and the blobs drift.
CAPTION_SURFACE = '#080d15'
CAPTION_FILL = 0.94
CAPTION_H = 22
CAPTION_PAD = 14

CORAL = '#ff6a3d'
EMBER = '#ff9f6e'
BLUSH = '#ffcab0'
CYAN = '#22d3ee'
VIOLET = '#8b6dff'
SPHERE = '#f472b6'

RUST = ('#ff8a4c', '#ffcf87')
PY = ('#4b8bf0', '#7fd7ff')
GO = ('#00c8b8', '#6ef0dd')
TS = ('#a78bfa', '#d6c9ff')

ADVANCE = {'mono': 0.56, 'sans': 0.52}

# --------------------------------------------------------------------------- #
# shared svg chrome
# --------------------------------------------------------------------------- #
STYLE = """
 text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif}
 .mono{font-family:'JetBrains Mono','Cascadia Code',Consolas,ui-monospace,'Courier New',monospace}
 /* 1. aurora blobs drifting on independent cycles */
 .drift-a{transform-box:fill-box;transform-origin:50% 50%;animation:drift-a 24s ease-in-out infinite}
 .drift-b{transform-box:fill-box;transform-origin:50% 50%;animation:drift-b 31s ease-in-out infinite}
 .drift-c{transform-box:fill-box;transform-origin:50% 50%;animation:drift-c 19s ease-in-out infinite}
 /* 2. orbital rings */
 .spin{transform-box:fill-box;transform-origin:50% 50%;animation:spin 26s linear infinite}
 .spin-rev{transform-box:fill-box;transform-origin:50% 50%;animation:spin 38s linear infinite reverse}
 /* 3. light running along a stroke */
 .dash{stroke-dasharray:10 26;animation:dash 3.6s linear infinite}
 .flow{stroke-dasharray:5 44;animation:flow 2.45s linear infinite}
 .ghostflow{stroke-dasharray:46 600;animation:ghostflow 7s linear infinite}
 /* 4. sheen sweeping the wordmark */
 .sweep{animation:sweep 7s linear infinite}
 /* 5. voice ripples leaving the core */
 .ripple{transform-box:fill-box;transform-origin:50% 50%;animation:ripple 3.6s cubic-bezier(.2,.6,.3,1) infinite}
 /* 6. equaliser bars */
 .eq{transform-box:fill-box;animation:eq 1.15s ease-in-out infinite alternate}
 .up{transform-origin:50% 100%}
 .dn{transform-origin:50% 0%}
 /* 7. light pulses riding the left accent spine */
 .spimp{animation:spimp 5.2s linear infinite}
 /* 8. status dot */
 .blink{animation:blink 2.4s ease-in-out infinite}
 .pulse{animation:pulse 4.5s ease-in-out infinite}
 /* 9. staggered entrance */
 .enter{animation:enter .62s cubic-bezier(.34,1.42,.52,1) both}
 .enter-soft{animation:enter-soft .8s cubic-bezier(.34,1.42,.52,1) both}
 /* 10. true mesh blending - screen adds light where two washes overlap, which is
     what a mesh gradient actually is; plain alpha just stacks grey. The frame
     group is isolation:isolate so the blend can never reach the page behind. */
 .mesh{mix-blend-mode:screen}
 /* 11. light travelling the frame edge, distance supplied per asset as --edge */
 .edgeflow{stroke-linecap:round;animation:edgeflow 9s linear infinite}
 /* 12. the core ring breathing between a circle and a squircle; `d` needs both
     paths to carry the same commands, and `from` is the plain circle so a
     renderer without CSS `d` shows exactly the current design */
 .morph{animation:morph 9.5s cubic-bezier(.45,0,.55,1) infinite alternate}
 /* 13. the wordmark settling from open tracking into its final fit. The masked
     copy inside #nm carries the same class, or the sheen would drift off the
     letters while the tracking changes under it. */
 .settle{animation:settle 1.6s cubic-bezier(.22,.68,.32,1) both}
 /* 14. a packet riding a path. Drawn as a 0.1-long round-capped dash on the very
     path it travels, so the dot is always exactly on the line and needs no
     offset-path; at rest it sits at the path's start, which is the right place
     for a renderer that never ticks the clock. --len is the measured path
     length, supplied per element, so one keyframe serves every route. */
 .packet{fill:none;stroke-linecap:round;animation:packet 3.6s linear infinite}
 /* 15. a second grain plate drifting against the first, so the texture lives */
 .grainx{animation:grainx 26s steps(9) infinite}
 .drift-d{transform-box:fill-box;transform-origin:50% 50%;animation:drift-d 27s ease-in-out infinite}
 @keyframes drift-a{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(34px,-24px) scale(1.12)}}
 @keyframes drift-b{0%,100%{transform:translate(0,0) scale(1.06)}50%{transform:translate(-42px,20px) scale(.94)}}
 @keyframes drift-c{0%,100%{transform:translate(0,0) scale(.96)}50%{transform:translate(24px,30px) scale(1.1)}}
 @keyframes drift-d{0%,100%{transform:translate(0,0) scale(1.04)}50%{transform:translate(-30px,26px) scale(.92)}}
 @keyframes spin{to{transform:rotate(360deg)}}
 @keyframes dash{to{stroke-dashoffset:-360}}
 @keyframes flow{to{stroke-dashoffset:-490}}
 @keyframes ghostflow{to{stroke-dashoffset:-646}}
 @keyframes sweep{0%{transform:translateX(-230px)}58%{transform:translateX(840px)}100%{transform:translateX(840px)}}
 @keyframes ripple{0%{transform:scale(.5);opacity:.6}70%{opacity:.1}100%{transform:scale(1.85);opacity:0}}
 @keyframes eq{from{transform:scaleY(.2)}to{transform:scaleY(1)}}
 @keyframes spimp{from{transform:translateY(-40px)}to{transform:translateY(calc(var(--spine-h) + 6px))}}
 @keyframes twinkle{0%,100%{opacity:.15;scale:.6}50%{opacity:.9;scale:1.25}}
 @keyframes drift-t{from{translate:0 0}to{translate:0 6px}}
 .twinkle{transform-box:fill-box;transform-origin:50% 50%;animation:twinkle 4.2s ease-in-out infinite,drift-t 9s ease-in-out infinite alternate}
 @keyframes blink{0%,100%{opacity:.35}50%{opacity:1}}
 @keyframes pulse{0%,100%{opacity:.3}50%{opacity:.9}}
 @keyframes edgeflow{to{stroke-dashoffset:calc(-1 * var(--edge))}}
 @keyframes grainx{0%{transform:translate(0,0)}100%{transform:translate(-140px,90px)}}
 @keyframes enter{from{opacity:.62;transform:translateY(10px)}to{opacity:1;transform:none}}
 @keyframes enter-soft{from{opacity:.8;transform:translateY(9px)}to{opacity:1;transform:none}}
 @keyframes gwsweep{from{transform:translateX(-420px)}to{transform:translateX(1520px)}}
 .gws{animation:gwsweep 8.5s cubic-bezier(.45,0,.55,1) infinite}
 @keyframes btsweep{0%{transform:translateX(-140px)}60%{transform:translateX(150px)}100%{transform:translateX(150px)}}
 .btsweep{animation:btsweep 5.2s cubic-bezier(.45,0,.55,1) infinite}
 @media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transform:none!important;scale:1!important;translate:0 0!important}}
"""


def n(value) -> str:
    """Compact number formatting — keeps .42 from leaking out as 0.42000000000000004."""
    if isinstance(value, int):
        return str(value)
    out = f'{value:.3f}'.rstrip('0').rstrip('.')
    return '0' if out in {'', '-0'} else out


# The morph keyframes carry the two ring paths, so they are appended rather than
# written inline: `from` is the plain circle, which is exactly what the design
# showed before this effect existed, and is what any renderer without CSS `d`
# animation falls back to.
#
# settle and packet are appended for the same reason - their end values are
# numbers the layout already depends on, so they are generated from the same
# constants rather than retyped into the stylesheet where they could drift.
STYLE += (
    ' @keyframes morph{from{d:path(\''
    + ring_d(ORB_CX, ORB_CY, CORE_R, CIRCLE_K * CORE_R)
    + '\')}to{d:path(\''
    + ring_d(ORB_CX, ORB_CY, CORE_R, float(CORE_R))
    + '\')}}'
    + f' @keyframes settle{{from{{letter-spacing:{n(SETTLE_FROM)}px}}'
      f'to{{letter-spacing:{n(SETTLE_TRACK)}px}}}}'
      ' @keyframes packet{from{stroke-dashoffset:0}to{stroke-dashoffset:calc(-1 * var(--len))}}'
)


def cubic_len(p0, p1, p2, p3, steps=96):
    """Length of a cubic by chord sampling.

    The packet keyframe travels exactly one path length, and the dash gap has to
    be at least that long or the dot would wrap back onto the line it already
    crossed. Sampling is deterministic, so builds stay byte-for-byte stable.
    """
    total = 0.0
    px, py = p0
    for i in range(1, steps + 1):
        t = i / steps
        v = 1 - t
        x = v**3 * p0[0] + 3 * v * v * t * p1[0] + 3 * v * t * t * p2[0] + t**3 * p3[0]
        y = v**3 * p0[1] + 3 * v * v * t * p1[1] + 3 * v * t * t * p2[1] + t**3 * p3[1]
        total += hypot(x - px, y - py)
        px, py = x, y
    return total


def packet(d, color, length, *, size=5, delay=0.0, duration=3.6, opacity=1.0):
    """A dot travelling one exact lap of `d`, drawn as a round-capped dash.

    Dash travel beats offset-path here on two counts: the dot cannot drift off
    the line it is meant to be following, and the resting state is the start of
    the path, so an unrendered frame shows it parked at the origin of its route
    rather than stranded in a corner.
    """
    return (f'<path class="packet" d="{d}" stroke="{color}" stroke-width="{n(size)}" '
            f'stroke-opacity="{n(opacity)}" stroke-dasharray=".1 {n(length)}" '
            f'style="--len:{n(length)};animation-delay:{n(delay)}s;'
            f'animation-duration:{n(duration)}s"/>')


LINE_HEIGHT = 1.2       # SVG's own default, and the spacing every multi-line
                        # block in this design was measured against


def text(x, y, body, *, size=16, fill=INK, weight=None, mono=False,
         anchor=None, tracking=None, opacity=None, text_length=None, extra=''):
    """One <text> per line, with the shared attribute set.

    SVG has no <br/>. A break element inside <text> is not part of the language:
    renderers ignore it entirely, so a wrapped sentence silently loses
    everything after the break. The three intro column descriptions were all
    written as two lines, with the card dividers extended to 330 to hold the
    second one - and the browser drew only the first. So a break in `body`
    becomes a separate <text> here, stepped by the default line height, which
    is exactly what the layout arithmetic and the verifier already assume.

    `text_length` pins the rendered advance width. Layout here is computed from
    an advance estimate, and the mono stack resolves to a different face on every
    platform (Consolas 0.550em, JetBrains Mono 0.600em, DejaVu Sans Mono
    0.602em), so without a pin the same label lands 5-11px off-centre in its
    pill depending on which font the visitor happens to have. textLength makes
    the estimate authoritative: the browser fits the run to exactly this width,
    adjusting inter-glyph spacing rather than distorting the glyphs. It is a
    property of a whole run, so a pinned body must stay on one line.
    """
    parts = [f'font-size="{n(size)}"', f'fill="{fill}"']
    if weight:
        parts.append(f'font-weight="{weight}"')
    if mono:
        parts.append('class="mono"')
    if anchor:
        parts.append(f'text-anchor="{anchor}"')
    if tracking is not None:
        parts.append(f'letter-spacing="{n(tracking)}"')
    if text_length is not None:
        parts.append(f'textLength="{n(text_length)}" lengthAdjust="spacing"')
    if opacity is not None:
        parts.append(f'opacity="{n(opacity)}"')
    if extra:
        parts.append(extra)
    attrs = ' '.join(parts)
    lines = body.split('<br/>')
    if len(lines) > 1 and text_length is not None:
        raise ValueError('textLength pins a single run; it cannot span a break')
    out = []
    for i, line in enumerate(lines):
        y_attr = f'x="{n(x)}" y="{n(y + i * size * LINE_HEIGHT)}"'
        # x and y lead the attribute list so the element reads left edge, then
        # baseline, then everything else - one line of the source is one line of
        # the output
        out.append(f'<text {y_attr} {attrs}>{line}</text>')
    return ''.join(out)


def run_width(label: str, size: float, mono: bool, tracking: float = 0) -> float:
    """Width of a text run, using per-family advance widths."""
    return len(label) * size * ADVANCE['mono' if mono else 'sans'] + tracking * len(label)


# one source for the tracking a pill label is drawn at, so pill_width() and the
# label can never disagree about how wide the run is
PILL_TRACK = 0.4


def pill_width(label: str, size: float, pad: float, dot: bool) -> float:
    return run_width(label, size, True, PILL_TRACK) + pad * 2 + (16 if dot else 0)


def pill(x, y, label, color, *, h=26, size=12, pad=14, dot=False, weight=400):
    """A rounded tag: dark chip, accent edge, accent label. Returns (markup, width).

    The chip is filled with a neutral dark rather than a 10% wash of the accent.
    That is not just taste. These pills sit at the right edge of every data row,
    which is exactly where the mesh wash is brightest, and `screen` blending
    roughly doubles the luminance under them - a 10% accent fill cannot cover
    that, so the labels measured 2.1:1 to 3.5:1, far under the 4.5:1 they need.
    A dark surface absorbs whatever is behind it, so the label's contrast is set
    by the chip and the accent rather than by where on the panel the pill lands.
    """
    width = pill_width(label, size, pad, dot)
    label_w = run_width(label, size, True, PILL_TRACK)
    body = (
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(width)}" height="{n(h)}" rx="{n(h / 2)}" '
        f'fill="{CHIP}" fill-opacity="{n(CHIP_FILL)}" stroke="{color}" stroke-opacity="{n(CHIP_EDGE)}"/>'
    )
    if dot:
        body += f'<circle cx="{n(x + pad + 4)}" cy="{n(y + h / 2)}" r="4" fill="{color}"/>'
    body += text(
        x + pad + (16 if dot else 0), y + h / 2 + size * 0.36, escape(label),
        size=size, fill=color, mono=True, tracking=PILL_TRACK, weight=weight or None,
        text_length=label_w,
    )
    return body, width


def orbit_caption(cx, baseline, label, size, tracking):
    """The hero's orbit annotation, on its own dark plate.

    Centred on cx, with the plate's optical centre on the run's cap centre -
    which the shared CAP ratio puts at `baseline - CAP*size`, the same
    arithmetic the top bar and the data rows use. The plate's width is the
    label's own run_width plus padding, and that same number is pinned onto the
    label as textLength, so the plate cannot drift away from the type on a
    machine whose font stack resolves differently.
    """
    label_w = run_width(label, size, True, tracking)
    width = label_w + CAPTION_PAD * 2
    top = baseline - CAP * size - CAPTION_H / 2
    plate = (f'<rect x="{n(cx - width / 2)}" y="{n(top)}" width="{n(width)}" '
             f'height="{CAPTION_H}" rx="{n(CAPTION_H / 2)}" fill="{CAPTION_SURFACE}" '
             f'fill-opacity="{n(CAPTION_FILL)}"/>')
    return plate + text(cx, baseline, label, size=size, fill=INK_FAINT, mono=True,
                        anchor='middle', tracking=tracking, text_length=label_w)


def pill_row_right(labels, colors, *, right=RIGHT, y=0, h=26, size=11, pad=14, gap=8):
    """Tag row flush to the content right edge."""
    widths = [pill_width(l, size, pad, False) for l in labels]
    x = right - (sum(widths) + gap * (len(labels) - 1))
    out = ''
    for label, color, width in zip(labels, colors, widths):
        out += pill(x, y, label, color, h=h, size=size, pad=pad)[0]
        x += width + gap
    return out


def aurora(ident, cx, cy, rx, ry, color, opacity, drift='', blend=True):
    """One soft mesh blob, optionally drifting. Ids are explicit so builds stay
    byte-for-byte reproducible (a hash() id would vary per process).

    The wash is composited with `screen` rather than plain alpha: that is what
    makes two overlapping blobs add light into a mesh instead of stacking into
    a flat wash of grey. The frame group is isolation:isolate, so the blend
    stops at the panel edge and never reaches the page behind the <img>.
    """
    grad = (
        f'<radialGradient id="{ident}">'
        f'<stop stop-color="{color}" stop-opacity="{n(opacity)}"/>'
        f'<stop offset=".55" stop-color="{color}" stop-opacity="{n(opacity * 0.35)}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
        '</radialGradient>'
    )
    cls = ' class="mesh"' if blend else ''
    ellipse = (f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" '
               f'fill="url(#{ident})"{cls}/>')
    return grad, (f'<g class="{drift}">{ellipse}</g>' if drift else ellipse)


def ghost_number(value, y, size, color, *, x=RIGHT, opacity=0.3):
    """Outlined section numeral with light running around its outline.

    A faint solid stroke carries the shape; a dashed bright stroke travels over
    it, so the numeral reads as glass rather than a flat watermark.
    """
    body = escape(value)
    base = text(x, y, body, size=size, fill='none', anchor='end',
                extra=f'stroke="{color}" stroke-opacity="{n(opacity * 0.5)}" stroke-width="1.2"')
    flow = text(x, y, body, size=size, fill='none', anchor='end',
                extra=f'stroke="{color}" stroke-opacity="{n(opacity + 0.45)}" stroke-width="2" class="ghostflow"')
    return base + flow


def wordmark(fill):
    return ('<tspan fill="' + INK + '">Lil</tspan>'
            '<tspan fill="' + fill + '"> KALINOV</tspan>'
            '<tspan fill="' + EMBER + '">.</tspan>')


def dust(height, name, width=W):
    """An even field of twinkle dust confined to the top and bottom gutters.

    Specks are parked in the two clear bands - above the first text run and
    below the last - at evenly spaced x, so the field reads as measured rather
    than scattered. Positions are seeded from the asset name (stable per
    build) and only the per-speck phase varies, so the panel breathes while
    staying regular. No speck can land on a word: the bands are the gutters.
    """
    seed = sum(ord(c) for c in name)
    top0, top1 = 12, 22
    bot0, bot1 = height - 24, height - 12
    out = '<g opacity=".5">'
    for band, count, x0, x1 in [
        (top0, 7, 40, width - 40),    # 7 specks across the top gutter
        (bot0, 5, int(width * 0.1), int(width * 0.9)),  # 5 across the bottom
    ]:
        y_lo = band
        for i in range(count):
            x = x0 + (x1 - x0) * i / (count - 1)
            y = y_lo + ((seed + i * 7) % 11) / 10  # 0..1 within the 10px band
            r = 1.1 if i % 3 else 1.6
            delay = -((seed + i * 1.13) % 4.2)
            out += (f'<circle class="twinkle" cx="{n(x)}" cy="{n(y)}" r="{n(r)}" '
                    f'fill="{BLUSH}" style="animation-delay:{n(delay)}s"/>')
    return out + '</g>'


def spine(height, accent, *, short=False):
    """The shared left accent spine: a gradient bar with a breathing glow and
    two light pulses riding its full length.

    Drawn identically in every asset (same x, same top inset, same bottom
    inset) so the side rule reads as even across the whole set. It sits in the
    left margin at SPINE_X=26, clear of the tag pills on AXIS=52 and the body
    copy on TEXT=74, so it never covers a word. `short` is for the footer, which
    has no 58px top bar, so its spine may run much longer.
    """
    top = SPINE_TOP_SHORT if short else SPINE_TOP
    bot = height - (SPINE_BOT_SHORT if short else SPINE_BOT)
    bar_h = bot - top
    glow = (f'<rect x="{SPINE_X - 3}" y="{top}" width="{SPINE_W + 6}" height="{n(bar_h)}" '
            f'rx="{(SPINE_W + 6) / 2}" fill="{accent}" opacity=".28" filter="url(#soft)" class="pulse"/>')
    return (
        f'{glow}'
        f'<g clip-path="url(#spc)">'
        f'<rect x="{SPINE_X}" y="{top}" width="{SPINE_W}" height="{n(bar_h)}" rx="{SPINE_W / 2}" '
        f'fill="url(#spineg)"/>'
        f'<rect class="spimp" x="{SPINE_X}" y="{top}" width="{SPINE_W}" height="{SPINE_SEG}" rx="{SPINE_W / 2}" '
        f'fill="#ffffff" fill-opacity=".85" style="--spine-h:{n(bar_h)};filter:url(#soft)"/>'
        f'<rect class="spimp" x="{SPINE_X}" y="{top}" width="{SPINE_W}" height="{SPINE_SEG}" rx="{SPINE_W / 2}" '
        f'fill="{EMBER}" fill-opacity=".8" style="--spine-h:{n(bar_h)};animation-delay:2.6s;filter:url(#soft)"/>'
        f'</g>'
    )


def shell(name, height, radius, body, title, defs_extra='', spine_color=None, spine_short=False, width=W):
    """Assemble a complete, accessible SVG document."""
    # the travelling edge light needs the frame's own perimeter, so the dash it
    # draws and the distance it travels are one exact loop
    perim = round(2 * ((width - 4) + (height - 4)))
    sp_top = SPINE_TOP_SHORT if spine_short else SPINE_TOP
    sp_bot = height - (SPINE_BOT_SHORT if spine_short else SPINE_BOT)
    spine_def = f'<clipPath id="spc"><rect x="{SPINE_X}" y="{sp_top}" width="{SPINE_W}" height="{n(sp_bot - sp_top)}" rx="{SPINE_W / 2}"/></clipPath>'
    spine_grad = (f'<linearGradient id="spineg" gradientUnits="userSpaceOnUse" '
                  f'x1="{SPINE_X}" y1="{sp_top}" x2="{SPINE_X}" y2="{n(sp_bot)}">'
                  f'<stop stop-color="{EMBER}"/><stop offset=".5" stop-color="{CORAL}"/>'
                  f'<stop offset="1" stop-color="{CYAN}"/></linearGradient>')
    if spine_color:
        body = spine(height, spine_color, short=spine_short) + body
    # a shared field of drifting dust: deterministic positions (seeded on the
    # asset name) so builds stay byte-stable, twinkling on independent phases.
    # It lives in the frame group, behind the copy, so it never covers a word.
    body = dust(height, name, width) + body
    document = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
<defs>
 <linearGradient id="panel" x1="0" y1="0" x2="0.35" y2="1">
  <stop stop-color="{PANEL_TOP}"/><stop offset="1" stop-color="{PANEL_BOT}"/>
 </linearGradient>
 <linearGradient id="brand" gradientUnits="userSpaceOnUse" x1="196" y1="182" x2="600" y2="262">
  <stop stop-color="{CORAL}"/><stop offset=".55" stop-color="{EMBER}"/><stop offset="1" stop-color="{BLUSH}"/>
 </linearGradient>
 <linearGradient id="brandx" x1="0" y1="0" x2="1" y2="0">
  <stop stop-color="{CORAL}"/><stop offset="1" stop-color="{EMBER}"/>
 </linearGradient>
 <linearGradient id="topline" gradientUnits="userSpaceOnUse" x1="40" y1="0" x2="{width - 40}" y2="0">
  <stop stop-color="{CORAL}" stop-opacity="0"/><stop offset=".5" stop-color="{EMBER}" stop-opacity=".85"/><stop offset="1" stop-color="{CORAL}" stop-opacity="0"/>
 </linearGradient>
 <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
  <stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".42"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
 </linearGradient>
 <filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="9"/></filter>
 <filter id="softer" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="18"/></filter>
 <filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" stitchTiles="stitch"/>
  <feColorMatrix type="saturate" values="0"/>
 </filter>
 <clipPath id="frame"><rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{radius}"/></clipPath>
 {spine_def}
 {spine_grad}
 {defs_extra}
</defs>
<style>{STYLE}</style>
<g clip-path="url(#frame)" style="isolation:isolate">
<rect x=".5" y=".5" width="{n(width - 1)}" height="{n(height - 1)}" rx="{radius}" fill="url(#panel)"/>
{body}
<g transform="skewX(-18)"><rect class="gws" x="0" y="-60" width="120" height="{height + 120}" fill="url(#sheen)" opacity=".34"/></g>
<rect class="grainx" x="-170" y="-110" width="{width + 340}" height="{height + 220}" filter="url(#grain)" opacity=".05" style="mix-blend-mode:overlay"/>
<rect class="edgeflow" x="2" y="2" width="{width - 4}" height="{height - 4}" rx="{max(radius - 2, 4)}" fill="none" stroke="{GLOW_EDGE}" stroke-width="2.4" filter="url(#soft)" style="stroke-dasharray:240 {perim - 240};--edge:{perim}"/>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{radius - 1}" fill="none" stroke="{GLOW_EDGE}"/>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{radius}" fill="none" stroke="{STROKE}"/>
</g>
</svg>'''
    (ASSETS / name).write_text(document, encoding='utf-8')


# --------------------------------------------------------------------------- #
# hero
# --------------------------------------------------------------------------- #
def build_hero():
    cx, cy = ORB_CX, ORB_CY
    defs, blobs = '', ''
    # the corner bloom balances the warm orb on the right with a cool light on
    # the left, and it is kept dim and high so it never sits under the headline.
    # The opacities are higher than a plain-alpha wash would need: `screen` only
    # ever adds light, so raising them deepens the mesh without muddying it.
    # au-c is pulled left and down off the caption: centred under the orb it
    # lit the orbit caption's own background to 0.08 luminance and the 11px
    # label could not clear 2.4:1 no matter how light its ink was.
    # au-d is the one blob that sits under type rather than beside it: the top
    # bar's two labels sit inside its plateau, and at 0.14 they measured 4.56
    # and 4.61 against a 4.5 floor - passing by 1%. Nothing in the drift cycle
    # moves it, so that margin is stable, but it is thinner than anywhere else
    # in the design and one colour tweak away from failing. 0.11 costs the
    # corner bloom a step nobody can see and buys the bar ~8%.
    for args in [
        ('au-a', cx - 40, cy - 20, 330, 300, CORAL, 0.4, 'drift-a'),
        ('au-b', cx + 70, cy + 40, 300, 280, VIOLET, 0.3, 'drift-b'),
        ('au-c', cx - 190, cy + 200, 260, 210, CYAN, 0.2, 'drift-c'),
        ('au-d', 90, 20, 250, 150, CYAN, 0.11, 'drift-d'),
    ]:
        grad, body = aurora(*args)
        defs += grad
        blobs += body

    # The sheen is masked to the wordmark, so the light only crosses the letters.
    # The mask's copy of the name carries the same settle class as the visible
    # one: while the tracking is still easing in, the two would otherwise pull
    # apart and the sheen would ride the wrong letterforms.
    defs += (
        f'<mask id="nm" maskUnits="userSpaceOnUse" x="0" y="{n(NAME_Y - 130)}" width="800" height="170">'
        + text(TEXT, NAME_Y, wordmark('#ffffff'), size=NAME_SIZE, weight=800,
               tracking=SETTLE_TRACK, extra='class="settle"')
        + '</mask>'
    )

    orbit = ''
    for rx, ry, tilt, color, cls in [
        (170, 71, -24, EMBER, 'spin'),
        (148, 61, 20, VIOLET, 'spin-rev'),
    ]:
        orbit += (
            f'<g transform="rotate({tilt} {cx} {cy})">'
            f'<g class="{cls}">'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" '
            f'stroke-opacity=".22" stroke-width="1.4"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" '
            f'stroke-opacity=".85" stroke-width="2" class="dash" style="animation-duration:11s"/>'
            f'<circle cx="{n(cx + rx)}" cy="{cy}" r="3.4" fill="{color}"/>'
            '</g></g>'
        )

    # voice ripples leaving the core, staggered so they read as one pulse train
    ripples = ''
    for delay in (0, 1.2, 2.4):
        ripples += (
            f'<circle class="ripple" cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{EMBER}" '
            f'stroke-width="1.5" style="animation-delay:{n(delay)}s"/>'
        )

    # avatar disc in the orbital centre: the ico.jpg shipped with the repo,
    # inlined as a data URI so the SVG stays a single self-contained file
    # behind camo. It fills the morphing core where the "K." mark used to be;
    # the ring and ripples are redrawn over it.
    avatar_image = ''
    avatar_clip = ''
    ico = ASSETS / 'ico.jpg'
    if ico.exists():
        avatar_b64 = base64.b64encode(ico.read_bytes()).decode('ascii')
        avatar_clip = f'<clipPath id="avr"><circle cx="{n(cx)}" cy="{n(cy)}" r="{AVR_R}"/></clipPath>'
        avatar_image = (
            f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{AVR_R}" fill="{PANEL_BOT}"/>'
            f'<image x="{n(cx - AVR_R)}" y="{n(cy - AVR_R)}" width="{AVR_R * 2}" height="{AVR_R * 2}" '
            f'href="data:image/jpeg;base64,{avatar_b64}" clip-path="url(#avr)" '
            f'preserveAspectRatio="xMidYMid slice"/>'
            f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{AVR_R}" fill="none" stroke="url(#brandx)" '
            f'stroke-opacity=".8" stroke-width="1.6"/>'
        )




    # Staggered entrance. The hero uses `enter-soft`, which never starts fully
    # transparent: a renderer that paints the SVG before the animation clock
    # ticks (link previews, archiving, print) then shows a slightly dim but
    # fully legible masthead instead of a blank panel.
    def enter(inner, delay, cls='enter'):
        return f'<g class="{cls}" style="animation-delay:{n(delay)}s">{inner}</g>'

    # top bar: the dot and both labels ride the bar's own centre line, so the
    # row is placed by CAP arithmetic rather than a hardcoded baseline.
    # The two labels take INK_SOFT, one step above body copy, because this is
    # the page's header: at INK_MUTE they were the dimmest type in the hero and
    # the only two runs in it with no margin over AA - 4.56 and 4.61 against a
    # 4.5 floor, because the corner bloom pools under the bar. The slash drops
    # to INK_MUTE so the two halves of the slug still separate.
    top_mid = TOPBAR_H / 2
    top_base = top_mid + CAP * 13.5
    body = f'''
{defs}
{blobs}
{enter(f'''
<rect x="0" y="0" width="{W}" height="{TOPBAR_H}" fill="#ffffff" opacity=".02"/>
<path d="M0 {TOPBAR_H}.5H{W}" stroke="{HAIRLINE}"/>
<path d="M0 {TOPBAR_H}.5H{W}" stroke="url(#topline)" stroke-width="1.5" class="flow" style="stroke-dasharray:90 {W}"/>
<circle cx="{AXIS + 5}" cy="{n(top_mid)}" r="4.5" fill="url(#brandx)"/>
{text(TEXT, top_base, 'LilKALINOV <tspan fill="' + INK_MUTE + '">/</tspan> personal space', size=13.5, fill=INK_SOFT, mono=True)}
{text(RIGHT, top_base, '<tspan fill="' + CYAN + '">●</tspan> BUILD · TEST · SHIP', size=12.5, fill=INK_SOFT, mono=True, anchor='end', tracking=1)}
''', 0, 'enter-soft')}
{enter(text(TEXT, 104, 'SYSTEMS / VOICE / PRIME', size=13, fill=CORAL, mono=True, tracking=4.2, weight=600), 0.06, 'enter-soft')}
{enter(f'''
{text(TEXT, NAME_Y, wordmark('url(#brand)'), size=NAME_SIZE, weight=800, tracking=SETTLE_TRACK, extra='class="settle"')}
<g mask="url(#nm)"><rect class="sweep" x="0" y="{n(NAME_Y - 120)}" width="175" height="130" fill="url(#sheen)"/></g>
''', 0.1, 'enter-soft')}
{enter(text(TEXT, 256, 'Голос, код и инфраструктура — в одном контуре.', size=25, fill=INK_SOFT), 0.18, 'enter-soft')}
{enter(text(TEXT, 292, 'Rust-ядро. Python-сервисы. Плагины, которые работают.', size=18, fill=INK_MUTE), 0.23, 'enter-soft')}
{enter(f'''
<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{CYAN}" stroke-opacity=".16"/>
<circle class="spin" cx="{cx}" cy="{cy}" r="78" fill="none" stroke="{EMBER}" stroke-opacity=".5" stroke-width="1.2" stroke-dasharray="3 14"/>
{orbit}
<circle class="mesh" cx="{cx}" cy="{cy}" r="60" fill="{CORAL}" opacity=".3" filter="url(#softer)"/>
{ripples}
{avatar_clip}
{avatar_image}
<path class="morph" d="{ring_d(cx, cy, CORE_R, CIRCLE_K * CORE_R)}" fill="none" stroke="url(#brandx)" stroke-opacity=".75" stroke-width="1.6"/>
<circle class="pulse" cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{CORAL}" stroke-width="2" filter="url(#soft)"/>
{orbit_caption(cx, cy + 116, 'SPHEREPRIME · IN ORBIT', 11, 2.6)}
''', 0.14)}
'''
    shell('hero.svg', HERO_H, HERO_R, body,
          'Lil KALINOV — системный разработчик и QA. Rust, Python, Go и голосовые '
          'интерфейсы Astra.',
          spine_color=CORAL)


# --------------------------------------------------------------------------- #
# intro / about
# --------------------------------------------------------------------------- #
def build_intro():
    grad, blob = aurora('au-i', 250, 120, 300, 150, CORAL, 0.1, 'drift-b')
    lead = ('Соединяю надёжное ядро с полезной механикой: скорость в Rust и Go, '
            'сервисы на Python,<br/>голос — через Astra Plugin SDK.')
    # descriptions wrap to two lines: one long line would overrun the column
    focus = (
        ('RUST · GO', 'Скорость и надёжность',
         'Ядро, сетевые слои и всё, что<br/>живёт рядом с пользователем.', RUST[0]),
        ('PYTHON', 'Сервисы и плагины',
         'Интеграции, автоматизация и<br/>расширения для ассистента.', PY[0]),
        ('ASTRA', 'Живой диалог',
         'Распознавание и синтез речи,<br/>голосовые интерфейсы.', VIOLET),
    )
    col_w = (RIGHT - TEXT - 2 * COL_GAP) / 3
    cards = ''
    for i, (label, name, desc, color) in enumerate(focus):
        x = TEXT + i * (col_w + COL_GAP)
        anim = f'class="enter" style="animation-delay:{n(0.09 * i + 0.12)}s"'
        inner = (
            f'<circle cx="{n(x + 5)}" cy="226" r="5" fill="{color}"/>'
            + text(x, 258, escape(label), size=11, fill=color, mono=True, tracking=1.8, weight=600)
            + text(x, 288, escape(name), size=20, weight=600)
            + text(x, 312, desc, size=14.5, fill=INK_MUTE)
        )
        cards += (
            f'<path d="M{n(x - COL_GAP / 2)} 214V330" stroke="{HAIRLINE}"/>' if i else ''
        ) + f'<g {anim}>{inner}</g>'

    body = f'''
{grad}
{blob}
{text(TEXT, HEAD_EYEBROW, 'ABOUT / ПРОФИЛЬ', size=11.5, fill=INK_FAINT, mono=True, tracking=2.8, weight=600)}
{text(TEXT, HEAD_TITLE, 'Системный разработчик и QA', size=38, weight=700, tracking=-0.9)}
{text(TEXT, HEAD_SUB, lead, size=17, fill=INK_MUTE)}
{ghost_number('K', HEAD_SUB, 128, CORAL, opacity=0.22)}
<path d="M{AXIS} 200H{RIGHT}" stroke="{HAIRLINE}"/>
{cards}
'''
    shell('intro.svg', INTRO_H, CARD_R, body,
          'Привет, я Lil KALINOV. Системный разработчик и QA. Rust и Go — для '
          'скорости, Python — для сервисов и плагинов, голосовые интерфейсы Astra — '
          'для живого диалога. Фокус: скорость и надёжность, сервисы и плагины, '
          'живой диалог.', spine_color=CORAL)


# --------------------------------------------------------------------------- #
# featured project cards
# --------------------------------------------------------------------------- #
def art_voice():
    """Mirrored equaliser: real per-bar animation growing from the centre line."""
    primary, secondary = RUST
    # 15 bars at 16px pitch, centred on ART_CX, so the equaliser leaves an equal
    # 30px margin at each end of the corridor instead of hanging off its right
    cx, cy, count, gap, width = ART_CX, 112, 15, 16, 6
    glow = f'<ellipse class="mesh" cx="{n(cx)}" cy="{cy}" rx="132" ry="76" fill="{primary}" opacity=".16" filter="url(#softer)"/>'
    bars = ''
    for i in range(count):
        wave = abs(sin(i * 0.72)) * (0.62 + 0.38 * abs(cos(i * 0.31)))
        height = 10 + 46 * wave
        x = cx + (i - (count - 1) / 2) * gap - width / 2
        anim = f'animation-duration:{n(1.0 + (i % 4) * 0.19)}s;animation-delay:{n(-((i * 0.11) % 1.4))}s'
        bars += (
            f'<rect class="eq up" x="{n(x)}" y="{n(cy - height)}" width="{width}" height="{n(height)}" '
            f'rx="{n(width / 2)}" fill="{primary}" opacity=".95" style="{anim}"/>'
            f'<rect class="eq dn" x="{n(x)}" y="{n(cy)}" width="{width}" height="{n(height)}" '
            f'rx="{n(width / 2)}" fill="{secondary}" opacity=".7" style="{anim}"/>'
        )
    base = f'<path d="M{n(cx - 96)} {cy}.5H{n(cx + 96)}" stroke="{primary}" stroke-opacity=".22"/>'
    return '', glow + bars + base


def art_bridge():
    """PrimeProxy: two banks, a gap, and traffic that keeps crossing it."""
    primary, secondary = PY
    defs = (
        f'<linearGradient id="bank" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{secondary}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{secondary}" stop-opacity=".05"/></linearGradient>'
        f'<linearGradient id="bankx" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{primary}"/><stop offset="1" stop-color="{secondary}"/></linearGradient>'
    )
    bank_w, bank_h, bank_y = 90, 48, 88
    # the banks take the two ends of the corridor, so the gap grows with it and
    # the right bank lands exactly on RIGHT
    banks = ''
    for bx in (ART_X0, ART_X1 - bank_w):
        banks += (f'<rect x="{n(bx)}" y="{bank_y}" width="{bank_w}" height="{bank_h}" rx="13" '
                  f'fill="url(#bank)" stroke="{secondary}" stroke-opacity=".45"/>')
        for row in range(3):
            on = row == 0
            banks += (f'<rect x="{n(bx + 14)}" y="{102 + row * 12}" width="{26 if on else 20}" height="4" '
                      f'rx="2" fill="{primary if on else secondary}" opacity="{".95" if on else ".3"}"/>')
    # one seam down the middle of the gap. It used to be a pair of uprights 24px
    # apart, which read as two bars crowding each other inside a 38px slot
    seam = (f'<path d="M{n(ART_CX)} 74V150" stroke="{secondary}" stroke-opacity=".22" '
            f'stroke-dasharray="2 7"/>')
    paths, packets = '', ''
    for i, bow in enumerate((8, 15, 22)):
        p0 = (ART_X0 + bank_w, 112 - bow / 3)
        p1 = (ART_CX - 27, 112 - bow)
        p2 = (ART_CX + 27, 112 + bow)
        p3 = (ART_X1 - bank_w, 112 + bow / 3)
        d = (f'M{n(p0[0])} {n(p0[1])}C{n(p1[0])} {n(p1[1])},'
             f'{n(p2[0])} {n(p2[1])},{n(p3[0])} {n(p3[1])}')
        paths += f'<path d="{d}" fill="none" stroke="{secondary}" stroke-opacity=".18" stroke-width="2"/>'
        paths += (f'<path d="{d}" fill="none" stroke="url(#bankx)" stroke-width="2.4" class="flow" '
                  f'style="animation-delay:{n(-i * 0.5)}s"/>')
        # one solid packet per bridge: the dash above reads as current, this
        # reads as a request actually crossing the gap
        packets += packet(d, EMBER, cubic_len(p0, p1, p2, p3), size=4.4,
                          delay=-i * 0.62, duration=3.1, opacity=.9)
    return defs, banks + seam + paths + packets


def art_router():
    """PrimeRouter: one hub fanning requests out to several LLM providers."""
    primary, secondary = GO
    # the hub's left edge lands on ART_X0 and the provider nodes stop short of
    # the corner badge, so the fan spans the corridor instead of one edge of it
    hub_x, hub_y = 800, 112
    node_x, node_r = 1010, 13
    # symmetric about the hub, and clear of the badge band at y=27..61
    endpoints = [(68, primary), (112, secondary), (156, VIOLET)]
    edges, packets = '', ''
    for i, (ey, color) in enumerate(endpoints):
        p0 = (hub_x + 22, hub_y)
        p1 = (922, hub_y)
        p2 = (node_x - 55, ey)
        p3 = (node_x - 9, ey)
        d = f'M{p0[0]} {p0[1]}C{p1[0]} {p1[1]} {p2[0]} {p2[1]} {p3[0]} {p3[1]}'
        edges += f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity=".16" stroke-width="2.4"/>'
        edges += (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.4" class="flow" '
                  f'style="animation-delay:{n(-i * 0.62)}s"/>')
        # the request itself, one full lap of its own route
        packets += packet(d, color, cubic_len(p0, p1, p2, p3), size=4.6,
                          delay=-i * 0.9, duration=2.8, opacity=.95)
        # a node that breathes while its edge is carrying a packet
        edges += (f'<circle class="pulse" cx="{node_x}" cy="{ey}" r="{node_r}" fill="none" stroke="{color}" '
                  f'stroke-width="1.2" stroke-opacity=".5" style="animation-delay:{n(-i * 0.4)}s"/>'
                  f'<circle cx="{node_x}" cy="{ey}" r="10" fill="{color}" opacity=".14"/>'
                  f'<circle cx="{node_x}" cy="{ey}" r="10" fill="none" stroke="{color}" stroke-opacity=".7"/>'
                  f'<circle cx="{node_x}" cy="{ey}" r="3" fill="{color}"/>')
    hub = (
        f'<circle cx="{hub_x}" cy="{hub_y}" r="30" fill="none" stroke="{secondary}" '
        f'stroke-opacity=".3" stroke-dasharray="2 9" class="spin-rev" style="animation-duration:20s"/>'
        f'<circle class="mesh" cx="{hub_x}" cy="{hub_y}" r="21" fill="{primary}" opacity=".18" filter="url(#soft)"/>'
        f'<circle cx="{hub_x}" cy="{hub_y}" r="19" fill="url(#panel)" stroke="{secondary}" stroke-opacity=".8"/>'
        f'<circle class="pulse" cx="{hub_x}" cy="{hub_y}" r="8" fill="{primary}"/>'
    )
    return '', edges + packets + hub


def build_card(filename, number, label, name, description, tags, accent, art_builder):
    primary, secondary = accent
    art_defs, art_body = art_builder()
    tags_markup, x = '', AXIS
    for tag in tags:
        # pad 22 puts the label on the TEXT axis while the outline stays on AXIS
        markup, width = pill(x, CARD_TAG_Y, tag, primary, h=CARD_TAG_H, size=11.5, pad=22)
        tags_markup += markup
        x += width + 8

    # the card's accent now lives on the shared left spine (see spine()), so the
    # old bar at AXIS that swallowed the first tag pill is gone. Only the art
    # glow gradient remains in defs.
    glow_grad, glow = aurora(f'au-{number}', ART_CX, 110, 178, 140, primary, 0.11, 'drift-c')
    defs_extra = glow_grad

    # the corner badge is chrome, not corridor: the glyph is sized off the same
    # radius as the ring so moving one moves both
    bx, by, br = BADGE_CX, BADGE_CY, BADGE_R
    tail, shaft, head = n(bx - 0.41 * br), n(0.76 * br), n(0.29 * br)
    badge = (f'<circle cx="{bx}" cy="{by}" r="{br}" fill="#ffffff" fill-opacity=".04" stroke="{STROKE}"/>'
             f'<path d="M{tail} {by}h{shaft}m-{head} -{head} {head} {head}-{head} {head}" fill="none" '
             f'stroke="{INK_MUTE}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>')

    body = f'''
{art_defs}
{glow}
<rect x="0" y="0" width="{W}" height="{TOPBAR_H}" fill="#ffffff" opacity=".018"/>
<g class="enter">
{text(TEXT, HEAD_EYEBROW, escape(number) + ' / ' + escape(label), size=11.5, fill=primary, mono=True, tracking=2.6, weight=600)}
{text(TEXT, HEAD_TITLE, escape(name), size=38, weight=700, tracking=-0.9)}
{text(TEXT, HEAD_SUB, escape(description), size=17, fill=INK_MUTE)}
{tags_markup}
</g>
<path d="M{DIV} {CARD_BAR_Y}V{CARD_TAG_Y + CARD_TAG_H}" stroke="{HAIRLINE}"/>
<g class="enter" style="animation-delay:.16s">{art_body}</g>
{badge}
'''
    shell(filename, CARD_H, CARD_R, body, f'{name}: {description}', defs_extra=defs_extra,
          spine_color=primary)


def build_cards():
    build_card('astra.svg', '01', 'VOICE × ASTRA', 'Astra Plugins',
               'Голос и поиск для Astra: Silero STT, DDG WebSearch, Google STT.',
               ['RUST', 'ASTRA', 'STT', 'VOICE'], RUST, art_voice)
    build_card('primeproxy.svg', '02', 'NETWORK × FREEDOM', 'PrimeProxy',
               'Мост там, где нет связи. Плагин прямо в Astra.',
               ['PYTHON', 'MTPROTO', 'ASTRA'], PY, art_bridge)
    build_card('primerouter.svg', '03', 'AI × ROUTING', 'PrimeRouter & CLI',
               'Маршрутизация LLM-провайдеров и собственный CLI.',
               ['GO', 'RUST', 'SPHEREPRIME'], GO, art_router)


# --------------------------------------------------------------------------- #
# data sections — everything a Markdown table used to carry
# --------------------------------------------------------------------------- #
def section_head(number, label, title, subtitle, accent, blob_color):
    # The wash sits high and inboard, behind the head block and the ghost
    # numeral. It used to be centred on x=990, which is the tag column: screen
    # blending then lifted every language chip on the panel and their labels
    # dropped to 3:1. A wash has to respect what is legible underneath it.
    grad, blob = aurora(f'au-{number}', 780, 44, 290, 132, blob_color, 0.15, 'drift-c')
    return grad + blob + (
        text(TEXT, HEAD_EYEBROW, escape(number) + ' / ' + escape(label),
             size=11.5, fill=accent, mono=True, tracking=2.6, weight=600)
        + text(TEXT, HEAD_TITLE, escape(title), size=38, weight=700, tracking=-0.9)
        + text(TEXT, HEAD_SUB, escape(subtitle), size=17, fill=INK_MUTE)
        # the numeral shares the subtitle's baseline, which centres its cap height
        # on the head block (eyebrow cap top ~50 .. subtitle descender ~137)
        + ghost_number(number, HEAD_SUB, 116, accent, opacity=0.3)
        + f'<path d="M{AXIS} {HEAD_RULE}H{RIGHT}" stroke="{HAIRLINE}"/>'
    )


def data_row(y, name, description, tags, colors, dot, delay):
    """One data row: marker in the AXIS gutter, copy on the TEXT axis, tags flush right."""
    name_size, tag_h = 20, 26
    # centre the tags on the name's cap height, not its baseline
    cap_centre = y + 37 - CAP * name_size
    inner = (
        f'<path d="M{AXIS} {y}H{RIGHT}" stroke="{HAIRLINE}"/>'
        f'<circle cx="{AXIS + 5}" cy="{n(cap_centre)}" r="5" fill="{dot}"/>'
        + text(TEXT, y + 37, escape(name), size=name_size, weight=600)
        + text(TEXT, y + 58, escape(description), size=15.5, fill=INK_MUTE)
        + pill_row_right(tags, colors, y=cap_centre - tag_h / 2, h=tag_h, size=11, pad=14)
    )
    return f'<g class="enter" style="animation-delay:{n(delay)}s">{inner}</g>'


def build_section(filename, number, label, title, subtitle, rows, accent, blob_color, alt):
    height = HEAD_RULE + len(rows) * ROW_H + 34
    body = section_head(number, label, title, subtitle, accent, blob_color)
    for i, (name, description, tags, colors, dot) in enumerate(rows):
        body += data_row(HEAD_RULE + i * ROW_H, name, description, tags, colors, dot, 0.1 + 0.085 * i)
    shell(filename, height, CARD_R, body, alt, spine_color=accent)


def build_sections():
    build_section(
        'plugins.svg', '04', 'ASTRA PLUGINS', 'Плагины Astra',
        'Голос и поиск для ассистента — без вмешательства в ядро.',
        [('astra-silero', 'Распознавание речи Silero прямо в Astra.',
          ['RUST', 'STT'], [RUST[0], RUST[0]], RUST[0]),
         ('astra-websearch-ddg', 'Реальный поиск через DuckDuckGo без лимитов.',
          ['RUST', 'SEARCH'], [RUST[0], RUST[0]], RUST[0]),
         ('Astra-Google-STT', 'Распознавание речи через Google STT.',
          ['RUST', 'STT'], [RUST[0], RUST[0]], RUST[0]),
         ('Astra-PrimeProxy', 'PrimeProxy как плагин: сетевой слой прямо в ассистенте.',
          ['RUST', 'MTPROTO'], [RUST[0], RUST[0]], RUST[0])],
        RUST[0], RUST[0],
        'Плагины Astra: astra-silero и Astra-Google-STT — распознавание речи, '
        'astra-websearch-ddg — поиск через DuckDuckGo, Astra-PrimeProxy — сетевой слой.')
    build_section(
        'sphereprime.svg', '05', 'SPHEREPRIME', 'Команда SpherePrime',
        'Проекты организации, где я работаю вместе с dwertyfa.',
        [('PrimeProxy', 'Локальный MTProto-прокси для Telegram с WebSocket-транспортом.',
          ['PYTHON'], [PY[0]], PY[0]),
         ('PrimeAI', 'AI-провайдер для Astra с маршрутизацией запросов через Router API.',
          ['TYPESCRIPT'], [TS[0]], TS[0]),
         ('Prime CLI', 'Терминальный AI-ассистент: код, MCP и несколько моделей.',
          ['GO'], [GO[0]], GO[0])],
        SPHERE, SPHERE,
        'SpherePrime: PrimeProxy — MTProto-прокси на Python, PrimeAI — AI-провайдер '
        'на TypeScript, Prime CLI — терминальный ассистент на Go.')


# --------------------------------------------------------------------------- #
# footer / CTA
# --------------------------------------------------------------------------- #
def wave_path(amp: float, phase: float, speed_units: float):
    """Two harmonics under a bell envelope — an organic pulse, not a zigzag."""
    points = []
    for step in range(121):
        t = step / 120
        x = AXIS - 12 + t * (W - 2 * (AXIS - 12))
        envelope = sin(pi * t) ** 0.7
        y = 112 - envelope * amp * (
            sin(2 * pi * 2.6 * t + phase) + 0.54 * sin(2 * pi * 5.1 * t + 0.9)
            + 0.27 * sin(2 * pi * speed_units * t)
        )
        points.append(f'{n(x)} {n(y)}')
    return 'M' + 'L'.join(points)


def build_footer():
    defs = (
        f'<linearGradient id="waveg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{CORAL}" stop-opacity="0"/><stop offset=".18" stop-color="{CORAL}"/>'
        f'<stop offset=".5" stop-color="{EMBER}"/><stop offset=".82" stop-color="{VIOLET}"/>'
        f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>'
    )
    layers = ''
    for amp, phase, units, dash, dur in [
        (7.0, 0.0, 8.3, '4 26', 2.2),
        (13.0, 0.0, 8.3, '14 30', 3.4),
        (18.5, 1.6, 6.1, '2 18', 4.8),
    ]:
        d = wave_path(amp, phase, units)
        layers += f'<path d="{d}" fill="none" stroke="{CORAL}" stroke-opacity=".1" stroke-width="5" filter="url(#soft)"/>'
        layers += (f'<path d="{d}" fill="none" stroke="url(#waveg)" stroke-width="1.8" '
                   f'style="stroke-dasharray:{dash};animation:dash {dur}s linear infinite;'
                   f'animation-delay:{n(-phase)}s"/>')

    pill_x, pill_w, pill_y, pill_h = RIGHT - 268, 268, 26, 44
    cta = (
        f'<rect x="{pill_x}" y="{pill_y}" width="{pill_w}" height="{pill_h}" rx="{pill_h / 2}" '
        f'fill="url(#brandx)" opacity=".16" stroke="{CORAL}" stroke-opacity=".5"/>'
        f'<text x="{n(pill_x + 30)}" y="{n(pill_y + pill_h / 2 + 6)}" fill="{BLUSH}" font-size="18" font-weight="600" text-anchor="middle">+</text>'
        + text(pill_x + 48, pill_y + pill_h / 2 + 5.5, '@LilKALINOV', size=16, fill=BLUSH,
               mono=True, weight=700, tracking=0.5)
        + f'<path d="M{RIGHT - 34} {pill_y + 17}l9 5-9 5" fill="none" stroke="{BLUSH}" '
          f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    body = f'''
{defs}
<ellipse cx="250" cy="70" rx="300" ry="90" fill="url(#waveg)" opacity=".1" filter="url(#softer)"/>
<g class="enter">
{text(TEXT, 56, 'Есть задача?', size=26, weight=700, tracking=-0.5)}
{text(TEXT, 82, 'Решим её вместе — от архитектуры до продакшена.', size=15.5, fill=INK_MUTE)}
</g>
<g class="enter" style="animation-delay:.12s">{cta}</g>
{layers}
'''
    shell('footer.svg', FOOTER_H, HERO_R, body,
          'Есть задача? Решим её вместе — от архитектуры до продакшена. '
          'Написать LilKALINOV в Telegram: @LilKALINOV', spine_color=CORAL, spine_short=True)


def build_buttons():
    """Two big link pills, one row, each wrapped in its own Markdown <a> on the
    README. Anything drawn inside a panel SVG is not clickable behind GitHub's
    camo proxy, so the only links the page actually follows live here. Each
    button is a half-canvas panel (BTN_W) so the two sit side by side.
    """
    for filename, label, accent, url in [
        ('btn-telegram.svg', 'Telegram', CYAN, 'https://t.me/LilKALINOV'),
        ('btn-sphereprime.svg', 'SpherePrime', SPHERE, 'https://github.com/SpherePrime'),
    ]:
        w, h = LINK_PILL_W, LINK_PILL_H
        x = (BTN_W - w) / 2            # centre the pill in its half-canvas panel
        y = (LINKS_H - h) / 2
        label_w = run_width(label, 20, True, PILL_TRACK)
        cx = x + w / 2
        ax = x + w - 26               # outbound arrow parked at the pill's right
        ay = y + h / 2
        arrow = (f'<path d="M{n(ax - 14)} {n(ay + 9)}h28M{n(ax)} {n(ay - 9)}v18" fill="none" '
                 f'stroke="{accent}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
        mask = (f'<mask id="bkm" maskUnits="userSpaceOnUse" x="{n(x)}" y="{n(y)}" '
                f'width="{n(w)}" height="{n(h)}">'
                f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{h / 2}" fill="#fff"/></mask>')
        body = f'''
{mask}
<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{h / 2}" fill="{CHIP}" fill-opacity="{CHIP_FILL}" stroke="{accent}" stroke-opacity="{CHIP_EDGE}"/>
<rect class="btsweep" x="{n(x)}" y="{n(y)}" width="180" height="{n(h)}" fill="url(#sheen)" mask="url(#bkm)"/>
{text(cx - 12, y + h / 2 + 7, escape(label), size=20, fill=accent, mono=True, weight=700, tracking=PILL_TRACK, anchor='middle', text_length=label_w)}
{arrow}
'''
        shell(filename, LINKS_H, CARD_R, body,
              f'Кнопка {label} — откроет {url}.',
              spine_color=accent, spine_short=True, width=BTN_W)

def version_asset(match):
    """Point every image at a content-hashed copy so GitHub cannot cache it."""
    path = re.sub(r'-[0-9a-f]{12}(?=\.svg$)', '', match.group(1))
    data = (ROOT / path).read_bytes()
    versioned = path.removesuffix('.svg') + f'-{hashlib.sha256(data).hexdigest()[:12]}.svg'
    (ROOT / versioned).write_bytes(data)
    return f'src="{versioned}"'


def sync_readme_and_preview():
    """Keep the README's image URLs, the asset folder and preview.html in step.

    GitHub caches camo-served images aggressively; a content-hashed filename
    busts that cache the moment a design changes. The plain files stay as the
    editable source; only superseded hashed copies are removed.
    """
    readme_path = ROOT / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    readme = re.sub(r'src="(\./assets/[^"?]+\.svg)(?:\?[^"]*)?"', version_asset, readme)
    readme_path.write_text(readme, encoding='utf-8')

    keep = set(re.findall(r'\./assets/([\w.-]+\.svg)', readme))
    for stale in sorted(ASSETS.glob('*.svg')):
        # canonical files stay as the editable source; only superseded copies go
        if stale.name not in keep and not re.fullmatch(r'[a-z0-9-]+(?<!-[0-9a-f]{12})\.svg', stale.name):
            stale.unlink()

    body = readme.strip()
    preview = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LilKALINOV — GitHub profile preview</title>
<style>
:root{{color-scheme:dark}}
body{{margin:0;background:#0b0e16;color:#e6edf3;font:16px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
main{{max-width:1012px;margin:28px auto;padding:8px 12px}}
img{{display:block;width:100%;height:auto;margin:0 0 10px;border-radius:6px}}
</style></head>
<body>
<main>{body}</main>
</body></html>'''
    (ROOT / 'preview.html').write_text(preview, encoding='utf-8')
    print('README image URLs re-hashed, stale copies removed, preview.html rebuilt.')


def main():
    ASSETS.mkdir(exist_ok=True)
    build_hero()
    build_intro()
    build_cards()
    build_sections()
    build_footer()
    build_buttons()
    sync_readme_and_preview()
    print('Generated 10 SVG assets in assets/')


if __name__ == '__main__':
    main()
