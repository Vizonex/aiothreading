# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

"""
made for threading coroutines over asyncio.
"""

from .core import Thread, Worker
from .pool import ThreadPool, ThreadPoolResult
from .types import PrematureStopException, QueueID, TaskID

__authors__ = ["Vizonex", "x42005e1f"]
__version__ = "0.2.0"


__all__ = (
    "PrematureStopException",
    "QueueID",
    "TaskID",
    "Thread",
    "ThreadPool",
    "ThreadPoolResult",
    "Worker",
)
