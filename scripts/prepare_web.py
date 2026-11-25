"""Stage runtime files and convert music to OGG for Pygbag."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT/'build'/'web-src'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', help='Optional FFmpeg executable path')
    args = parser.parse_args()
    ffmpeg = shutil.which(args.ffmpeg or 'ffmpeg')
    if ffmpeg is None and args.ffmpeg is None:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            ffmpeg = get_ffmpeg_exe()
        except (ImportError, RuntimeError):
            parser.error('Install requirements-web.txt to obtain the bundled FFmpeg executable.')
    if ffmpeg is None:
        parser.error('Install FFmpeg or pass --ffmpeg with its executable path.')
    if STAGE.resolve().parent != (ROOT/'build').resolve():
        raise ValueError('Web staging path must be inside this project build directory.')
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copy2(ROOT/'main.py', STAGE/'main.py')
    for folder in ('griductive', 'assets'):
        shutil.copytree(ROOT/folder, STAGE/folder,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.mp3', '*.m4a', '*.wav', '*.flac', 'experiments'))
    shutil.copytree(ROOT/'data'/'puzzles', STAGE/'data'/'puzzles')
    for source in sorted((ROOT/'assets'/'sounds').iterdir()):
        if source.suffix.lower() not in ('.mp3', '.m4a', '.wav', '.flac'):
            continue
        target = STAGE/'assets'/'sounds'/source.with_suffix('.ogg').name
        subprocess.run([ffmpeg, '-nostdin', '-y', '-loglevel', 'error', '-i', str(source),
                        '-vn', '-c:a', 'libvorbis', '-q:a', '4', str(target)], check=True)
        print(f'Converted {source.name}')
    attribution = STAGE/'assets'/'ATTRIBUTION.md'
    with attribution.open('a', encoding='utf-8') as stream:
        stream.write('\n## Browser music conversion\n\n'
                     'This build converts the listed music tracks to OGG Vorbis. '
                     'The files retain their original track titles and source credits.\n')
    print(f'Web sources ready at {STAGE}')


if __name__ == '__main__':
    main()
