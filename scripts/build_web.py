"""Build the browser game with its loading screen and full-page background."""
from pathlib import Path
import shutil
import subprocess
import sys
import json
from PIL import Image
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'build'/'web-src'/'build'/'web'
STAGE = ROOT/'build'/'web-src'


def optimize_assets():
    from griductive.ui import config
    background = STAGE/'assets'/'images'/config.BACKGROUND_FILE
    with Image.open(background) as image:
        image = image.convert('RGB')
        image.thumbnail((1600, 1000), Image.Resampling.LANCZOS)
        image.quantize(colors=256).save(background, optimize=True)

    # Retain glyphs used by the current source, stages, configuration and filenames.
    text = ''.join(path.read_text(encoding='utf-8')
                   for folder in ('griductive', 'data/puzzles')
                   for path in (STAGE/folder).rglob('*')
                   if path.suffix in ('.py', '.json'))
    text += ''.join(path.name for path in (ROOT/'assets').rglob('*'))
    text += ''.join(str(value) for key, value in vars(config).items() if not key.startswith('_'))
    unicodes = set(range(0x20, 0x250)) | set(range(0x2000, 0x2070))
    unicodes.update(map(ord, text))
    options = subset.Options()
    options.name_IDs = ['*']
    options.name_legacy = True
    options.recalc_timestamp = False
    font_path = STAGE/'assets'/'fonts'/config.BODY_FONT
    font = TTFont(font_path)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    font.save(font_path)
    font.close()
    with (STAGE/'assets'/'ATTRIBUTION.md').open('a', encoding='utf-8') as stream:
        stream.write('\nWeb optimization changes include a resized, 256-color background '
                     'and a body-font subset containing the current game text.\n')
    print(f'Web background {background.stat().st_size:,} bytes, body font {font_path.stat().st_size:,} bytes')


def main():
    subprocess.run([sys.executable, str(ROOT/'scripts'/'prepare_web.py'),
                    *sys.argv[1:]], cwd=ROOT, check=True)
    optimize_assets()
    music_dir = ROOT/'build'/'web-music'
    if music_dir.resolve().parent != (ROOT/'build').resolve():
        raise ValueError('Music staging must remain inside the project build directory.')
    if music_dir.exists():
        shutil.rmtree(music_dir)
    music_dir.mkdir()
    tracks = sorted((STAGE/'assets'/'sounds').glob('*.ogg'), key=lambda path: path.stem.casefold())
    for track in tracks:
        shutil.move(str(track), str(music_dir/track.name))
    (STAGE/'assets'/'sounds'/'tracks.json').write_text(
        json.dumps([track.name for track in tracks], ensure_ascii=False), encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--title', 'Griductive',
                    '--width', '1180', '--height', '850', 'build/web-src'],
                   cwd=ROOT, check=True)
    shutil.copytree(music_dir, OUTPUT/'music')
    page_assets = OUTPUT/'page'
    page_assets.mkdir(exist_ok=True)
    for name in ('page.css', 'page.js'):
        shutil.copy2(ROOT/'web'/name, page_assets/name)
    # These files load before the Python runtime and its archive are available.
    from griductive.ui import config
    shutil.copy2(STAGE/'assets'/'images'/config.BACKGROUND_FILE, page_assets/'background.png')
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
