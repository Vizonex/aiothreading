# Copyright 2022 Amethyst Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

import enum
from asyncio import AbstractEventLoop, Task
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    Literal,
    NewType,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from aiologic import Event, SimpleQueue
from aiologic.lowlevel import Flag

T = TypeVar("T")
R = TypeVar("R")

Queue = SimpleQueue

TaskID = NewType("TaskID", int)
QueueID = NewType("QueueID", int)

TracebackStr = str

LoopInitializer = Callable[..., AbstractEventLoop]
PoolTask = Optional[Tuple[TaskID, Callable[..., R], Sequence[T], Dict[str, T]]]
PoolResult = Tuple[TaskID, Optional[R], Optional[TracebackStr]]


class StopEnum(enum.Enum):
    PREMATURE_STOP = enum.auto()


class Namespace(Generic[R]):
    result: Union[R, Literal[StopEnum.PREMATURE_STOP]]
    exception: Union[Optional[BaseException], Literal[StopEnum.PREMATURE_STOP]]


@dataclass
class Unit(Generic[R]):
    """Container for what to call on the child thread."""

    target: Callable[..., Coroutine[Any, Any, R]]
    args: Sequence[Any]
    kwargs: Dict[str, Any]
    namespace: Namespace[R]
    stop_flag: Flag[Optional[Tuple[AbstractEventLoop, Task[R]]]]
    complete_event: Event
    initializer: Optional[Callable[..., Any]] = None
    initargs: Sequence[Any] = ()
    loop_initializer: Optional[LoopInitializer] = None


class ProxyException(Exception):
    pass


class PrematureStopException(Exception):
    """Raised when a `Worker` Stopped Mid-Execution"""
