"""Short-term Memory — Redis-based session memory (TTL 24h)."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Redis HASH-based session memory with 24-hour TTL."""

    TTL = 86400  # 24 hours

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key = f"session:{session_id}"
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            import redis
            from app.core.config import get_settings
            settings = get_settings()
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )
        return self._redis

    def save(self, field: str, value: Any):
        """Save a field to session memory."""
        try:
            r = self._get_redis()
            r.hset(self.key, field, json.dumps(value, default=str))
            r.expire(self.key, self.TTL)
        except Exception as e:
            logger.warning("ShortTermMemory save failed: %s", e)

    def get(self, field: str) -> Any | None:
        """Get a field from session memory."""
        try:
            r = self._get_redis()
            val = r.hget(self.key, field)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning("ShortTermMemory get failed: %s", e)
            return None

    def get_all(self) -> dict:
        """Get all fields from session memory."""
        try:
            r = self._get_redis()
            data = r.hgetall(self.key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            logger.warning("ShortTermMemory get_all failed: %s", e)
            return {}

    def clear(self):
        """Delete session memory."""
        try:
            r = self._get_redis()
            r.delete(self.key)
        except Exception as e:
            logger.warning("ShortTermMemory clear failed: %s", e)
