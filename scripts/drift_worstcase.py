"""Build worst-case renders: every aurora blob frozen at a drift extreme.

Animations run forever, so `--virtual-time-budget` never settles and the
headless capture comes back empty. Rather than fight the clock, this strips the
drift classes and writes the 50% keyframe position in as a static transform, so
each variant is a still image whose blob geometry is exactly the extreme the
animation actually reaches.

The measurement then takes the worst ratio per run across all variants, which
is the honest question: does any run drop below AA at any point in the cycle,
or only in the still I happened to capture?

Writes the variants into a scratch dir and prints the page URL to capture.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / '_drift')

# the 50% stop of every drift keyframe, in the order the generator emits them
EXTREME = {
    'drift-a': 'translate(34px,-24px) scale(1.12)',
    'drift-b': 'translate(-42px,20px) scale(.94)',
    'drift-c': 'translate(24px,30px) scale(1.1)',
    'drift-d': 'translate(-30px,26px) scale(.92)',
}
ORDER = ['hero.svg', 'intro.svg', 'astra.svg', 'primeproxy.svg',
         'primerouter.svg', 'plugins.svg', 'sphereprime.svg', 'footer.svg']
PAGE = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0}img{display:block;width:1100px;height:auto}</style>'
        '</head><body>\n{body}\n</body></html>\n')


def freeze(src: Path, dst: Path, at: set) -> None:
    """Copy `src` to `dst` with the named drift classes pinned to 50%."""
    text = src.read_text(encoding='utf-8')
    for name, transform in EXTREME.items():
        pattern = re.compile(r'class="' + name + r'"')
        if name in at:
            text = pattern.sub(f'style="transform:{transform}"', text)
        else:
            text = pattern.sub('', text)
    # The reduced-motion reset is `transform:none!important`, which would win
    # over the inline transform above and silently freeze every blob back at
    # its authored position - all five variants then render byte-identical, so
    # the test quietly measures nothing. `animation:none` is kept: it is what
    # stops the still-running keyframes, and leaving each element at its
    # authored state is exactly the still we want.
    text = text.replace('transform:none!important', '/*drift-open*/')
    dst.write_text(text, encoding='utf-8')


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    if OUT.exists():
        # the served dir is locked by the http.server holding it open
        for child in sorted(OUT.iterdir()):
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    # one variant per single blob at its extreme, plus all four at once: a blob
    # only ever adds light, but drift also translates it, so a blob at 50% can
    # have moved away from a given run. Taking the worst across all of these
    # covers both directions.
    variants = [{'drift-a'}, {'drift-b'}, {'drift-c'}, {'drift-d'},
                {'drift-a', 'drift-b', 'drift-c', 'drift-d'}]

    pages = []
    for i, at in enumerate(variants):
        # each variant needs its own assets directory: sharing one means every
        # page serves whichever variant was written last, and all five captures
        # come back byte-identical - a test that silently measures nothing
        slot = OUT / f'v{i}'
        (slot / 'assets').mkdir(parents=True)
        for name in ORDER:
            freeze(ASSETS / name, slot / 'assets' / name, at)
        page = OUT / f'v{i}.html'
        body = '\n'.join(f'<img src="v{i}/assets/{name}">' for name in ORDER)
        page.write_text(PAGE.replace('{body}', body), encoding='utf-8')
        pages.append((i, '+'.join(sorted(at)), page.name))

    for i, label, name in pages:
        print(f'v{i}.html  blobs at 50%: {label}')
    print(f'\nserve {OUT} and capture v0..v{len(pages) - 1}.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
