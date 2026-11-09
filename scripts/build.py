import base64
import hashlib
from pathlib import Path

from kit import hero, stats, sections, links, footer, cards, readme
from kit.data import (
    REPO_TOTAL, LANGUAGES, HIGHLIGHTS, STATS_META, LINKS, SECTIONS, PROJECTS, LAYOUT
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
TELEGRAM = 'https://t.me/SpherePrime'


class Writer:
    def __init__(self):
        self.written = set()

    def save(self, name, svg):
        data = svg.encode('utf-8')
        filename = f'{name}-{hashlib.sha256(data).hexdigest()[:12]}.svg'
        (ASSETS / filename).write_bytes(data)
        self.written.add(filename)
        return f'./assets/{filename}'

    def prune(self):
        for stale in ASSETS.glob('*.svg'):
            if stale.name not in self.written:
                stale.unlink()


def load_avatar():
    photo = ASSETS / 'ico.jpg'
    if not photo.exists():
        photo = ASSETS / 'avatar.png'
    data = photo.read_bytes()
    mime = 'image/png' if data[:8] == b'\x89PNG\r\n\x1a\n' else 'image/jpeg'
    return mime, base64.b64encode(data).decode('ascii')


def project_card(writer, key, number, phase, wide=False):
    project = PROJECTS[key]
    svg = cards.wide(project, number, phase) if wide else cards.half(project, number, phase)
    width = '100%' if wide else '49%'
    src = writer.save(key, svg)
    if not project.get('url'):
        return readme.image(src, project['alt'], width)
    return readme.linked(project['url'], src, project['alt'], width)


def build():
    writer = Writer()
    blocks = []
    phase = 0.0
    count = 0
    for entry in LAYOUT:
        kind = entry[0]
        phase += 1.3
        if kind == 'hero':
            src = writer.save('hero', hero.build(load_avatar()))
            blocks.append(readme.block(readme.image(src, 'LilKALINOV — со-основатель SpherePrime, Lead QA Astra: софт для ИИ-агентов, тестирование и открытый код.', '100%')))
        elif kind == 'links':
            items = []
            for index, (key, label, caption, href) in enumerate(LINKS):
                src = writer.save(key, links.build(index + 1, label, caption, index * .25))
                items.append(readme.linked(href, src, f'{label} — {caption}', '32%'))
            blocks.append(readme.block(*items))
        elif kind == 'stats':
            src = writer.save('stats', stats.build(REPO_TOTAL, LANGUAGES, HIGHLIGHTS, STATS_META))
            blocks.append(readme.block(readme.image(src, f'{REPO_TOTAL}+ репозитория с SpherePrime / LilKALINOV, языки и проекты в цифрах.', '100%')))
        elif kind == 'section':
            number, title, caption, counter = SECTIONS[entry[1]]
            src = writer.save(f'section-{entry[1]}', sections.build(number, title, caption, counter, phase))
            blocks.append(readme.block(readme.image(src, f'{number} — {title}. {caption}', '100%')))
        elif kind == 'wide':
            count += 1
            blocks.append(readme.block(project_card(writer, entry[1], f'{count:02d}', phase, wide=True)))
        elif kind == 'pair':
            pair = []
            for i, key in enumerate(entry[1:]):
                count += 1
                pair.append(project_card(writer, key, f'{count:02d}', phase + i * 2.7))
            blocks.append(readme.block(*pair))
        elif kind == 'footer':
            src = writer.save('footer', footer.build())
            blocks.append(readme.block(readme.linked(TELEGRAM, src, 'Есть идея? Обсудим проекты, QA или SpherePrime. Написать в Telegram.', '100%')))
    writer.prune()
    content = readme.render(blocks)
    (ROOT / 'README.md').write_text(content, encoding='utf-8')
    (ROOT / 'preview.html').write_text(readme.preview(content), encoding='utf-8')
    total = sum((ASSETS / name).stat().st_size for name in writer.written)
    print(f'{len(writer.written)} SVG, {total / 1024:.0f} KB')


if __name__ == '__main__':
    build()
