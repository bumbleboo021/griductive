"""Browser startup using bundled stages and cooperative analysis."""
from pathlib import Path
import platform
import pygame
from griductive.engine.browser import BrowserAnalyzer
from griductive.ui import config
from griductive.ui.window import GameWindow


async def main():
    root = Path(__file__).resolve().parents[1]
    config.MUSIC_FILE = Path(config.MUSIC_FILE).with_suffix('.ogg').name
    pygame.init()
    try:
        view = GameWindow(root/'data/puzzles/3x3/level_01.json', BrowserAnalyzer,
                          root/'data/puzzles', 'Browser semantic analyzer | development mode')
        # Recalculate CSS sizing after SDL establishes the actual canvas dimensions.
        platform.window.window_resize()
        view.draw()
        platform.window.eval('window.griductiveGameReady && window.griductiveGameReady()')
        await view.run_web()
    finally:
        pygame.quit()
