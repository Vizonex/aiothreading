import asyncio
import sys
import threading
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from typing import Any, Callable, Coroutine, Generic

import pytest

from aiothreading import Thread, ThreadPool, Worker
from aiothreading.types import R

UVLOOP_MODULE = "uvloop" if sys.platform != "win32" else "winloop"

try:
    uvloop = import_module(UVLOOP_MODULE)
except ModuleNotFoundError:
    uvloop = None  # type: ignore[assignment]


async def _sleepy() -> int:
    await asyncio.sleep(0.05)
    return threading.get_native_id()


async def _eternity() -> None:
    await asyncio.sleep(300)


def factories() -> list[tuple[str, Callable[..., asyncio.AbstractEventLoop]]]:
    _factories = [("asyncio", asyncio.new_event_loop)]
    if uvloop is not None:
        _factories.append((UVLOOP_MODULE, uvloop.new_event_loop))
    return _factories


@dataclass(frozen=True)
class StandardLoopFactory:
    """Standard loop factories for anyio,
    examples: (uvloop, winloop, asyncio, rloop)"""

    name: str
    loop_factory: Callable[..., asyncio.AbstractEventLoop]

    def __str__(self) -> str:
        return self.name

    def factory(
        self,
    ) -> tuple[str, dict[str, Callable[..., asyncio.AbstractEventLoop]]]:
        """simplest and most creative shortcut to this mess..."""
        return ("asyncio", {"loop_factory": self.loop_factory})


@pytest.fixture(
    params=[
        StandardLoopFactory(name, factory) for name, factory in factories()
    ],
    ids=str,
)
def anyio_backend(
    request: pytest.FixtureRequest,
) -> list[tuple[str, dict[str, Callable[..., asyncio.AbstractEventLoop]]]]:
    return request.param.factory()  # type: ignore[no-any-return]


@dataclass
class ThreadFixture(Generic[R]):
    name: str
    loop_name: str
    thread_type: type[Thread[R]]
    target: Callable[..., Coroutine[Any, Any, R]]
    loop_initalizer: Callable[..., asyncio.AbstractEventLoop]

    def __str__(self) -> str:
        return f"{self.name}+{self.loop_name}"

    def factory(self) -> Thread[R]:
        return self.thread_type(
            target=self.target,
            name=self.name,
            loop_initializer=self.loop_initalizer,
        )


@dataclass
class ThreadPoolFixture:
    name: str
    thread_type: type[ThreadPool]
    loop_initalizer: Callable[..., asyncio.AbstractEventLoop]

    def __str__(self) -> str:
        return self.name

    def factory(self) -> Callable[..., ThreadPool]:
        return partial(self.thread_type, loop_initializer=self.loop_initalizer)


def thread_fixtures(
    thread_type: type[Thread[R]],
    target: Callable[..., Coroutine[Any, Any, R]],
    name: str,
) -> list[ThreadFixture[R]]:
    return [
        ThreadFixture(name, loop_name, thread_type, target, factory)
        for loop_name, factory in factories()
    ]


def thread_pool_fixtures(
    thread_pool_type: type[ThreadPool],
) -> list[ThreadPoolFixture]:
    return [
        ThreadPoolFixture(name, thread_pool_type, factory)
        for name, factory in factories()
    ]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Thread, _sleepy, "sleepy_thread"),
    ids=str,
)
def sleepy_thread(
    request: pytest.FixtureRequest,
) -> Callable[..., Thread[int]]:
    return request.param.factory  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Worker, _sleepy, "sleepy_worker"),
    ids=str,
)
def sleepy_woker(request: pytest.FixtureRequest) -> Callable[..., Thread[int]]:
    return request.param.factory  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Thread, _eternity, "enternity_thread"),
    ids=str,
)
def enternity_thread(
    request: pytest.FixtureRequest,
) -> Callable[[], Thread[int]]:
    return request.param.factory  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Worker, _eternity, "enternity_worker"),
    ids=str,
)
def enternity_worker(
    request: pytest.FixtureRequest,
) -> Callable[..., Worker[None]]:
    return request.param.factory  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session", params=thread_pool_fixtures(ThreadPool), ids=str
)
def thread_pool_type(
    request: pytest.FixtureRequest,
) -> Callable[..., ThreadPool]:
    return request.param.factory()  # type: ignore[no-any-return]
