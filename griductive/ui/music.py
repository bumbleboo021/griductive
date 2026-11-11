"""Local music selection and streamed looping playback."""
from pathlib import Path
import pygame
from griductive.ui.assets import ASSETS
from griductive.ui import config


class Music:
    def __init__(self):
        self.path = ASSETS/'sounds'/config.MUSIC_FILE
        self.enabled = False

    def tracks(self):
        extensions = {'.wav', '.ogg', '.mp3', '.flac'}
        return sorted((path for path in (ASSETS/'sounds').glob('*')
                       if path.is_file() and path.suffix.lower() in extensions),
                      key=lambda path: path.stem.casefold())

    def poll(self):
        return None

    def select(self, path):
        previous = self.path
        was_enabled = self.enabled
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(max(0, min(1, config.MUSIC_VOLUME)))
            pygame.mixer.music.play(loops=-1, fade_ms=400)
            self.path = Path(path)
            self.enabled = True
            return f'Playing {self.path.stem}.'
        except (pygame.error, OSError) as exc:
            self.enabled = False
            if was_enabled:
                try:
                    pygame.mixer.music.load(str(previous))
                    pygame.mixer.music.play(loops=-1)
                    self.enabled = True
                except (pygame.error, OSError):
                    pass
            return f'Music unavailable: {exc}'

    def toggle(self):
        if self.enabled:
            self.stop()
            return 'Music off.'
        return self.select(self.path)

    def stop(self):
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        self.enabled = False
