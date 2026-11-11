"""Build the browser game with its loading screen and full-page background."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'build'/'web-src'/'build'/'web'


def main():
    subprocess.run([sys.executable, str(ROOT/'scripts'/'prepare_web.py'),
                    *sys.argv[1:]], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--title', 'Griductive',
                    '--width', '1180', '--height', '850', 'build/web-src'],
                   cwd=ROOT, check=True)
    page_assets = OUTPUT/'page'
    page_assets.mkdir(exist_ok=True)
    for name in ('page.css', 'page.js'):
        shutil.copy2(ROOT/'web'/name, page_assets/name)
    # These files load before the Python runtime and its archive are available.
    from griductive.ui import config
    shutil.copy2(ROOT/'assets'/'images'/config.BACKGROUND_FILE, page_assets/'background.png')
    shutil.copy2(ROOT/'assets'/'fonts'/config.HEADING_FONT, page_assets/'heading.ttf')
    index = OUTPUT/'index.html'
    html = index.read_text(encoding='utf-8')
    html = html.replace('</head>', '<link rel="stylesheet" href="page/page.css">\n'
                        '<script src="page/page.js" defer></script>\n</head>', 1)
    html = html.replace('<body>', '''<body>
    <section id="loading-screen" aria-label="Loading Griductive">
      <div class="loading-card">
        <h1>Griductive</h1>
        <div class="loading-spinner" aria-hidden="true"></div>
        <p id="loading-message" role="status">Loading your game…</p>
        <button id="play-button" type="button" hidden>Play</button>
      </div>
    </section>''', 1)
    index.write_text(html, encoding='utf-8')
    print(f'Browser game ready at {OUTPUT}')


if __name__ == '__main__':
    # Allow importing the shared configuration when launched as a script.
    sys.path.insert(0, str(ROOT))
    main()
