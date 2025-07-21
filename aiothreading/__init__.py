# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

"""
made for threading coroutines over asyncio.
"""

__authors__ = ["Vizonex", "x42005e1f"]

from .__version__ import (
    __version__ as __version__,
)
from .core import (
    Thread as Thread,
    Worker as Worker,
)
from .pool import (
    ThreadPool as ThreadPool,
    ThreadPoolResult as ThreadPoolResult,
)
from .scheduler import (
    RoundRobin as RoundRobin,
    Scheduler as Scheduler,
)
from .types import (
    PrematureStopException as PrematureStopException,
    QueueID as QueueID,
    TaskID as TaskID,
)
