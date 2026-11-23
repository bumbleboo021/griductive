"""Live diagnostics describe actual calls, including fallback and failed queries."""
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from griductive.agent.adapter import Agent
from griductive.domain.models import Clue, Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer
from griductive.ui.agent_inspector import ObservedAnalyzer

ROOT = Path(__file__).resolve().parents[2]


def state():
    return GameEngine(load_puzzle(ROOT/'tests/fixtures/chain_3.json'), ReferenceAnalyzer()).public_state()


def install_solver(monkeypatch, outcomes):
    results = iter(outcomes)
    solver = ModuleType('griductive.sat.dpll')
    solver.solve = lambda **kwargs: next(results)
    monkeypatch.setitem(sys.modules, solver.__name__, solver)


def test_missing_solver_fallback_is_not_a_sat_query(monkeypatch):
    monkeypatch.setitem(sys.modules, 'griductive.sat.dpll', None)
    agent = Agent()
    observed = ObservedAnalyzer(agent)
    public = state()
    result = observed.analyze(public)
    assert result == ReferenceAnalyzer().analyze(public)
    record, = observed.snapshot()
    assert record.backend == 'Reference fallback'
    assert record.queries == () and agent.last_query_count == 0
    assert record.cnf_counts[0] == 9
    assert record.state is public and record.note
    bad = replace(public, clues=(Clue('bad', 'FACT', ('A1',), status=Status.CRIMINAL),))
    assert not observed.analyze(bad).consistent
    assert observed.snapshot()[-1].queries == ()


def test_strict_agent_keeps_import_error_observable(monkeypatch):
    monkeypatch.setitem(sys.modules, 'griductive.sat.dpll', None)
    observed = ObservedAnalyzer(Agent(strict_dpll=True))
    with pytest.raises(ImportError):
        observed.analyze(state())
    record, = observed.snapshot()
    assert record.consistent is None
    assert record.backend == 'CNF / DPLL' and 'ModuleNotFoundError' in record.note


@pytest.mark.parametrize('failure_at', [0, 1, 2])
def test_sat_timeout_is_logged_at_each_query_position(monkeypatch, failure_at):
    sat = SimpleNamespace(is_sat=True, is_timeout=False)
    timeout = SimpleNamespace(is_sat=False, is_timeout=True)
    install_solver(monkeypatch, [sat]*failure_at+[timeout])
    agent = Agent(strict_dpll=True)
    observed = ObservedAnalyzer(agent)
    with pytest.raises(TimeoutError):
        observed.analyze(state())
    record, = observed.snapshot()
    assert len(record.queries) == failure_at+1 == agent.last_query_count
    assert record.queries[-1][2] == 'TIMEOUT'
    assert record.consistent is None


def test_unsat_base_is_logged_without_any_classifications(monkeypatch):
    install_solver(monkeypatch, [SimpleNamespace(is_sat=False, is_timeout=False)])
    agent = Agent(strict_dpll=True)
    observed = ObservedAnalyzer(agent)
    assert not observed.analyze(state()).consistent
    record, = observed.snapshot()
    assert record.queries == (('KB', 'BASE_CHECK', 'UNSAT', None),)
    assert record.verdicts == () and agent.last_query_count == 1


def test_entailment_query_records_are_reset_between_calls(monkeypatch):
    sat = SimpleNamespace(is_sat=True, is_timeout=False)
    unsat = SimpleNamespace(is_sat=False, is_timeout=False)
    install_solver(monkeypatch, [sat]+[unsat]*8+[sat]*17)
    observed = ObservedAnalyzer(Agent(strict_dpll=True))
    first = observed.analyze(state())
    second = observed.analyze(state())
    assert all(status == Status.CRIMINAL for _, status in first.verdicts)
    assert all(status == Status.UNKNOWN for _, status in second.verdicts)
    a, b = observed.snapshot()
    assert len(a.queries) == 9 and len(b.queries) == 17
    assert a.queries[1][3] == 'CRIMINAL'
    assert b.queries[1][3] is None


