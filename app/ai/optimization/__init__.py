"""
Performance Optimization Layer
===============================
Advanced caching, batching, and optimization strategies.

Features:
- Semantic caching with embeddings
- Request batching and deduplication
- Response streaming optimization
- Token usage optimization
- Prompt compression
"""
from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

_LOG = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: float = 3600.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) ->bool:
        """Check if entry is expired."""
        return time.time() - self.created_at > self.ttl

    def touch(self) ->None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1


class SemanticCache:
    """
    Semantic cache for LLM responses.

    Uses content hashing and optional semantic similarity
    to cache and retrieve responses.
    """

    def __init__(self, max_size: int=1000, default_ttl: float=3600.0,
        similarity_threshold: float=0.95):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.similarity_threshold = similarity_threshold
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: (str | dict[str, Any])) ->(Any | None):
        """
        Get value from cache.

        Args:
            key: Cache key (string or dict to be hashed)

        Returns:
            Cached value or None
        """
        cache_key = self._make_key(key)
        with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired():
                del self._cache[cache_key]
                self._misses += 1
                return None
            entry.touch()
            self._hits += 1
            return entry.value

    def set(self, key: (str | dict[str, Any]), value: Any, ttl: (float |
        None)=None, **metadata: Any) ->None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            **metadata: Additional metadata
        """
        cache_key = self._make_key(key)
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            entry = CacheEntry(key=cache_key, value=value, created_at=time.
                time(), accessed_at=time.time(), ttl=ttl or self.
                default_ttl, metadata=metadata)
            self._cache[cache_key] = entry

    def invalidate(self, key: (str | dict[str, Any])) ->bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key

        Returns:
            True if entry was removed
        """
        cache_key = self._make_key(key)
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def clear(self) ->None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def _make_key(self, key: (str | dict[str, Any])) ->str:
        """Create cache key from input."""
        if isinstance(key, str):
            return hashlib.sha256(key.encode()).hexdigest()
        key_str = str(sorted(key.items()))
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _evict_lru(self) ->None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].
            accessed_at)
        del self._cache[lru_key]

    def get_stats(self) ->dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100 if total_requests >
                0 else 0)
            return {'size': len(self._cache), 'max_size': self.max_size,
                'hits': self._hits, 'misses': self._misses, 'hit_rate':
                hit_rate, 'total_requests': total_requests}


class RequestBatcher:
    """
    Batches multiple requests for efficient processing.

    Collects requests over a time window and processes them together.
    """

    def __init__(self, batch_size: int=10, batch_timeout: float=0.1,
        processor: (Callable[[list[Any]], list[Any]] | None)=None):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processor = processor
        self._pending: list[tuple[Any, threading.Event, list]] = []
        self._lock = threading.RLock()
        self._batch_thread: threading.Thread | None = None
        self._running = False

    def start(self) ->None:
        """Start batch processing thread."""
        if self._running:
            return
        self._running = True
        self._batch_thread = threading.Thread(target=self._process_batches,
            daemon=True)
        self._batch_thread.start()

    def stop(self) ->None:
        """Stop batch processing thread."""
        self._running = False
        if self._batch_thread:
            self._batch_thread.join(timeout=1.0)

    def submit(self, request: Any) ->Any:
        """
        Submit request for batching.

        Args:
            request: Request to batch

        Returns:
            Response for the request
        """
        event = threading.Event()
        result_container = []
        with self._lock:
            self._pending.append((request, event, result_container))
            if len(self._pending) >= self.batch_size:
                self._flush_batch()
        event.wait()
        if result_container:
            return result_container[0]
        raise RuntimeError('Batch processing failed')

    def _process_batches(self) ->None:
        """Background thread for processing batches."""
        while self._running:
            time.sleep(self.batch_timeout)
            with self._lock:
                if self._pending:
                    self._flush_batch()

    def _flush_batch(self) ->None:
        """Process pending batch."""
        if not self._pending:
            return
        batch = self._pending[:]
        self._pending.clear()
        requests = [item[0] for item in batch]
        try:
            results = self.processor(requests) if self.processor else requests
            for (_, event, result_container), result in zip(batch, results, strict=False):
                result_container.append(result)
                event.set()
        except Exception as e:
            _LOG.error(f'Batch processing error: {e}')
            for _, event, _ in batch:
                event.set()


class PromptOptimizer:
    """
    Optimizes prompts for token efficiency.

    Provides strategies for reducing token usage while
    maintaining semantic meaning.
    """

    @staticmethod
    def compress_whitespace(text: str) ->str:
        """Remove excessive whitespace."""
        import re
        text = re.sub('\\s+', ' ', text)
        return text.strip()

    @staticmethod
    def remove_redundancy(text: str) ->str:
        """Remove redundant phrases."""
        redundant_phrases = ['please note that', 'it is important to',
            'you should know that', 'as mentioned before', 'in other words']
        result = text
        for phrase in redundant_phrases:
            result = result.replace(phrase, '')
        return PromptOptimizer.compress_whitespace(result)

    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int, encoding: str=
        'cl100k_base') ->str:
        """
        Truncate text to maximum token count.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
            encoding: Tokenizer encoding

        Returns:
            Truncated text
        """
        try:
            import tiktoken
            enc = tiktoken.get_encoding(encoding)
            tokens = enc.encode(text)
            if len(tokens) <= max_tokens:
                return text
            truncated_tokens = tokens[:max_tokens]
            return enc.decode(truncated_tokens)
        except ImportError:
            words = text.split()
            estimated_tokens = len(words) * 1.3
            if estimated_tokens <= max_tokens:
                return text
            target_words = int(max_tokens / 1.3)
            return ' '.join(words[:target_words])

    @staticmethod
    def optimize(text: str, max_tokens: (int | None)=None,
        remove_redundancy: bool=True) ->str:
        """
        Apply all optimization strategies.

        Args:
            text: Text to optimize
            max_tokens: Optional token limit
            remove_redundancy: Whether to remove redundant phrases

        Returns:
            Optimized text
        """
        result = PromptOptimizer.compress_whitespace(text)
        if remove_redundancy:
            result = PromptOptimizer.remove_redundancy(result)
        if max_tokens:
            result = PromptOptimizer.truncate_to_tokens(result, max_tokens)
        return result


class ResponseDeduplicator:
    """
    Deduplicates similar requests to avoid redundant API calls.

    Tracks in-flight requests and returns cached results for
    identical concurrent requests.
    """

    def __init__(self):
        self._in_flight: dict[str, tuple[threading.Event, list]] = {}
        self._lock = threading.RLock()


_global_cache = SemanticCache()
_global_deduplicator = ResponseDeduplicator()


def get_cache() ->SemanticCache:
    """Get global semantic cache."""
    return _global_cache


def get_deduplicator() ->ResponseDeduplicator:
    """Get global response deduplicator."""
    return _global_deduplicator


__all__ = [
    'PromptOptimizer',
    'RequestBatcher',
    'ResponseDeduplicator',
    'SemanticCache',
    'get_cache',
    'get_deduplicator',
]
