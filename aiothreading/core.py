# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex
# 2025 Modified by x42005e1f

import asyncio
import sys
import threading
from collections.abc import Callable, Coroutine, Generator, Sequence
from inspect import iscoroutinefunction
from typing import Any, Generic, Literal, NoReturn

from aiologic import Event, Flag

from .types import (
    LoopInitializer,
    Namespace,
    PrematureStopException,
    R,
    StopEnum,
    Unit,
)

if sys.version_info >= (3, 11):
    from asyncio import Runner
else:
    from taskgroup import Runner


def _asyncio_run(unit: Unit[R]) -> R | Literal[StopEnum.PREMATURE_STOP]:
    with Runner(loop_factory=unit.loop_initializer) as runner:
        if unit.initializer:
            unit.initializer(*unit.initargs)

        task: asyncio.Task[R] | None = None

        async def main() -> R:
            nonlocal task

            loop = asyncio.get_running_loop()
            task = asyncio.current_task()
            assert task is not None

            if not unit.stop_flag.set((loop, task)):
                task.cancel()

            return await unit.target(*unit.args, **unit.kwargs)

        try:
            return runner.run(main())
        except asyncio.CancelledError:
            # Suppress MainTask's cancellation only...
            if task is not None and not task.cancelled():
                raise

            return StopEnum.PREMATURE_STOP
        finally:
            del task  # break reference cycles


async def not_implemented(*args: Any, **kwargs: Any) -> NoReturn:
    """Default function to call when none given."""
    raise NotImplementedError


