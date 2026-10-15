"""Fixed-timestep accumulator.

Logic always advances in whole steps of 1/hz seconds, whatever the real frame rate,
so the simulation stays deterministic. Integer arithmetic avoids float drift: one
millisecond adds `hz` units and one step costs 1000 units.
"""

from __future__ import annotations


class FixedStep:
    def __init__(self, hz: int = 60, max_steps_per_frame: int = 5) -> None:
        self.hz = hz
        self.max_steps_per_frame = max_steps_per_frame
        self._units = 0

    def advance(self, elapsed_ms: int) -> int:
        """Add real elapsed time and return how many logic steps to run now."""
        self._units += max(0, elapsed_ms) * self.hz
        steps, self._units = divmod(self._units, 1000)
        if steps > self.max_steps_per_frame:
            # Too far behind (window dragged, breakpoint...): drop the backlog
            # instead of fast-forwarding the game.
            steps = self.max_steps_per_frame
            self._units = 0
        return steps
