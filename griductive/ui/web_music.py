"""Browser music streams from separate URLs after the player selects a track."""
import json
import platform
from pathlib import Path
import pygame
from griductive.ui.assets import ASSETS
from griductive.ui.music import Music


class WebMusic(Music):
    def __init__(self):
        super().__init__()
        self.names = json.loads((ASSETS/'sounds'/'tracks.json').read_text(encoding='utf-8'))
        self.last_message = None
        self.next_poll = 0

    def tracks(self):
        return [ASSETS/'sounds'/name for name in self.names]

    def select(self, path):
        name = Path(path).name
        if name not in self.names:
            return 'Music unavailable: unknown track.'
        self.last_message = None
        return platform.window.eval(f'window.griductiveMusic.select({json.dumps(name)})')

    def toggle(self):
        self.last_message = None
        return platform.window.eval(f'window.griductiveMusic.toggle({json.dumps(self.path.name)})')

    def stop(self):
        platform.window.eval('window.griductiveMusic.stop()')
        self.enabled = False

    def poll(self):
        now = pygame.time.get_ticks()
        if now < self.next_poll:
            return None
        self.next_poll = now+250
        state = json.loads(platform.window.eval('JSON.stringify(window.griductiveMusic.state())'))
        self.enabled = state['enabled']
        if state['name']:
            self.path = ASSETS/'sounds'/state['name']
        message = state['message']
        if message and message != self.last_message:
            self.last_message = message
            return message
        return None
