"""Pygame view with a single daemon worker for potentially slow analysis."""
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
import asyncio
import sys
import pygame
import re
import hashlib
import math
from griductive.ui.music import Music
from griductive.domain.models import Status
from griductive.engine.game import GameEngine, Outcome
from griductive.engine.puzzle import load_puzzle
from griductive.ui.assets import Artwork, ui_font
from griductive.ui import config as cfg
from griductive.ui.character_card import draw_character, reveal_progress
from griductive.ui.config import BG, PANEL, TEXT, MUTED, ACCENT



class GameWindow:
    def __init__(self, path, factory, puzzle_dir, analyzer_name):
        flags = 0 if sys.platform == 'emscripten' else pygame.SCALED
        self.screen = pygame.display.set_mode(cfg.WINDOW_SIZE, flags)
        pygame.display.set_caption("Griductive | Deduction desk")
        self.font = ui_font(cfg.FONT_SIZE)
        self.small = ui_font(cfg.SMALL_FONT_SIZE)
        self.tiny = ui_font(cfg.TINY_FONT_SIZE)
        self.heading = ui_font(cfg.HEADING_FONT_SIZE, heading=True)
        self.artwork = Artwork()
        self.background = self.artwork.background(self.screen.get_size())
        self.reveal_started = {}
        self.last_revealed = None
        self.auto_focus_cell = None
        self.auto_focus_until = 0
        self.factory, self.puzzle_dir, self.analyzer_name = factory, Path(puzzle_dir), analyzer_name
        self.engine = GameEngine(self.artwork.cast_puzzle(load_puzzle(path)), factory())
        self.queue = Queue()
        self.analysis_task = None
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

    def label(self, text, pos, color=TEXT, font=None):
        self.screen.blit((font or self.font).render(str(text), True, color), pos)

    def clue_text(self, clue):
        if clue.kind == 'QUOTE':
            pool = cfg.CHARACTER_QUOTES or ['...']
            seed = clue.id+'|'+self.engine.title+'|'+','.join(c.name for c in self.engine.public_state().characters)
            index = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:4],'big') % len(pool)
            return pool[index]
        names = {char.cell: char.name for char in self.engine.public_state().characters}
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

    def button(self, key, text, rect, enabled=True, focused=False):
        self.buttons[key] = (rect, enabled)
        amount = self.hover(key, rect, enabled, focused=focused)
        visible = rect.move(0, -round(cfg.HOVER_LIFT*amount))
        base = cfg.BUTTON if enabled else cfg.BUTTON_DISABLED
        color = tuple(round(a+(b-a)*amount*.3) for a,b in zip(base,ACCENT))
        pygame.draw.rect(self.screen, color, visible, border_radius=8)
        if amount > 0:
            pygame.draw.rect(self.screen, ACCENT, visible, max(1,round(amount*2)), border_radius=8)
        if focused:
            pygame.draw.rect(self.screen, ACCENT, visible, 2, border_radius=8)
        font = self.small if self.font.size(text)[0] > rect.width-24 else self.font
        self.wrapped(text, visible.inflate(-24,-14), TEXT if enabled else MUTED, font)

    def hover(self, key, rect, enabled=True, focused=False):
        active_scope = ('notice' if self.notification else 'music' if self.music_picker else 'help' if self.help_open else
                        'verdict' if self.verdict_cell else 'stage' if self.picker else 'main')
        hovered = enabled and self.hover_scope == active_scope and rect.collidepoint(pygame.mouse.get_pos())
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
        self.busy = True
        self.message = "Checking the revealed information..."
        if sys.platform == 'emscripten':
            self.analysis_task = asyncio.create_task(self.run_browser_action(action))
            return
        def run():
            try:
                result = action()
            except Exception as exc:
                result = Outcome("ERROR", f"{type(exc).__name__}: {exc}")
            self.queue.put(result)
        Thread(target=run, daemon=True).start()

    async def run_browser_action(self, action):
        try:
            await asyncio.sleep(0)
            await self.engine.prepare_analysis()
            result = action()
        except Exception as exc:
            result = Outcome('ERROR', f'{type(exc).__name__}: {exc}')
        self.queue.put(result)

    def update(self):
        try:
            result = self.queue.get_nowait()
        except Empty:
            result = None
        if result:
            self.busy = False
            self.message = f"{result.code}: {result.message}"
            if result.code in ('CONTRADICTED', 'NOT_PROVABLE'):
                self.notification = result
                self.verdict_cell = None
            if result.cell:
                self.selected = result.cell
                if self.auto and result.code in ('ACCEPTED','SOLVED'):
                    self.auto_focus_cell = result.cell
                    self.auto_focus_until = pygame.time.get_ticks()+max(cfg.REVEAL_DURATION_MS,cfg.HOVER_DURATION_MS*2)+150
            if result.code != "ACCEPTED":
                self.auto = False
            self.next_step = pygame.time.get_ticks()+cfg.REVEAL_DURATION_MS+150
        if self.auto and not self.busy and pygame.time.get_ticks() >= self.next_step:
            self.start(self.engine.step)

    def load(self, path):
        try:
            engine = GameEngine(self.artwork.cast_puzzle(load_puzzle(path)), self.factory())
        except Exception as exc:
            self.message = f"LOAD ERROR: {exc}"
            return
        self.engine = engine
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
        self.message = "Puzzle loaded. Select a card or ask for a hint."

    def action(self, key):
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
            self.last_revealed = None
            self.auto_focus_cell = None
            self.reveal_started.clear()
            self.auto = False
            self.selected, self.clue_id = 'A1', None
            self.verdict_cell = None
            self.clue_scroll = 0
            self.clue_scroll_target = 0.0
            self.message = "Restarted with the original face-up cards."
        elif key == "hint":
            self.start(self.engine.hint)
        elif key == "auto":
            self.auto = not self.auto
            if not self.auto:
                self.auto_focus_cell = None
            self.message = "Auto Solve started." if self.auto else "Stopped; the current step may finish."
        elif key in ("criminal", "innocent") and self.verdict_cell:
            cell, status = self.verdict_cell, Status(key.upper())
            self.verdict_cell = None
            self.start(lambda: self.engine.submit_verdict(cell, status))

    def open_verdict(self):
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
        public = self.engine.public_state()
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

    def event(self, event):
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
                if close and close[0].collidepoint(event.pos):
                    self.music_picker = False
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
            return False
        if event.type == pygame.MOUSEWHEEL and self.clue_panel.collidepoint(pygame.mouse.get_pos()):
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
        self.hover_scope = 'main'
        self.pointer_hover = False
        self.screen.fill(BG)
        if self.background:
            self.screen.blit(self.background, (0, 0))
        self.buttons = {}
        state = self.engine.public_state()
        known = dict(state.verdicts)
        now = pygame.time.get_ticks()
        if self.last_revealed is not None:
            for cell in known.keys() - self.last_revealed:
                self.reveal_started[cell] = now
        self.last_revealed = set(known)
        public_clues = dict(zip((cell for cell, _ in state.verdicts), state.clues))
        self.label("GRIDUCTIVE", (30, 22), ACCENT, self.heading)
        self.label(self.engine.title, (30, 63))
        self.label(f"{len(known)}/{len(state.characters)} proved", (626, 65), MUTED)
        self.button('music', 'Music On' if self.music.enabled else 'Music Off', pygame.Rect(790,22,140,38))
        self.button('choose_music', 'Tracks', pygame.Rect(942,22,130,38))
        self.button('help', '?', pygame.Rect(1107,22,38,38))
        self.label("Only proved verdicts reveal a clue.", (790, 62), MUTED, self.small)
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
            focused = (char.cell == self.selected or
                       (char.cell == self.auto_focus_cell and now < self.auto_focus_until))
            amount = self.hover('card-'+char.cell, rect,
                                status is not None or (not self.busy and not self.auto), focused=focused)
            rect = rect.move(0,-round(cfg.HOVER_LIFT*amount))
            color = tuple(round(a+(b-a)*amount*.15) for a,b in zip(color,ACCENT))
            pygame.draw.rect(self.screen, color, rect, border_radius=cfg.CARD_RADIUS)
            if amount > 0:
                pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=cfg.CARD_RADIUS)
            if char.cell in highlighted:
                pygame.draw.rect(self.screen, cfg.HIGHLIGHT, rect, 3, border_radius=cfg.CARD_RADIUS)
            progress = reveal_progress(self.reveal_started.get(char.cell), now)
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
        free = not self.busy and not self.auto
        self.button("stage", "Stage", pygame.Rect(790, 626, 170, 46), free)
        self.button("restart", "Restart", pygame.Rect(975, 626, 170, 46), free)
        self.button("hint", "Hint", pygame.Rect(790, 682, 170, 46), free and not self.engine.solved)
        self.button("auto", "Stop" if self.auto else "Auto Solve", pygame.Rect(975, 682, 170, 46), self.auto or (free and not self.engine.solved))
        message_y = min(cfg.MESSAGE_Y, self.screen.get_height()-72)
        pygame.draw.rect(self.screen, PANEL, (30, message_y, 1115, 60), border_radius=10)
        self.wrapped(self.message, pygame.Rect(46, message_y+11, 1080, 44), font=self.font)
        if self.picker:
            self.draw_picker()
        if self.verdict_cell:
            self.draw_verdict_popup()
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
        pygame.display.flip()

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
        self.label('Choose music',(rect.x+24,rect.y+22),ACCENT,self.heading)
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
        rect.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=14)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=14)
        self.label(title, (rect.x+24, rect.y+20), color, self.font)
        self.wrapped(text, pygame.Rect(rect.x+24, rect.y+62, rect.width-48, 100), font=self.font)
        self.button('dismiss_notification', 'Continue', pygame.Rect(rect.centerx-85, rect.bottom-61, 170, 44))

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
            ('Use the controls', 'Stage chooses a level. Restart resets its reveals. Hint points to a provable character. Auto Solve plays proved moves, and Stop pauses it. Music switches the ambient loop on or off.'),
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

    async def run_web(self):
        running = True
        try:
            while running:
                for event in pygame.event.get():
                    if not self.event(event):
                        running = False
                self.update()
                self.draw()
                await asyncio.sleep(0)
        finally:
            if self.analysis_task is not None:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass
            self.music.stop()
