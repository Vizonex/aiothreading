# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

import asyncio
import logging
import threading
from typing import Any, Callable, Dict, Optional, Sequence

from .types import Context, R, Unit

log = logging.getLogger(__name__)


# NOTE: Were not using multiprocessing however it's a good idea to
# have a Context to prevent variables from bleeding out
context = Context()


async def not_implemented(*args: Any, **kwargs: Any) -> None:
    """Default function to call when none given."""
    raise NotImplementedError()


def get_context() -> Context:
    """Get the current active global context."""
    global context
    return context


class Thread:
    """Execute a coroutine on a spreate thread"""

    def __init__(
        self,
        group: None = None,
        target: Callable = None,
        name: str = None,
        args: Sequence[Any] = None,
        kwargs: Dict[str, Any] = None,
        *,
        daemon: bool = None,
        initializer: Optional[Callable] = None,
        initargs: Sequence[Any] = (),
        loop_initializer: Optional[Callable] = None,
        thread_target: Optional[Callable] = None,
    ) -> None:
        # From aiomultiprocess
        if target is not None and not asyncio.iscoroutinefunction(target):
            raise ValueError("target must be coroutine function")

        if initializer is not None and asyncio.iscoroutinefunction(initializer):
            raise ValueError("initializer must be synchronous function")

        if loop_initializer is not None and asyncio.iscoroutinefunction(
            loop_initializer
        ):
            raise ValueError("loop_initializer must be synchronous function")

        self.unit = Unit(
            target=target or not_implemented,
            args=args or (),
            kwargs=kwargs or {},
            initializer=initializer,
            initargs=initargs,
            loop_initializer=loop_initializer,
        )
        self.aio_thread = threading.Thread(
            group=group,
            target=thread_target or Thread.run_async,
            args=(self.unit,),
            name=name,
            daemon=daemon,
        )

        # Special object/Event used to determine if were done or not...
        self.is_complete = threading.Event()

    def __await__(self) -> Any:
        """Enable awaiting of the thread result by chaining to `start()` & `join()`."""
        if not self.is_alive():
            self.start()

        return self.join().__await__()

    def start(self) -> None:
        """Start the child process."""
        return self.aio_thread.start()

    async def join(self, timeout: Optional[int] = None) -> None:
        """Wait for the process to finish execution without blocking the main thread."""
        if not self.is_alive():
            raise ValueError("must start thread before joining it")

        if timeout is not None:
            return await asyncio.wait_for(self.join(), timeout)

        while self.aio_thread.is_alive():
            await asyncio.sleep(0.005)

    @staticmethod
    def run_async(unit: Unit) -> R:
        """Initialize the child thread and event loop, then execute the coroutine."""
        try:
            if unit.loop_initializer is None:
                loop = asyncio.new_event_loop()
            else:
                loop = unit.loop_initializer()

            asyncio.set_event_loop(loop)

            if unit.initializer:
                unit.initializer(*unit.initargs)

            # TODO: Provide clean exit methods to thread even
            # though threading isn't nessesarly designed for
            # clean exits...
            result: R = loop.run_until_complete(unit.target(*unit.args, **unit.kwargs))

            # Shudown everything after so that nothing complains back to us with a RuntimeWarning
            asyncio.set_event_loop(None)
            loop.close()
            return result

        except Exception as e:
            log.exception(f"aio thread {threading.get_ident()} failed")
            # Shutdown the loop if there was indeed failure...
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                pass
            raise e

    def start(self) -> None:
        """Start the child thread."""
        return self.aio_thread.start()

    @property
    def name(self):
        """Child Thread Name."""
        return self.aio_thread.name

    def is_alive(self) -> bool:
        """Is the thread running."""
        return self.aio_thread.is_alive()

    @property
    def daemon(self) -> bool:
        """Should the thread be a daemon."""
        return self.aio_thread.daemon

    @daemon.setter
    def daemon(self, value: bool):
        """Should the thread be a daemon."""
        self.aio_thread.daemon = value

    @property
    def ident(self) -> Optional[int]:
        """Thread Identifier of the thread, or None if not started"""
        return self.aio_thread.ident

    @property
    def native_id(self) -> Optional[int]:
        """Native integral thread ID of this thread, or None if it has not been started."""
        return self.aio_thread.native_id


class Worker(Thread):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, thread_target=Worker.run_async, **kwargs)
        self.unit.namespace.result = None

    @staticmethod
    def run_async(unit: Unit) -> R:
        """Initialize the thread and event loop, then execute the coroutine."""
        try:
            result: R = Thread.run_async(unit)
            unit.namespace.result = result
            return result

        except BaseException as e:
            unit.namespace.result = e
            raise

    async def join(self, timeout: int = None) -> Any:
        """Wait for the worker to finish, and return the final result."""
        await super().join(timeout)
        return self.result

    @property
    def result(self) -> R:
        """Easy access to the resulting value from the coroutine."""
        if self.unit.namespace.result is None:
            raise ValueError("coroutine not completed")

        return self.unit.namespace.result


