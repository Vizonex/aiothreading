import asyncio
import sys
import threading
from functools import partial
from typing import Callable

import pytest

from aiothreading import Thread, ThreadPool, Worker

# XXX: Policies are deprecated in 3.14 and onwards
if sys.version_info <= (3, 13):
    if sys.platform == "win32":
        from winloop import EventLoopPolicy
    else:
        from uvloop import EventLoopPolicy

    @pytest.fixture(  # type: ignore[misc]
        scope="session",
        params=(
            EventLoopPolicy(),
            asyncio.DefaultEventLoopPolicy(),
        ),
    )
    def event_loop_policy(
        request: pytest.FixtureRequest,
    ) -> asyncio.AbstractEventLoopPolicy:
        return request.param  # type: ignore[no-any-return]


async def _sleepy() -> int:
    await asyncio.sleep(0.05)
    return threading.get_native_id()


async def _eternity() -> None:
    await asyncio.sleep(300)


if sys.platform == "win32":
    from winloop import new_event_loop as new_uv_event_loop

    UV_MARK = pytest.mark.winloop
else:
    from uvloop import new_event_loop as new_uv_event_loop

    UV_MARK = pytest.mark.uvloop


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        partial(Thread, target=_sleepy, name="sleepy_thread"),
        pytest.param(
            partial(
                Worker,
                target=_sleepy,
                name="sleepy_thread",
                loop_initializer=new_uv_event_loop,
            ),
            marks=UV_MARK,
        ),
    ),
)
def sleepy_thread(
    request: pytest.FixtureRequest,
) -> Callable[..., Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        partial(Worker, target=_sleepy, name="sleepy_worker"),
        pytest.param(
            partial(
                Worker,
                target=_sleepy,
                name="sleepy_worker",
                loop_initializer=new_uv_event_loop,
            ),
            marks=UV_MARK,
        ),
    ),
)
def sleepy_woker(request: pytest.FixtureRequest) -> Callable[..., Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        partial(Thread, target=_eternity, name="enternity_thread"),
        pytest.param(
            partial(
                Thread,
                target=_eternity,
                name="enternity_thread",
                loop_initializer=new_uv_event_loop,
            ),
            marks=UV_MARK,
        ),
    ),
)
def enternity_thread(
    request: pytest.FixtureRequest,
) -> Callable[[], Thread[int]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        partial(Worker, target=_eternity, name="enternity_thread"),
        pytest.param(
            partial(
                Worker,
                target=_eternity,
                name="enternity_thread",
                loop_initializer=new_uv_event_loop,
            ),
            marks=UV_MARK,
        ),
    ),
)
def enternity_worker(
    request: pytest.FixtureRequest,
) -> Callable[..., Worker[None]]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        partial(ThreadPool),
        pytest.param(
            partial(ThreadPool, loop_initializer=new_uv_event_loop),
            marks=UV_MARK,
        ),
    ),
)
def thread_pool_type(
    request: pytest.FixtureRequest,
) -> Callable[..., ThreadPool]:
    return request.param  # type: ignore[no-any-return]
