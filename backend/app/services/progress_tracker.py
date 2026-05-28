from typing import Dict, Optional
from dataclasses import dataclass
import threading


@dataclass
class ProgressState:
    current: int
    total: int
    model_name: str
    completed: bool = False


class ProgressTracker:
    def __init__(self):
        self._state: Dict[str, ProgressState] = {}
        self._lock = threading.Lock()

    def update_progress(
        self, session_id: str, current: int, total: int, model_name: str
    ) -> None:
        with self._lock:
            self._state[session_id] = ProgressState(
                current=current,
                total=total,
                model_name=model_name,
                completed=(current >= total)
            )
            print(f"[ProgressTracker] Updated {session_id}: {current}/{total} - {model_name}")

    def get_progress(self, session_id: str) -> Optional[ProgressState]:
        with self._lock:
            return self._state.get(session_id)


_progress_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    return _progress_tracker
