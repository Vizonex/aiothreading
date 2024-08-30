"""some other cleaver utilities for use with Threads and asyncio
These utilities are currently experimental but are meant to provide 
shared acessabilities to asyncio and threading both synchronously 
and asynchronously. 

These Include: 
- Lock
- RLock
- Condition
- Semaphore 
- BoundedSemaphore
- Event


WARNING
-------
All of the following listed above are Currently Experimental and all 
are held subject to change in the near futrue.

"""


# NOTE: From the Author (Vizonex):
# - I knew these would never get implemented by anyone else but hopefully someone at least 
# finds these to be inpirational or even somewhat useful with it's core concepts 
# to begin with, most concepts were taken from the core threading library which I highly 
# recommend you visit and read up on it's documentation.

import threading
import asyncio
from typing import Optional, Union, Callable


class Lock:
    """A Special lock that can be shared over asyncio and threads alike"""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        self.sync_aquire = self._lock.acquire
        self.locked = self._lock.locked
        self.release = self._lock.release
        self.release_lock = self._lock.release_lock
        self.sync_aquire = self._lock.acquire

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Returns True if lock was aquired and false if that ended up failing any eventloop can visit this without problems..."""
        if timeout is not None:
            try:
                return await asyncio.wait_for(self.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # Make sure we don't block so that the loop attempting to aquire the lock can visit other tasks...
            while self.sync_aquire(timeout=0.005) == False:
                await asyncio.sleep(0.005)
            # Lock aquired
            return True

    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self):
        return self.release()




    



class RLock:
    """A Special lock that can be shared over different asyncio loops and threads alike with RLocking
    Features where a thread can aquire this lock multiple times as long as it's the same thread,
    Asyncio Loops meanwhile can access these on the same threads without blocking"""

    def __init__(self) -> None:
        self._lock = threading.RLock()

        # Install Internal function calls
        self._is_owned = self.lock._is_owned
        self._release_save = self.lock._release_save 
        self._acquire_restore = self.lock._acquire_restore


    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Returns True if lock was aquired and false if that ended up failing"""
        if timeout is not None:
            try:
                return await asyncio.wait_for(self.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # Make sure we don't block so that the loop attempting to aquire the lock can visit other tasks...
            while not self._lock.acquire(blocking=False):
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
        return self._lock.acquire(blocking=blocking, timeout=timeout)

    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self, *args):
        return self.release()

    def release(self) -> None:
        return self.lock.release()
    


        
 

