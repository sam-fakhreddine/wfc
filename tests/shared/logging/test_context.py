"""Unit tests for request context middleware."""

import asyncio
import pytest

from wfc.shared.logging.context import (
    request_context,
    get_request_id,
    set_request_id,
    clear_request_id,
)


class TestRequestContext:
    """Test request context management."""

    def test_generate_request_id(self):
        """Test that request context generates a UUID."""
        with request_context() as request_id:
            assert request_id is not None
            assert isinstance(request_id, str)
            assert len(request_id) == 36

    def test_get_request_id_in_context(self):
        """Test getting request_id from context."""
        with request_context() as request_id:
            retrieved_id = get_request_id()
            assert retrieved_id == request_id

    def test_get_request_id_outside_context(self):
        """Test getting request_id outside context returns None."""
        clear_request_id()
        request_id = get_request_id()
        assert request_id is None

    def test_set_request_id_manually(self):
        """Test manually setting request_id."""
        test_id = "test-request-123"
        set_request_id(test_id)

        retrieved_id = get_request_id()
        assert retrieved_id == test_id

        clear_request_id()

    def test_nested_contexts(self):
        """Test that nested contexts maintain separate request_ids."""
        with request_context() as outer_id:
            outer_retrieved = get_request_id()
            assert outer_retrieved == outer_id

            with request_context() as inner_id:
                inner_retrieved = get_request_id()
                assert inner_retrieved == inner_id
                assert inner_id != outer_id

            back_to_outer = get_request_id()
            assert back_to_outer == outer_id

    @pytest.mark.asyncio
    async def test_async_context_isolation(self):
        """Test that context is isolated between async tasks."""
        results = []

        async def task_with_context(task_num):
            with request_context() as request_id:
                await asyncio.sleep(0.01)
                retrieved_id = get_request_id()
                results.append((task_num, request_id, retrieved_id))

        await asyncio.gather(task_with_context(1), task_with_context(2), task_with_context(3))

        assert len(results) == 3
        request_ids = [r[1] for r in results]

        assert len(set(request_ids)) == 3

        for task_num, original_id, retrieved_id in results:
            assert original_id == retrieved_id

    def test_clear_request_id(self):
        """Test clearing request_id."""
        set_request_id("test-123")
        assert get_request_id() == "test-123"

        clear_request_id()
        assert get_request_id() is None

    def test_context_manager_cleanup(self):
        """Test that context manager cleans up after exit."""
        with request_context() as request_id:
            assert get_request_id() == request_id

        assert get_request_id() is None

    def test_unique_request_ids(self):
        """Test that each context generates a unique request_id."""
        ids = []
        for _ in range(10):
            with request_context() as request_id:
                ids.append(request_id)

        assert len(set(ids)) == 10
