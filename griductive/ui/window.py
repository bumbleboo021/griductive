"""Pygame view with a single daemon worker for potentially slow analysis."""
from pathlib import Path
from functools import partial
from queue import Queue, Empty
from threading import Thread
import pygame
import re
import hashlib
import math
from griductive.ui.music import Music
from griductive.ui.agent_inspector import ObservedAnalyzer, AgentInspector
from griductive.domain.models import Status
from griductive.engine.game import GameEngine, Outcome
from griductive.engine.puzzle import load_puzzle
from griductive.ui.assets import Artwork, ui_font
from griductive.ui import config as cfg
from griductive.ui.character_card import draw_character, reveal_progress
from griductive.ui.config import BG, PANEL, TEXT, MUTED, ACCENT
from griductive.ui import screens
from griductive.ui.screens import (
    StageEntry,
    StageRecord,
    draw_centered_text,
    main_canvas_rect,
    short_stage_title,
    spawn_cleared_particles,
)



class GameWindow:
    def __init__(self, path, factory, puzzle_dir, analyzer_name, start_screen='game'):
        self.screen = pygame.display.set_mode(cfg.WINDOW_SIZE, pygame.SCALED)
        self.output_surface = None
        pygame.display.set_caption("Griductive | Deduction desk")
        self.font = ui_font(cfg.FONT_SIZE)
        self.small = ui_font(cfg.SMALL_FONT_SIZE)
        self.tiny = ui_font(cfg.TINY_FONT_SIZE)
        self.heading = ui_font(cfg.HEADING_FONT_SIZE, heading=True)
        self.title_font = ui_font(cfg.TITLE_FONT_SIZE, heading=True)
        self.subtitle_font = ui_font(cfg.SUBTITLE_FONT_SIZE, heading=True)
        self.artwork = Artwork()
        self.background = self.artwork.background(self.screen.get_size())
        self.reveal_started = {}
        self.last_revealed = None
        self.auto_focus_cell = None
        self.auto_focus_until = 0
        self.factory, self.puzzle_dir, self.analyzer_name = factory, Path(puzzle_dir), analyzer_name
        self.current_path = Path(path).resolve()
        self.observer = ObservedAnalyzer(factory())
        self.logic_heuristic = getattr(self.observer.analyzer, 'heuristic', None) or 'smallest'
        self.inspector = AgentInspector()
        self.engine = GameEngine(self.artwork.cast_puzzle(load_puzzle(path)), self.observer)
        self.queue = Queue()
        self.analysis_sequence_before = 0
        self.busy = self.auto = self.picker = False
        self.selected, self.clue_id = 'A1', None
        self.verdict_cell = None
        self.verdict_choice = 'innocent'
        self.verdict_rect = None
        self.notification = None
        self.help_open = False
        self.music = Music()
        self.music_picker = False
        self.music_tracks = []
        self.music_hits = []
        self.music_scroll = 0
        self.hover_values = {}
        self.hover_time = pygame.time.get_ticks()
        self.hover_delta = 0
        self.hover_scope = 'main'
        self.pointer_hover = False
        self.last_cursor = None
        self.stage_names = {}
        self.stage_scroll_track = None
        self.stage_scroll_thumb = None
        self.stage_drag_offset = None
        self.clue_scroll = self.file_scroll = self.next_step = self.max_scroll = 0
        self.clue_scroll_target = 0.0
        self.clue_panel = pygame.Rect(780,96,380,514)
        self.clue_viewport = pygame.Rect(794,160,342,436)
        self.buttons, self.cards = {}, {}
        self.clue_hits, self.file_hits, self.files = [], [], []
        self.message = "Select a card, read the revealed clues, then call a verdict."
        # Screen state, menu navigation, and elapsed timer
        self.screen_state = start_screen
        self.stage_select_return = 'home'
        self.has_active_session = start_screen == 'game'
        self.moves = 0
        self.hints_used = 0
        self.auto_used = False
        self.stage_elapsed_ms = 0
        self.last_timer_tick = pygame.time.get_ticks()
        self.stage_records = {}
        self._stage_catalog = None
        self.stage_filter = 'all'
        self.stage_select_scroll = 0
        self.stage_select_max_scroll = 0
        self.stage_select_hits = []
        self.cleared_pending_until = None
        self.cleared_dismissed = False
        self.cleared_particles = []
        self._home_preview_chars = None

    def label(self, text, pos, color=TEXT, font=None):
        self.screen.blit((font or self.font).render(str(text), True, color), pos)

    def clue_text(self, clue):
        if clue.kind == 'QUOTE':
            state = self.public_view_state()
            pool = cfg.CHARACTER_QUOTES
            if isinstance(pool, dict):
                # The engine emits revealed verdicts and clues in the same board order.
                owner = next((cell for (cell, _), item in zip(state.verdicts, state.clues)
                              if item.id == clue.id), None)
                name = next((c.name for c in state.characters if c.cell == owner), None)
                pool = pool.get(name)
            pool = pool or ['...']
            seed = clue.id+'|'+self.engine.title+'|'+','.join(c.name for c in state.characters)
            index = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:4],'big') % len(pool)
            return pool[index]
        names = {char.cell: char.name for char in self.public_view_state().characters}
        def display(match):
            cell = match.group(0)
            name = names.get(cell, cell)
            return f'{name} ({cell})' if cfg.SHOW_CELL_IN_CLUES else name
        return re.sub(r'\b[A-E][1-5]\b', display, clue.text)

    def lines(self, text, width, font=None):
        font = font or self.small
        result, line = [], ""
        for word in str(text).split():
            if line and font.size(line+" "+word)[0] > width:
                result.append(line)
                line = word
            else:
                line = (line+" "+word).strip()
        return result + [line]

    def clue_height(self, clue):
        return 40+len(self.lines(self.clue_text(clue), self.clue_viewport.width-24))*self.small.get_linesize()

    def wrapped(self, text, rect, color=TEXT, font=None):
        font = font or self.small
        old = self.screen.get_clip()
        self.screen.set_clip(old.clip(rect))
        for i, line in enumerate(self.lines(text, rect.width, font)):
            self.label(line, (rect.x, rect.y+i*font.get_linesize()), color, font)
        self.screen.set_clip(old)

    def button(self, key, text, rect, enabled=True, focused=False, style='default'):
        self.buttons[key] = (rect, enabled)
        amount = self.hover(key, rect, enabled, focused=focused)
        visible = rect.move(0, -round(cfg.HOVER_LIFT*amount))
        if not enabled:
            base = cfg.BUTTON_DISABLED
            border_accent = ACCENT
        elif style == 'primary':
            base = cfg.BUTTON_PRIMARY
            border_accent = ACCENT
        elif style == 'danger':
            base = cfg.BUTTON_DANGER
            border_accent = cfg.DANGER
        elif style == 'gold':
            base = (76, 62, 34)
            border_accent = cfg.HIGHLIGHT
        else:
            base = cfg.BUTTON
            border_accent = ACCENT
        color = tuple(round(a+(b-a)*amount*.32) for a,b in zip(base,border_accent))
        pygame.draw.rect(self.screen, color, visible, border_radius=9)
        if style in ('primary', 'gold') and enabled:
            pygame.draw.rect(self.screen, border_accent, visible, max(1, round(1 + amount)), border_radius=9)
        elif amount > 0:
            pygame.draw.rect(self.screen, border_accent, visible, max(1,round(amount*2)), border_radius=9)
        elif style == 'danger' and enabled:
            pygame.draw.rect(self.screen, cfg.DANGER, visible, 1, border_radius=9)
        if focused:
            pygame.draw.rect(self.screen, border_accent, visible, 2, border_radius=9)
        font = self.small if self.font.size(text)[0] > rect.width-20 else self.font
        if font.size(text)[0] <= visible.width-16:
            draw_centered_text(self.screen, font, text, visible.center, TEXT if enabled else MUTED)
        else:
            self.wrapped(text, visible.inflate(-20,-12), TEXT if enabled else MUTED, font)

    def hover(self, key, rect, enabled=True, focused=False):
        pointer = self.mouse_position()
        active_scope = (
            'notice' if self.notification else
            'music' if self.music_picker else
            'help' if self.help_open else
            'pause' if self.screen_state == 'pause' else
            'cleared' if self.screen_state == 'cleared' else
            'home' if self.screen_state == 'home' else
            'stage_select' if self.screen_state == 'stage_select' else
            'verdict' if self.verdict_cell else
            'stage' if self.picker else
            'agent' if self.inspector.open and pointer[0] >= cfg.WINDOW_SIZE[0] else
            'main'
        )
        hovered = enabled and self.hover_scope == active_scope and rect.collidepoint(pointer)
        self.pointer_hover |= hovered
        previous = self.hover_values.get(key, 0.0)
        step = self.hover_delta/max(1,cfg.HOVER_DURATION_MS)
        active = hovered or (focused and self.hover_scope == active_scope)
        value = min(1.0, previous+step) if active else max(0.0, previous-step)
        self.hover_values[key] = value
        return value

    def start(self, action):
        if self.busy:
            return
        records = self.observer.snapshot()
        self.analysis_sequence_before = records[-1].number if records else 0
        self.busy = True
        self.message = "Checking the revealed information..."
        def run():
            try:
                result = action()
            except Exception as exc:
                result = Outcome("ERROR", f"{type(exc).__name__}: {exc}")
            self.queue.put(result)
        Thread(target=run, daemon=True).start()

    def _tick_stage_timer(self, now=None):
        now = pygame.time.get_ticks() if now is None else now
        delta = max(0, min(250, now - self.last_timer_tick))
        self.last_timer_tick = now
        if (self.screen_state == 'game' and not self.engine.solved and
                not self.help_open and not self.music_picker and not self.picker and
                not self.notification):
            self.stage_elapsed_ms += delta

    def record_stage_completion(self):
        existing = self.stage_records.get(self.current_path)
        if existing is None:
            self.stage_records[self.current_path] = StageRecord(self.stage_elapsed_ms)
        else:
            self.stage_records[self.current_path] = StageRecord(
                min(existing.best_time_ms, self.stage_elapsed_ms),
            )

    def maybe_open_cleared(self, now=None):
        now = pygame.time.get_ticks() if now is None else now
        if (self.screen_state == 'game' and self.cleared_pending_until is not None
                and not self.cleared_dismissed and now >= self.cleared_pending_until):
            self.cleared_pending_until = None
            self.open_cleared()

    def open_cleared(self):
        self.auto = False
        self.verdict_cell = None
        self.notification = None
        self.screen_state = 'cleared'
        self.cleared_particles = spawn_cleared_particles(main_canvas_rect())

    def open_pause(self):
        if self.busy:
            return
        self.auto = False
        self.verdict_cell = None
        self.screen_state = 'pause'

    def resume_game(self):
        self.screen_state = 'game'
        self.has_active_session = True
        self.last_timer_tick = pygame.time.get_ticks()

    def go_home(self):
        if self.busy:
            return
        self.auto = False
        self.picker = False
        self.verdict_cell = None
        self.notification = None
        if self.inspector.open:
            self.set_inspector_open(False)
        self.screen_state = 'home'

    def open_stage_select(self, return_to=None):
        if self.busy:
            return
        self.auto = False
        self.picker = False
        self.verdict_cell = None
        self.notification = None
        if self.inspector.open:
            self.set_inspector_open(False)
        self.stage_select_return = return_to or self.screen_state
        self.stage_select_scroll = 0
        self.screen_state = 'stage_select'

    def discover_stages(self):
        if self._stage_catalog is None:
            entries = []
            for idx, path in enumerate(sorted(self.puzzle_dir.rglob("*.json")), 1):
                try:
                    puzzle = load_puzzle(path)
                except (ValueError, OSError):
                    continue
                entries.append(StageEntry(
                    path=path.resolve(),
                    title=puzzle.title,
                    short_title=short_stage_title(puzzle.title),
                    size=puzzle.size,
                    index=idx,
                ))
            self._stage_catalog = entries
        return self._stage_catalog

    def next_stage_path(self):
        stages = self.discover_stages()
        for i, entry in enumerate(stages):
            if entry.path == self.current_path:
                return stages[i + 1].path if i + 1 < len(stages) else None
        return stages[0].path if stages else None

    def home_preview_characters(self):
        if self._home_preview_chars is None:
            catalog = list(self.artwork.catalog.values())
            preferred = ('furina', 'arlecchino', 'nahida')
            chosen = []
            for name in preferred:
                if name in self.artwork.catalog:
                    chosen.append(self.artwork.catalog[name])
            for item in catalog:
                if len(chosen) >= 3:
                    break
                if item not in chosen:
                    chosen.append(item)
            while len(chosen) < 3:
                chosen.append(None)
            self._home_preview_chars = chosen[:3]
        return self._home_preview_chars

    def reset_stage_metrics(self):
        self.moves = 0
        self.hints_used = 0
        self.auto_used = False
        self.stage_elapsed_ms = 0
        self.last_timer_tick = pygame.time.get_ticks()
        self.cleared_pending_until = None
        self.cleared_dismissed = False
        self.screen_state = 'game'
        self.has_active_session = True

    def update(self):
        now = pygame.time.get_ticks()
        self._tick_stage_timer(now)
        try:
            result = self.queue.get_nowait()
        except Empty:
            result = None
        if result:
            self.busy = False
            records = self.observer.snapshot()
            if records and records[-1].number > self.analysis_sequence_before:
                self.observer.finish_action(result, self.engine.public_state())
            self.message = f"{result.code}: {result.message}"
            if result.code == 'HINT':
                self.hints_used += 1
            elif result.code in ('ACCEPTED', 'SOLVED'):
                self.moves += 1
            if result.code in ('CONTRADICTED', 'NOT_PROVABLE'):
                self.notification = result
                self.verdict_cell = None
            if result.cell:
                self.selected = result.cell
                if self.auto and result.code in ('ACCEPTED','SOLVED'):
                    self.auto_focus_cell = result.cell
                    self.auto_focus_until = now+max(cfg.REVEAL_DURATION_MS,cfg.HOVER_DURATION_MS*2)+150
            if result.code == 'SOLVED':
                self.record_stage_completion()
                self.cleared_pending_until = now+cfg.REVEAL_DURATION_MS+150
            if result.code != "ACCEPTED":
                self.auto = False
            self.next_step = now+cfg.REVEAL_DURATION_MS+150
        self.maybe_open_cleared(now)
        if self.screen_state == 'game' and self.auto and not self.busy and now >= self.next_step:
            self.start(self.engine.step)

    def load(self, path):
        try:
            observer = ObservedAnalyzer(self.factory())
            engine = GameEngine(self.artwork.cast_puzzle(load_puzzle(path)), observer)
        except Exception as exc:
            self.message = f"LOAD ERROR: {exc}"
            return
        self.current_path = Path(path).resolve()
        self.engine = engine
        self.observer = observer
        self.inspector.reset()
        self.notification = None
        self.last_revealed = None
        self.auto_focus_cell = None
        self.reveal_started.clear()
        self.selected, self.clue_id = 'A1', None
        self.verdict_cell = None
        self.clue_scroll = 0
        self.clue_scroll_target = 0.0
        self.picker = self.auto = False
        self.stage_drag_offset = None
        self.reset_stage_metrics()
        self.message = "Puzzle loaded. Select a card or ask for a hint."

    def logical_position(self, position):
        if self.output_surface is None:
            return position
        return (round(position[0]*self.screen.get_width()/self.output_surface.get_width()),
                round(position[1]*self.screen.get_height()/self.output_surface.get_height()))

    def mouse_position(self):
        return self.logical_position(pygame.mouse.get_pos())

    def public_view_state(self):
        record = self.inspector.selected_record(self.observer)
        return (record.after_state or record.state) if record else self.engine.public_state()

    def browse_history(self, amount):
        if self.busy:
            return
        self.auto = False
        self.auto_focus_cell = None
        self.inspector.browse(amount, len(self.observer.snapshot()))
        self.clear_replay_view()

    def clear_replay_view(self):
        self.verdict_cell = None
        self.clue_id = None
        self.clue_scroll = self.clue_scroll_target = 0
        self.reveal_started.clear()
        self.last_revealed = None

    def set_inspector_open(self, opened):
        if self.inspector.open == opened:
            return
        self.inspector.open = opened
        self.inspector.focused = opened
        if not opened:
            self.inspector.reset()
            self.clear_replay_view()
        width, height = cfg.WINDOW_SIZE
        if opened:
            width += cfg.AGENT_PANEL_WIDTH
        # SDL's SCALED renderer must be recreated when its logical size changes.
        # Keep fonts, audio, cached artwork, and the running engine intact.
        pygame.display.quit()
        pygame.display.init()
        if opened:
            desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
            scale = min(1.0, max(1,desktop_width-48)/width,
                        max(1,desktop_height-80)/height)
            self.output_surface = pygame.display.set_mode((max(1,round(width*scale)),
                                                          max(1,round(height*scale))))
            self.screen = pygame.Surface((width,height)).convert()
        else:
            self.screen = pygame.display.set_mode((width,height), pygame.SCALED)
            self.output_surface = None
        pygame.display.set_caption('Griductive | Deduction desk')
        self.last_cursor = None

    def action(self, key):
        if key == 'pause':
            self.open_pause()
            return
        if key == 'reopen_cleared':
            self.cleared_dismissed = False
            self.open_cleared()
            return
        if key == 'agent_live':
            self.inspector.reset()
            self.clear_replay_view()
            return
        if key == 'agent':
            self.set_inspector_open(not self.inspector.open)
            self.inspector.reset()
            return
        if key == 'choose_music':
            self.auto = False
            self.music_tracks = self.music.tracks()
            self.music_scroll = 0
            self.music_picker = True
            return
        if key == 'music':
            self.message = self.music.toggle()
            return
        if key == 'help':
            self.auto = False
            self.help_open = True
            return
        # Recheck current state: multiple mouse events can arrive before a redraw.
        if (self.busy or self.auto) and not (key == "auto" and self.auto):
            return
        if (self.inspector.selected_record(self.observer) is not None and
                key in ('agent_reference','agent_logic','agent_heuristic','agent_analyze','agent_step',
                        'hint','auto','criminal','innocent')):
            return
        if key in ('agent_reference', 'agent_logic', 'agent_heuristic'):
            try:
                heuristic = self.logic_heuristic
                if key in ('agent_logic', 'agent_heuristic'):
                    from griductive.agent.adapter import Agent
                    if key == 'agent_heuristic':
                        if not isinstance(self.observer.analyzer, Agent):
                            return
                        heuristic = 'jw' if heuristic == 'smallest' else 'smallest'
                    factory = partial(Agent, heuristic=heuristic)
                    name = f'Logic Agent ({heuristic})'
                else:
                    from griductive.engine.reference import ReferenceAnalyzer
                    factory = ReferenceAnalyzer
                    name = 'ReferenceAnalyzer'
                observer = ObservedAnalyzer(factory())
            except Exception as exc:
                self.message = f'Analyzer unavailable: {exc}'
                return
            self.factory = factory
            self.logic_heuristic = heuristic
            self.analyzer_name = name
            self.observer = observer
            self.engine.set_analyzer(observer)
            self.inspector.reset()
            self.message = f'Switched to {name}; proved cards preserved; history cleared.'
            return
        if key == 'agent_analyze':
            def analyze():
                result = self.engine.analyze()
                return Outcome('ANALYZED' if result.consistent else 'INCONSISTENT',
                               'Public-state analysis recorded. No card revealed.')
            self.start(analyze)
            self.inspector.reset()
            return
        if key == 'agent_step':
            self.start(self.engine.step)
            self.inspector.reset()
            return
        if key in ('load','stage'):
            self.files = sorted(self.puzzle_dir.rglob("*.json"))
            self.stage_names = {}
            for path in self.files:
                try:
                    self.stage_names[path] = load_puzzle(path).title
                except (ValueError, OSError) as exc:
                    self.message = f'Stage unavailable: {path.name}: {exc}'
            self.files = [path for path in self.files if path in self.stage_names]
            self.file_scroll, self.picker = 0, True
            self.stage_drag_offset = None
        elif key == "restart":
            self.notification = None
            self.engine.restart()
            self.observer.clear()
            self.inspector.reset()
            self.last_revealed = None
            self.auto_focus_cell = None
            self.reveal_started.clear()
            self.auto = False
            self.selected, self.clue_id = 'A1', None
            self.verdict_cell = None
            self.clue_scroll = 0
            self.clue_scroll_target = 0.0
            self.reset_stage_metrics()
            self.message = "Restarted with the original face-up cards."
        elif key == "hint":
            self.start(self.engine.hint)
        elif key == "auto":
            self.auto = not self.auto
            if self.auto:
                self.auto_used = True
            else:
                self.auto_focus_cell = None
            self.message = "Auto Solve started." if self.auto else "Stopped; the current step may finish."
        elif key in ("criminal", "innocent") and self.verdict_cell:
            cell, status = self.verdict_cell, Status(key.upper())
            self.verdict_cell = None
            self.start(lambda: self.engine.submit_verdict(cell, status))

    def open_verdict(self):
        if self.inspector.selected_record(self.observer) is not None:
            return
        if (self.selected is not None and not self.busy and not self.auto
                and self.selected not in dict(self.engine.public_state().verdicts)):
            self.verdict_cell = self.selected
            self.verdict_choice = 'innocent'

    def select_character(self, cell, open_popup=True):
        self.selected = cell
        self.verdict_cell = None
        self.verdict_rect = None
        for key in ('criminal','innocent','cancel_verdict'):
            self.buttons.pop(key,None)
        public = self.public_view_state()
        card_clues = dict(zip((c for c, _ in public.verdicts),public.clues))
        if cell not in card_clues:
            self.clue_id = None
            if open_popup:
                self.open_verdict()
            return
        self.clue_id = card_clues[cell].id
        self.clue_scroll_target = 0.0
        for clue in public.clues:
            if clue.id == self.clue_id:
                break
            self.clue_scroll_target += self.clue_height(clue)+8

    def move_selection(self, dx, dy):
        if self.selected is None or self.busy or self.auto:
            return
        size = self.engine.public_state().size
        column = ord(self.selected[0])-ord('A')
        row = int(self.selected[1:])-1
        column = max(0,min(size-1,column+dx))
        row = max(0,min(size-1,row+dy))
        cell = f'{chr(ord("A")+column)}{row+1}'
        if cell != self.selected:
            self.select_character(cell, open_popup=False)

    def _clicked_button(self, pos, *keys):
        for key in keys:
            entry = self.buttons.get(key)
            if entry and entry[1] and entry[0].collidepoint(pos):
                return key
        return None

    def _event_home(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.resume_game()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._clicked_button(
                event.pos,
                'home_play', 'home_stages', 'home_help', 'home_help_cta', 'home_music', 'home_quit'
            )
            if clicked == 'home_play':
                self.resume_game()
            elif clicked == 'home_stages':
                self.open_stage_select('home')
            elif clicked in ('home_help', 'home_help_cta'):
                self.action('help')
            elif clicked == 'home_music':
                self.action('choose_music')
            elif clicked == 'home_quit':
                return False
        return True

    def _event_stage_select(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.screen_state = self.stage_select_return
            if self.screen_state == 'game':
                self.last_timer_tick = pygame.time.get_ticks()
            return True
        if event.type == pygame.MOUSEWHEEL:
            self.stage_select_scroll = max(
                0, min(self.stage_select_max_scroll, self.stage_select_scroll - event.y * 64)
            )
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._clicked_button(
                event.pos,
                'stage_back', 'stage_filter_all', 'stage_filter_3', 'stage_filter_4', 'stage_filter_5'
            )
            if clicked == 'stage_back':
                self.screen_state = self.stage_select_return
                if self.screen_state == 'game':
                    self.last_timer_tick = pygame.time.get_ticks()
                return True
            if clicked and clicked.startswith('stage_filter_'):
                value = clicked.split('_')[-1]
                self.stage_filter = 'all' if value == 'all' else int(value)
                self.stage_select_scroll = 0
                return True
            for rect, path in self.stage_select_hits:
                if rect.collidepoint(event.pos):
                    self.load(path)
                    break
        return True

    def _event_pause(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.resume_game()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._clicked_button(
                event.pos,
                'pause_resume', 'pause_restart', 'pause_stages',
                'pause_music', 'pause_help', 'pause_home', 'pause_quit'
            )
            if clicked == 'pause_resume':
                self.resume_game()
            elif clicked == 'pause_restart':
                self.action('restart')
            elif clicked == 'pause_stages':
                self.open_stage_select('pause')
            elif clicked == 'pause_music':
                self.action('choose_music')
            elif clicked == 'pause_help':
                self.action('help')
            elif clicked == 'pause_home':
                self.go_home()
            elif clicked == 'pause_quit':
                return False
        return True

    def _event_cleared(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cleared_dismissed = True
                self.resume_game()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                next_path = self.next_stage_path()
                if next_path is not None:
                    self.load(next_path)
                else:
                    self.open_stage_select('cleared')
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._clicked_button(
                event.pos, 'cleared_next', 'cleared_replay', 'cleared_board', 'cleared_stages', 'cleared_home'
            )
            if clicked == 'cleared_next':
                next_path = self.next_stage_path()
                if next_path is not None:
                    self.load(next_path)
                else:
                    self.open_stage_select('cleared')
            elif clicked == 'cleared_replay':
                self.action('restart')
            elif clicked == 'cleared_board':
                self.cleared_dismissed = True
                self.resume_game()
            elif clicked == 'cleared_stages':
                self.open_stage_select('cleared')
            elif clicked == 'cleared_home':
                self.go_home()
        return True

    def event(self, event):
        if self.output_surface is not None and hasattr(event, 'pos'):
            attributes = dict(event.dict)
            attributes['pos'] = self.logical_position(event.pos)
            event = pygame.event.Event(event.type, attributes)
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.WINDOWFOCUSLOST:
            self.stage_drag_offset = None
        if self.notification:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.notification = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                button = self.buttons.get('dismiss_notification')
                if button and button[0].collidepoint(event.pos):
                    self.notification = None
            return True
        if self.music_picker:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.music_picker = False
            elif event.type == pygame.MOUSEWHEEL:
                self.music_scroll = max(0,min(max(0,len(self.music_tracks)-7),self.music_scroll-event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                close = self.buttons.get('close_music')
                toggle = self.buttons.get('music')
                if close and close[0].collidepoint(event.pos):
                    self.music_picker = False
                elif toggle and toggle[1] and toggle[0].collidepoint(event.pos):
                    self.action('music')
                else:
                    for rect, path in self.music_hits:
                        if rect.collidepoint(event.pos):
                            self.select_music(path)
                            break
            return True
        if self.help_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.help_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                button = self.buttons.get('close_help')
                if button and button[0].collidepoint(event.pos):
                    self.help_open = False
            return True
        if self.screen_state == 'home':
            return self._event_home(event)
        if self.screen_state == 'stage_select':
            return self._event_stage_select(event)
        if self.screen_state == 'pause':
            return self._event_pause(event)
        if self.screen_state == 'cleared':
            return self._event_cleared(event)
        if self.inspector.open and not (self.music_picker or self.help_open or self.picker or self.verdict_cell):
            pointer = getattr(event, 'pos', self.mouse_position())
            over_panel = pointer[0] >= cfg.WINDOW_SIZE[0]
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.inspector.focused = over_panel
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.set_inspector_open(False)
                    return True
                elif self.inspector.focused and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.browse_history(-1 if event.key == pygame.K_LEFT else 1)
                elif self.inspector.focused and event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.inspector.scroll += -60 if event.key == pygame.K_UP else 60
            elif event.type == pygame.MOUSEWHEEL and over_panel:
                self.inspector.scroll += -event.y*60
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and over_panel:
                for key in ('agent_close','agent_prev','agent_next','agent_live',
                            'agent_analyze','agent_step','agent_auto','agent_reference','agent_logic','agent_heuristic'):
                    entry = self.buttons.get(key)
                    if entry and entry[1] and entry[0].collidepoint(event.pos):
                        if key == 'agent_close':
                            self.set_inspector_open(False)
                        elif key in ('agent_prev','agent_next'):
                            self.browse_history(-1 if key == 'agent_prev' else 1)
                        else:
                            self.action('auto' if key == 'agent_auto' else key)
                        break
            self.inspector.scroll = max(0, min(self.inspector.scroll, self.inspector.max_scroll))
            if ((event.type != pygame.KEYDOWN and over_panel) or
                    (event.type == pygame.KEYDOWN and self.inspector.focused)):
                return True
        if event.type == pygame.KEYDOWN and not self.picker:
            directions = {pygame.K_w:(0,-1),pygame.K_UP:(0,-1),
                          pygame.K_s:(0,1),pygame.K_DOWN:(0,1),
                          pygame.K_a:(-1,0),pygame.K_LEFT:(-1,0),
                          pygame.K_d:(1,0),pygame.K_RIGHT:(1,0)}
            if event.key in directions:
                dx, dy = directions[event.key]
                if self.verdict_cell:
                    if dy > 0:
                        self.verdict_choice = 'cancel_verdict'
                    elif dy < 0 and self.verdict_choice == 'cancel_verdict':
                        self.verdict_choice = 'innocent'
                    elif dx:
                        self.verdict_choice = 'innocent' if dx < 0 else 'criminal'
                else:
                    self.move_selection(dx, dy)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.verdict_cell:
                    if self.verdict_choice == 'cancel_verdict':
                        self.verdict_cell = None
                    else:
                        self.action(self.verdict_choice)
                else:
                    self.open_verdict()
                return True
        if self.verdict_cell:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.verdict_cell = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.verdict_rect and not self.verdict_rect.collidepoint(event.pos):
                    self.verdict_cell = None
                else:
                    for key in ('criminal', 'innocent', 'cancel_verdict'):
                        entry = self.buttons.get(key)
                        if entry and entry[1] and entry[0].collidepoint(event.pos):
                            if key == 'cancel_verdict':
                                self.verdict_cell = None
                            else:
                                self.action(key)
                            break
            return True
        if self.picker:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.stage_drag_offset = None
            elif event.type == pygame.MOUSEMOTION and self.stage_drag_offset is not None:
                self.drag_stage_scroll(event.pos[1])
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.picker = False
                    self.stage_drag_offset = None
            elif event.type == pygame.MOUSEWHEEL:
                self.file_scroll = max(0, min(max(0, len(self.files)-8), self.file_scroll-event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.stage_scroll_track and self.stage_scroll_track.inflate(8,0).collidepoint(event.pos):
                    self.stage_drag_offset = (event.pos[1]-self.stage_scroll_thumb.top
                                              if self.stage_scroll_thumb.collidepoint(event.pos)
                                              else self.stage_scroll_thumb.height//2)
                    self.drag_stage_scroll(event.pos[1])
                    return True
                close = self.buttons.get('close_stage')
                if close and close[0].collidepoint(event.pos):
                    self.picker = False
                    self.stage_drag_offset = None
                    return True
                for rect, path in self.file_hits:
                    if rect.collidepoint(event.pos):
                        self.load(path)
                        break
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.open_pause()
            return True
        if event.type == pygame.MOUSEWHEEL and self.clue_panel.collidepoint(self.mouse_position()):
            movement = getattr(event,'precise_y',event.y)
            self.clue_scroll_target = max(0, min(self.max_scroll, self.clue_scroll_target-movement*cfg.CLUE_SCROLL_STEP))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for cell, rect in self.cards.items():
                if rect.collidepoint(event.pos):
                    self.select_character(cell)
            for rect, clue in self.clue_hits:
                if rect.collidepoint(event.pos):
                    self.clue_id = clue.id if self.clue_id != clue.id else None
            for key, (rect, enabled) in self.buttons.items():
                if enabled and rect.collidepoint(event.pos):
                    self.action(key)
                    break
        return True

    def drag_stage_scroll(self, mouse_y):
        track = self.stage_scroll_track
        thumb = self.stage_scroll_thumb
        if track is None or thumb is None:
            return
        travel = track.height-thumb.height
        if travel > 0:
            position = max(0,min(travel,mouse_y-self.stage_drag_offset-track.y))
            self.file_scroll = round(position/travel*max(0,len(self.files)-8))

    def draw(self):
        tick = pygame.time.get_ticks()
        self.hover_delta = min(50, max(0,tick-self.hover_time))
        self.hover_time = tick
        self.maybe_open_cleared(tick)
        self.hover_scope = 'main'
        self.pointer_hover = False
        self.screen.fill(BG)
        if self.background:
            self.screen.blit(self.background, (0, 0))
        self.buttons = {}
        if self.screen_state == 'home':
            screens.draw_home(self)
            if self.help_open:
                self.draw_help()
            if self.music_picker:
                self.draw_music_picker()
        elif self.screen_state == 'stage_select':
            screens.draw_stage_select(self)
            if self.help_open:
                self.draw_help()
            if self.music_picker:
                self.draw_music_picker()
        else:
            self._draw_gameplay(tick)
            if self.inspector.open:
                self.inspector.draw(self)
            if self.screen_state == 'game':
                if self.picker:
                    self.draw_picker()
                if self.verdict_cell:
                    self.draw_verdict_popup()
            elif self.screen_state == 'pause':
                screens.draw_pause_overlay(self)
            elif self.screen_state == 'cleared':
                screens.draw_cleared_overlay(self)
            if self.help_open:
                self.draw_help()
            if self.music_picker:
                self.draw_music_picker()
            if self.notification:
                self.draw_notification()
        cursor = pygame.SYSTEM_CURSOR_HAND if self.pointer_hover else pygame.SYSTEM_CURSOR_ARROW
        if cursor != self.last_cursor and pygame.display.get_driver() != 'dummy':
            pygame.mouse.set_cursor(cursor)
            self.last_cursor = cursor
        if self.output_surface is not None:
            pygame.transform.smoothscale(self.screen, self.output_surface.get_size(), self.output_surface)
        pygame.display.flip()

    def _draw_gameplay(self, now):
        history_record = self.inspector.selected_record(self.observer)
        state = self.public_view_state()
        known = dict(state.verdicts)
        if self.last_revealed is not None and history_record is None:
            for cell in known.keys() - self.last_revealed:
                self.reveal_started[cell] = now
        self.last_revealed = set(known) if history_record is None else None
        public_clues = dict(zip((cell for cell, _ in state.verdicts), state.clues))
        self.label("GRIDUCTIVE", (30, 22), ACCENT, self.heading)
        self.label(self.engine.title, (30, 63))
        self.label(f"{len(known)}/{len(state.characters)} proved", (626, 65), MUTED)
        screens.draw_game_hud(self)
        self.button('agent', 'Agent', pygame.Rect(790,22,140,38))
        self.button('choose_music', 'Music', pygame.Rect(942,22,130,38))
        self.button('help', '?', pygame.Rect(1107,22,38,38))
        self.label("Only proved verdicts reveal clues.", (790, 70), MUTED, self.tiny)
        clue = next((c for c in state.clues if c.id == self.clue_id), None)
        highlighted = set(clue.referenced_cells) if clue else set()
        self.cards = {}
        gap = cfg.CARD_GAP
        width = (cfg.BOARD_WIDTH-gap*(state.size-1))//state.size
        height = (cfg.BOARD_HEIGHT-gap*(state.size-1))//state.size
        for col in range(state.size):
            self.label(chr(65+col), (cfg.BOARD_X+col*(width+gap)+width//2, cfg.BOARD_Y-28), MUTED)
        for index, char in enumerate(state.characters):
            row, col = divmod(index, state.size)
            rect = pygame.Rect(cfg.BOARD_X+col*(width+gap), cfg.BOARD_Y+row*(height+gap), width, height)
            self.cards[char.cell] = rect
            if col == 0:
                self.label(str(row+1), (cfg.BOARD_X-30, rect.centery-10), MUTED)
            status = known.get(char.cell)
            color = PANEL if status is None else (cfg.CRIMINAL_CARD if status == Status.CRIMINAL else cfg.INNOCENT_CARD)
            focused = (char.cell == (history_record.move_cell if history_record else self.selected) or
                       (char.cell == self.auto_focus_cell and now < self.auto_focus_until))
            amount = self.hover('card-'+char.cell, rect,
                                status is not None or (not self.busy and not self.auto and history_record is None), focused=focused)
            rect = rect.move(0,-round(cfg.HOVER_LIFT*amount))
            color = tuple(round(a+(b-a)*amount*.15) for a,b in zip(color,ACCENT))
            pygame.draw.rect(self.screen, color, rect, border_radius=cfg.CARD_RADIUS)
            if amount > 0:
                pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=cfg.CARD_RADIUS)
            if char.cell in highlighted:
                pygame.draw.rect(self.screen, cfg.HIGHLIGHT, rect, 3, border_radius=cfg.CARD_RADIUS)
            progress = 1.0 if history_record else reveal_progress(self.reveal_started.get(char.cell), now)
            draw_character(self, char, rect, status, public_clues.get(char.cell), progress, state.size)
        pygame.draw.rect(self.screen, PANEL, self.clue_panel, border_radius=12)
        pygame.draw.rect(self.screen, (65,85,102), self.clue_panel, 1, border_radius=12)
        self.label("REVEALED CLUES", (794, 108), ACCENT)
        self.label("Click to highlight cells. Scroll for more.", (794, 135), MUTED, self.small)
        viewport = self.clue_viewport
        heights = [self.clue_height(clue) for clue in state.clues]
        total_height = sum(heights)+8*max(0,len(heights)-1)
        self.max_scroll = max(0,total_height-viewport.height)
        self.clue_scroll_target = max(0,min(self.max_scroll,self.clue_scroll_target))
        self.clue_scroll = max(0,min(self.max_scroll,self.clue_scroll))
        blend = 1-math.exp(-self.hover_delta/max(1,cfg.CLUE_SCROLL_TIME_MS))
        self.clue_scroll += (self.clue_scroll_target-self.clue_scroll)*blend
        if abs(self.clue_scroll_target-self.clue_scroll)<.1:
            self.clue_scroll = self.clue_scroll_target
        self.screen.set_clip(viewport)
        self.clue_hits = []
        y = viewport.y-round(self.clue_scroll)
        for clue,h in zip(state.clues,heights):
            text = self.clue_text(clue)
            rect = pygame.Rect(viewport.x, y, viewport.width, h)
            pygame.draw.rect(self.screen, (60, 58, 44) if clue.id == self.clue_id else BG, rect, border_radius=8)
            self.label('Personal remark' if clue.kind == 'QUOTE' else clue.id, (rect.x+12, rect.y+10), MUTED if clue.kind == 'QUOTE' else ACCENT, self.small)
            self.wrapped(text, pygame.Rect(rect.x+12, rect.y+32, rect.width-24, h-32))
            if rect.colliderect(viewport):
                self.clue_hits.append((rect.clip(viewport), clue))
            y += h+8
        self.screen.set_clip(None)
        if self.max_scroll:
            track = pygame.Rect(1145,viewport.y,4,viewport.height)
            pygame.draw.rect(self.screen,BG,track,border_radius=2)
            thumb_height = max(28,round(viewport.height*viewport.height/total_height))
            thumb_y = track.y+round((track.height-thumb_height)*self.clue_scroll/self.max_scroll)
            pygame.draw.rect(self.screen,ACCENT,(track.x,thumb_y,track.width,thumb_height),border_radius=2)
        free = not self.busy and not self.auto and history_record is None
        self.button("stage", "Stage", pygame.Rect(790, 626, 170, 46), free)
        self.button("restart", "Restart", pygame.Rect(975, 626, 170, 46), free)
        self.button("hint", "Hint", pygame.Rect(790, 682, 170, 46), free and not self.engine.solved)
        self.button("auto", "Stop" if self.auto else "Auto Solve", pygame.Rect(975, 682, 170, 46), self.auto or (free and not self.engine.solved))
        message_y = min(cfg.MESSAGE_Y, self.screen.get_height()-72)
        pygame.draw.rect(self.screen, PANEL, (30, message_y, 1115, 60), border_radius=10)
        message = (f'HISTORY - call {history_record.number}: board after action. Return to Live to continue.'
                   if history_record else self.message)
        self.wrapped(message, pygame.Rect(46, message_y+11, 1080, 44), font=self.font)

    def select_music(self, path):
        self.message = self.music.select(path)

    def draw_music_picker(self):
        self.hover_scope = 'music'
        veil = pygame.Surface(self.screen.get_size(),pygame.SRCALPHA)
        veil.fill((0,0,0,180))
        self.screen.blit(veil,(0,0))
        rect = pygame.Rect(0,0,700,540)
        rect.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen,PANEL,rect,border_radius=14)
        self.label('Music',(rect.x+24,rect.y+22),ACCENT,self.heading)
        self.button('music', 'Music On' if self.music.enabled else 'Music Off',
                    pygame.Rect(rect.right-174,rect.y+22,150,40))
        self.label('Select a track to play. Scroll for more.',(rect.x+24,rect.y+70),MUTED,self.small)
        self.music_hits = []
        for index,path in enumerate(self.music_tracks[self.music_scroll:self.music_scroll+7]):
            row = pygame.Rect(rect.x+24,rect.y+110+index*44,rect.width-48,38)
            current = '  (selected)' if path==self.music.path else ''
            self.button('track-'+str(path),path.stem+current,row)
            self.music_hits.append((row,path))
        if not self.music_tracks:
            self.label('Add music to assets/sounds/.',(rect.x+24,rect.y+116),MUTED)
        self.wrapped(self.message,pygame.Rect(rect.x+24,rect.bottom-112,rect.width-48,48),font=self.small)
        self.button('close_music','Close',pygame.Rect(rect.right-174,rect.bottom-58,150,42))

    def draw_notification(self):
        self.hover_scope = 'notice'
        result = self.notification
        contradicted = result.code == 'CONTRADICTED'
        color = (245, 139, 139) if contradicted else cfg.HIGHLIGHT
        title = 'Incorrect verdict' if contradicted else 'Not enough evidence'
        character = next((c for c in self.engine.public_state().characters if c.cell == result.cell), None)
        name = character.name if character else 'this character'
        text = (f'The revealed clues prove the opposite verdict for {name}. '
                'Read the clues again and try another verdict.' if contradicted else
                f'The revealed clues do not yet prove whether {name} is criminal or innocent. '
                'Solve another character first, or use Hint to find a provable move.')
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 165))
        self.screen.blit(veil, (0, 0))
        rect = pygame.Rect(0, 0, 520, 240)
        rect.center = main_canvas_rect().center
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=14)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=14)
        self.label(title, (rect.x+24, rect.y+20), color, self.font)
        self.wrapped(text, pygame.Rect(rect.x+24, rect.y+62, rect.width-48, 100), font=self.font)
        self.button('dismiss_notification', 'Continue', pygame.Rect(rect.centerx-85, rect.bottom-61, 170, 44), style='primary')

    def draw_verdict_popup(self):
        self.hover_scope = 'verdict'
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 135))
        self.screen.blit(veil, (0, 0))
        card = self.cards[self.verdict_cell]
        rect = pygame.Rect(card.centerx-180, card.centery-92, 360, 184)
        rect.clamp_ip(self.screen.get_rect().inflate(-32, -32))
        self.verdict_rect = rect
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=12)
        character = next(c for c in self.engine.public_state().characters if c.cell == self.verdict_cell)
        self.wrapped(f'{character.name} ({character.cell})', pygame.Rect(rect.x+18, rect.y+15, rect.width-36, 28), font=self.font)
        self.label('What can you prove?', (rect.x+18, rect.y+49), MUTED, self.small)
        enabled = not self.busy and not self.auto
        self.button('innocent', 'Innocent', pygame.Rect(rect.x+18, rect.y+78, 155, 44), enabled,
                    focused=self.verdict_choice == 'innocent')
        self.button('criminal', 'Criminal', pygame.Rect(rect.x+187, rect.y+78, 155, 44), enabled,
                    focused=self.verdict_choice == 'criminal')
        self.button('cancel_verdict', 'Cancel', pygame.Rect(rect.x+119, rect.y+132, 122, 38),
                    focused=self.verdict_choice == 'cancel_verdict')

    def draw_picker(self):
        self.hover_scope = 'stage'
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 190))
        self.screen.blit(veil, (0, 0))
        pygame.draw.rect(self.screen, PANEL, (190, 115, 800, 565), border_radius=14)
        self.label('Choose a stage', (215, 138), ACCENT, self.heading)
        self.label('Select a stage. Scroll or drag the bar to see more.', (215, 185), MUTED, self.small)
        self.file_hits = []
        for i, path in enumerate(self.files[self.file_scroll:self.file_scroll+8]):
            rect = pygame.Rect(215, 223+i*44, 750, 38)
            self.button('stage-'+str(path), self.stage_names[path], rect)
            self.file_hits.append((rect, path))
        self.stage_scroll_track = self.stage_scroll_thumb = None
        if len(self.files) > 8:
            track = pygame.Rect(974,223,8,346)
            thumb_height = max(30,round(track.height*8/len(self.files)))
            offset = round((track.height-thumb_height)*self.file_scroll/(len(self.files)-8))
            thumb = pygame.Rect(track.x,track.y+offset,track.width,thumb_height)
            self.stage_scroll_track, self.stage_scroll_thumb = track, thumb
            hovered = self.hover('stage-scrollbar',track.inflate(8,0))
            pygame.draw.rect(self.screen,BG,track,border_radius=4)
            color = ACCENT if hovered or self.stage_drag_offset is not None else MUTED
            pygame.draw.rect(self.screen,color,thumb,border_radius=4)
        if not self.files:
            self.label('No playable stages found.', (215, 230), MUTED)
        self.button('close_stage', 'Close', pygame.Rect(815, 594, 150, 44))
        if self.message.startswith('Stage unavailable') or self.message.startswith('LOAD ERROR'):
            self.wrapped(self.message, pygame.Rect(215, 646, 750, 25), font=self.small)

    def draw_help(self):
        self.hover_scope = 'help'
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 180))
        self.screen.blit(veil, (0, 0))
        rect = pygame.Rect(0, 0, 680, 610)
        rect.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=14)
        self.label('How to play', (rect.x+28, rect.y+24), ACCENT, self.heading)
        sections = [
            ('Read the revealed clues', 'Every character is criminal or innocent. Every clue is true, including clues from criminals. Personal remarks carry no evidence.'),
            ('Choose a verdict', 'WASD or arrows select a card; Enter opens its choices. Innocent is selected first. Use Left/Right for Innocent/Criminal, Down for Cancel, and Enter to confirm. Escape closes the choices. You can also click cards and choices.'),
            ('Reveal the next lead', 'An accepted verdict reveals a new clue. Click a solved card or a clue in the side panel to highlight the cells it refers to.'),
            ('Understand the wording', 'Neighbors include diagonals. Connected means linked horizontally or vertically within the region. Shared neighbors touch both people. Exactly means that number, at least means that many or more, and odd means 1, 3, 5 and so on.'),
            ('Keep investigating', 'Incorrect verdict means the opposite is proved. Not enough evidence means neither verdict is proved yet. Continue with another card or use Hint.'),
            ('Use the controls', 'Stage chooses a level. Restart resets its reveals. Hint points to a provable character. Auto Solve plays proved moves. Agent opens live reasoning and one-move solving. Music opens track selection and the audio on/off toggle.'),
        ]
        y = rect.y+82
        for title, text in sections:
            self.label(title, (rect.x+28,y), ACCENT, self.small)
            y += 23
            lines = self.lines(text, rect.width-56, self.small)
            height = len(lines)*self.small.get_linesize()
            self.wrapped(text, pygame.Rect(rect.x+28,y,rect.width-56,height), font=self.small)
            y += height+15
        self.button('close_help', 'Got it', pygame.Rect(rect.right-178, rect.bottom-62, 150, 44))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        try:
            self.draw()
            while running:
                for event in pygame.event.get():
                    if not self.event(event):
                        running = False
                self.update()
                self.draw()
                clock.tick(60)
        finally:
            self.music.stop()