class Condition:
    """Class that implements a condition-variable over 
    asyncio and threading
    """

    def __init__(self, lock:Union[threading.Lock, threading.RLock, Lock, RLock, None] = None) -> None:
        if isinstance(lock, (Lock, RLock)):
            # Extract the real lock
            thread_lock = lock._lock
        else:
            thread_lock = lock

        self._condition = threading.Condition(lock=thread_lock)
        
        # Install the condition variable's functions for faster speeds and ease of access...
        self.release = self._condition.release
        self._release_save = self._condition._release_save
        self._is_owned = self._condition._is_owned
        self._acquire_restore = self._condition._acquire_restore
        self.notify = self._condition.notify
        self.sync_wait = self._condition.wait
        self.sync_wait_for = self._condition.wait_for
        self.notify_all = self._condition.notify_all
        self.notifyAll = self._condition.notifyAll
        
    
    def sync_aquire(self, blocking:bool = True, timeout:Optional[float] = None):    
        """aquires a condition synchronously"""
        # Custom function for providing a secondary way of syncing conditions...
        return self._condition.acquire(blocking, timeout)

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Returns True if lock was aquired and false if that ended up failing"""
        if timeout is not None:
            try:
                return await asyncio.wait_for(self.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # Make sure we don't block so that the loop attempting to aquire the lock can visit other tasks...
            while not self._condition.acquire(blocking=False):
                await asyncio.sleep(0.005)
            # Lock aquired
            return True

    __aenter__ = acquire
    __enter__ = sync_aquire

    async def __aexit__(self, t, v, tb):
        return self._condition.release()

    def __exit__(self, t, v, tb):
        return self._condition.release()
    
    async def wait(self, timeout=None):
        """Waits asynchronously until notified or until a timeout occurs"""
        if timeout is not None:
            try:
                return await asyncio.wait_for(self.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                # Faild to aquire the lock
                return False
        else:
            # See: threading.Condition.wait
            if not self._is_owned():
                raise RuntimeError("cannot wait on un-acquired lock")
            
            # NOTE: Our asynchronous lock we made is compatable with threading's condition.
            waiter = Lock()
            waiter.sync_aquire()
            self._condition._waiters.append(waiter)
            saved_state = self._release_save()
            gotit = False
            try:    # restore state no matter what (e.g., KeyboardInterrupt)
                if timeout is None:
                    # Let this asyncio loop visit other things...
                    await waiter.acquire()
                    gotit = True
                else:
                    if timeout > 0:
                        gotit = await waiter.acquire(timeout)
                    else:
                        gotit = await waiter.acquire()
                return gotit
            finally:
                self._acquire_restore(saved_state)
                if not gotit:
                    try:
                        self._condition._waiters.remove(waiter)
                    except ValueError:
                        pass


    async def wait_for(self, predicate:Callable[..., bool], timeout:Optional[float] = None):
        """Wait until a condition evaluates to True. On whatever current eventloop is being used..."""
        loop = asyncio.get_event_loop()
        _time = loop.time
        endtime = None
        waittime = timeout
        result = predicate()
        while not result:
            if waittime is not None:
                if endtime is None:
                    endtime = _time() + waittime
                else:
                    waittime = endtime - _time()
                    if waittime <= 0:
                        break
            await self.wait(waittime)
            result = predicate()
        return result
    


class Semaphore:
    """This class implements Semaphore Objects for asyncio/threads"""

    def __init__(self, value:int = 1) -> None:
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        
        # Use our Condition variable for delivering better 
        # asynchronous visitation...
        self._cond = Condition(threading.Lock())
        self._value = value
    
    async def acquire(self, blocking:bool = True, timeout=None):
        """Acquire a semaphore, decrementing the internal counter by one.

        When invoked without arguments: if the internal counter is larger than
        zero on entry, decrement it by one and return immediately. If it is zero
        on entry, block, waiting until some other thread has called release() to
        make it larger than zero. This is done with proper interlocking so that
        if multiple acquire() calls are blocked, release() will wake exactly one
        of them up. The implementation may pick one at random, so the order in
        which blocked threads are awakened should not be relied on. There is no
        return value in this case.

        When invoked with blocking set to true, do the same thing as when called
        without arguments, and return true.

        When invoked with blocking set to false, do not block. If a call without
        an argument would block, return false immediately; otherwise, do the
        same thing as when called without arguments, and return true.

        When invoked with a timeout other than None, it will block for at
        most timeout seconds.  If acquire does not complete successfully in
        that interval, return false.  Return true otherwise.

        """

        # blocking functionality should be retained so 
        # that Threading.Semaphore's rules are being obeyed
        
        if not blocking and timeout is not None:
            raise ValueError("can't specify timeout for non-blocking acquire")
        # Get the thread's owning eventloop
        loop = asyncio.get_event_loop()
        # Implement _time function
        _time = loop.time

        rc = False
        endtime = None
        async with self._cond:
            while self._value == 0:
                if timeout is not None:
                    if endtime is None:
                        endtime = _time() + timeout
                    else:
                        timeout = endtime - _time()
                        if timeout <= 0:
                            break
                await self._cond.wait(timeout)
            else:
                self._value -= 1
                rc = True
        return rc

    __aenter__ = acquire

    def release(self, n=1):
        """Release a semaphore, incrementing the internal counter by one or more.

        When the counter is zero on entry and another thread is waiting for it
        to become larger than zero again, wake up that thread.

        """
        if n < 1:
            raise ValueError('n must be one or more')
        with self._cond:
            self._value += n
            for _ in range(n):
                self._cond.notify()

    async def __aexit__(self, t, v, tb):
        self.release()    


class BoundedSemaphore(Semaphore):
    """Mirror of threading.BoundedSemaphore but with some Asynchronous capabilities added onto it"""
    def __init__(self, value: int = 1) -> None:
        Semaphore.__init__(self, value)
        self._initial_value = value
    
    def release(self, n=1):
        if n < 1:
            raise ValueError('n must be one or more')
        
        with self._cond:
            if self._value + n > self._initial_value:
                raise ValueError("Semaphore released too many times")
            self._value += n
            for _ in range(n):
                self._cond.notify()

    async def async_release(self, n = 1):
        """Provides the ability of releasing with the Bounded Semaphore asynchronously"""
        if n < 1:
            raise ValueError('n must be one or more')
        
        async with self._cond:
            if self._value + n > self._initial_value:
                raise ValueError("Semaphore released too many times")
            self._value += n
            for _ in range(n):
                self._cond.notify()
    
    async def __aexit__(self, t, v, tb):
        return await self.async_release()
    

class Event:
    """Class implementing event objects but for multiple use-cases with asyncio & Threading.

    Events manage a flag that can be set to true with the set() method and reset
    to false with the clear() method. The wait() method blocks until the flag is
    true.  The flag is initially false.

    SEE: threading.Event for more info...
    """

    def __init__(self) -> None:
        self._cond = Condition(threading.Lock())
        self._flag = False

    # TODO: (Vizonex) is _at_fork_reinit really nessary?
    # def _at_fork_reinit(self):
    #     self._cond._condition._at_fork_reinit()

    def is_set(self):
        """Returns True if the flag is set to True"""
        return self._flag

    isSet = is_set
    
    def set(self):
        """Sets the internal flag to True"""
        with self._cond:
            self._flag = True
            self._cond.notify_all()

    def clear(self):
        """Resets the intenal flag to false"""
        with self._cond:
            self._flag = False
    
    async def wait(self, timeout:Optional[float] = None):
        """Waits for the Event's internal flag to be set to True asynchronously
        allowing for whatever holds the current eventloop to visit other 
        important tasks..."""
        async with self._cond:
            signaled = self._flag
            if not signaled:
               signaled = await self._cond.wait(timeout)
            return signaled
    
    def sync_wait(self, timeout=None):
        """Blocks synchornously until the internal flag is true.

        From threading.Event Docs:
 
        If the internal flag is true on entry, return immediately. Otherwise,
        block until another thread calls set() to set the flag to true, or until
        the optional timeout occurs.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        This method returns the internal flag on exit, so it will always return
        True except if a timeout is given and the operation times out.

        """
        with self._cond:
            signaled = self._flag
            if not signaled:
                signaled = self._cond.sync_aquire(timeout)
            return signaled 
    

