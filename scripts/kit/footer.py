from .canvas import document, frame, text, label, delay, arrow, text_width
from .scope import oscilloscope
from .theme import FULL_WIDTH, PAPER, GREY, DIM, LINE, SIGNAL, INK

HEIGHT = 360


def button(x, y, caption):
    width = text_width(caption, 18, weight=700) + 86
    return f'''
<g class="rise" style="{delay(.8)}">
  <rect x="{x}" y="{y}" width="{width:.0f}" height="60" fill="{SIGNAL}"/>
  {text(x + 24, y + 37, caption, 18, INK, 700)}
  <g transform="translate({x + width - 34:.0f} {y + 30})"><g class="nudge">{arrow(0, 0, 8, INK, 2.2)}</g></g>
</g>'''


def build():
    css = '@keyframes nudge{0%,70%,100%{transform:translate(0,0)}80%{transform:translate(4px,-4px)}}.nudge{animation:nudge 3s ease-in-out infinite}'
    body = (frame(FULL_WIDTH, HEIGHT, 'контакт', 't.me/sphereprime', phase=6)
            + '<clipPath id="big"><rect x="20" y="64" width="760" height="140"/></clipPath>'
            + f'<g clip-path="url(#big)"><g class="reveal">{text(22, 178, "Есть идея?", 116, PAPER, 800, spacing=-5)}</g></g>'
            + f'<g class="rise" style="{delay(.5)}">{text(28, 230, "Напиши — обсудим проекты, QA, автоматизацию или сотрудничество.", 21, GREY)}</g>'
            + button(28, 254, 'Написать в Telegram')
            + label(FULL_WIDTH - 28, 120, 'инструменты', anchor='end', fill=PAPER)
            + label(FULL_WIDTH - 28, 146, 'тестирование', anchor='end', fill=PAPER)
            + label(FULL_WIDTH - 28, 172, 'плагины', anchor='end', fill=PAPER)
            + label(FULL_WIDTH - 28, 198, 'ai-агенты', anchor='end', fill=SIGNAL)
            + f'<path d="M560 284H{FULL_WIDTH - 28}" stroke="{LINE}"/>'
            + oscilloscope(560, 284, FULL_WIDTH - 588, 22, SIGNAL, duration=5.6, stroke=1.4)
            + text(FULL_WIDTH - 28, 336, '© 2026 LilKALINOV · SpherePrime', 11, DIM, anchor='end', mono=True))
    return document(FULL_WIDTH, HEIGHT, body, 'Есть идея? Напиши — обсудим проекты, QA или SpherePrime. Написать в Telegram: t.me/SpherePrime', css=css)
