# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex
# 2025 Modified by x42005e1f

import asyncio
import os
import sys
from concurrent.futures import Future, InvalidStateError
from functools import partial
from types import TracebackType
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from aiologic import Condition, CountdownEvent, SimpleQueue
from deprecated_params import deprecated_params  # type: ignore[import-untyped]

from .core import Thread
from .types import LoopInitializer, ProxyException, R, T

from deprecation_alias import deprecated


MAX_TASKS_PER_CHILD = (
    0  # number of tasks to execute before recycling a child process
)
CHILD_CONCURRENCY = (
    0  # number of tasks to execute simultaneously per child process
)

_T = TypeVar("_T")


def _on_complete(
    loop: asyncio.AbstractEventLoop,
    task: Optional[asyncio.Task[Any]],
    future: Future[Any],
) -> None:
    if future.cancelled() and task is not None:
        loop.call_soon_threadsafe(task.cancel)


async def _work(
    any_completed: Condition[None],
    all_completed: CountdownEvent,
    exception_handler: Optional[Callable[[BaseException], None]],
    func: Callable[..., Coroutine[Any, Any, Any]],
    args: Sequence[Any],
    kwargs: Dict[str, Any],
    future: Future[Any],
) -> None:
    try:
        if future.cancelled():
            return

        future.add_done_callback(
            partial(
                _on_complete,
                asyncio.get_running_loop(),
                asyncio.current_task(),
            )
        )

        result = await func(*args, **kwargs)
    except BaseException as exc:
        try:
            if exception_handler is not None:
                exception_handler(exc)
        finally:
            # TODO: set original exception instead of ProxyException
            try:
                future.set_exception(
                    ProxyException().with_traceback(
                        exc.__traceback__,
                    )
                )
            except InvalidStateError:  # future is cancelled
                pass
    else:
        try:
            future.set_result(result)
        except InvalidStateError:  # future is cancelled
            pass
    finally:
        any_completed.notify_all()
        all_completed.down()

        del future  # break a reference cycle with the exception


