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
CHARACTER_QUOTES = {
    "Arlecchino": ["Staring into my eyes is ill-advised. I can't promise you'll like what you see."],
    "Ayaka": ["I only wish life could be as leisurely as this a little more often... How greedy of me."],
    "Chiori": ["Looking at that tragic ensemble you call an outfit, it’s no mystery why you’re still single."],
    "Columbina": ["What a starry night... wouldn't it be lovely to sing a sweet lullaby right outside Sandrone's door?"],
    "Escoffier": ["What are you, an idiot sandwich?"],
    "Eula": ["Hmph, a snowy day like this is practically begging for a mug of warm milk, mark my words, vengeance will be mine!"],
    "Furina": ["Buy me Prada, Balenciaga, cut the drama, let's go Bahama"],
    "Ganyu": ["Only the chosen one deserves the fresh cocomilk from the cocogoat"],
    "Hu Tao": ["Silly-churl, billy-churl, silly-billy hilichurl."],
    "Kazuha": ["This scenery is wonderful... Surely enough to convince anyone to become a wanderer."],
    "Keqing": ["I'm all for work-life balance, but I think this is pushing it"],
    "Lumine": ["Multiple catastrophic crises threatening Teyvat? Oh, you mean a surge in Primogem rewards."],
    "Linnea": [" So shiny... Lumi, no! You can't eat that!"],
    "Mitya": ["Riemann Hypothesis is such a child plaything"],
    "Nahida": ["Get some good rest! Ya know... Use the bathroom and flush your anxiety-dookie away"],
    "Nicole": ["So, the lore is...."],
    "Odette": ["Witness the snow swan's grace"],
    "Raiden Ei": ["After all, very few in eternity ever get the privilege of tasting my cooking"],
    "Sandrone": ["What do you mean clank clank clank? I designed to go plap plap plap"],
    "Skirk": ["The Abyss is like the world's shadow. It's always there, and it will never perish."],
    "Venti": ["Ehe"],
    "Vesna": ["One for you, one for me, one for Her Majesty, and another for me! None for Danica, hehe!"],
    "Vodyanitsa": ["Odette, do you wanna build a snowman?"],
    "Xiangling": [" I can't decide whether Pyro slimes taste better with salt and pepper or garlic and herbs."],
    "Xianyun": ["Oh did you know when Shenhe and Ganyu were kids..."],
    "Yae Miko": ["Right here! Right now! Emerge! Come on out! Show them!"],
    "Yelan": ["No, i won't step on you"],
    "Zibai": ["I would rather parry a Celestial nail than hanging out with you."],
}

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
