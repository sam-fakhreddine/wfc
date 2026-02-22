"""
Phase 1 - TASK-011 Tests
Test TokenBucket rate limiting.
"""

import time
import threading
from wfc.shared.resource_pool import TokenBucket


class TestTokenBucket:
    """Test TokenBucket rate limiting."""

    def test_token_bucket_initialization(self):
        """TokenBucket should initialize with capacity and refill rate."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)

        assert bucket.capacity == 10
        assert bucket.refill_rate == 5.0
        assert bucket.tokens == 10.0

    def test_acquire_within_capacity(self):
        """acquire() should succeed when tokens available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        result = bucket.acquire(tokens=1)

        assert result is True
        assert 8.5 <= bucket.get_available_tokens() <= 9.5

    def test_acquire_multiple_tokens(self):
        """acquire() should handle acquiring multiple tokens at once."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        result = bucket.acquire(tokens=5)

        assert result is True
        assert 4.5 <= bucket.get_available_tokens() <= 5.5

    def test_acquire_fails_when_insufficient_tokens(self):
        """acquire() should fail when insufficient tokens (non-blocking)."""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        bucket.acquire(tokens=5)

        result = bucket.acquire(tokens=1, timeout=0.0)

        assert result is False

    def test_acquire_waits_with_timeout(self):
        """acquire() should wait for tokens when timeout > 0."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)

        bucket.acquire(tokens=5)

        start = time.time()
        result = bucket.acquire(tokens=1, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 1.0
        assert elapsed > 0.05

    def test_refill_over_time(self):
        """Tokens should refill over time based on refill_rate."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)

        bucket.acquire(tokens=10)

        time.sleep(0.5)

        available = bucket.get_available_tokens()
        assert 3.5 <= available <= 6.5

    def test_refill_does_not_exceed_capacity(self):
        """Refill should not exceed bucket capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=100.0)

        bucket.acquire(tokens=5)

        time.sleep(1.0)

        available = bucket.get_available_tokens()
        assert available <= 10.0

    def test_concurrent_acquire_is_thread_safe(self):
        """Concurrent acquire() should be safe via Lock."""
        bucket = TokenBucket(capacity=100, refill_rate=1.0)
        results = []

        def acquire_token():
            result = bucket.acquire(tokens=1)
            results.append(result)

        threads = []
        for _ in range(100):
            thread = threading.Thread(target=acquire_token)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 100
        assert all(results)

        assert bucket.get_available_tokens() < 1.0

    def test_get_available_tokens_includes_refill(self):
        """get_available_tokens() should account for time-based refill."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)

        bucket.acquire(tokens=10)

        assert bucket.get_available_tokens() < 0.5

        time.sleep(0.2)

        available = bucket.get_available_tokens()
        assert 1.5 <= available <= 4.0
