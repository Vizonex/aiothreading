# Copyright 2022 Amy Reese
# Licensed under the MIT license

# 2024 Modfified By Vizonex

import asyncio
import os
import threading
from functools import wraps
from unittest import skipUnless


RUN_PERF_TESTS = bool(os.environ.get("PERF_TESTS", False))


def do_nothing():
    return


async def two():
    return 2


async def sleepy():
    await asyncio.sleep(0.1)
    return threading.get_native_id()


async def mapper(value):
    return value * 2


async def starmapper(*values):
    return [value * 2 for value in values]


DUMMY_CONSTANT = None


def initializer(value):
    global DUMMY_CONSTANT

    DUMMY_CONSTANT = value
    _loop = asyncio.get_event_loop()


async def get_dummy_constant():
    return DUMMY_CONSTANT


async def raise_fn():
    raise RuntimeError("raising")


async def terminate(process):
    await asyncio.sleep(0.5)
    process.terminate()


def async_test(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(fn(*args, **kwargs))
    return wrapper


def perf_test(fn):
    @wraps(fn)
    @skipUnless(RUN_PERF_TESTS, "Performance test")
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(fn(*args, **kwargs))
    return wrapper
