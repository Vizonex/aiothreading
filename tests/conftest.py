import asyncio
import sys
import threading
from functools import partial
from typing import Callable

import pytest
from _pytest.mark.structures import ParameterSet  # typehinting

from aiothreading import Thread, ThreadPool, Worker
from aiothreading.types import R

try:
    if sys.platform != "win32":
        import uvloop
    else:
        import winloop as uvloop
except ModuleNotFoundError:
    uvloop = None


async def _sleepy() -> int:
    await asyncio.sleep(0.05)
    return threading.get_native_id()


async def _eternity() -> None:
    await asyncio.sleep(300)


@pytest.fixture(
    params=[
        pytest.param(
            ("asyncio", {"loop_factory": uvloop.new_event_loop}),
            id="asyncio+uvloop",
        ),
        pytest.param(
            ("asyncio", {"loop_factory": uvloop.new_event_loop}), id="asyncio"
        ),
        # TODO: Coming soon...
        # pytest.param(('trio', {'restrict_keyboard_interrupt_to_checkpoints': True}), id='trio')
    ]
)
def anyio_backend(request):
    return request.param


def thread_fixtures(
    thread_type: type[Thread], target: Callable[..., R], name: str
) -> list[ParameterSet]:
    if uvloop is not None:
        return [
            pytest.param(
                partial(thread_type, target=target, name=name),
                id="asyncio-thread",
            ),
            pytest.param(
                partial(
                    thread_type,
                    target=target,
                    name=name,
                    loop_initializer=uvloop.new_event_loop,
                ),
                id="uvloop-thread",
            ),
        ]
    else:
        return [
            pytest.param(
                partial(thread_type, target=target, name=name),
                id="asyncio-thread",
            )
        ]


def thread_pool_fixtures(
    thread_pool_type: type[ThreadPool],
) -> list[ParameterSet]:
    if uvloop is not None:
        return [
            pytest.param(thread_pool_type, id="threadpool-asyncio"),
            pytest.param(
                partial(
                    thread_pool_type, loop_initializer=uvloop.new_event_loop
                ),
                id="threadpool-uvloop",
            ),
        ]
    else:
        return [
            pytest.param(thread_pool_type, id="threadpool-asyncio"),
        ]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Thread, _sleepy, "sleepy_thread"),
)
def sleepy_thread(
    request: pytest.FixtureRequest,
) -> Callable[..., Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session", params=thread_fixtures(Worker, _sleepy, "sleepy_worker")
)
def sleepy_woker(request: pytest.FixtureRequest) -> Callable[..., Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Thread, _eternity, "enternity_thread"),
)
def enternity_thread(
    request: pytest.FixtureRequest,
) -> Callable[[], Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(
    scope="session",
    params=thread_fixtures(Worker, _eternity, "enternity_worker"),
)
def enternity_worker(
    request: pytest.FixtureRequest,
) -> Callable[..., Worker[None]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(scope="session", params=thread_pool_fixtures(ThreadPool))
def thread_pool_type(
    request: pytest.FixtureRequest,
) -> Callable[..., ThreadPool]:
    return request.param  # type: ignore[no-any-return]
