"""Bounded, thread-safe observations of live public-state analysis calls."""
from collections import deque
from dataclasses import dataclass, field, replace
from threading import Lock
from time import perf_counter
from griductive.domain.models import PublicState


@dataclass(frozen=True)
class ExperimentTotals:
    analysis_calls: int = 0
    sat_calls: int | None = 0
    decisions: int | None = 0
    propagations: int | None = 0
    backtracks: int | None = 0
    deduction_steps: int = 0
    reveal_waves: int = 0
    runtime_ms: float = 0.0


def add_counter(total, value):
    return total+value if total is not None and value is not None else None

@dataclass(frozen=True)
class Observation:
    number: int
    backend: str
    state: PublicState
    elapsed_ms: float
    consistent: bool | None
    verdicts: tuple
    queries: tuple
    cnf_counts: tuple | None
    sat_calls: int | None = None
    decisions: int | None = None
    propagations: int | None = None
    backtracks: int | None = None
    solver_runtime_ms: float | None = None
    totals: ExperimentTotals = field(default_factory=ExperimentTotals)
    after_state: PublicState | None = None
    move_cell: str | None = None
    note: str = ''
    outcome: str = ''
    new_clues: tuple = ()


class ObservedAnalyzer:
    """Delegates once per call; observations never use hidden puzzle data."""

    def __init__(self, analyzer, capacity=128):
        self.analyzer = analyzer
        self._records = deque(maxlen=capacity)
        self._lock = Lock()
        self._number = 0
        self._totals = ExperimentTotals()

    def snapshot(self):
        with self._lock:
            return tuple(self._records)

    def clear(self):
        with self._lock:
            self._records.clear()
            self._number = 0
            self._totals = ExperimentTotals()

    def analyze(self, state):
        started = perf_counter()
        result, error = None, ''
        try:
            result = self.analyzer.analyze(state)
            return result
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            elapsed_ms = (perf_counter()-started)*1000
            trace = getattr(self.analyzer, 'last_trace_step', None)
            queries = tuple((q.cell, q.assumption_type, q.outcome, q.entailed)
                            for q in getattr(trace, 'sat_queries', ()))
            backend = getattr(self.analyzer, 'last_backend', type(self.analyzer).__name__)
            note = error or getattr(self.analyzer, 'last_fallback_reason', '') or ''
            counts = getattr(self.analyzer, 'last_cnf_counts', None)
            if counts is None:
                # Diagnostic encoding for comparison, never used as hidden knowledge.
                # Keep its overhead outside the measured analysis runtime.
                try:
                    from griductive.logic.encoder import encode
                    cnf = encode(state)
                    counts = (cnf.num_primary_vars, cnf.num_aux_vars, cnf.num_clauses)
                except Exception:
                    pass
            from griductive.engine.reference import ReferenceAnalyzer
            sat_calls = getattr(self.analyzer, 'last_sat_calls',
                                0 if isinstance(self.analyzer, ReferenceAnalyzer) else None)
            metrics = getattr(self.analyzer, 'last_solver_metrics', {})
            counters = {key: metrics.get(key) if sat_calls else None
                        for key in ('decisions','propagations','backtracks')}
            with self._lock:
                self._number += 1
                old = self._totals
                self._totals = replace(
                    old, analysis_calls=old.analysis_calls+1,
                    sat_calls=add_counter(old.sat_calls, sat_calls),
                    runtime_ms=old.runtime_ms+elapsed_ms,
                    **{key: add_counter(getattr(old,key), counters[key]) if sat_calls != 0
                       else getattr(old,key) for key in counters})
                self._records.append(Observation(
                    self._number, backend, state, elapsed_ms,
                    getattr(result, 'consistent', None),
                    tuple(getattr(result, 'verdicts', ())), queries,
                    counts, sat_calls=sat_calls, **counters,
                    solver_runtime_ms=getattr(self.analyzer,'last_solver_runtime_ms',None),
                    totals=self._totals, note=note))

    def finish_action(self, outcome, public_state):
        with self._lock:
            if not self._records:
                return
            record = self._records[-1]
            if record.after_state is not None:
                return  # UI completion can only count a reveal once.
            old_ids = {c.id for c in record.state.clues}
            added = len(set(dict(public_state.verdicts))-set(dict(record.state.verdicts)))
            accepted = outcome.code in ('ACCEPTED','SOLVED') and added > 0
            if accepted:
                self._totals = replace(self._totals,
                                       deduction_steps=self._totals.deduction_steps+added,
                                       reveal_waves=self._totals.reveal_waves+1)
            self._records[-1] = replace(
                record, outcome=f'{outcome.code}: {outcome.cell or ""} {outcome.message}',
                after_state=public_state, move_cell=outcome.cell, totals=self._totals,
                new_clues=tuple(c.id for c in public_state.clues if c.id not in old_ids))


