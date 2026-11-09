from .theme import SIGNAL, PAPER

REPO_TOTAL = 34
LANGUAGES = [
    ('Rust', 18, SIGNAL),
    ('Go', 14, PAPER),
    ('Python', 16, '#ff8040'),
    ('C/C++/C#', 12, '#e0ded7'),
    ('TypeScript', 12, '#b9b7b0'),
    ('JavaScript', 10, '#9e9c96'),
    ('Assembly', 6, '#7e7d77'),
    ('HTML/CSS', 8, '#595854'),
]
HIGHLIGHTS = [
    (10, '+', 'языков и систем', 'Rust · Go · Python · C/C++ · Asm'),
    (4, '', 'UI-платформы', 'Tauri · Electron · Flutter · Qt'),
    (4, '', 'плагина для Astra', 'STT · Silero · DDG · Proxy'),
]
STATS_META = 'github · ноябрь 2026'

LINKS = [
    ('link-telegram', 'Telegram', 't.me/SpherePrime', 'https://t.me/SpherePrime'),
    ('link-sphereprime', 'SpherePrime', 'github.com/SpherePrime', 'https://github.com/SpherePrime'),
    ('link-portfolio', 'Портфолио', 'lilkalinov.github.io/portfolio', 'https://lilkalinov.github.io/portfolio/'),
]

SECTIONS = {
    'prime': ('01', 'SpherePrime', 'Агентные инструменты для разработчиков: терминал, десктоп, роутинг, прокси.', '04 ПРОЕКТА'),
    'plugins': ('02', 'Плагины для Astra', 'Расширения голосового ассистента: распознавание речи, оффлайн-синтез и поиск.', '04 ПЛАГИНА'),
    'journey': ('03', 'Опыт и Путь', 'От модификаций Stella и Lead QA в Astra к собственной студии.', '02 НАПРАВЛЕНИЯ'),
}

