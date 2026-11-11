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
    view = GameWindow(ROOT/'tests/fixtures/chain_3.json', ReferenceAnalyzer,
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
    click(window, window.cards['B1'].center)
    click(window, window.buttons['innocent'][0].center)
    wait(window)
    assert window.message.startswith('CONTRADICTED')
    assert window.notification.code == 'CONTRADICTED'
    click(window, window.buttons['dismiss_notification'][0].center)
    click(window, window.cards['B1'].center)
    click(window, window.buttons['criminal'][0].center)
    wait(window)
    assert len(window.engine.public_state().clues) == 2
    assert window.notification is None
    click(window, window.clue_hits[0][0].center)
    assert window.clue_id == 'clue-A1'
    click(window, window.buttons['restart'][0].center)
    assert len(window.engine.public_state().clues) == 1


def test_load_picker_and_failure_keeps_game(window):
    click(window, window.buttons['stage'][0].center)
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
    window.load(ROOT/f'tests/fixtures/chain_{size}.json')
    window.draw()
    assert len(window.cards) == size*size
    assert all(window.screen.get_rect().contains(rect) for rect in window.cards.values())
    from griductive.ui import config
    expected_height = (config.BOARD_HEIGHT-config.CARD_GAP*(size-1))//size
    assert all(rect.height == expected_height and rect.width > 0 for rect in window.cards.values())


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


def test_reveal_animation_and_restart(window):
    from griductive.ui.character_card import reveal_progress
    from griductive.ui import config
    assert reveal_progress(1000, 1000) == 0
    assert 0 < reveal_progress(1000, 1000+config.REVEAL_DURATION_MS//2) < 1
    assert reveal_progress(1000, 1000+config.REVEAL_DURATION_MS) == 1
    assert reveal_progress(None, 1000) == 1
    window.engine.step()
    window.draw()
    assert 'B1' in window.reveal_started
    window.action('restart')
    window.draw()
    assert window.reveal_started == {}


def test_clue_appears_only_after_portrait_moves(window, monkeypatch):
    from griductive.ui.character_card import draw_character
    state = window.engine.public_state()
    card = state.characters[0]
    rect = window.cards['A1']
    drawn = []
    original = window.wrapped
    def record(text, *args, **kwargs):
        drawn.append(text)
        return original(text, *args, **kwargs)
    monkeypatch.setattr(window, 'wrapped', record)
    draw_character(window, card, rect, state.verdicts[0][1], state.clues[0], .4, 3)
    assert window.clue_text(state.clues[0]) not in drawn
    drawn.clear()
    draw_character(window, card, rect, state.verdicts[0][1], state.clues[0], 1, 3)
    # A long character name can wrap; compare the rendered lines.
    expected = window.lines(window.clue_text(state.clues[0]), rect.width-18, window.small)
    assert all(line in drawn for line in expected)


def test_random_cast_preserves_logic_and_restart(window):
    from random import Random
    from griductive.engine.puzzle import load_puzzle
    puzzle = load_puzzle(ROOT/'tests/fixtures/chain_3.json')
    one = window.artwork.cast_puzzle(puzzle, Random(1))
    two = window.artwork.cast_puzzle(puzzle, Random(2))
    assert one.characters != two.characters
    assert one.solution == two.solution == puzzle.solution
    assert one.clues == two.clues == puzzle.clues
    assert len({c.name for c in one.characters}) == 9
    assert [c.name.casefold() for c in one.characters] != sorted(c.name.casefold() for c in one.characters)
    names = window.engine.public_state().characters
    window.action('restart')
    assert window.engine.public_state().characters == names


def test_clue_uses_current_character_name(window):
    state = window.engine.public_state()
    name = next(c.name for c in state.characters if c.cell == 'B1')
    assert window.clue_text(state.clues[0]) == f'{name} is criminal.'


def test_quote_comes_from_config_and_stays_stable(window,monkeypatch):
    from griductive.domain.models import Clue
    from griductive.ui import config
    monkeypatch.setattr(config,'CHARACTER_QUOTES',['First remark.','Second remark.'])
    clue=Clue('q','QUOTE',())
    first=window.clue_text(clue)
    assert first in config.CHARACTER_QUOTES
    assert window.clue_text(clue)==first
    window.action('restart')
    assert window.clue_text(clue)==first


def test_verdict_popup_dismissal_and_solved_cards(window):
    assert 'criminal' not in window.buttons and 'innocent' not in window.buttons
    before = window.engine.public_state()
    click(window, window.cards['B1'].center)
    assert window.verdict_cell == 'B1'
    assert window.screen.get_rect().contains(window.verdict_rect)
    window.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    window.draw()
    assert window.verdict_cell is None
    click(window, window.cards['B1'].center)
    click(window, window.buttons['cancel_verdict'][0].center)
    assert window.verdict_cell is None
    click(window, window.cards['B1'].center)
    click(window, (10, 10))
    assert window.verdict_cell is None
    assert window.engine.public_state() == before
    click(window, window.cards['A1'].center)
    assert window.verdict_cell is None
    assert window.clue_id == 'clue-A1'


def test_unproved_verdict_notification_blocks_clicks_without_revealing(window):
    before = window.engine.public_state()
    click(window, window.cards['C1'].center)
    click(window, window.buttons['innocent'][0].center)
    wait(window)
    assert window.notification.code == 'NOT_PROVABLE'
    assert window.engine.public_state() == before
    click(window, window.cards['B1'].center)
    assert window.verdict_cell is None
    assert window.notification is not None
    assert window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    window.draw()
    assert window.notification is None
    click(window, window.cards['B1'].center)
    click(window, window.buttons['criminal'][0].center)
    wait(window)
    assert window.notification is None
    assert len(window.engine.public_state().clues) == 2


def test_help_opens_and_blocks_board_until_closed(window):
    click(window,window.buttons['help'][0].center)
    assert window.help_open
    click(window,window.cards['B1'].center)
    assert window.verdict_cell is None
    click(window,window.buttons['close_help'][0].center)
    assert not window.help_open
    click(window,window.buttons['help'][0].center)
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    assert not window.help_open


def test_stage_names_and_music_toggle(window):
    from griductive.engine.puzzle import load_puzzle
    click(window,window.buttons['stage'][0].center)
    assert window.stage_names
    assert all(name==load_puzzle(path).title for path,name in window.stage_names.items())
    click(window,window.buttons['close_stage'][0].center)
    assert not window.picker
    click(window,window.buttons['music'][0].center)
    assert window.music.enabled
    click(window,window.buttons['music'][0].center)
    assert not window.music.enabled


def test_hover_animates_buttons_and_cards(window,monkeypatch):
    monkeypatch.setattr(pygame.time,'get_ticks',lambda:window.hover_time+50)
    stage_position = window.buttons['stage'][0].center
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:stage_position)
    window.draw()
    assert 0 < window.hover_values['stage'] < 1
    card_position = window.cards['B1'].center
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:card_position)
    window.draw()
    assert window.hover_values['card-B1'] > 0
    click(window,window.cards['B1'].center)
    prior=window.hover_values['card-B1']
    window.draw()
    assert window.hover_values['card-B1'] <= prior


