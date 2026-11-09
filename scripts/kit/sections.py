from .canvas import document, frame, text, label, delay
from .theme import FULL_WIDTH, PAPER, GREY, LINE, SIGNAL

HEIGHT = 150


def build(number, title, caption, counter, phase):
    css = '@keyframes bob{0%,100%{transform:translateY(-3px)}50%{transform:translateY(4px)}}.bob{animation:bob 2.2s ease-in-out infinite}'
    body = (frame(FULL_WIDTH, HEIGHT, f'раздел {number}', counter, phase=phase, grid=False)
            + f'<clipPath id="num"><rect x="20" y="58" width="150" height="86"/></clipPath>'
            + f'<g clip-path="url(#num)"><g class="reveal">{text(24, 130, number, 92, SIGNAL, 800, spacing=-4)}</g></g>'
            + f'<clipPath id="ttl"><rect x="170" y="62" width="900" height="56"/></clipPath>'
            + f'<g clip-path="url(#ttl)"><g class="reveal" style="{delay(.15)}">{text(176, 106, title, 46, PAPER, 800, spacing=-1.5)}</g></g>'
            + f'<g class="rise" style="{delay(.5)}">{text(178, 132, caption, 15, GREY)}</g>'
            + f'<path d="M168 70V130" stroke="{LINE}"/>'
            + f'<g transform="translate({FULL_WIDTH - 44} 104)"><g class="bob"><path d="M0 -14V12M-8 4L0 12L8 4" fill="none" stroke="{PAPER}" stroke-width="1.8"/></g></g>'
            + label(FULL_WIDTH - 64, 109, 'листай', anchor='end'))
    return document(FULL_WIDTH, HEIGHT, body, f'{number} — {title}. {caption}', css=css)
