"""UI settings in pixels. Restart the game after editing this file.

The board fills the left side. Coordinates use the logical window size below.
Pygame scales the window to fit the display and maps mouse input automatically.
"""

# Board dimensions are shared by every level; cell dimensions are calculated.
BOARD_X = 58
BOARD_Y = 132
BOARD_WIDTH = 700
BOARD_HEIGHT = 600
WINDOW_SIZE = (1180, 850)
AGENT_PANEL_WIDTH = 600  # Extra logical width while the inspector is docked.
MESSAGE_Y = 948
CARD_GAP = 10
CARD_RADIUS = 10
CARD_PADDING = 9

# Desired portrait side lengths for each board size. Available card space caps
# these values automatically so portraits cannot cover names or status labels.
PORTRAIT_SIZE = {3: 210, 4: 150, 5: 110}
PORTRAIT_TOP = 36
STATUS_HEIGHT = 17
ORIGIN_GAP = 7
ORIGIN_MIN_WIDTH = 52

# Card reveal: portrait shrinks/slides into a compact header, then clue fades in.
REVEAL_DURATION_MS = 650
SOLVED_PORTRAIT_SIZE = {3: 36, 4: 28, 5: 24}
BACKGROUND_FILE = 'Background \u00b7 Genshin Impact.png'
BACKGROUND_DIM = 155  # 0 = bright image, 255 = black
RANDOMIZE_CAST = True  # Fresh cast on Load; Restart preserves the current cast.
SHOW_CELL_IN_CLUES = False  # True: "Ayaka (B1)"; False: "Ayaka".
HOVER_DURATION_MS = 140
HOVER_LIFT = 3
CLUE_SCROLL_STEP = 55  # Pixels per wheel notch.
CLUE_SCROLL_TIME_MS = 110  # Lower values settle more quickly.
MUSIC_FILE = 'Chon Mat Gui Vàng Instrumental.mp3'  # Relative to assets/sounds/.
MUSIC_VOLUME = 0.22
CHARACTER_QUOTES = [
    'Even the stars have their secrets.',
    'A cup of tea makes every mystery easier.',
    'I wonder what tomorrow will bring.',
    'The wind carries stories from far away.',
    'There is always time for a little adventure.',
    'I could use a quiet afternoon.',
]

FONT_SIZE = 17
SMALL_FONT_SIZE = 13
TINY_FONT_SIZE = 11
HEADING_FONT_SIZE = 29
BODY_FONT = 'zh-cn.ttf'
HEADING_FONT = 'Genshin Impact DRIP FONT.ttf'

BG = (17, 24, 34)
PANEL = (29, 40, 54)
TEXT = (233, 239, 246)
MUTED = (160, 178, 196)
ACCENT = (104, 218, 192)
CRIMINAL_CARD = (74, 46, 52)
INNOCENT_CARD = (30, 68, 66)
HIGHLIGHT = (242, 197, 100)
BUTTON = (47, 70, 83)
BUTTON_DISABLED = (35, 43, 53)