class AgentInspector:
    def __init__(self):
        self.open = False
        self.focused = True
        self.index = -1  # Follow the newest call until the user browses history.
        self.scroll = 0
        self.max_scroll = 0

    def reset(self):
        self.index, self.scroll = -1, 0

    def selected_record(self, observer):
        records = observer.snapshot()
        if not self.open or self.index < 0 or not records:
            return None
        return records[min(self.index, len(records)-1)]

    def browse(self, amount, count):
        current = count-1 if self.index < 0 else min(self.index, count-1)
        self.index = max(0, min(count-1, current+amount)) if count else -1
        if self.index == count-1:
            self.index = -1
        self.scroll = 0

    def lines(self, view, record):
        """Render only data that was public at this call, not current hidden clues."""
        names = {c.cell: c.name for c in record.state.characters}
        lines = [f'Backend: {record.backend} | Analysis time: {record.elapsed_ms:.1f} ms',
                 f'Known verdicts: {len(record.state.verdicts)}']
        value = lambda x: 'N/A' if x is None else str(x)
        primary, auxiliary, clauses = record.cnf_counts or (None,None,None)
        lines += ['', 'EXPERIMENT METRICS (input KB / selected call)',
                  f'Primary variables: {value(primary)} | Auxiliary variables: {value(auxiliary)}',
                  f'CNF clauses: {value(clauses)} | SAT calls: {value(record.sat_calls)}',
                  f'Decisions: {value(record.decisions)} | Propagations: {value(record.propagations)} | Backtracks: {value(record.backtracks)}',
                  f'Runtime (analysis): {record.elapsed_ms:.2f} ms']
        totals = record.totals
        lines += ['', 'RUN TOTALS',
                  f'Analysis calls: {totals.analysis_calls} | SAT calls: {value(totals.sat_calls)}',
                  f'Decisions: {value(totals.decisions if totals.sat_calls else None)} | Propagations: {value(totals.propagations if totals.sat_calls else None)} | Backtracks: {value(totals.backtracks if totals.sat_calls else None)}',
                  f'Deduction steps: {totals.deduction_steps} | Reveal waves: {totals.reveal_waves}',
                  f'Runtime: {totals.runtime_ms:.2f} ms']
        if record.note:
            lines.append(record.note)
        if record.consistent is not None:
            lines.append('Public knowledge: consistent' if record.consistent else 'Public knowledge: INCONSISTENT')
        if record.outcome:
            lines.append(f'Action result: {record.outcome}')
        if record.new_clues:
            lines.append('Newly revealed: '+', '.join(record.new_clues))
        lines += ['', 'CLASSIFICATION (all unresolved characters)']
        lines.extend(f'{cell} {names.get(cell, cell)}: {getattr(status, "value", status)}'
                     for cell, status in record.verdicts)
        if record.queries:
            lines += ['', 'SAT QUERIES',
                      'UNSAT under an assumption proves its opposite. SAT alone does not prove a verdict.']
            for cell, assumption, outcome, entailed in record.queries:
                question = {'BASE_CHECK': 'Check public KB',
                            'ASSUME_INNOCENT': f'Assume {cell} innocent (NOT C)',
                            'ASSUME_CRIMINAL': f'Assume {cell} criminal (C)'}.get(assumption, assumption)
                conclusion = f' -> proved {entailed}' if entailed else ''
                lines.append(f'{question}: {outcome}{conclusion}')
        return lines

    def draw(self, view):
        import pygame
        from griductive.ui.config import BG, PANEL, TEXT, MUTED, ACCENT
        from griductive.ui import config
        view.hover_scope = 'agent'
        rect = pygame.Rect(config.WINDOW_SIZE[0]+12, 12,
                           config.AGENT_PANEL_WIDTH-24, config.WINDOW_SIZE[1]-24)
        self.rect = rect
        pygame.draw.rect(view.screen, PANEL, rect, border_radius=14)
        view.label('Agent inspector', (rect.x+20, rect.y+18), ACCENT, view.heading)
        view.button('agent_close', 'Close', pygame.Rect(rect.right-110, rect.y+16, 90, 38))
        view.wrapped('Live analysis calls. Click the board to play, or this panel to browse with arrow keys.',
                     pygame.Rect(rect.x+20, rect.y+64, rect.width-40, 44), MUTED, view.small)
        preview = self.selected_record(view.observer) is not None
        free = not view.busy and not view.auto and not preview
        view.button('agent_reference', 'Use Reference', pygame.Rect(rect.x+20, rect.y+116, 240, 40), free)
        view.button('agent_logic', 'Use Logic Agent', pygame.Rect(rect.x+272, rect.y+116, 284, 40), free)
        view.label('Historical board: after action' if preview else 'Live board | Switching clears history.',
                   (rect.x+20, rect.y+170), MUTED, view.small)
        view.button('agent_live','Live',pygame.Rect(rect.right-100,rect.y+164,80,30),preview)
        records = view.observer.snapshot()
        index = len(records)-1 if self.index < 0 else min(self.index, len(records)-1)
        label = (f'Analysis call {records[index].number} | {len(records)} retained'
                 if records else 'No analysis yet. Click Analyze or Next move.')
        if view.busy:
            label += ' | Working...'
        view.label(label, (rect.x+20, rect.y+198), ACCENT, view.small)
        viewport = pygame.Rect(rect.x+20, rect.y+230, rect.width-40, rect.height-370)
        pygame.draw.rect(view.screen, BG, viewport, border_radius=8)
        if records:
            raw_lines = self.lines(view, records[index])
        else:
            raw_lines = [f'Configured analyzer: {type(view.observer.analyzer).__name__}',
                         'Analyze classifies the current public board without revealing a card.',
                         'Next move proves and reveals one character. Auto Solve records calls here too.',
                         'Logic Agent uses CNF/DPLL when available; reference fallback is labeled explicitly.',
                         'Use the mouse wheel to scroll details. Left/Right browse calls.']
        lines = [part for line in raw_lines for part in (view.lines(line, viewport.width-38, view.small) or [''])]
        line_height = max(20, view.small.get_linesize()+3)
        self.max_scroll = max(0, len(lines)*line_height-viewport.height+20)
        self.scroll = max(0, min(self.scroll, self.max_scroll))
        old_clip = view.screen.get_clip()
        view.screen.set_clip(viewport)
        for i, line in enumerate(lines):
            y = viewport.y+10+i*line_height-self.scroll
            if viewport.y-line_height < y < viewport.bottom:
                view.label(line, (viewport.x+12, y), TEXT, view.small)
        view.screen.set_clip(old_clip)
        if self.max_scroll:
            track = pygame.Rect(viewport.right-7, viewport.y+6, 3, viewport.height-12)
            thumb_h = max(24, round(track.height*viewport.height/(self.max_scroll+viewport.height)))
            y = track.y+round((track.height-thumb_h)*self.scroll/self.max_scroll)
            pygame.draw.rect(view.screen, ACCENT, (track.x,y,3,thumb_h), border_radius=2)
        bottom = rect.bottom-120
        for key, title, x, width, enabled in [
                ('agent_prev','Previous call',20,262,index>0 and not view.busy),
                ('agent_next','Next call',294,262,bool(records) and index<len(records)-1 and not view.busy)]:
            view.button(key, title, pygame.Rect(rect.x+x,bottom,width,42), enabled)
        bottom += 56
        for key, title, x, width, enabled in [
                ('agent_analyze','Analyze',20,164,free),
                ('agent_step','Next move',196,164,free and not view.engine.solved),
                ('agent_auto','Stop' if view.auto else 'Auto Solve',372,184,
                 view.auto or (free and not view.engine.solved))]:
            view.button(key, title, pygame.Rect(rect.x+x,bottom,width,42), enabled)