def test_music_picker_switches_tracks_and_preserves_choice(window,tmp_path,monkeypatch):
    import wave
    import griductive.ui.music as music_module
    sounds=tmp_path/'sounds'
    sounds.mkdir()
    for name in ('First.wav','Second.wav'):
        with wave.open(str(sounds/name),'wb') as audio:
            audio.setparams((1,2,22050,0,'NONE','not compressed'))
            audio.writeframes(b'\0\0'*2205)
    (sounds/'Unsupported.m4a').write_bytes(b'placeholder')
    monkeypatch.setattr(music_module,'ASSETS',tmp_path)
    click(window,window.buttons['choose_music'][0].center)
    assert window.music_picker
    assert [p.name for p in window.music_tracks]==['First.wav','Second.wav']
    before=window.engine.public_state()
    click(window,window.cards['B1'].center)
    assert window.verdict_cell is None
    rect,path=window.music_hits[1]
    click(window,rect.center)
    assert window.music.enabled and window.music.path==path
    click(window,window.buttons['close_music'][0].center)
    assert not window.music_picker
    click(window,window.buttons['music'][0].center)
    assert not window.music.enabled
    click(window,window.buttons['music'][0].center)
    assert window.music.enabled and window.music.path==path
    assert window.engine.public_state()==before
    window.music.stop()


def test_invalid_music_keeps_previous_track(window,tmp_path):
    window.music.toggle()
    previous=window.music.path
    broken=tmp_path/'broken.mp3'
    broken.write_bytes(b'invalid audio')
    message=window.music.select(broken)
    assert message.startswith('Music unavailable')
    assert window.music.path==previous and window.music.enabled
    window.music.stop()


