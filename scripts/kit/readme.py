from html import escape

PREVIEW = '''<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LilKALINOV — preview</title>
<style>
body{margin:0;background:#0d1117;color:#e6edf3;font:16px/1.5 -apple-system,"Segoe UI",sans-serif}
main{max-width:1012px;margin:24px auto;padding:24px;border:1px solid #30363d;border-radius:6px}
img{max-width:100%;height:auto}
p{margin:0 0 16px}
</style>
<main>@@BODY@@</main></html>'''


def image(src, alt, width):
    return f'<img src="{src}" width="{width}" alt="{escape(alt, quote=True)}" />'


def linked(href, src, alt, width):
    return f'<a href="{href}">{image(src, alt, width)}</a>'


def block(*items):
    inner = '\n  '.join(items)
    return f'<p align="center">\n  {inner}\n</p>'


def render(blocks):
    return '\n\n'.join(blocks) + '\n'


def preview(readme):
    return PREVIEW.replace('@@BODY@@', readme)