class Thread(Generic[R]):
    """Execute a coroutine on a spreate thread"""

    __slots__ = ("unit", "aio_thread", "__weakref__")

    def __init__(
        self,
        group: None = None,
        target: Callable[..., Coroutine[Any, Any, R]] | None = None,
        name: str | None = None,
        args: Sequence[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        *,
        daemon: bool | None = None,
        initializer: Callable[..., Any] | None = None,
        initargs: Sequence[Any] = (),
        loop_initializer: LoopInitializer | None = None,
        thread_target: Callable[..., Any] | None = None,
    ) -> None:
        if target is not None and not iscoroutinefunction(target):
            raise ValueError("target must be coroutine function")

        if initializer is not None and iscoroutinefunction(initializer):
            raise ValueError("initializer must be synchronous function")

        if loop_initializer is not None and iscoroutinefunction(
            loop_initializer
        ):
            raise ValueError("loop_initializer must be synchronous function")

        self.unit = Unit(
            target=target or not_implemented,
            args=args or (),
            kwargs=kwargs or {},
            namespace=Namespace(),
            stop_flag=Flag(),
            complete_event=Event(),
            initializer=initializer,
            initargs=initargs,
            loop_initializer=loop_initializer,
        )
        self.aio_thread = threading.Thread(
            group=group,
            target=thread_target or self.run_async,
            args=(self.unit,),
            name=name,
            daemon=daemon,
        )

    def __await__(self) -> Any:
        """Enable awaiting of the thread result
        by chaining to `start()` & `join()`."""
        if not self.is_started():
            self.start()

        return (yield from self.join().__await__())

    @staticmethod
    def run_async(
        unit: Unit[R], *, _set_complete_event: bool = True
    ) -> R | Literal[StopEnum.PREMATURE_STOP]:
        """Initializes the child thread and event loop,
        then executes the coroutine."""
        try:
            return _asyncio_run(unit)  # type: ignore[arg-type]
        finally:
            if _set_complete_event:
                unit.complete_event.set()

    def start(self) -> None:
        """Start the child thread."""
        return self.aio_thread.start()

    async def join(self, timeout: float | None = None) -> Any:
        """Wait for the process to finish execution without
        blocking the main thread."""
        if not self.is_started():
            raise RuntimeError("must start thread before joining it")

        if timeout is not None:
            await asyncio.wait_for(self.unit.complete_event, timeout)
        else:
            await self.unit.complete_event

    @property
    def name(self) -> str:
        """Child thread name."""
        return self.aio_thread.name

    @property
    def ident(self) -> int | None:
        """Thread ID of child, or None if not started."""
        return self.aio_thread.ident

    @property
    def native_id(self) -> int | None:
        """Native thread ID of child, or None if not started."""
        return self.aio_thread.native_id

    def is_started(self) -> bool:
        """Is child thread started."""
        return self.aio_thread.is_alive() or bool(self.unit.complete_event)

    def is_alive(self) -> bool:
        """Is child thread running."""
        return self.aio_thread.is_alive() and not self.unit.complete_event

    def is_stopped(self) -> bool:
        """Is child thread stopped."""
        return bool(self.unit.complete_event)

    @property
    def daemon(self) -> bool:
        """Should child thread be daemon."""
        return self.aio_thread.daemon

    @daemon.setter
    def daemon(self, value: bool) -> None:
        """Should child thread be daemon."""
        self.aio_thread.daemon = value

    def terminate(self) -> None:
        """Terminates child thread from running"""
        if not self.unit.stop_flag.set(None):
            loop_task = self.unit.stop_flag.get()

            if loop_task is not None:
                loop, task = loop_task

                try:
                    loop.call_soon_threadsafe(task.cancel)
                except RuntimeError:  # event loop is closed
                    pass


class Worker(Thread[R]):
    def __init__(
        self,
        group: None = None,
        target: Callable[..., Coroutine[Any, Any, R]] | None = None,
        name: str | None = None,
        args: Sequence[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        *,
        daemon: bool | None = None,
        initializer: Callable[..., Any] | None = None,
        initargs: Sequence[Any] = (),
        loop_initializer: LoopInitializer | None = None,
    ) -> None:
        super().__init__(
            group,
            target,
            name,
            args,
            kwargs,
            daemon=daemon,
            initializer=initializer,
            initargs=initargs,
            loop_initializer=loop_initializer,
            thread_target=None,
        )

    def __await__(self) -> Generator[Any, Any, R]:
        """Enable awaiting of the thread result by chaining to
        `start()` & `join()`."""
        if not self.is_started():
            self.start()

        return (yield from self.join().__await__())

    @staticmethod
    def run_async(
        unit: Unit[R], *, _set_complete_event: bool = True
    ) -> R | Literal[StopEnum.PREMATURE_STOP]:
        """Initializes the child thread and event loop,
        then executes the coroutine."""
        try:
            unit.namespace.result = result = Thread.run_async(
                unit,
                _set_complete_event=False,
            )

            if result is StopEnum.PREMATURE_STOP:
                unit.namespace.exception = StopEnum.PREMATURE_STOP
            else:
                unit.namespace.exception = None
        except BaseException as e:
            unit.namespace.result = result = StopEnum.PREMATURE_STOP
            unit.namespace.exception = e
        finally:
            if _set_complete_event:
                unit.complete_event.set()

            del unit  # break a reference cycle with the exception

        return result

    async def join(self, timeout: float | None = None) -> R:
        """Wait for the worker to finish, and return the final result."""
        await super().join(timeout)
        return self.result

    @property
    def result(self) -> R:
        """Easy access to the resulting value from the coroutine."""
        if not self.is_stopped():
            raise ValueError("coroutine not completed")

        exception = self.exception

        if exception is not None:
            try:
                raise exception
            finally:  # break a reference cycle with the exception
                del exception
                del self

        result = self.unit.namespace.result

        if result is StopEnum.PREMATURE_STOP:
            raise PrematureStopException("Thread was stopped prematurely...")

        return result

    @property
    def exception(self) -> BaseException | None:
        """Easy access to the exception from the coroutine."""
        if not self.is_stopped():
            raise ValueError("coroutine not completed")

        exception = self.unit.namespace.exception

        if exception is StopEnum.PREMATURE_STOP:
            raise PrematureStopException("Thread was stopped prematurely...")

        return exception
