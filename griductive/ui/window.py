"""Pygame view with a single daemon worker for potentially slow analysis."""
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
import pygame
from griductive.domain.models import Status
from griductive.engine.game import GameEngine, Outcome
from griductive.engine.puzzle import load_puzzle

BG, PANEL = (17, 24, 34), (29, 40, 54)
TEXT, MUTED, ACCENT = (233, 239, 246), (160, 178, 196), (104, 218, 192)


class GameWindow:
    def __init__(self, path, factory, puzzle_dir, analyzer_name):
        self.screen = pygame.display.set_mode((1180, 820))
        pygame.display.set_caption("Griductive | Deduction desk")
        self.font = pygame.font.Font(None, 24)
        self.small = pygame.font.Font(None, 20)
        self.heading = pygame.font.Font(None, 38)
        self.factory, self.puzzle_dir, self.analyzer_name = factory, Path(puzzle_dir), analyzer_name
        self.engine = GameEngine(load_puzzle(path), factory())
        self.queue = Queue()
        self.busy = self.auto = self.picker = False
        self.selected = self.clue_id = None
        self.clue_scroll = self.file_scroll = self.next_step = self.max_scroll = 0
        self.buttons, self.cards = {}, {}
        self.clue_hits, self.file_hits, self.files = [], [], []
        self.path_text = ""
        self.message = "Select a card, read the revealed clues, then call a verdict."

    def label(self, text, pos, color=TEXT, font=None):
        self.screen.blit((font or self.font).render(str(text), True, color), pos)

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

    def wrapped(self, text, rect, color=TEXT, font=None):
        font = font or self.small
        old = self.screen.get_clip()
        self.screen.set_clip(old.clip(rect))
        for i, line in enumerate(self.lines(text, rect.width, font)):
            self.label(line, (rect.x, rect.y+i*font.get_linesize()), color, font)
        self.screen.set_clip(old)

    def button(self, key, text, rect, enabled=True):
        self.buttons[key] = (rect, enabled)
        pygame.draw.rect(self.screen, (47, 70, 83) if enabled else (35, 43, 53), rect, border_radius=8)
        self.label(text, (rect.x+13, rect.y+13), TEXT if enabled else MUTED)

    def start(self, action):
        if self.busy:
            return
        self.busy = True
        self.message = "Checking the revealed information..."
        def run():
            try:
                result = action()
            except Exception as exc:
                result = Outcome("ERROR", f"{type(exc).__name__}: {exc}")
            self.queue.put(result)
        Thread(target=run, daemon=True).start()

    def update(self):
        try:
            result = self.queue.get_nowait()
        except Empty:
            result = None
        if result:
            self.busy = False
            self.message = f"{result.code}: {result.message}"
            if result.cell:
                self.selected = result.cell
            if result.code != "ACCEPTED":
                self.auto = False
            self.next_step = pygame.time.get_ticks()+450
        if self.auto and not self.busy and pygame.time.get_ticks() >= self.next_step:
            self.start(self.engine.step)

    def load(self, path):
        try:
            engine = GameEngine(load_puzzle(path), self.factory())
        except Exception as exc:
            self.message = f"LOAD ERROR: {exc}"
            return
        self.engine = engine
        self.selected = self.clue_id = None
        self.clue_scroll = 0
        self.picker = self.auto = False
        pygame.key.stop_text_input()
        self.message = "Puzzle loaded. Select a card or ask for a hint."

    def action(self, key):
        # Recheck current state: multiple mouse events can arrive before a redraw.
        if (self.busy or self.auto) and not (key == "auto" and self.auto):
            return
        if key == "load":
            self.files = sorted(self.puzzle_dir.rglob("*.json"))
            self.file_scroll, self.path_text, self.picker = 0, "", True
            pygame.key.start_text_input()
        elif key == "restart":
            self.engine.restart()
            self.auto = False
            self.selected = self.clue_id = None
            self.clue_scroll = 0
            self.message = "Restarted with the original face-up cards."
        elif key == "hint":
            self.start(self.engine.hint)
        elif key == "auto":
            self.auto = not self.auto
            self.message = "Auto Solve started." if self.auto else "Stopped; the current step may finish."
        elif key in ("criminal", "innocent") and self.selected:
            cell, status = self.selected, Status(key.upper())
            self.start(lambda: self.engine.submit_verdict(cell, status))

    def event(self, event):
        if event.type == pygame.QUIT:
            return False
        if self.picker:
            if event.type == pygame.TEXTINPUT:
                self.path_text += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.picker = False
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.path_text = self.path_text[:-1]
                elif event.key == pygame.K_RETURN and self.path_text.strip():
                    self.load(Path(self.path_text.strip().strip('"')).expanduser())
            elif event.type == pygame.MOUSEWHEEL:
                self.file_scroll = max(0, min(max(0, len(self.files)-8), self.file_scroll-event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, path in self.file_hits:
                    if rect.collidepoint(event.pos):
                        self.load(path)
                        break
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False
        if event.type == pygame.MOUSEWHEEL and pygame.mouse.get_pos()[0] > 760:
            self.clue_scroll = max(0, min(self.max_scroll, self.clue_scroll-event.y*40))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for cell, rect in self.cards.items():
                if rect.collidepoint(event.pos):
                    self.selected = cell
            for rect, clue in self.clue_hits:
                if rect.collidepoint(event.pos):
                    self.clue_id = clue.id if self.clue_id != clue.id else None
            for key, (rect, enabled) in self.buttons.items():
                if enabled and rect.collidepoint(event.pos):
                    self.action(key)
                    break
        return True

    def draw(self):
        self.screen.fill(BG)
        self.buttons = {}
        state = self.engine.public_state()
        known = dict(state.verdicts)
        self.label("GRIDUCTIVE", (30, 22), ACCENT, self.heading)
        self.label(self.engine.title, (30, 63))
        self.label(f"{len(known)}/{len(state.characters)} proved", (626, 65), MUTED)
        self.wrapped(self.analyzer_name, pygame.Rect(790, 32, 360, 28), MUTED)
        self.label("Only proved verdicts reveal a clue.", (790, 62), MUTED, self.small)
        clue = next((c for c in state.clues if c.id == self.clue_id), None)
        highlighted = set(clue.cells) if clue else set()
        self.cards = {}
        width, height = (700-10*(state.size-1))//state.size, (470-10*(state.size-1))//state.size
        for col in range(state.size):
            self.label(chr(65+col), (58+col*(width+10)+width//2, 104), MUTED)
        for index, char in enumerate(state.characters):
            row, col = divmod(index, state.size)
            rect = pygame.Rect(58+col*(width+10), 132+row*(height+10), width, height)
            self.cards[char.cell] = rect
            if col == 0:
                self.label(str(row+1), (28, rect.centery-10), MUTED)
            status = known.get(char.cell)
            color = PANEL if status is None else ((74, 46, 52) if status == Status.CRIMINAL else (30, 68, 66))
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            if char.cell in highlighted:
                pygame.draw.rect(self.screen, (242, 197, 100), rect, 3, border_radius=10)
            if char.cell == self.selected:
                pygame.draw.rect(self.screen, ACCENT, rect.inflate(-8, -8), 2, border_radius=7)
            self.wrapped(f"{char.cell}  {char.name}", pygame.Rect(rect.x+10, rect.y+10, width-20, 20))
            self.wrapped(char.profession, pygame.Rect(rect.x+10, rect.y+31, width-20, 20), MUTED)
            self.label(status.value if status else "UNRESOLVED", (rect.x+10, rect.y+54), ACCENT if status else MUTED, self.small)
            if height > 100:
                self.label("Clue revealed" if status else "Clue face-down", (rect.x+10, rect.bottom-29), MUTED, self.small)
        self.label("REVEALED CLUES", (790, 105), ACCENT)
        self.label("Click to highlight cells. Scroll for more.", (790, 132), MUTED, self.small)
        viewport = pygame.Rect(780, 160, 380, 440)
        self.screen.set_clip(viewport)
        self.clue_hits = []
        y = viewport.y-self.clue_scroll
        for clue in state.clues:
            h = 40+len(self.lines(clue.text, 340))*self.small.get_linesize()
            rect = pygame.Rect(786, y, 368, h)
            pygame.draw.rect(self.screen, (60, 58, 44) if clue.id == self.clue_id else PANEL, rect, border_radius=8)
            self.label(clue.id, (rect.x+12, rect.y+10), ACCENT, self.small)
            self.wrapped(clue.text, pygame.Rect(rect.x+12, rect.y+32, 340, h-32))
            if rect.colliderect(viewport):
                self.clue_hits.append((rect.clip(viewport), clue))
            y += h+8
        self.max_scroll = max(0, y+self.clue_scroll-viewport.bottom)
        self.screen.set_clip(None)
        free = not self.busy and not self.auto
        self.button("load", "Load", pygame.Rect(30, 626, 105, 46), free)
        self.button("restart", "Restart", pygame.Rect(145, 626, 115, 46), free)
        self.button("hint", "Hint", pygame.Rect(270, 626, 100, 46), free and not self.engine.solved)
        self.button("auto", "Stop" if self.auto else "Auto Solve", pygame.Rect(380, 626, 145, 46), self.auto or (free and not self.engine.solved))
        can_call = free and self.selected is not None and self.selected not in known
        self.button("criminal", "Criminal", pygame.Rect(790, 626, 170, 46), can_call)
        self.button("innocent", "Innocent", pygame.Rect(975, 626, 170, 46), can_call)
        self.label(f"Selected: {self.selected or 'none'}", (560, 642), MUTED)
        pygame.draw.rect(self.screen, PANEL, (30, 694, 1115, 90), border_radius=10)
        self.wrapped(self.message, pygame.Rect(46, 710, 1080, 66), font=self.font)
        if self.picker:
            self.draw_picker()
        pygame.display.flip()

    def draw_picker(self):
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 190))
        self.screen.blit(veil, (0, 0))
        pygame.draw.rect(self.screen, PANEL, (190, 115, 800, 565), border_radius=14)
        self.label("Load a puzzle", (215, 138), ACCENT, self.heading)
        self.label("Choose a file, or type its path and press Enter. Escape closes.", (215, 185), MUTED)
        self.file_hits = []
        for i, path in enumerate(self.files[self.file_scroll:self.file_scroll+8]):
            rect = pygame.Rect(215, 223+i*40, 750, 35)
            pygame.draw.rect(self.screen, BG, rect, border_radius=6)
            self.wrapped(str(path.relative_to(self.puzzle_dir)), rect.inflate(-16, -8))
            self.file_hits.append((rect, path))
        self.label("Path (scroll the list to see more puzzles):", (215, 554), MUTED, self.small)
        pygame.draw.rect(self.screen, BG, (215, 580, 750, 42), border_radius=5)
        self.wrapped(self.path_text or "Type a JSON file path...", pygame.Rect(225, 590, 730, 28))
        self.wrapped(self.message, pygame.Rect(215, 637, 750, 36))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        self.draw()
        while running:
            for event in pygame.event.get():
                if not self.event(event):
                    running = False
            self.update()
            self.draw()
            clock.tick(60)
