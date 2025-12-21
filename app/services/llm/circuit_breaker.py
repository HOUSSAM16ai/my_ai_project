"""
Circuit Breaker Module for LLM Services
=======================================
Manages the circuit breaker state to prevent cascading failures
when upstream LLM providers are down or rate-limited.
"""
import logging
import os
import time
from typing import Any

_LOG = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Singleton Circuit Breaker for LLM calls.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._state: dict[str, Any] = {'errors': [], 'open_until': 0.0,
            'open_events': 0}

    @property
    def is_allowed(self) ->bool:
        """Check if the circuit is closed (traffic allowed)."""
        now = time.time()
        return not self._state['open_until'] > now

    def note_error(self) ->None:
        """Record an error and potentially open the circuit."""
        now = time.time()
        window = float(os.getenv('LLM_BREAKER_WINDOW', '60') or 60.0)
        threshold = int(os.getenv('LLM_BREAKER_ERROR_THRESHOLD', '6') or 6)
        cooldown = float(os.getenv('LLM_BREAKER_COOLDOWN', '30') or 30.0)
        self._state['errors'].append(now)
        cutoff = now - window
        self._state['errors'] = [t for t in self._state['errors'] if t >=
            cutoff]
        if len(self._state['errors']) >= threshold and self._state['open_until'
            ] <= now:
            self._state['open_until'] = now + cooldown
            self._state['open_events'] += 1
            _LOG.warning(
                'LLM Circuit Breaker OPEN (errors=%d threshold=%d cooldown=%ds)'
                , len(self._state['errors']), threshold, cooldown)

    def get_state(self) ->dict[str, Any]:
        """Return a copy of the current state for telemetry."""
        now = time.time()
        window = float(os.getenv('LLM_BREAKER_WINDOW', '60') or 60.0)
        return {'open': self._state['open_until'] > now, 'open_until': self
            ._state['open_until'], 'recent_error_count': len([t for t in
            self._state['errors'] if t >= now - window]), 'open_events':
            self._state['open_events']}
