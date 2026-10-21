"""Pull live repository facts for the profile build.

Every number on the profile page is fetched, not hardcoded: non-fork
repositories of both LilKALINOV and the SpherePrime organisation, with
their stars, languages, last-push dates and the first readable line of
each README. The classification rule is the owner's: a repository whose
name starts with "astra" is a plugin for the Astra voice assistant.

The result is cached in data/repos.json so a build without network (and
the layout verifier, which imports this module's neighbours) still has a
deterministic input; the built-in snapshot below is the same data.

Run:  python scripts/fetch_repos.py
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'repos.json'
OWNER = 'LilKALINOV'
ORG = 'SpherePrime'

# an offline snapshot of the live data, so a build with no network and no
# cache still renders the full page (star counts degrade gracefully)
FALLBACK = [
    {'name': 'PrimeAi', 'owner': ORG, 'stars': 6, 'langs': ['TypeScript', 'CSS'],
     'pushed': '2026-10-16T14:09:06Z', 'line': 'AI provider using the Router API with automatic route selection.'},
    {'name': 'CLI', 'owner': ORG, 'stars': 3, 'langs': ['Go'],
     'pushed': '2026-10-21T01:43:31Z', 'line': 'An agentic coding assistant for the terminal.'},
    {'name': 'PrimeProxy', 'owner': ORG, 'stars': 2, 'langs': ['Rust'],
     'pushed': '2026-10-21T01:19:15Z', 'line': ''},
    {'name': 'Prime-server', 'owner': ORG, 'stars': 0, 'langs': ['TypeScript', 'CSS', 'PLpgSQL'],
     'pushed': '2026-10-20T21:05:14Z', 'line': 'Self-hosted AI request router: Fastify, PostgreSQL, Redis.'},
    {'name': 'PrimeReplay', 'owner': ORG, 'stars': 0, 'langs': ['Rust', 'Slint'],
     'pushed': '2026-10-07T13:46:10Z', 'line': 'Rust + slint'},
    {'name': 'PrimeBD', 'owner': ORG, 'stars': 0, 'langs': [],
     'pushed': '2026-10-06T21:43:33Z', 'line': ''},
    {'name': 'SpherePrime-site', 'owner': ORG, 'stars': 0, 'langs': ['TypeScript', 'CSS'],
     'pushed': '2026-09-22T03:56:28Z', 'line': ''},
    {'name': 'FlagshipRouter', 'owner': ORG, 'stars': 0, 'langs': [],
     'pushed': '2026-10-04T14:15:47Z',
     'line': 'Free AI models for every coding tool - a local OpenAI-compatible gateway.'},
    {'name': 'Skill-MCP', 'owner': ORG, 'stars': 0, 'langs': ['JavaScript', 'Python'],
     'pushed': '2026-10-09T15:19:26Z', 'line': ''},
    {'name': 'astra-silero', 'owner': OWNER, 'stars': 0, 'langs': ['Rust', 'Python'],
     'pushed': '2026-09-22T21:09:10Z', 'line': 'Silero TTS - local Russian text-to-speech for Astra'},
    {'name': 'astra-websearch-ddg', 'owner': OWNER, 'stars': 0, 'langs': ['Rust'],
     'pushed': '2026-09-11T15:43:20Z', 'line': 'Real search via DuckDuckGo with no limits'},
    {'name': 'Astra-Google-STT', 'owner': OWNER, 'stars': 1, 'langs': ['Rust'],
     'pushed': '2026-09-10T14:53:09Z', 'line': 'Free, keyless speech-to-text for Astra'},
    {'name': 'Astra-PrimeProxy', 'owner': ORG, 'stars': 0, 'langs': ['Rust', 'HTML', 'JavaScript'],
     'pushed': '2026-09-23T21:04:03Z', 'line': ''},
]


def gh(*args: str) -> str:
    out = subprocess.run(['gh', 'api', *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f'gh api {args[0]}: {out.stderr.strip()[:200]}')
    return out.stdout


def gh_json(*args: str):
    return json.loads(gh(*args))


def search(query: str) -> list[dict]:
    return gh_json(f'search/repositories?q={query}+fork:false&per_page=100')['items']


def readme_line(owner: str, name: str) -> str:
    """First readable line of a repo README, stripped of markdown noise.

    Headings, badges, table rules and HTML are skipped, emphasis markers are
    dropped; the result feeds card descriptions when no curated Russian text
    exists for the repository.
    """
    try:
        raw = gh(f'repos/{owner}/{name}/readme', '-H', 'Accept: application/vnd.github.raw')
    except RuntimeError:
        return ''
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith(('#', '|', '![', '[!', '<', '---', '```')):
            continue
        s = re.sub(r'[*`_\[\]]', '', s).strip()
        if s:
            return s[:140]
    return ''


def fetch_all() -> list[dict]:
    """Live non-fork repos of both accounts, deduped with the org copy winning.

    The authenticated search does return the account's private repositories,
    so the public-only filter is explicit: anything marked private (or any
    non-public visibility) is dropped before it can reach the page.
    """
    entries: dict[str, dict] = {}
    for query in (f'user:{OWNER}', f'org:{ORG}'):
        for r in search(query):
            if r.get('private') or r.get('visibility', 'public') != 'public':
                continue
            entry = {
                'name': r['name'],
                'owner': r['owner']['login'],
                'stars': r['stargazers_count'],
                'pushed': r['pushed_at'],
            }
            entries[r['name'].lower()] = entry   # org runs last, so it wins ties
    repos = []
    for key, entry in entries.items():
        owner, name = entry['owner'], entry['name']
        try:
            langs = gh_json(f'repos/{owner}/{name}/languages')
            entry['langs'] = [k for k, _ in sorted(langs.items(), key=lambda kv: -kv[1])][:4]
        except RuntimeError:
            entry['langs'] = []
        entry['line'] = readme_line(owner, name)
        entry['plugin'] = name.lower().startswith('astra')
        repos.append(entry)
    repos.sort(key=lambda r: (r['stars'], r['pushed']), reverse=True)
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(repos, ensure_ascii=False, indent=1), encoding='utf-8')
    return repos


def load_cached() -> list[dict]:
    """The last successful fetch, or the built-in snapshot when there is none."""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    return [dict(r) for r in FALLBACK]


def load() -> list[dict]:
    """Live fetch with a graceful fall to the cache."""
    try:
        return fetch_all()
    except (RuntimeError, ValueError, KeyError) as err:
        print(f'live fetch unavailable ({err}); using cached snapshot', file=__import__('sys').stderr)
        return load_cached()


def pushed_day(iso: str):
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(timezone.utc).date()
    except ValueError:
        return None


if __name__ == '__main__':
    data = fetch_all()
    print(f'cached {len(data)} non-fork repositories to {DATA_FILE.relative_to(ROOT)}')
