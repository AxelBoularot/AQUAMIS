import time


class BatterySimulator:

    def __init__(self, start_level: float = 87.0, drain_per_sec: float = 1.0, charge_per_sec: float = 2.0):
        self.level = float(max(0.0, min(100.0, start_level)))
        self._charging = False
        self._drain_per_sec = float(max(0.01, drain_per_sec))
        self._charge_per_sec = float(max(0.01, charge_per_sec))
        self._last_t = time.time()

    @property
    def charging(self) -> bool:
        return self._charging

    def update(self) -> None:
        now = time.time()
        dt = max(0.0, now - self._last_t)
        self._last_t = now

        if self._charging:
            self.level += self._charge_per_sec * dt
            if self.level >= 100.0:
                self.level = 100.0
                self._charging = False
        else:
            self.level -= self._drain_per_sec * dt
            if self.level <= 10.0:
                self.level = 10.0
                self._charging = True

    def percent(self) -> int:
        return int(round(self.level))

    def consumption_pct_per_min(self) -> float:
                                                                    
        return float(self._drain_per_sec) * 60.0

    def remaining_minutes(self, *, floor_percent: float = 10.0) -> float | None:
           
        if self._charging:
            return None
        floor_percent = float(max(0.0, min(100.0, floor_percent)))
        if self.level <= floor_percent:
            return 0.0
        if self._drain_per_sec <= 0:
            return None
        remaining_pct = self.level - floor_percent
        return (remaining_pct / float(self._drain_per_sec)) / 60.0
