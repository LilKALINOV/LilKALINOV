import math


def speech_wave(x, y, width, amplitude, seed, points=96):
    coords = []
    for k in range(points + 1):
        t = k / points
        envelope = math.sin(math.pi * t) ** .6
        burst = .55 + .45 * math.sin(t * (7 + seed) + seed * 1.7)
        value = (math.sin(t * 46 + seed * 2.3) * .6 + math.sin(t * 91 + seed) * .3 + math.sin(t * 17 - seed) * .25)
        coords.append(f'{x + width * t:.1f} {y + amplitude * envelope * burst * value:.1f}')
    return 'M' + 'L'.join(coords)


def oscilloscope(x, y, width, amplitude, color, duration=4.8, frames=6, stroke=1.6):
    shapes = [speech_wave(x, y, width, amplitude, seed) for seed in range(frames)]
    shapes.append(shapes[0])
    return (f'<path d="{shapes[0]}" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linejoin="round">'
            f'<animate attributeName="d" dur="{duration}s" repeatCount="indefinite" values="{";".join(shapes)}" '
            f'calcMode="spline" keySplines="{";".join([".45 0 .55 1"] * frames)}"/></path>')
