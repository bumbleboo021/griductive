"""Real Pygame event/render checks using SDL's offscreen driver."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
from pathlib import Path
from time import monotonic, sleep
import pygame
import pytest
from griductive.engine.reference import ReferenceAnalyzer
from griductive.ui.window import GameWindow

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def window():
    pygame.init()
    view = GameWindow(ROOT/'data/puzzles/3x3/tutorial.json', ReferenceAnalyzer,
                      ROOT/'data/puzzles', 'Reference analyzer | development mode')
    view.draw()
    yield view
    pygame.quit()


def click(view, point):
    view.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    view.draw()


def wait(view):
    deadline = monotonic()+5
    while view.busy and monotonic() < deadline:
        view.update()
        sleep(.005)
    assert not view.busy
    view.draw()


def test_manual_hint_reveal_restart_and_highlight(window):
    click(window, window.buttons['hint'][0].center)
    wait(window)
    assert window.selected == 'B1'
    assert len(window.engine.public_state().clues) == 1
    click(window, window.buttons['innocent'][0].center)
    wait(window)
    assert window.message.startswith('CONTRADICTED')
    click(window, window.buttons['criminal'][0].center)
    wait(window)
    assert len(window.engine.public_state().clues) == 2
    click(window, window.clue_hits[0][0].center)
    assert window.clue_id == 'clue-A1'
    click(window, window.buttons['restart'][0].center)
    assert len(window.engine.public_state().clues) == 1


def test_load_picker_and_failure_keeps_game(window):
    click(window, window.buttons['load'][0].center)
    assert window.picker
    before = window.engine
    window.load(ROOT/'does-not-exist.json')
    assert window.engine is before and window.picker
    rect, path = next((r,p) for r,p in window.file_hits if '4x4' in str(p))
    click(window, rect.center)
    assert not window.picker
    assert window.engine.public_state().size == 4


def test_auto_solve_and_worker_error(window):
    click(window, window.buttons['auto'][0].center)
    for _ in range(10):
        window.next_step = 0
        window.update()
        wait(window)
        if not window.auto:
            break
    assert window.engine.solved
    assert window.message.startswith('SOLVED')
    def fail():
        raise RuntimeError('teammate failure')
    window.start(fail)
    wait(window)
    assert 'teammate failure' in window.message


@pytest.mark.parametrize('size', [3,4,5])
def test_render_sizes(window, size):
    window.load(ROOT/f'data/puzzles/{size}x{size}/tutorial.json')
    window.draw()
    assert len(window.cards) == size*size
    assert all(window.screen.get_rect().contains(rect) for rect in window.cards.values())


def test_slow_worker_keeps_events_responsive_and_blocks_reset(window):
    from threading import Event
    from griductive.engine.game import Outcome
    release = Event()
    def slow():
        release.wait(2)
        return Outcome('HINT', 'finished')
    window.start(slow)
    try:
        # A stale enabled button from the previous frame must not open the picker.
        window.action('load')
        assert not window.picker
        window.draw()
        assert not window.buttons['restart'][1]
        assert not window.event(pygame.event.Event(pygame.QUIT))
    finally:
        release.set()
        wait(window)
