"""some other cleaver utilities for use with Threads and asyncio"""

import threading
import asyncio
from typing import Optional


class Lock:
    """A Special lock that can be shared over asyncio and threads alike"""

    def __init__(self) -> None:
        self.lock = threading.Lock()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Returns True if lock was aquired and false if that ended up failing any eventloop can visit this without problems..."""
        if timeout is not None:
            try:
                return await asyncio.wait(self.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # Make sure we don't block so that the loop attempting to aquire the lock can visit other tasks...
            while self.lock.acquire(timeout=0.005) == False:
                await asyncio.sleep(0.005)
            # Lock aquired
            return True

    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self):
        return self.release()

    def release(self) -> None:
        return self.lock.release()

    def locked(self) -> bool:
        return self.lock.locked()


class RLock:
    """A Special lock that can be shared over different asyncio loops and threads alike with RLocking
    Features where a thread can aquire this lock multiple times as long as it's the same thread,
    Asyncio Loops meanwhile can access these on the same threads without blocking"""

    def __init__(self) -> None:
        self.lock = threading.RLock()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Returns True if lock was aquired and false if that ended up failing"""
        if timeout is not None:
            try:
                return await asyncio.wait(self.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # Make sure we don't block so that the loop attempting to aquire the lock can visit other tasks...
            while self.lock.acquire(timeout=0.005) == False:
                await asyncio.sleep(0.005)
            # Lock aquired
            return True

    def sync_aquire(self, blocking: bool = True, timeout: float = -1):
        """From RLock's Python Docs:

            Acquire a lock, blocking or non-blocking.

        When invoked without arguments: if this thread already owns the lock,
        increment the recursion level by one, and return immediately. Otherwise,
        if another thread owns the lock, block until the lock is unlocked. Once
        the lock is unlocked (not owned by any thread), then grab ownership, set
        the recursion level to one, and return. If more than one thread is
        blocked waiting until the lock is unlocked, only one at a time will be
        able to grab ownership of the lock. There is no return value in this
        case.

        When invoked with the blocking argument set to true, do the same thing
        as when called without arguments, and return true.

        When invoked with the blocking argument set to false, do not block. If a
        call without an argument would block, return false immediately;
        otherwise, do the same thing as when called without arguments, and
        return true.

        When invoked with the floating-point timeout argument set to a positive
        value, block for at most the number of seconds specified by timeout
        and as long as the lock cannot be acquired.  Return true if the lock has
        been acquired, false if the timeout has elapsed.

        """
        return self.lock.acquire(blocking=blocking, timeout=timeout)

    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self, *args):
        return self.release()

    def release(self) -> None:
        return self.lock.release()
