# Browser build and GitHub Pages

The browser version runs the bundled game using Pygbag and pygame-ce. It uses
the development semantic analyzer with cooperative search and a 15-second
analysis deadline. Searches yield every 128 visited nodes so the game can draw
and process input. A timeout appears as an error and leaves the board available
for another action.

## Local setup

Use Python 3.12. Create a separate environment for the web tools. The web
requirements include an FFmpeg executable through `imageio-ffmpeg`.

```powershell
python -m venv .venv-web
.\.venv-web\Scripts\python.exe -m pip install -r requirements-web.txt
.\.venv-web\Scripts\python.exe scripts/build_web.py
.\.venv-web\Scripts\python.exe -m http.server 8000 --directory build/web-src/build/web
```

Open `http://localhost:8000` and press Play when the loading screen is ready. The first visit downloads
the Python and Pygame WebAssembly runtime from Pygbag's CDN. Internet access is
required. Music starts through the game's Music or Tracks buttons.

If FFmpeg is outside PATH, use `scripts/build_web.py --ffmpeg "C:/path/to/ffmpeg.exe"`.
With no explicit path, staging uses FFmpeg from PATH when available and otherwise
uses the executable bundled with `imageio-ffmpeg`.
The staging command recreates `build/web-src` from the current source, assets,
and puzzle files. It converts music to OGG inside that generated directory.
Run `scripts/build_web.py` again after editing source or assets, then refresh the page.

The build command prepares assets, packages the game, and adds the browser page.

```powershell
.\.venv-web\Scripts\python.exe scripts/build_web.py
```

The deployable output is `build/web-src/build/web/`. Serve that directory over
HTTP to test the completed build. Runtime source, fonts, portraits, stage JSON,
and credits are included in the game archive. Five converted tracks are served
separately from `music/` and load after a player requests playback. Generated builds and the local
web environment are excluded from Git.

## GitHub Pages

1. Push the source changes to the repository's `web-deploy` branch.
2. Open the repository's Settings, then Pages, and select GitHub Actions as the
   build and deployment source.
3. Open Actions and run **Deploy browser game**, or push another change to `web-deploy`.
4. Open the URL reported by the deployment job, normally
   `https://YOUR_USERNAME.github.io/YOUR_REPOSITORY/`.

The workflow in `.github/workflows/web.yml` installs pinned Python build tools
and bundled FFmpeg through pip,
stages the game, builds it, uploads the web artifact, and deploys it through Pages.
The workflow's push trigger names `web-deploy`.

## Loading screen and page background

`web/page.css` styles the loading card, spinner, Play button, and full-browser
background. `web/page.js` follows the runtime's loading status and reveals the
game after its first frame is drawn. The page background fills the space beside
the canvas while the game keeps its original proportions.

The build copies `config.BACKGROUND_FILE` and `config.HEADING_FONT` into the page's
static assets so they can appear before Python finishes loading. Change the
background dimming in `web/page.css` through the `body::before` overlay opacity.

## Performance settings

The browser starts at 30 FPS. The FPS button at the top switches between 30 and
60. `WEB_FPS` in `griductive/ui/config.py` sets the browser default.
`PORTRAIT_CACHE_BYTES` and `TEXT_CACHE_BYTES` cap resized portraits and rendered
text at 8 MiB and 4 MiB respectively. Least-recently-used surfaces are evicted
when a cache reaches its budget. Text wrapping and formatted clues are cached
and reset when loading another stage.

The build reduces the web background to at most 1600 by 1000 pixels with a
256-color palette. It subsets the body font to characters used by the current
source, configuration, stage files and asset filenames, plus basic Latin and
punctuation. Rebuild after adding text or characters. These generated copies
are created in the staging directory.

The music manifest is packaged in `assets/sounds/tracks.json`. The browser streams
selected OGG files through HTML audio and releases the previous audio source
when switching tracks or stopping. Desktop playback uses the local Pygame music
implementation.

## Browser checks

- Select stages across all three grid sizes and check artwork and complete clues.
- Use mouse controls, WASD/arrows, Enter, Cancel, and Escape inside popups.
- Try accepted and rejected verdicts, Hint, Auto Solve, Stop, and Restart.
- Scroll the stage and clue panels and test Tracks and Music after clicking the page.
- Check browser console errors and test the deployed repository URL as well as localhost.

The browser entry point is `griductive/web_app.py`. A future team agent must expose
an asynchronous `prepare(public_state)` that yields during search and a synchronous
`analyze(public_state)` that returns its prepared result. `GameWindow` prepares the
analysis before asking the engine to apply a move. The desktop CLI accepts its
existing synchronous analyzer interface.

## References

- [Pygbag packaging and asynchronous loop](https://pygame-web.github.io/wiki/pygbag/)
- [Pygbag browser behavior](https://pygame-web.github.io/wiki/pygbag-code/)
- [GitHub Pages deployment](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
