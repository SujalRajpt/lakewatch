from threading import Lock


class LakeControl:
    def __init__(self):
        self._stress_levels = {}
        self._lock = Lock()

    def initialize_lake(self, lake_id: str, stress_level: float = 0):
        with self._lock:
            self._stress_levels[lake_id] = stress_level

    def set_stress_level(self, lake_id: str, stress_level: float):

        if not 0 <= stress_level <= 100:
            raise ValueError("stress_level must be between 0 and 100")

        with self._lock:
            if lake_id not in self._stress_levels:
                raise KeyError(lake_id)

            self._stress_levels[lake_id] = stress_level

    def get_stress_level(self, lake_id: str) -> float:

        with self._lock:
            return self._stress_levels.get(lake_id, 0)

    def get_all_levels(self):

        with self._lock:
            return self._stress_levels.copy()


lake_control = LakeControl()
