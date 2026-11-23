"""Cooperative semantic analyzer for the browser's single event loop."""
import asyncio
from griductive.engine.reference import ReferenceAnalyzer


class BrowserAnalyzer:
    def __init__(self):
        self.reference = ReferenceAnalyzer(timeout=15.0)
        self.state = None
        self.result = None

    async def prepare(self, state):
        if state == self.state:
            return
        steps = self.reference.analyze_steps(state)
        while True:
            try:
                next(steps)
            except StopIteration as finished:
                self.state, self.result = state, finished.value
                return
            await asyncio.sleep(0)

    def analyze(self, state):
        if self.state != state or self.result is None:
            raise RuntimeError('Browser analysis must be prepared before applying a move.')
        return self.result
