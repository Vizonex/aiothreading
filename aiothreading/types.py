# Copyright 2022 Amethyst Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

import enum
from asyncio import AbstractEventLoop, Task
from collections.abc import Callable, Coroutine, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Literal, NewType, TypeVar

from aiologic import Event, Flag, SimpleQueue

T = TypeVar("T")
R = TypeVar("R")

Queue = SimpleQueue

TaskID = NewType("TaskID", int)
QueueID = NewType("QueueID", int)

TracebackStr = str

LoopInitializer = Callable[..., AbstractEventLoop]
PoolTask = tuple[TaskID, Callable[..., R], Sequence[T], dict[str, T]] | None
PoolResult = tuple[TaskID, R | None, TracebackStr | None]


class StopEnum(enum.Enum):
    PREMATURE_STOP = enum.auto()


class Namespace(Generic[R]):
    result: R | Literal[StopEnum.PREMATURE_STOP]
    exception: BaseException | None | Literal[StopEnum.PREMATURE_STOP]


@dataclass
class Unit(Generic[R]):
    """Container for what to call on the child thread."""

    target: Callable[..., Coroutine[Any, Any, R]]
    args: Sequence[Any]
    kwargs: dict[str, Any]
    namespace: Namespace[R]
    stop_flag: Flag[tuple[AbstractEventLoop, Task[R]] | None]
    complete_event: Event
    initializer: Callable[..., Any] | None = None
    initargs: Sequence[Any] = ()
    loop_initializer: LoopInitializer | None = None


class ProxyException(Exception):
    pass


class PrematureStopException(Exception):
    """Raised when a `Worker` Stopped Mid-Execution"""
