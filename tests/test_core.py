# # Modified by Vizonex

import asyncio
import threading
from typing import Callable

import pytest

from aiothreading import PrematureStopException, Thread, Worker


async def sleepy() -> int:
    await asyncio.sleep(0.1)
    return threading.get_native_id()


SleepyThread = Callable[..., Thread[int]]
SleepyWorker = Callable[..., Worker[int]]

EternityThread = Callable[..., Thread[None]]
EternityWorker = Callable[..., Worker[None]]


@pytest.mark.asyncio
async def test_thread(sleepy_thread: SleepyThread) -> None:
    p = sleepy_thread()
    p.start()

    assert p.name == "sleepy_thread"
    assert p.native_id
    assert p.is_alive()

    await p.join()
    assert not p.is_alive()


@pytest.mark.asyncio
async def test_thread_await_1(sleepy_thread: SleepyThread) -> None:
    await sleepy_thread()


@pytest.mark.asyncio
async def test_thread_await_2(sleepy_thread: SleepyThread) -> None:
    t = sleepy_thread()
    t.start()
    await t


@pytest.mark.asyncio
async def test_thread_join(sleepy_thread: SleepyThread) -> None:
    t = sleepy_thread()
    t.start()
    await t.join()

    t = sleepy_thread()
    with pytest.raises(
        RuntimeError, match="must start thread before joining it"
    ):
        await t.join()


@pytest.mark.asyncio
async def test_thread_daemon(sleepy_thread: SleepyThread) -> None:
    p = sleepy_thread()
    assert not p.daemon
    p.daemon = True
    assert p.daemon
    p.start()
    await p.join()


@pytest.mark.asyncio
async def test_thread_join_timeout(sleepy_thread: SleepyThread) -> None:
    t = sleepy_thread()
    t.start()
    # Should take no longer than 0.05 seconds so let's give it 0.1...
    await t.join(0.1)


@pytest.mark.asyncio
async def test_thread_join_timeout_2(enternity_thread: EternityThread) -> None:
    t = enternity_thread()
    t.start()
    with pytest.raises(asyncio.exceptions.TimeoutError):
        await t.join(0.01)
    # I'm not waiting 5 minutes, no sir :/
    t.terminate()


@pytest.mark.asyncio
async def test_thread_termination(enternity_thread: EternityThread) -> None:
    et = enternity_thread()
    et.start()
    loop = asyncio.get_event_loop()
    start = loop.time()
    et.terminate()
    end = loop.time()
    await et
    assert (end - start) < 300, "termination failed"


@pytest.mark.asyncio
async def test_worker(sleepy_woker: SleepyWorker) -> None:
    p = sleepy_woker()
    p.start()

    assert p.name == "sleepy_worker"
    native_id = p.native_id
    assert p.is_alive()

    result = await p.join()
    assert result == native_id
    assert not p.is_alive()


@pytest.mark.asyncio
async def test_worker_terminate(enternity_worker: EternityWorker) -> None:
    et = enternity_worker()
    et.start()
    loop = asyncio.get_event_loop()
    start = loop.time()
    et.terminate()
    end = loop.time()
    with pytest.raises(
        PrematureStopException, match="Thread was stopped prematurely..."
    ):
        await et
    assert (end - start) < 300, "termination failed"
