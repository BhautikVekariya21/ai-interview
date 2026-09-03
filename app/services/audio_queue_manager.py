"""
Audio Queue Manager — Sequential playback without overlap.
Manages the interview audio flow:
  [Intro] → [Transition+Q1] → [Transition+Q2] → ... → [Outro]
"""

import time
import uuid
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from loguru import logger

from app.schemas.tts_schemas import AudioQueueItem


class PlaybackState(str, Enum):
    """Current state of the audio queue."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class AudioQueueManager:
    """
    Manages ordered audio playback for interview sessions.
    
    Guarantees:
      - No overlapping audio (strict sequential playback)
      - FIFO ordering
      - Pause / Resume / Skip / Repeat support
      - Progress tracking
      - Callback hooks for frontend sync
    
    In a web context, this manages server-side state.
    Audio delivery to client happens via HTTP streaming.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())[:8]
        self._queue: List[AudioQueueItem] = []
        self._audio_data: Dict[str, bytes] = {}  # id → audio bytes
        self._current_index: int = -1
        self._state: PlaybackState = PlaybackState.IDLE
        self._history: List[str] = []  # IDs of played items

        # Stats
        self._total_play_time: float = 0.0
        self._started_at: Optional[float] = None
        self._completed_at: Optional[float] = None

        logger.debug(f"AudioQueue created: {self.session_id}")

    # ─── Queue Management ────────────────────────────────────

    def add_item(
        self,
        item: AudioQueueItem,
        audio_bytes: Optional[bytes] = None,
    ):
        """Add an item to the end of the queue."""
        self._queue.append(item)
        if audio_bytes:
            self._audio_data[item.id] = audio_bytes
            item.audio_size_bytes = len(audio_bytes)
            item.status = "ready"

        logger.debug(
            f"Queue [{self.session_id}] += {item.audio_type} "
            f"'{item.id}' ({item.status})"
        )

    def add_items(
        self,
        items: List[AudioQueueItem],
        audio_map: Optional[Dict[str, bytes]] = None,
    ):
        """Add multiple items to the queue."""
        for item in items:
            audio = None
            if audio_map and item.id in audio_map:
                audio = audio_map[item.id]
            self.add_item(item, audio)

    def insert_after_current(
        self,
        item: AudioQueueItem,
        audio_bytes: Optional[bytes] = None,
    ):
        """
        Insert an item immediately after the current playing item.
        Used for follow-up questions.
        """
        insert_pos = self._current_index + 1
        if insert_pos > len(self._queue):
            insert_pos = len(self._queue)

        self._queue.insert(insert_pos, item)
        if audio_bytes:
            self._audio_data[item.id] = audio_bytes
            item.audio_size_bytes = len(audio_bytes)
            item.status = "ready"

        logger.info(
            f"Queue [{self.session_id}] inserted follow-up "
            f"at position {insert_pos}"
        )

    # ─── Playback Control ────────────────────────────────────

    def next(self) -> Optional[AudioQueueItem]:
        """
        Advance to the next item and return it.
        Returns None when queue is exhausted.
        """
        if self._started_at is None:
            self._started_at = time.time()

        # Mark previous as done
        if 0 <= self._current_index < len(self._queue):
            prev = self._queue[self._current_index]
            prev.status = "done"
            self._history.append(prev.id)
            self._total_play_time += prev.duration_estimate_seconds

        # Advance
        self._current_index += 1

        if self._current_index >= len(self._queue):
            self._state = PlaybackState.COMPLETED
            self._completed_at = time.time()
            logger.info(
                f"Queue [{self.session_id}] completed — "
                f"{len(self._history)} items played"
            )
            return None

        current = self._queue[self._current_index]
        current.status = "playing"
        self._state = PlaybackState.PLAYING

        logger.debug(
            f"Queue [{self.session_id}] now playing: "
            f"{current.audio_type} '{current.id}'"
        )
        return current

    def get_current(self) -> Optional[AudioQueueItem]:
        """Get the currently playing item."""
        if 0 <= self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None

    def get_current_audio(self) -> Optional[bytes]:
        """Get audio bytes for the current item."""
        current = self.get_current()
        if current and current.id in self._audio_data:
            return self._audio_data[current.id]
        return None

    def get_audio_by_id(self, item_id: str) -> Optional[bytes]:
        """Get audio bytes for a specific item."""
        return self._audio_data.get(item_id)

    def get_previous(self) -> Optional[AudioQueueItem]:
        """Get the previously played item (for repeat)."""
        if self._current_index > 0:
            return self._queue[self._current_index - 1]
        return None

    def get_previous_audio(self) -> Optional[bytes]:
        """Get audio for the previous item (for repeat)."""
        prev = self.get_previous()
        if prev and prev.id in self._audio_data:
            return self._audio_data[prev.id]
        return None

    def skip(self) -> Optional[AudioQueueItem]:
        """Skip the current item and move to next."""
        current = self.get_current()
        if current:
            current.status = "skipped"
            logger.info(
                f"Queue [{self.session_id}] skipped: {current.id}"
            )
        return self.next()

    def pause(self):
        """Pause playback."""
        self._state = PlaybackState.PAUSED
        logger.info(f"Queue [{self.session_id}] PAUSED")

    def resume(self):
        """Resume playback."""
        if self._state == PlaybackState.PAUSED:
            self._state = PlaybackState.PLAYING
            logger.info(f"Queue [{self.session_id}] RESUMED")

    def reset(self):
        """Reset queue to beginning."""
        self._current_index = -1
        self._state = PlaybackState.IDLE
        self._history.clear()
        self._total_play_time = 0.0
        for item in self._queue:
            item.status = "pending"
        logger.info(f"Queue [{self.session_id}] RESET")

    # ─── Status ──────────────────────────────────────────────

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def total_items(self) -> int:
        return len(self._queue)

    @property
    def items_played(self) -> int:
        return len(self._history)

    @property
    def items_remaining(self) -> int:
        return max(0, len(self._queue) - self._current_index - 1)

    @property
    def is_complete(self) -> bool:
        return self._state == PlaybackState.COMPLETED

    @property
    def progress_percent(self) -> float:
        if not self._queue:
            return 0.0
        return round(
            (self._current_index + 1) / len(self._queue) * 100, 1
        )

    @property
    def estimated_remaining_seconds(self) -> float:
        remaining = 0.0
        for i in range(self._current_index + 1, len(self._queue)):
            remaining += self._queue[i].duration_estimate_seconds
        return round(remaining, 1)

    def get_status(self) -> Dict[str, Any]:
        """Get complete queue status."""
        return {
            "session_id": self.session_id,
            "state": self._state.value,
            "total_items": self.total_items,
            "current_index": self._current_index,
            "items_played": self.items_played,
            "items_remaining": self.items_remaining,
            "progress_percent": self.progress_percent,
            "total_play_time_seconds": round(
                self._total_play_time, 1
            ),
            "estimated_remaining_seconds": (
                self.estimated_remaining_seconds
            ),
            "current_item": (
                self.get_current().model_dump()
                if self.get_current()
                else None
            ),
            "queue": [item.model_dump() for item in self._queue],
        }

    def get_all_items(self) -> List[AudioQueueItem]:
        """Get all queue items."""
        return list(self._queue)