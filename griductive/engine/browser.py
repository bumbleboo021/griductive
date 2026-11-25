"""Cooperative analyzers for the browser's single event loop."""
import asyncio
from time import perf_counter
from griductive.agent.adapter import Agent
from griductive.agent.trace import SatQueryRecord, TraceStep
from griductive.domain.models import Analysis, Status
from griductive.engine.reference import ReferenceAnalyzer


class BrowserAnalyzer:
    last_backend = 'ReferenceAnalyzer'
    last_sat_calls = 0

    def __init__(self):
        self.reference = ReferenceAnalyzer(timeout=15.0)
        self.state = None
        self.result = None
        self.last_prepare_ms = None

    async def prepare(self, state):
        if state == self.state and self.result is not None:
            return
        steps = self.reference.analyze_steps(state)
        compute_s = 0.0
        while True:
            started = perf_counter()
            try:
                next(steps)
            except StopIteration as finished:
                compute_s += perf_counter() - started
                self.state, self.result = state, finished.value
                self.last_prepare_ms = compute_s * 1000
                return
            compute_s += perf_counter() - started
            await asyncio.sleep(0)

    def analyze(self, state):
        if self.state != state or self.result is None:
            raise RuntimeError('Browser analysis must be prepared before applying a move.')
        return self.result


class BrowserAgent(Agent):
    """Cooperative CNF/DPLL agent that yields between SAT queries in the browser."""

    def __init__(self, timeout_seconds: float = 15.0, strict_dpll: bool = False,
                 *, on_sat_result=None, heuristic: str | None = None) -> None:
        super().__init__(timeout_seconds=timeout_seconds, strict_dpll=strict_dpll,
                         on_sat_result=on_sat_result, heuristic=heuristic)
        self._prepared_state = None
        self._prepared_result = None
        self.last_prepare_ms = None

    async def prepare(self, state):
        if state == self._prepared_state and self._prepared_result is not None:
            return
        self.last_trace_step = TraceStep(1, [clue.id for clue in state.clues])
        self.last_backend = 'CNF / DPLL'
        self.last_fallback_reason = None
        self.last_cnf_counts = None
        self.last_query_count = 0
        self.last_sat_calls = 0
        self.last_solver_metrics = dict(decisions=0, propagations=0, backtracks=0)
        self.last_solver_runtime_ms = 0.0
        self.last_prepare_ms = None
        self._prepared_state = None
        self._prepared_result = None

        from griductive.logic.encoder import encode
        from griductive.sat.dpll import solve

        compute_s = 0.0
        started = perf_counter()
        cnf_result = encode(state)
        self.last_cnf_counts = (cnf_result.num_primary_vars,
                                cnf_result.num_aux_vars, cnf_result.num_clauses)
        compute_s += perf_counter() - started
        await asyncio.sleep(0)

        started = perf_counter()
        base_res = self._solve_recorded(
            solve,
            clauses=cnf_result.clauses,
            total_vars=cnf_result.total_vars,
            assumptions=(),
            timeout_seconds=self.timeout_seconds,
        )
        compute_s += perf_counter() - started
        outcome_str = (
            'TIMEOUT' if getattr(base_res, 'is_timeout', False)
            else 'SAT' if base_res.is_sat else 'UNSAT'
        )
        self.last_trace_step.sat_queries.append(
            SatQueryRecord(cell='KB', assumption_type='BASE_CHECK', outcome=outcome_str)
        )
        if getattr(base_res, 'is_timeout', False):
            self.last_query_count = self.last_sat_calls
            self.last_prepare_ms = compute_s * 1000
            raise TimeoutError('SAT solver timed out while checking KB consistency')
        if not base_res.is_sat:
            self.last_query_count = self.last_sat_calls
            self.last_prepare_ms = compute_s * 1000
            self._prepared_state = state
            self._prepared_result = Analysis(consistent=False, verdicts=())
            return

        solved_cells = {cell for cell, _ in state.verdicts}
        unresolved_cells = [c.cell for c in state.characters if c.cell not in solved_cells]
        verdicts = []
        for cell in unresolved_cells:
            var_id = cnf_result.cell_to_var[cell]
            await asyncio.sleep(0)
            started = perf_counter()
            res_innocent = self._solve_recorded(
                solve,
                clauses=cnf_result.clauses,
                total_vars=cnf_result.total_vars,
                assumptions=(-var_id,),
                timeout_seconds=self.timeout_seconds,
            )
            compute_s += perf_counter() - started
            if getattr(res_innocent, 'is_timeout', False):
                self.last_trace_step.sat_queries.append(
                    SatQueryRecord(cell, 'ASSUME_INNOCENT', 'TIMEOUT')
                )
                self.last_query_count = self.last_sat_calls
                self.last_prepare_ms = compute_s * 1000
                raise TimeoutError(f'SAT solver timed out while analyzing cell {cell}')
            if not res_innocent.is_sat:
                verdicts.append((cell, Status.CRIMINAL))
                self.last_trace_step.sat_queries.append(
                    SatQueryRecord(cell=cell, assumption_type='ASSUME_INNOCENT',
                                   outcome='UNSAT', entailed='CRIMINAL')
                )
                continue
            self.last_trace_step.sat_queries.append(
                SatQueryRecord(cell=cell, assumption_type='ASSUME_INNOCENT',
                               outcome='SAT', entailed=None)
            )

            await asyncio.sleep(0)
            started = perf_counter()
            res_criminal = self._solve_recorded(
                solve,
                clauses=cnf_result.clauses,
                total_vars=cnf_result.total_vars,
                assumptions=(var_id,),
                timeout_seconds=self.timeout_seconds,
            )
            compute_s += perf_counter() - started
            if getattr(res_criminal, 'is_timeout', False):
                self.last_trace_step.sat_queries.append(
                    SatQueryRecord(cell, 'ASSUME_CRIMINAL', 'TIMEOUT')
                )
                self.last_query_count = self.last_sat_calls
                self.last_prepare_ms = compute_s * 1000
                raise TimeoutError(f'SAT solver timed out while analyzing cell {cell}')
            if not res_criminal.is_sat:
                verdicts.append((cell, Status.INNOCENT))
                self.last_trace_step.sat_queries.append(
                    SatQueryRecord(cell=cell, assumption_type='ASSUME_CRIMINAL',
                                   outcome='UNSAT', entailed='INNOCENT')
                )
                continue
            self.last_trace_step.sat_queries.append(
                SatQueryRecord(cell=cell, assumption_type='ASSUME_CRIMINAL',
                               outcome='SAT', entailed=None)
            )
            verdicts.append((cell, Status.UNKNOWN))

        self.last_query_count = self.last_sat_calls
        self.last_prepare_ms = compute_s * 1000
        self._prepared_state = state
        self._prepared_result = Analysis(consistent=True, verdicts=tuple(verdicts))

    def analyze(self, state):
        if self._prepared_state == state and self._prepared_result is not None:
            return self._prepared_result
        raise RuntimeError('Browser analysis must be prepared before applying a move.')
