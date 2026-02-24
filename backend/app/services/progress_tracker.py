"""
Progress tracking service for forecast operations.
Maintains in-memory state of ongoing forecast operations and provides
progress updates to clients via Server-Sent Events.
"""
from typing import Dict, Optional
from dataclasses import dataclass
import threading


@dataclass
class ProgressState:
    """Represents the current state of a forecast operation."""
    current: int
    total: int
    model_name: str
    completed: bool = False


class ProgressTracker:
    """
    Thread-safe progress tracker for forecast operations.
    Uses session IDs to track individual forecast jobs.
    """
    
    def __init__(self):
        self._state: Dict[str, ProgressState] = {}
        self._lock = threading.Lock()
    
    def update_progress(
        self, session_id: str, current: int, total: int, model_name: str
    ) -> None:
        """Update progress for a given session (synchronous)."""
        with self._lock:
            self._state[session_id] = ProgressState(
                current=current,
                total=total,
                model_name=model_name,
                completed=(current >= total)
            )
            print(f"[ProgressTracker] Updated {session_id}: {current}/{total} - {model_name}")
    
    def get_progress(self, session_id: str) -> Optional[ProgressState]:
        """Get current progress for a session (synchronous)."""
        with self._lock:
            return self._state.get(session_id)
    
    def clear_progress(self, session_id: str) -> None:
        """Clear progress state for a session (synchronous)."""
        with self._lock:
            if session_id in self._state:
                del self._state[session_id]


# Global instance
_progress_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    return _progress_tracker