def test_observer_bounds_history_and_keeps_only_public_inputs():
    observed = ObservedAnalyzer(ReferenceAnalyzer(), capacity=2)
    public = state()
    for _ in range(3):
        observed.analyze(public)
    records = observed.snapshot()
    assert [r.number for r in records] == [2, 3]
    assert all(r.state.clues == public.clues for r in records)
    assert not hasattr(records[0].state, 'solution')
    observed.clear()
    assert observed.snapshot() == ()


def test_solver_counters_are_summed_per_call_and_per_run(monkeypatch):
    def result(sat):
        return SimpleNamespace(is_sat=sat, is_timeout=False,
                               stats=dict(decisions=1, propagations=2, backtracks=3))
    install_solver(monkeypatch, ([result(True)]+[result(False)]*8)*2)
    observed = ObservedAnalyzer(Agent(strict_dpll=True))
    observed.analyze(state())
    observed.analyze(state())
    first, second = observed.snapshot()
    assert (first.sat_calls, first.decisions, first.propagations, first.backtracks) == (9,9,18,27)
    assert second.sat_calls == 9 and second.decisions == 9
    assert second.totals.sat_calls == 18 and second.totals.decisions == 18
    assert second.totals.propagations == 36 and second.totals.backtracks == 54
    assert first.totals.sat_calls == 9  # Historical totals stay immutable.
    assert second.totals.runtime_ms == first.elapsed_ms+second.elapsed_ms
    assert second.solver_runtime_ms >= 0


def test_missing_counter_is_unavailable_not_zero(monkeypatch):
    result = SimpleNamespace(is_sat=False, is_timeout=False, decisions=2, backtracks=1)
    install_solver(monkeypatch, [result])
    observed = ObservedAnalyzer(Agent(strict_dpll=True))
    observed.analyze(state())
    record, = observed.snapshot()
    assert record.decisions == 2 and record.backtracks == 1
    assert record.propagations is None and record.totals.propagations is None


def test_raising_solver_still_counts_the_call(monkeypatch):
    solver = ModuleType('griductive.sat.dpll')
    def fail(**kwargs):
        raise RuntimeError('solver failure')
    solver.solve = fail
    monkeypatch.setitem(sys.modules, solver.__name__, solver)
    observed = ObservedAnalyzer(Agent(strict_dpll=True))
    with pytest.raises(RuntimeError):
        observed.analyze(state())
    record, = observed.snapshot()
    assert record.sat_calls == 1 and record.queries == ()
    assert record.totals.sat_calls == 1 and record.totals.decisions is None
    assert 'solver failure' in record.note


def test_reveal_totals_ignore_hints_and_survive_history_eviction():
    observed = ObservedAnalyzer(ReferenceAnalyzer(), capacity=2)
    engine = GameEngine(load_puzzle(ROOT/'tests/fixtures/chain_3.json'), observed)
    before = engine.public_state()
    outcome = engine.step()
    after = engine.public_state()
    observed.finish_action(outcome, after)
    observed.finish_action(outcome, after)  # Duplicate completion is harmless.
    first = observed.snapshot()[-1]
    assert first.state == before and first.after_state == after
    assert first.totals.deduction_steps == first.totals.reveal_waves == 1
    hint = engine.hint()
    observed.finish_action(hint, engine.public_state())
    assert observed.snapshot()[-1].totals.deduction_steps == 1
    while not engine.solved:
        outcome = engine.step()
        observed.finish_action(outcome, engine.public_state())
    last = observed.snapshot()[-1]
    assert len(observed.snapshot()) == 2
    assert last.totals.deduction_steps == last.totals.reveal_waves == 8
    assert last.totals.analysis_calls == 9 and last.totals.sat_calls == 0
    assert first.totals.deduction_steps == 1
    assert last.cnf_counts is not None  # Public diagnostic encoding for Reference.
    observed.clear()
    observed.analyze(before)
    reset = observed.snapshot()[-1]
    assert reset.totals.analysis_calls == 1 and reset.totals.deduction_steps == 0
