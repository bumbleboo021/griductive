"""Local portraits and their filename metadata: name · origin · game.png."""
from dataclasses import dataclass, replace
import random
from pathlib import Path
import pygame
from griductive.ui import config

ASSETS = Path(__file__).resolve().parents[2] / 'assets'


@dataclass(frozen=True)
class Portrait:
    name: str
    origin: str
    path: Path


def character_catalog():
    result = {}
    for path in sorted((ASSETS / 'images' / 'Character Icons').glob('*.png')):
        parts = [part.strip() for part in path.stem.split('\u00b7')]
        if len(parts) >= 2:
            result[parts[0].casefold()] = Portrait(parts[0], parts[1], path)
    return result


class Artwork:
    def __init__(self):
        self.catalog = character_catalog()
        self.images = {}
        self.originals = {}

    def portrait(self, name, size):
        record = self.catalog.get(name.casefold())
        if record is None:
            return None
        key = (record.path, size)
        if key not in self.images:
            if record.path not in self.originals:
                self.originals[record.path] = pygame.image.load(str(record.path)).convert_alpha()
            original = self.originals[record.path]
            scale = min(size[0]/original.get_width(), size[1]/original.get_height())
            fitted_size = (max(1,round(original.get_width()*scale)),
                           max(1,round(original.get_height()*scale)))
            fitted = pygame.transform.smoothscale(original, fitted_size)
            canvas = pygame.Surface(size, pygame.SRCALPHA)
            canvas.blit(fitted, ((size[0]-fitted_size[0])//2, size[1]-fitted_size[1]))
            self.images[key] = canvas
        return self.images[key]

    def cast_puzzle(self, puzzle, rng=None):
        """Randomize public display metadata only; cell-based logic stays intact."""
        if not config.RANDOMIZE_CAST or puzzle.fixed_cast:
            return puzzle
        count = len(puzzle.characters)
        if len(self.catalog) < count:
            # Custom installations with too few portraits retain their JSON cast.
            return puzzle
        chosen = (rng or random.SystemRandom()).sample(list(self.catalog.values()), count)
        return replace(puzzle, characters=tuple(
            replace(char, name=portrait.name, profession=portrait.origin)
            for char, portrait in zip(puzzle.characters, chosen)))

    def background(self, size):
        path = ASSETS / 'images' / config.BACKGROUND_FILE
        if not path.exists():
            return None
        image = pygame.image.load(str(path)).convert()
        scale = max(size[0]/image.get_width(), size[1]/image.get_height())
        image = pygame.transform.smoothscale(image, (round(image.get_width()*scale), round(image.get_height()*scale)))
        canvas = pygame.Surface(size)
        canvas.blit(image, ((size[0]-image.get_width())//2, (size[1]-image.get_height())//2))
        shade = pygame.Surface(size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, config.BACKGROUND_DIM))
        canvas.blit(shade, (0, 0))
        return canvas


def ui_font(size, heading=False):
    filename = config.HEADING_FONT if heading else config.BODY_FONT
    path = ASSETS / 'fonts' / filename
    return pygame.font.Font(str(path) if path.exists() else None, size)
