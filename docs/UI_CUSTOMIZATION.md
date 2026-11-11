# Customize the UI

Each stage and restart begins with the top-left character selected. WASD and
arrow keys move selection one cell at a time without opening a popup. Board edges
stop movement. Enter opens an unresolved card's choices with Innocent selected.
A/Left selects Innocent, D/Right selects Criminal, S/Down selects Cancel, and
W/Up returns from Cancel to Innocent. Enter confirms; Escape closes the popup.
Mouse clicks still open cards and activate choices. Solved-card navigation selects
its clue in the side panel. Navigation waits while analysis or Auto Solve is active
and is blocked by Stage, Tracks, Help, and rejection dialogs.

The Stage picker supports mouse-wheel scrolling and a draggable scrollbar on its
right edge. Hold the left mouse button on the thumb and move it up or down.
Clicking the track jumps the list toward that position. The bar is hidden when
all stages fit on screen.

Revealed clues share a bordered panel with a clipped scrolling area and a position
indicator. Wheel and trackpad input scroll smoothly while the pointer is inside
that panel. `CLUE_SCROLL_STEP` sets pixels per wheel notch and
`CLUE_SCROLL_TIME_MS` controls easing time. Lower easing times settle sooner.

Use **Tracks** beside Music On/Off to choose music. The picker lists WAV, OGG,
MP3 (including VBR), and FLAC files directly inside `assets/sounds/`. Selecting
a track starts it and keeps the choice for the current game session. Closing
and reopening Tracks refreshes the file list. Escape or Close dismisses it.
M4A files are omitted from the list. Add the MP3 version of your track to use it.
The Music toggle stops or restarts the selected track.

Fill in `assets/ATTRIBUTION.md` with sources and licenses for your artwork,
fonts, and music. Store accompanying license files in `assets/licenses/`.

Buttons, stage rows and character cards animate on hover with a small lift and
accent outline. Adjust `HOVER_DURATION_MS` and `HOVER_LIFT` in `config.py`.
Hover feedback applies to the active popup and ignores disabled controls.

**Stage** opens the named level list. Each bundled JSON now has a root `name`
field, such as `"name": "3x3 - Quiet Rows"`. The picker and board heading use it.
Older JSON using `title` still loads. Put new stage files under `data/puzzles/`.
Scroll the list for additional levels, select one to play, or close with Escape.

The **?** button at the top right opens the how-to-play panel. Escape or Got it
closes it. Opening help pauses Auto Solve after any in-progress analysis.

**Music Off / Music On** toggles the bundled original ambient loop. Music starts
off and keeps playing across stage changes when enabled. Set `MUSIC_FILE` to a
filename in `assets/sounds/` and `MUSIC_VOLUME` to a value between 0 and 1.
The default `ambient.wav` is a synthesized 16-second loop created for this project.
If the audio device or file is unavailable, the message panel reports the error.

Click an unresolved character to open its Criminal/Innocent verdict popup.
Cancel, Escape, or clicking outside dismisses it without changing the game.
Solved cards select their clue instead. The permanent verdict buttons and
Selected text have been removed. Load/Restart/Hint/Auto Solve now form a two-row
control group under the clue panel; the message panel sits below them.

Edit `CHARACTER_QUOTES` in `griductive/ui/config.py` to define personal remarks
for cards whose logical clues were safely removed. One quote is selected per
card/cast and stays stable across frames and Restart. Quotes cannot reveal any
hidden clue and do not affect the solver. They are labeled Personal remark in
the side panel. Empty quote lists fall back to `...`.

`RANDOMIZE_CAST = True` chooses a fresh, non-repeating portrait cast each time
the GUI loads a level. Characters are assigned to cells in random order; Restart
keeps that assignment unchanged. If there are too few icons, the puzzle's saved cast is used.
Set this to False to always use the names in the JSON. Headless benchmarks keep
the original JSON cast for reproducibility. Only names and origins change;
solutions, clue references, cell IDs, and initial reveals stay the same.

Displayed clues resolve cell IDs to the current names: `B1 is innocent` becomes
`Ayaka is innocent`. Set `SHOW_CELL_IN_CLUES = True` to display `Ayaka (B1)`.
The underlying structured clues still reference stable cell IDs for the solver.

