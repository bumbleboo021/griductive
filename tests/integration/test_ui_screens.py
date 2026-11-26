"""Integration tests for Home, Stage Select, Gameplay Timer HUD, and Pause menu."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
from pathlib import Path
from time import monotonic, sleep
import pygame
import pytest
from griductive.engine.reference import ReferenceAnalyzer
from griductive.ui.screens import format_duration
from griductive.ui.window import GameWindow

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def home_window():
    pygame.init()
    view = GameWindow(
        ROOT / 'data/puzzles/3x3/level_01.json',
        ReferenceAnalyzer,
        ROOT / 'data/puzzles',
        'Reference analyzer | development mode',
        start_screen='home',
    )
    view.draw()
    yield view
    pygame.quit()


def click(view, point):
    if view.output_surface is not None:
        point = (round(point[0]*view.output_surface.get_width()/view.screen.get_width()),
                 round(point[1]*view.output_surface.get_height()/view.screen.get_height()))
    view.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    view.draw()


def wait(view):
    deadline = monotonic() + 5
    while view.busy and monotonic() < deadline:
        view.update()
        sleep(0.005)
    assert not view.busy
    view.draw()


def test_duration_formatting():
    assert format_duration(0) == '00:00'
    assert format_duration(67_500) == '01:07'


def test_home_screen_navigation_help_music_and_quit(home_window):
    assert home_window.screen_state == 'home'
    assert 'home_play' in home_window.buttons
    assert 'home_stages' in home_window.buttons

    click(home_window, home_window.buttons['home_help'][0].center)
    assert home_window.help_open and home_window.screen_state == 'home'
    click(home_window, home_window.buttons['close_help'][0].center)
    assert not home_window.help_open

    click(home_window, home_window.buttons['home_music'][0].center)
    assert home_window.music_picker and home_window.screen_state == 'home'
    click(home_window, home_window.buttons['close_music'][0].center)
    assert not home_window.music_picker

    click(home_window, home_window.buttons['home_play'][0].center)
    assert home_window.screen_state == 'game'
    assert 'pause' in home_window.buttons

    click(home_window, home_window.buttons['pause'][0].center)
    assert home_window.screen_state == 'pause'
    click(home_window, home_window.buttons['pause_home'][0].center)
    assert home_window.screen_state == 'home'
    quit_center = home_window.buttons['home_quit'][0].center
    assert home_window.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=quit_center)) is False


def test_stage_select_filters_and_stage_loading(home_window):
    click(home_window, home_window.buttons['home_stages'][0].center)
    assert home_window.screen_state == 'stage_select'
    assert len(home_window.stage_select_hits) > 0

    click(home_window, home_window.buttons['stage_filter_4'][0].center)
    assert home_window.stage_filter == 4
    assert len(home_window.stage_select_hits) == 4
    assert all('4x4' in str(path) for _, path in home_window.stage_select_hits)

    rect, path = home_window.stage_select_hits[0]
    click(home_window, rect.center)
    assert home_window.screen_state == 'game'
    assert home_window.engine.public_state().size == 4
    assert home_window.current_path == path.resolve()


def test_pause_menu_esc_toggle_timer_and_closes_inspector(home_window):
    click(home_window, home_window.buttons['home_play'][0].center)
    home_window.action('agent')
    home_window.draw()
    assert home_window.inspector.open

    # Timer ticks while playing
    start_tick = home_window.last_timer_tick
    home_window._tick_stage_timer(start_tick + 200)
    assert home_window.stage_elapsed_ms == 200

    # Clicking Menu pauses gameplay and freezes timer
    click(home_window, home_window.buttons['pause'][0].center)
    assert home_window.screen_state == 'pause'
    home_window._tick_stage_timer(home_window.last_timer_tick + 200)
    assert home_window.stage_elapsed_ms == 200

    # Esc resumes gameplay
    home_window.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    home_window.draw()
    assert home_window.screen_state == 'game'

    # Returning to Main Menu cleanly closes docked inspector
    click(home_window, home_window.buttons['pause'][0].center)
    click(home_window, home_window.buttons['pause_home'][0].center)
    assert home_window.screen_state == 'home'
    assert not home_window.inspector.open


def test_no_lost_screen_on_mistakes_and_stage_cleared_progression(home_window):
    stages = home_window.discover_stages()
    home_window.load(ROOT / 'tests/fixtures/chain_3.json')
    home_window.draw()

    # Multiple wrong verdicts always show notification without failing the stage
    for _ in range(4):
        click(home_window, home_window.cards['B1'].center)
        click(home_window, home_window.buttons['innocent'][0].center)
        wait(home_window)
        assert home_window.notification is not None
        assert home_window.screen_state == 'game'
        click(home_window, home_window.buttons['dismiss_notification'][0].center)

    # Load stage 1 and solve it -> opens Stage Cleared overlay (star-free)
    home_window.load(stages[0].path)
    home_window.draw()
    home_window.stage_elapsed_ms = 42_000
    while not home_window.engine.solved:
        result = home_window.engine.step()
        home_window.queue.put(result)
        home_window.update()

    assert home_window.engine.solved
    assert home_window.cleared_pending_until is not None
    recorded = home_window.stage_records[stages[0].path].best_time_ms
    assert recorded >= 42_000

    # Trigger Stage Cleared overlay after reveal delay
    home_window.cleared_pending_until = 0
    home_window.update()
    home_window.draw()
    assert home_window.screen_state == 'cleared'
    assert 'cleared_next' in home_window.buttons

    # View Board dismisses overlay and reveals reopen pill
    click(home_window, home_window.buttons['cleared_board'][0].center)
    assert home_window.screen_state == 'game'
    assert home_window.cleared_dismissed
    assert 'reopen_cleared' in home_window.buttons

    # Timer stays stopped once solved
    home_window._tick_stage_timer(home_window.last_timer_tick + 200)
    assert home_window.stage_elapsed_ms == recorded

    # Reopen Stage Cleared and advance to Next Stage
    click(home_window, home_window.buttons['reopen_cleared'][0].center)
    assert home_window.screen_state == 'cleared'
    click(home_window, home_window.buttons['cleared_next'][0].center)
    assert home_window.screen_state == 'game'
    assert home_window.current_path == stages[1].path
    assert home_window.moves == 0