PROJECTS = {
    'cli': dict(
        kind='SPHEREPRIME · GO', title='Prime CLI', art='cli',
        lines=['Агентный AI-ассистент для кода в терминале.', 'Любые модели, MCP и LSP-контекст, сессии,', '12 дизайнов интерфейса и голосовой ввод.'],
        chips=['Go', 'Assembly', 'MCP', 'LSP'],
        cta='репозиторий', url_label='github.com/SpherePrime/CLI',
        url='https://github.com/SpherePrime/CLI',
        alt='Prime CLI — агентный AI-ассистент для кода в терминале: любые модели, MCP, LSP. Go. Открыть репозиторий SpherePrime.'),
    'desktop': dict(
        kind='SPHEREPRIME · TAURI & ELECTRON', title='Prime Desktop', art='desktop',
        lines=['Десктоп-воркспейс Prime на Tauri и Electron:', 'проекты, чаты, апрувы, диффы, терминалы,', 'SSH, автоматизации, MCP/LSP/Skills и голос.'],
        chips=['Rust', 'Tauri', 'Electron', 'React', 'HTML / CSS'],
        cta='репозиторий', url_label='github.com/SpherePrime/CLI/desktop',
        url='https://github.com/SpherePrime/CLI/tree/main/desktop',
        alt='Prime Desktop — десктоп-воркспейс Prime для Windows и Linux на Tauri, Electron и React. Открыть исходники.'),
    'primeai': dict(
        kind='SPHEREPRIME · TS', title='PrimeAi', art='router',
        lines=['AI-провайдер для Astra: Router API сам выбирает', 'маршрут, повторяет запросы и знает vision-модели.'],
        chips=['TypeScript', 'Bun', 'Router API'],
        url='https://github.com/SpherePrime/PrimeAi',
        alt='PrimeAi — AI-провайдер для Astra с автоматической маршрутизацией через Router API. Открыть репозиторий.'),
    'proxy': dict(
        kind='SPHEREPRIME · RUST', title='PrimeProxy', art='proxy',
        lines=['Локальный MTProto-прокси для Telegram', 'с WebSocket-транспортом. Быстро и тихо.'],
        chips=['Rust', 'MTProto', 'WebSocket'],
        url='https://github.com/SpherePrime/PrimeProxy',
        alt='PrimeProxy — локальный MTProto-прокси для Telegram с WebSocket-транспортом. Rust. Открыть репозиторий.'),
    'stt': dict(
        kind='ASTRA PLUGIN · RUST', title='Astra-Google-STT', art='stt',
        lines=['Keyless распознавание речи в Astra на базе', 'Google Web Speech API без ключей и регистрации.'],
        chips=['Rust', 'Web Speech API', 'Audio', 'Astra SDK'],
        url='https://github.com/LilKALINOV/Astra-Google-STT',
        alt='Astra-Google-STT — распознавание речи прямо внутри Astra. Rust. Открыть репозиторий.'),
    'silero': dict(
        kind='ASTRA PLUGIN · RUST / PY', title='Astra Silero', art='silero',
        lines=['Локальный оффлайн-синтез русской речи для Astra', 'на базе нейросети Silero TTS прямо на устройстве.'],
        chips=['Rust', 'Python', 'Silero TTS', 'On-device'],
        url='https://github.com/LilKALINOV/astra-silero',
        alt='Astra Silero — локальный синтез русской речи для Astra на базе Silero TTS. Открыть репозиторий.'),
    'ddg': dict(
        kind='ASTRA PLUGIN · RUST', title='Astra WebSearch DDG', art='ddg',
        lines=['Поиск в реальном времени через DuckDuckGo:', 'быстрые ответы из веба для Astra без лимитов и ключей.'],
        chips=['Rust', 'DuckDuckGo', 'Real-time', 'Web API'],
        url='https://github.com/LilKALINOV/astra-websearch-ddg',
        alt='Astra WebSearch DDG — поиск в реальном времени через DuckDuckGo для Astra. Открыть репозиторий.'),
    'astraproxy': dict(
        kind='ASTRA PLUGIN · RUST', title='Astra PrimeProxy', art='proxy',
        lines=['Интеграция быстрого MTProto-прокси для Astra', 'с WebSocket-транспортом и защитой соединений.'],
        chips=['Rust', 'MTProto', 'WebSocket', 'Network'],
        url='https://github.com/SpherePrime/Astra-PrimeProxy',
        alt='Astra PrimeProxy — защищенный прокси-транспорт для Astra. Rust. Открыть репозиторий.'),
    'journey': dict(
        kind='ЭВОЛЮЦИЯ · STELLA → ASTRA → PRIME', title='Путь к Prime', art='journey',
        lines=['От кастомных модов Stella к роли Lead QA в Astra.', 'Сегодня — со-основатель студии SpherePrime:', 'создаем инструменты для автономных ИИ-агентов.'],
        chips=['Stella', 'Lead QA Astra', 'SpherePrime', 'KNICE & MINICE'],
        cta='открыть профиль', url_label='github.com/LilKALINOV',
        url='https://github.com/LilKALINOV',
        alt='Путь: Stella → Astra → SpherePrime. Моддинг, Lead QA, со-основатель SpherePrime.'),
    'portfolio': dict(
        kind='PORTFOLIO · NATIVE & WEB UI', title='Портфолио', art='portfolio',
        lines=['Интерактивное портфолио, документация проектов,', 'нативные интерфейсы и открытый код.', 'Все материалы экосистемы.'],
        chips=['HTML / CSS', 'Flutter', 'Qt 5/6', 'Tauri'],
        cta='открыть сайт', url_label='lilkalinov.github.io/portfolio',
        url='https://lilkalinov.github.io/portfolio/',
        alt='Портфолио LilKALINOV — нативные интерфейсы, открытый код и архитектура. Открыть сайт.'),
}

LAYOUT = [
    ('hero',),
    ('links',),
    ('stats',),
    ('section', 'prime'),
    ('wide', 'cli'),
    ('wide', 'desktop'),
    ('pair', 'primeai', 'proxy'),
    ('section', 'plugins'),
    ('pair', 'stt', 'silero'),
    ('pair', 'ddg', 'astraproxy'),
    ('section', 'journey'),
    ('wide', 'journey'),
    ('wide', 'portfolio'),
    ('footer',),
]
