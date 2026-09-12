import time
from collections.abc import Callable


class CircuitBreaker:
    """Single-event-loop circuit with exactly one probe after each reset window."""

    def __init__(
        self, threshold: int, reset_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.clock = clock
        self.failures = 0
        self.opened_at: float | None = None
        self.probe_active = False

    @property
    def is_open(self) -> bool:
        return self.opened_at is not None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if self.probe_active or self.clock() - self.opened_at < self.reset_seconds:
            return False
        self.probe_active = True
        return True

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self.probe_active = False

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold or self.probe_active:
            self.opened_at = self.clock()
        self.probe_active = False

    def cancel_probe(self) -> None:
        self.probe_active = False
