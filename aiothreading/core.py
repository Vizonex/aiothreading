# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex
# 2025 Modified by x42005e1f

import asyncio
import threading
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Generic,
    Literal,
    NoReturn,
    Optional,
    Sequence,
    Union,
)

from aiologic import Event
from aiologic.lowlevel import Flag

from .types import (
    LoopInitializer,
    Namespace,
    PrematureStopException,
    R,
    StopEnum,
    Unit,
)


async def not_implemented(*args: Any, **kwargs: Any) -> NoReturn:
    """Default function to call when none given."""
    raise NotImplementedError


# asyncio.runners._cancel_all_tasks
def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    to_cancel = asyncio.all_tasks(loop)

    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue

        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during run_async() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


class Thread(Generic[R]):
    """Execute a coroutine on a spreate thread"""

    def __init__(
        self,
        group: None = None,
        target: Optional[Callable[..., Coroutine[Any, Any, R]]] = None,
        name: Optional[str] = None,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        *,
        daemon: Optional[bool] = None,
        initializer: Optional[Callable[..., Any]] = None,
        initargs: Sequence[Any] = (),
        loop_initializer: Optional[LoopInitializer] = None,
        thread_target: Optional[Callable[..., Any]] = None,
    ) -> None:
        if target is not None and not asyncio.iscoroutinefunction(target):
            raise ValueError("target must be coroutine function")

        if initializer is not None and asyncio.iscoroutinefunction(
            initializer
        ):
            raise ValueError("initializer must be synchronous function")

        if loop_initializer is not None and asyncio.iscoroutinefunction(
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
        """Enable awaiting of the thread result by chaining to `start()` & `join()`."""
        if not self.is_started():
            self.start()

        return (yield from self.join().__await__())

    @staticmethod
    def run_async(
        unit: Unit[R], *, _set_complete_event: bool = True
    ) -> Union[R, Literal[StopEnum.PREMATURE_STOP]]:
        """Initialize the child thread and event loop, then execute the coroutine."""
        try:
            if unit.loop_initializer is None:
                loop = asyncio.new_event_loop()
            else:
                loop = unit.loop_initializer()

            asyncio.set_event_loop(loop)

            try:
                if unit.initializer:
                    unit.initializer(*unit.initargs)

                task: asyncio.Task[R] = loop.create_task(
                    unit.target(
                        *unit.args,
                        **unit.kwargs,
                    )
                )

                if not unit.stop_flag.set((loop, task)):
                    task.cancel()

                try:
                    return loop.run_until_complete(task)
                except asyncio.CancelledError:
                    # Suppress MainTask's cancellation only...
                    if not task.cancelled():
                        raise

                    return StopEnum.PREMATURE_STOP
            finally:
                try:
                    _cancel_all_tasks(loop)
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.run_until_complete(loop.shutdown_default_executor())
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()
        finally:
            if _set_complete_event:
                unit.complete_event.set()

    def start(self) -> None:
        """Start the child thread."""
        return self.aio_thread.start()

    async def join(self, timeout: Optional[float] = None) -> Any:
        """Wait for the process to finish execution without blocking the main thread."""
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
    def ident(self) -> Optional[int]:
        """Thread ID of child, or None if not started."""
        return self.aio_thread.ident

    @property
    def native_id(self) -> Optional[int]:
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
    # TODO: fix __init__ and all arguments to it.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, thread_target=None, **kwargs)

    def __await__(self) -> Generator[Any, Any, R]:
        """Enable awaiting of the thread result by chaining to `start()` & `join()`."""
        if not self.is_started():
            self.start()

        return (yield from self.join().__await__())

    @staticmethod
    def run_async(
        unit: Unit[R], *, _set_complete_event: bool = True
    ) -> Union[R, Literal[StopEnum.PREMATURE_STOP]]:
        """Initialize the child thread and event loop, then execute the coroutine."""
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

    async def join(self, timeout: Optional[float] = None) -> R:
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
    def exception(self) -> Optional[BaseException]:
        """Easy access to the exception from the coroutine."""
        if not self.is_stopped():
            raise ValueError("coroutine not completed")

        exception = self.unit.namespace.exception

        if exception is StopEnum.PREMATURE_STOP:
            raise PrematureStopException("Thread was stopped prematurely...")

        return exception
