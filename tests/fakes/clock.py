class FakeClock:
    def __init__(self, initial_time: float = 0.0) -> None:
        self._current_time = initial_time

    def now(self) -> float:
        return self._current_time

    def advance(self, seconds: float) -> None:
        self._current_time += seconds
