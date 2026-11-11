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
credits, and five converted tracks are included. Generated builds and the local
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
