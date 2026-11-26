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
    point = view.window_position(point)
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


def test_hints_count_once_per_cell_and_reset_on_restart(home_window):
    home_window.load(ROOT / 'tests/fixtures/chain_3.json')
    home_window.draw()
    total_cells = len(home_window.engine.public_state().characters)
    initial_revealed = len(home_window.engine.public_state().verdicts)

    # Pressing Hint repeatedly while the same hint is already shown only counts once
    for _ in range(5):
        click(home_window, home_window.buttons['hint'][0].center)
        wait(home_window)
    assert home_window.selected == 'B1'
    assert home_window.hints_used == 1

    # Even if Hint is spammed before every single move, hints_used never exceeds cell count
    while not home_window.engine.solved:
        for _ in range(2):
            click(home_window, home_window.buttons['hint'][0].center)
            wait(home_window)
        result = home_window.engine.step()
        home_window.queue.put(result)
        home_window.update()
        home_window.draw()

    assert home_window.hints_used == total_cells - initial_revealed
    assert home_window.hints_used <= total_cells

    # Restart resets hint tracking cleanly
    home_window.action('restart')
    home_window.draw()
    assert home_window.hints_used == 0
    click(home_window, home_window.buttons['hint'][0].center)
    wait(home_window)
    assert home_window.hints_used == 1


def test_moves_count_both_wrong_and_correct_verdicts(home_window):
    home_window.load(ROOT / 'tests/fixtures/chain_3.json')
    home_window.draw()
    assert home_window.moves == 0

    # Cancelling popup does not count as a move
    click(home_window, home_window.cards['B1'].center)
    click(home_window, home_window.buttons['cancel_verdict'][0].center)
    assert home_window.moves == 0

    # Contradicted verdict counts as 1 move
    click(home_window, home_window.cards['B1'].center)
    click(home_window, home_window.buttons['innocent'][0].center)
    wait(home_window)
    assert home_window.notification.code == 'CONTRADICTED'
    assert home_window.moves == 1
    click(home_window, home_window.buttons['dismiss_notification'][0].center)

    # Unprovable verdict counts as 1 move
    click(home_window, home_window.cards['C1'].center)
    click(home_window, home_window.buttons['innocent'][0].center)
    wait(home_window)
    assert home_window.notification.code == 'NOT_PROVABLE'
    assert home_window.moves == 2
    click(home_window, home_window.buttons['dismiss_notification'][0].center)

    # Correct verdict counts as 1 move
    click(home_window, home_window.cards['B1'].center)
    click(home_window, home_window.buttons['criminal'][0].center)
    wait(home_window)
    assert home_window.notification is None
    assert home_window.moves == 3


def test_home_screen_has_no_idle_animation(home_window, monkeypatch):
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: (0, 0))
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 1000)
    home_window.draw()
    frame_a = pygame.image.tobytes(home_window.screen, 'RGB')

    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 1350)
    home_window.draw()
    frame_b = pygame.image.tobytes(home_window.screen, 'RGB')
    assert frame_a == frame_b


def test_window_maximize_and_agent_layout_rebalancing(home_window, monkeypatch):
    from griductive.ui import config as cfg

    # Native OS window Maximize button is enabled via RESIZABLE; no extra UI buttons added
    assert bool(pygame.display.get_surface().get_flags() & pygame.RESIZABLE)
    assert 'home_fullscreen' not in home_window.buttons
    assert not home_window.maximized

    click(home_window, home_window.buttons['home_play'][0].center)
    assert home_window.screen_state == 'game'
    assert 'fullscreen' not in home_window.buttons

    # Simulate clicking the OS titlebar Maximize button on a 1920x1009 desktop work area
    maximized_surface = pygame.Surface((1920, 1009))
    monkeypatch.setattr(pygame.display, 'get_surface', lambda: maximized_surface)
    set_mode_calls = []
    monkeypatch.setattr(pygame.display, 'set_mode', lambda *a, **kw: set_mode_calls.append((a, kw)) or maximized_surface)

    home_window.event(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    home_window.event(pygame.event.Event(pygame.WINDOWSIZECHANGED, x=1920, y=1009))
    home_window.draw()

    assert home_window.maximized
    assert home_window.output_surface is maximized_surface
    assert home_window.screen.get_size() == cfg.WINDOW_SIZE
    assert home_window.viewport_rect.x > 0 and home_window.viewport_rect.y == 0

    # Clicking Agent while maximized must NOT call set_mode (keeps OS maximize state)
    # and must auto-balance & center Board + Clues + Agent Inspector
    click(home_window, home_window.buttons['agent'][0].center)
    assert home_window.inspector.open
    assert home_window.maximized
    assert set_mode_calls == []
    assert home_window.screen.get_size() == (cfg.WINDOW_SIZE[0] + cfg.AGENT_PANEL_WIDTH, cfg.WINDOW_SIZE[1])

    frame_w, frame_h = home_window.frame_surface.get_size()
    assert abs((frame_w / frame_h) - (1920 / 1009)) < 0.01
    assert home_window.viewport_rect.x == (frame_w - home_window.screen.get_width()) // 2
    assert home_window.viewport_rect.y == (frame_h - home_window.screen.get_height()) // 2
    assert home_window.viewport_rect.y > 0

    # Clicking both board cards and Agent Inspector buttons works accurately while maximized
    click(home_window, home_window.cards['B1'].center)
    assert home_window.verdict_cell == 'B1'
    click(home_window, home_window.buttons['cancel_verdict'][0].center)
    assert home_window.verdict_cell is None

    click(home_window, home_window.buttons['agent_analyze'][0].center)
    wait(home_window)
    assert len(home_window.observer.snapshot()) == 1

    # Closing Agent while maximized stays maximized and re-centers the main desk
    click(home_window, home_window.buttons['agent_close'][0].center)
    assert not home_window.inspector.open
    assert home_window.maximized
    assert set_mode_calls == []
    assert home_window.screen.get_size() == cfg.WINDOW_SIZE
    assert home_window.viewport_rect.x > 0 and home_window.viewport_rect.y == 0

    # Restoring from OS titlebar returns cleanly to normal windowed mode
    restored_surface = pygame.Surface(cfg.WINDOW_SIZE)
    monkeypatch.setattr(pygame.display, 'get_surface', lambda: restored_surface)
    home_window.event(pygame.event.Event(pygame.WINDOWRESTORED))
    home_window.event(pygame.event.Event(pygame.WINDOWSIZECHANGED, x=cfg.WINDOW_SIZE[0], y=cfg.WINDOW_SIZE[1]))
    home_window.draw()
    assert not home_window.maximized
    assert home_window.output_surface is None