class ThreadPoolWorker(Thread[None]):
    """Individual worker thread for the async pool."""

    def __init__(
        self,
        tx: SimpleQueue[
            Optional[
                tuple[
                    Callable[..., Coroutine[Any, Any, Any]],
                    Sequence[Any],
                    Dict[str, Any],
                    Future[Any],
                ]
            ]
        ],
        concurrency: int = CHILD_CONCURRENCY,
        *,
        exception_handler: Optional[Callable[[BaseException], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(target=self.run, args=None, kwargs=None, **kwargs)

        self.tx = tx
        self.concurrency = concurrency
        self.exception_handler = exception_handler

        self.any_completed = Condition(None)
        self.all_completed = CountdownEvent()

    async def run(self) -> None:
        """Pick up work, schedule work, repeat."""
        while True:
            if self.pending < self.concurrency or self.concurrency <= 0:
                task_info = await self.tx.async_get()

                if task_info is None:
                    break

                self.all_completed.up()
                asyncio.create_task(
                    _work(
                        self.any_completed,
                        self.all_completed,
                        self.exception_handler,
                        *task_info,
                    )
                )
            else:
                await self.any_completed

        await self.all_completed

    def key(self) -> int:
        return len(self.tx) + self.pending

    @property
    def pending(self) -> int:
        return self.all_completed.value


class ThreadPoolResult(Awaitable[Sequence[_T]], AsyncIterable[_T]):
    """
    Asynchronous proxy for map/starmap results. Can be awaited or used with `async for`.
    """

    def __init__(self, futures: Sequence[asyncio.Future[_T]]):
        self.futures = futures

    def __await__(self) -> Generator[Any, Any, Sequence[_T]]:
        """Wait for all results and return them as a sequence"""
        return (yield from self.results().__await__())

    async def results(self) -> Sequence[_T]:
        """Wait for all results and return them as a sequence"""
        return [result async for result in self]

    async def __aiter__(self) -> AsyncIterator[_T]:
        """Return results one-by-one as they are ready"""
        try:
            for future in self.futures:
                yield await future
        finally:
            for future in self.futures:
                future.cancel()

            del future  # break a reference cycle with the exception

    async def results_generator(self) -> AsyncIterator[_T]:
        """Return results one-by-one as they are ready"""
        async for result in self:
            yield result


# NOTE: Not very many things have changed from aiomultiprocess's
# Pool Class Such as the removal of terminating since threads can't terminate
# Pool was also renamed to ThreadPool so aiomultiprocess doesn't overlap itself...


@deprecated_params(
    ["queuecount"], "Unused currently, Scheduled for deletion in 0.1.6"
)
class ThreadPool:
    """Execute coroutines on a pool of threads."""

    def __init__(
        self,
        threads: Optional[int] = None,
        initializer: Optional[Callable[..., Any]] = None,
        initargs: Sequence[Any] = (),
        # Scheduled for removal in soon as a performance optimization
        childconcurrency: int = CHILD_CONCURRENCY,
        loop_initializer: Optional[LoopInitializer] = None,
        exception_handler: Optional[Callable[[BaseException], None]] = None,
        *,
        queuecount: Optional[int] = None,  # queuecount is not used anymore
    ):
        if threads is None:
            if sys.version_info >= (3, 13):
                cpu_count = os.process_cpu_count()
            else:
                cpu_count = os.cpu_count()

            # From concurrent.futures.ThreadPoolExecutor
            threads = min(32, (cpu_count or 1) + 4)

        self.initializer = initializer
        self.initargs = initargs
        self.loop_initializer = loop_initializer
        self.childconcurrency = childconcurrency
        self.exception_handler = exception_handler

        # NOTE: Renamed processes to threads since were dealing with threads - Vizonex

        # Were going to use a list instead of a dictionary for initialization
        # This is more or less an optimization
        self.threads: List[ThreadPoolWorker] = []
        self.thread_count = threads

        self.running = True

    async def __aenter__(self) -> "ThreadPool":
        """Enable `async with ThreadPool() as pool` usage."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Automatically terminate the pool when falling out of scope."""
        self.terminate()
        await self.join()

    def _adjust_thread_count(self) -> None:
        if len(self.threads) < self.thread_count:
            for thread in self.threads:
                if not thread.key():
                    return

            thread = ThreadPoolWorker(
                SimpleQueue(),
                self.childconcurrency,
                initializer=self.initializer,
                initargs=self.initargs,
                loop_initializer=self.loop_initializer,
                exception_handler=self.exception_handler,
            )
            thread.start()

            self.threads.append(thread)

    def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, R]],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Future[R]:
        """Run a single coroutine on the pool."""
        if not self.running:
            raise RuntimeError("pool is closed")

        future: Future[R] = Future()

        self._adjust_thread_count()
        min(self.threads, key=ThreadPoolWorker.key).tx.put(
            (
                func,
                args,
                kwargs,
                future,
            )
        )

        return asyncio.wrap_future(future)

    @deprecated(
        deprecated_in="0.1.5",
        removed_in="0.1.9",
        details="Use submit() method instead",
    )
    async def apply(
        self,
        func: Callable[..., Coroutine[Any, Any, R]],
        args: Optional[Sequence[Any]] = None,
        kwds: Optional[Dict[str, Any]] = None,
    ) -> R:
        """Run a single coroutine on the pool."""
        if not self.running:
            raise RuntimeError("pool is closed")

        args = args or ()
        kwds = kwds or {}

        return await self.submit(func, *args, **kwds)

    def map(
        self,
        func: Callable[[T], Coroutine[Any, Any, R]],
        iterable: Union[Sequence[T], Iterable[T]],
    ) -> ThreadPoolResult[R]:
        """Run a coroutine once for each item in the iterable."""
        if not self.running:
            raise RuntimeError("pool is closed")

        futures = [self.submit(func, item) for item in iterable]

        return ThreadPoolResult(futures)

    def starmap(
        self,
        func: Callable[..., Coroutine[Any, Any, R]],
        iterable: Sequence[Sequence[T]],
    ) -> ThreadPoolResult[R]:
        """Run a coroutine once for each sequence of items in the iterable."""
        if not self.running:
            raise RuntimeError("pool is closed")

        futures = [self.submit(func, *items) for items in iterable]

        return ThreadPoolResult(futures)

    # TODO: Turn Close and Terminate into async functions?
    def close(self) -> None:
        """Close the pool to new visitors."""
        if self.running:
            self.running = False

            # TODO: Better signals for stopping threads from running.
            for thread in self.threads:
                if thread.is_alive():
                    thread.tx.put(None)

    def terminate(self) -> None:
        """No running by the pool!"""
        if self.running:
            self.close()

        for thread in self.threads:
            thread.terminate()

    async def join(self) -> None:
        """Waits for the pool to be finished gracefully."""
        if self.running:
            raise RuntimeError("pool is still open")

        for thread in self.threads:
            await thread.join()