def test_clue_scroll_eases_and_stays_inside_panel(window,monkeypatch):
    window.load(ROOT/'tests/fixtures/chain_5.json')
    while not window.engine.solved:
        window.engine.step()
    window.draw()
    assert window.max_scroll > 0
    assert window.clue_panel.contains(window.clue_viewport)
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:window.clue_viewport.center)
    monkeypatch.setattr(pygame.time,'get_ticks',lambda:window.hover_time+16)
    window.event(pygame.event.Event(pygame.MOUSEWHEEL,y=-1,precise_y=-.5))
    target=window.clue_scroll_target
    assert target>0 and window.clue_scroll==0
    window.draw()
    assert 0 < window.clue_scroll < target
    window.event(pygame.event.Event(pygame.MOUSEWHEEL,y=-10000))
    assert window.clue_scroll_target==window.max_scroll
    for _ in range(100):
        window.draw()
    assert window.clue_scroll==window.max_scroll
    assert all(window.clue_viewport.contains(rect) for rect,_ in window.clue_hits)
    rect,clue=window.clue_hits[-1]
    click(window,rect.center)
    assert window.clue_id==clue.id
    window.action('restart')
    window.draw()
    assert window.clue_scroll==window.clue_scroll_target==0


def test_wheel_outside_clues_does_not_scroll_them(window,monkeypatch):
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:window.buttons['stage'][0].center)
    window.event(pygame.event.Event(pygame.MOUSEWHEEL,y=-3))
    assert window.clue_scroll_target==0


@pytest.mark.parametrize('name',['Ayaka','Xiangling','Lumine'])
def test_portraits_keep_original_proportions(window,name):
    record=window.artwork.catalog[name.casefold()]
    original=pygame.image.load(str(record.path))
    portrait=window.artwork.portrait(name,(120,120))
    original_bounds=original.get_bounding_rect()
    bounds=portrait.get_bounding_rect()
    assert portrait.get_size()==(120,120)
    assert abs(bounds.width/bounds.height-original_bounds.width/original_bounds.height)<.04
    assert portrait is window.artwork.portrait(name,(120,120))


def test_auto_move_uses_hover_animation_and_clears_on_restart(window,monkeypatch):
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:(0,0))
    # Simulate the ordinary worker completion path for an Auto Solve move.
    window.auto = True
    result = window.engine.step()
    window.queue.put(result)
    window.update()
    assert window.auto_focus_cell == result.cell
    monkeypatch.setattr(pygame.time,'get_ticks',lambda:window.hover_time+50)
    window.draw()
    assert window.hover_values['card-'+result.cell]>0
    assert not window.pointer_hover
    window.auto = False
    window.action('restart')
    assert window.auto_focus_cell is None


def test_final_auto_move_keeps_focus_for_reveal(window,monkeypatch):
    for _ in range(7):
        window.engine.step()
    window.auto = True
    result = window.engine.step()
    assert result.code=='SOLVED'
    window.queue.put(result)
    window.update()
    assert not window.auto
    assert window.auto_focus_cell==result.cell
    assert window.auto_focus_until>pygame.time.get_ticks()


def test_stage_scrollbar_drags_both_directions_and_selects_stage(window):
    click(window,window.buttons['stage'][0].center)
    before=window.engine
    thumb=window.stage_scroll_thumb.copy()
    track=window.stage_scroll_track.copy()
    click(window,thumb.center)
    assert window.stage_drag_offset is not None
    window.event(pygame.event.Event(pygame.MOUSEMOTION,pos=(track.centerx,track.bottom+100),rel=(0,100),buttons=(1,0,0)))
    window.draw()
    assert window.file_scroll==len(window.files)-8
    window.event(pygame.event.Event(pygame.MOUSEMOTION,pos=(track.centerx,track.top-100),rel=(0,-100),buttons=(1,0,0)))
    window.draw()
    assert window.file_scroll==0
    window.event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(0,0)))
    assert window.stage_drag_offset is None
    click(window,(track.centerx,track.bottom-2))
    assert window.file_scroll>0
    window.event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(0,0)))
    window.draw()
    rect,path=window.file_hits[-1]
    click(window,rect.center)
    assert not window.picker and window.engine is not before


def test_stage_scrollbar_is_hidden_when_all_stages_fit(window):
    window.action('stage')
    window.files=window.files[:3]
    window.draw()
    assert window.stage_scroll_thumb is None and window.stage_scroll_track is None


