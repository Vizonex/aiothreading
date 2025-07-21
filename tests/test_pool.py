# Modified by Vizonex

# pylint: disable=import-error,import-outside-toplevel

import asyncio
from typing import Callable

import pytest

from aiothreading import ThreadPool

try:
    import async_timeout

    SKIP_ASYNC_TIMEOUT = False
except ModuleNotFoundError:
    SKIP_ASYNC_TIMEOUT = True


async def waiting(value: int) -> int:
    await asyncio.sleep(0.005)
    return value


async def mapper(value: int) -> int:
    return value * 2


async def starmapper(*values: int) -> list[int]:
    return [value * 2 for value in values]


@pytest.mark.asyncio
async def test_pool(thread_pool_type: Callable[..., ThreadPool]) -> None:
    async with thread_pool_type(2) as s:
        result = await s.submit(mapper, 1)
        assert result == 2


@pytest.mark.asyncio
async def test_pool_map(thread_pool_type: Callable[..., ThreadPool]) -> None:
    data = [i for i in range(40)]
    results = [i * 2 for i in range(40)]
    async with thread_pool_type(2) as s:
        async for d in s.map(mapper, data):
            assert d in results


if not SKIP_ASYNC_TIMEOUT:

    @pytest.mark.asyncio
    async def test_pool_can_execute_quick_enough(
        thread_pool_type: Callable[..., ThreadPool],
    ) -> None:
        data = {i for i in range(40)}
        # I'll give 3 seconds to try and
        # complete all of this
        # if it can't then it has failed me...
        async with async_timeout.timeout(3):
            async with thread_pool_type(2) as pool:
                results = await pool.map(waiting, data)

        # did all of them complete?
        # they don't have to be in order
        assert data == set(results)
