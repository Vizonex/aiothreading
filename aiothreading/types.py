# Copied from aiomultiprocess with a few modifications

import threading
from queue import Queue
from contextvars import Context
from asyncio import BaseEventLoop
from typing import (
    Any,
    Callable,
    Dict,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

T = TypeVar("T")
R = TypeVar("R")


TaskID = NewType("TaskID", int)
QueueID = NewType("QueueID", int)

TracebackStr = str

LoopInitializer = Callable[..., BaseEventLoop]
PoolTask = Optional[Tuple[TaskID, Callable[..., R], Sequence[T], Dict[str, T]]]
PoolResult = Tuple[TaskID, Optional[R], Optional[TracebackStr]]


class Namespace:
    def __init__(self) -> None:
        self.result = None 

class Unit(NamedTuple):
    """Container for what to call on the thread."""

    target: Callable
    args: Sequence[Any]
    kwargs: Dict[str, Any]
    namespace: Optional[Namespace] = Namespace()
    initializer: Optional[Callable] = None
    initargs: Sequence[Any] = ()
    loop_initializer: Optional[LoopInitializer] = None
    runner: Optional[Callable] = None

class ProxyException(Exception):
    pass
