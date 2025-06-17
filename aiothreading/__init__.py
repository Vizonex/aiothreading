# Copyright 2022 Amy Reese
# Licensed under the MIT license
# 2024 Modified by Vizonex

"""
made for threading coroutines over asyncio.
"""

__authors__ = ["Vizonex", "x42005e1f"]

from .__version__ import __version__
from .core import Thread, Worker
from .pool import ThreadPool, ThreadPoolResult
from .scheduler import RoundRobin, Scheduler
from .types import QueueID, TaskID