@pytest.mark.parametrize(('key','expected'),[(pygame.K_w,'B1'),(pygame.K_UP,'B1'),
    (pygame.K_s,'B3'),(pygame.K_DOWN,'B3'),(pygame.K_a,'A2'),(pygame.K_LEFT,'A2'),
    (pygame.K_d,'C2'),(pygame.K_RIGHT,'C2')])
def test_keyboard_card_navigation(window,key,expected):
    window.select_character('B2', open_popup=False)
    before=window.engine.public_state()
    window.event(pygame.event.Event(pygame.KEYDOWN,key=key))
    window.draw()
    assert window.selected==expected
    assert window.verdict_cell is None
    assert window.engine.public_state()==before


def test_navigation_edges_solved_cards_and_modal_blocking(window):
    assert window.selected == 'A1' and window.verdict_cell is None
    window.select_character('B1', open_popup=False)
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_LEFT))
    window.draw()
    assert window.selected=='A1' and window.verdict_cell is None
    assert window.clue_id=='clue-A1'
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_UP))
    assert window.selected=='A1'
    window.action('help')
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
    assert window.selected=='A1'
    window.help_open=False
    window.auto=True
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
    assert window.selected=='A1'
    window.auto=False
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
    window.draw()
    assert window.selected=='B1' and window.verdict_cell is None


@pytest.mark.parametrize(('key','choice'),[(pygame.K_a,'innocent'),
    (pygame.K_LEFT,'innocent'),(pygame.K_d,'criminal'),(pygame.K_RIGHT,'criminal'),
    (pygame.K_s,'cancel_verdict'),(pygame.K_DOWN,'cancel_verdict')])
def test_verdict_keyboard_focus_and_confirmation(window,key,choice,monkeypatch):
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_d))
    assert window.selected == 'B1' and window.verdict_cell is None
    before = window.engine.public_state()
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    assert window.verdict_cell == 'B1' and window.verdict_choice == 'innocent'
    window.event(pygame.event.Event(pygame.KEYDOWN,key=key))
    window.draw()
    assert window.verdict_choice == choice and window.selected == 'B1'
    assert window.engine.public_state() == before
    results = []
    monkeypatch.setattr(window,'start',lambda action:results.append(action()))
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    assert window.verdict_cell is None
    if choice == 'cancel_verdict':
        assert results == [] and window.engine.public_state() == before
    else:
        assert results[0].code == ('ACCEPTED' if choice == 'criminal' else 'CONTRADICTED')


def test_verdict_default_escape_and_solved_card_enter(window):
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    assert window.verdict_cell is None  # A1 is already revealed.
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_d))
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_KP_ENTER))
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_s))
    for key in (pygame.K_w, pygame.K_UP):
        window.event(pygame.event.Event(pygame.KEYDOWN,key=key))
        assert window.verdict_choice == 'innocent'
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_d))
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    assert window.selected == 'B1' and window.verdict_cell is None
    window.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    assert window.verdict_choice == 'innocent'
    window.action('restart')
    assert window.selected == 'A1' and window.verdict_cell is None
    window.load(ROOT/'tests/fixtures/chain_4.json')
    assert window.selected == 'A1' and window.verdict_cell is None


def test_surface_caches_stay_within_budget_and_reuse_text(window):
    from griductive.ui.cache import SurfaceCache
    cache = SurfaceCache(800)
    first = pygame.Surface((10,10), pygame.SRCALPHA)
    second = first.copy()
    third = first.copy()
    cache.put('first', first)
    cache.put('second', second)
    assert cache.get('first') is first
    cache.put('third', third)
    assert cache.get('second') is None
    assert cache.get('first') is first
    cache.put('first', third)
    assert cache.bytes_used == 800
    cache.put('oversized', pygame.Surface((100,100)))
    assert cache.bytes_used <= cache.max_bytes and cache.get('oversized') is None
    cache.clear()
    assert cache.bytes_used == 0
    before = dict(window.text_cache.items)
    window.draw()
    assert all(window.text_cache.get(key) is surface for key,surface in before.items())
    assert window.text_cache.bytes_used <= window.text_cache.max_bytes
    for side in range(30,250):
        window.artwork.portrait('Lumine',(side,side))
    assert window.artwork.images.bytes_used <= window.artwork.images.max_bytes


def test_frame_rate_control_preserves_board(window):
    before = window.engine.public_state()
    click(window, window.buttons['frame_rate'][0].center)
    assert window.target_fps == 30
    click(window, window.buttons['frame_rate'][0].center)
    assert window.target_fps == 60
    assert window.engine.public_state() == before