Cards now use a name/origin header and a large portrait. After a proved verdict,
the portrait shrinks and moves to the upper left; its newly public clue fades in
below the header. Initially revealed cards start in the finished layout. Clicking
a solved card selects and scrolls to its complete clue in the side panel; long
card clues end with an ellipsis. Restart and Load reset animation state.

Additional controls in `config.py`:

```python
REVEAL_DURATION_MS = 650
SOLVED_PORTRAIT_SIZE = {3: 36, 4: 28, 5: 24}
BACKGROUND_FILE = 'Background · Genshin Impact.png'
BACKGROUND_DIM = 155
```

Set duration to 0 for instant reveals. Larger duration means a slower transition.
The clue appears in the last 35% of the transition; Auto Solve waits for the
transition plus 150 ms between accepted moves. Background filenames are relative
to `assets/images/`; the image fills the window with its aspect ratio preserved
and edges cropped. Dim values run from 0 (bright) to 255 (black).

Edit `griductive/ui/config.py`, save, then close and restart the game:

```powershell
.\.venv-win\Scripts\python.exe main.py
```

## Portraits and character boxes

```python
PORTRAIT_SIZE = {3: 110, 4: 76, 5: 52}
```

The keys are board sizes (3x3, 4x4, 5x5). Values are desired icon widths/heights
in pixels. Increase a value for larger icons or decrease it for smaller icons.
The UI centers unresolved portraits and caps them to the inner card width and available height
below the name/origin. Once capped, raising the value alone has no effect.

Card dimensions are calculated from the board dimensions:

```python
cell_width = (BOARD_WIDTH - CARD_GAP * (size - 1)) // size
cell_height = (BOARD_HEIGHT - CARD_GAP * (size - 1)) // size
```

`CARD_GAP` changes space between cards. `CARD_PADDING` changes inner spacing.
`CARD_RADIUS` changes corner roundness. `PORTRAIT_TOP` positions the unresolved
portrait below the name and origin. `STATUS_HEIGHT` reserves the bottom status
line after a verdict. `ORIGIN_GAP` and `ORIGIN_MIN_WIDTH` are legacy settings
from the previous side-by-side card layout and no longer affect the new cards.

`BOARD_X` and `BOARD_Y` position the whole grid. Keep its right edge at or before
758 and bottom edge at or before `MESSAGE_Y - 20`. The board fills the left side
with vertical cards. `WINDOW_SIZE = (1180, 1020)` defines the logical drawing area
and Pygame scales the window to fit the display. `MESSAGE_Y` positions feedback
below the board. Mouse coordinates are mapped to the logical drawing area.

## Fonts, colors, and artwork

In `config.py`, change `FONT_SIZE`, `SMALL_FONT_SIZE`, `TINY_FONT_SIZE`, and
`HEADING_FONT_SIZE`. Font filenames (`BODY_FONT`, `HEADING_FONT`) are relative
to `assets/fonts/`. Larger fonts may require more room in card headers or buttons.

Colors are RGB tuples with three values from 0 to 255. Edit `BG`, `PANEL`, `TEXT`,
`MUTED`, `ACCENT`, `CRIMINAL_CARD`, `INNOCENT_CARD`, `HIGHLIGHT`, `BUTTON`, or
`BUTTON_DISABLED` in that same file.

Portraits live in `assets/images/Character Icons/` and match the puzzle character
name. Filename format: `Name · Origin · Game.png`. The origin comes from the
second filename segment. Add a matching character name to your puzzle JSON to use
an icon. Portrait assignment is deterministic; changing status does not change it.

## Other layout and interactions

`character_card.py` renders card contents and interpolates the reveal animation.
`assets.py` caches portrait surfaces and loads the background.
`window.py` contains `draw()` (board, clue panel, controls), `draw_picker()` (Load
popup), `button()` (button style), `event()` (input), and `action()` (actions).
For a new button, add its drawing call in `draw()` and behavior in `action()`;
`button()` registers its clickable rectangle automatically.

After layout edits, check all board sizes:

```powershell
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/3x3/level_01.json
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/4x4/level_01.json
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/5x5/level_01.json
.\.venv-win\Scripts\python.exe -m pytest tests/integration/test_ui.py -q
```
