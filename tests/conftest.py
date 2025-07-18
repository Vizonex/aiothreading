import asyncio
import sys
import threading
from functools import partial
from typing import Any, Callable

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


def thread(*args, **kwargs) -> partial[Thread[Any]]:  # type: ignore[no-untyped-def]
    return partial(Thread, *args, **kwargs)


def worker(*args, **kwargs) -> partial[Worker[Any]]:  # type: ignore[no-untyped-def]
    return partial(Worker, *args, **kwargs)


def threadpool(*args, **kwargs) -> partial[ThreadPool]:  # type: ignore[no-untyped-def]
    return partial(ThreadPool, *args, **kwargs)


@pytest.fixture(  # type: ignore[misc]
    scope="session",
    params=(
        thread(target=_sleepy, name="sleepy_thread"),
        pytest.param(
            thread(
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
        worker(target=_sleepy, name="sleepy_worker"),
        pytest.param(
            worker(
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
        thread(target=_eternity, name="enternity_thread"),
        pytest.param(
            thread(
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
        worker(target=_eternity, name="enternity_thread"),
        pytest.param(
            worker(
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
        threadpool(),
        pytest.param(
            threadpool(loop_initializer=new_uv_event_loop),
            marks=UV_MARK,
        ),
    ),
)
def thread_pool_type(
    request: pytest.FixtureRequest,
) -> Callable[..., ThreadPool]:
    return request.param  # type: ignore[no-any-return]
