from dataclasses import replace
from unittest import TestCase

from griductive.agent.adapter import Agent
from griductive.domain.models import Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.experiments.benchmark import ROOT, measure, validate


class ExperimentTests(TestCase):
    def setUp(self):
        self.puzzle = load_puzzle(ROOT / "data/puzzles/3x3/level_01.json")

    def test_opening_and_restart(self):
        engine = GameEngine(self.puzzle, Agent(strict_dpll=True))
        initial = engine.public_state()
        expected = {c.cell: Status.UNKNOWN for c in initial.characters if c.cell != "A1"}
        expected.update(B1=Status.INNOCENT, C1=Status.INNOCENT)
        self.assertEqual(dict(engine.analyze().verdicts), expected)
        self.assertEqual(engine.hint().cell, "B1")
        self.assertEqual(engine.public_state(), initial)
        self.assertEqual(engine.step().cell, "B1")
        self.assertEqual(engine.step().cell, "C1")
        engine.restart()
        self.assertEqual(engine.public_state(), initial)
        self.assertEqual(dict(engine.analyze().verdicts), expected)

    def test_differential_and_counters(self):
        self.assertEqual(validate(self.puzzle, 3)["checked_steps"], 8)
        row, steps = measure(self.puzzle, 3)
        self.assertEqual((row["status"], row["reveal_steps"], row["total_sat_calls"]),
                         ("SOLVED", 8, 74))
        calls = [call for step in steps for call in step["calls"]]
        self.assertEqual(len(calls), row["total_sat_calls"])
        self.assertEqual(sum(c["propagations"] for c in calls), row["total_propagations"])

    def test_stall_and_timeout(self):
        stalled = replace(self.puzzle, initially_revealed=())
        row, _ = measure(stalled, 3)
        self.assertEqual((row["status"], row["reveal_steps"]), ("STALLED", 0))
        row, steps = measure(self.puzzle, 0)
        self.assertEqual((row["status"], row["total_sat_calls"]), ("TIMEOUT", 1))
        self.assertEqual(steps[0]["calls"][0]["outcome"], "TIMEOUT")
