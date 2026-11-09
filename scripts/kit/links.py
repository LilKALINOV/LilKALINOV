from .canvas import document, frame, text, label, delay, arrow, text_width
from .theme import PAPER, GREY, SIGNAL

WIDTH = 356
HEIGHT = 92


def build(index, title, caption, phase):
    width = text_width(title, 22, weight=700)
    css = '@keyframes nudge{0%,70%,100%{transform:translate(0,0)}80%{transform:translate(4px,-4px)}}.nudge{animation:nudge 3.6s ease-in-out infinite}'
    body = (frame(WIDTH, HEIGHT, strip=False, grid=False)
            + label(24, 30, f'{index:02d}', SIGNAL)
            + text(24, 58, title, 22, PAPER, 700)
            + f'<rect class="fbl grow" style="{delay(.4 + phase)}" x="24" y="66" width="{width:.0f}" height="2" fill="{SIGNAL}"/>'
            + text(24, 82, caption, 11.5, GREY, mono=True)
            + f'<g transform="translate({WIDTH - 36} {HEIGHT / 2})"><g class="nudge" style="{delay(phase)}">{arrow(0, 0, 9, PAPER, 1.8)}</g></g>')
    return document(WIDTH, HEIGHT, body, f'{title} — {caption}', css=css)
