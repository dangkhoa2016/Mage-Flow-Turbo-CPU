from __future__ import annotations

import threading


class SingleFlight:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    def acquire(self) -> bool:
        return self._lock.acquire(blocking=False)

    def release(self) -> None:
        try:
            self._lock.release()
        except RuntimeError:
            pass
