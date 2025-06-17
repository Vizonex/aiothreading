import pytest
import sys 
import asyncio
import pytest_asyncio
from typing import Callable
from aiothreading import Thread, Worker
from functools import partial
import threading

# XXX: Policies are deprecated in 3.14 and onwards
if sys.version_info <= (3, 13):
    if sys.platform == "win32":
        from winloop import EventLoopPolicy
    else:
        from uvloop import EventLoopPolicy
    
    @pytest.fixture(
        scope="session",
        params=(
            EventLoopPolicy(),
            asyncio.DefaultEventLoopPolicy(),
        ),
    )
    def event_loop_policy(request):
        return request.param

async def _sleepy():
    await asyncio.sleep(0.05)
    return threading.get_native_id()

async def _eternity():
    await asyncio.sleep(300)


if sys.platform == "win32":
    from winloop import new_event_loop as new_uv_event_loop
    UV_MARK = pytest.mark.winloop
else:
    from uvloop import new_event_loop as new_uv_event_loop
    UV_MARK = pytest.mark.uvloop


def thread(*args, **kwargs):
    return partial(Thread, *args, **kwargs)

def worker(*args, **kwargs):
    return partial(Worker, *args, **kwargs)



@pytest.fixture(
    scope="session",
    params=(
        thread(target=_sleepy, name="sleepy_thread"),
        pytest.param(
            thread(target=_sleepy, name="sleepy_thread", loop_initializer=new_uv_event_loop),
            marks=UV_MARK
        )
    )
)
def sleepy_thread(request:pytest.FixtureRequest) -> Callable[..., Thread[int]]:
    return request.param

@pytest.fixture(
    scope="session",
    params=(
        worker(target=_sleepy, name="sleepy_worker"),
        pytest.param(
            worker(target=_sleepy, name="sleepy_worker", loop_initializer=new_uv_event_loop),
            marks=UV_MARK
        )
    )
)
def sleepy_woker(request:pytest.FixtureRequest) -> Callable[..., Thread[int]]:
    return request.param


@pytest.fixture(
    scope="session",
    params=(
        thread(target=_eternity, name="enternity_thread"),
        pytest.param(
            thread(target=_eternity, name="enternity_thread", loop_initializer=new_uv_event_loop),
            marks=UV_MARK
        )
    )
)
def enternity_thread(request:pytest.FixtureRequest) -> Callable[[], Thread[int]]:
    return request.param


@pytest.fixture(
    scope="session",
    params=(
        Worker(target=_eternity, name="enternity_thread"),
        pytest.param(
            Worker(target=_eternity, name="enternity_thread", loop_initializer=new_uv_event_loop),
            marks=UV_MARK
        )
    )
)
def enternity_worker(request:pytest.FixtureRequest) -> Callable[..., Worker[None]]:
    return request.param


