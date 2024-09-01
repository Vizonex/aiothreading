# Modified by Vizonex

import asyncio

# import sys
# import time
from unittest import TestCase, skip
from unittest.mock import patch

import aiothreading as ath
from _base import (
    async_test,
    do_nothing,
    get_dummy_constant,
    initializer,
    raise_fn,
    sleepy,
    two,
)

def shut_up(exc):
    return 

class CoreTest(TestCase):  # pylint: disable=too-many-public-methods
   
    # TODO: (Vizonex) Can we make execption printhing shut up during our tests?
    @async_test
    async def test_process(self):
        p = ath.Thread(target=sleepy, name="test_process",)
        p.start()

        self.assertEqual(p.name, "test_process")
        self.assertTrue(p.native_id)
        self.assertTrue(p.is_alive())

        await p.join()
        self.assertFalse(p.is_alive())

    @async_test
    async def test_process_await(self):
        p = ath.Thread(target=sleepy, name="test_process")
        await p

        p = ath.Thread(target=sleepy, name="test_process")
        p.start()
        await p

    @async_test
    async def test_process_join(self):
        p = ath.Thread(target=sleepy, name="test_process")

        with self.assertRaisesRegex(ValueError, "must start thread before joining it"):
            await p.join()

        p.start()
        await p.join()

    @async_test
    async def test_process_daemon(self):
        p = ath.Thread(daemon=False)
        self.assertEqual(p.daemon, False)
        p.daemon = True
        self.assertEqual(p.daemon, True)

        p = ath.Thread(daemon=True)
        self.assertEqual(p.daemon, True)
        p.daemon = False
        self.assertEqual(p.daemon, False)

    # We can't terminate or kill so skip both of these...
    # @async_test
    # async def test_process_terminate(self):
    #     start = time.time()
    #     p = ath.Thread(target=asyncio.sleep, args=(1,), name="test_process")
    #     p.start()

    #     # p.terminate()
    #     await p.join()
    #     self.assertLess(p.exitcode, 0)
    #     self.assertLess(time.time() - start, 0.6)

    # @async_test
    # async def test_process_kill(self):
    #     p = ath.Thread(target=sleepy)
    #     p.start()

    #     if sys.version_info >= (3, 7):
    #         await p.join()

    #     else:
    #         with self.assertRaises(AttributeError):
    #             p.kill()
    #         await p.join()

    # @async_test
    # async def test_process_close(self):
    #     p = ath.Thread(target=sleepy)
    #     p.start()

    #     # if sys.version_info >= (3, 7):
    #     #     with self.assertRaises(ValueError):
    #     #         self.assertIsNone(p.exitcode)
    #     #         p.close()

    #     #     await p.join()
    #     #     self.assertIsNotNone(p.exitcode)

    #     #     p.close()

    #     #     with self.assertRaises(ValueError):
    #     #         _ = p.exitcode

    #     # else:
    #     # with self.assertRaises(AttributeError):

    #     await p.join()

    @async_test
    async def test_process_timeout(self):
        p = ath.Thread(target=sleepy)
        p.start()

        with self.assertRaises(asyncio.TimeoutError):
            await p.join(timeout=0.01)

    @async_test
    async def test_worker(self):
        p = ath.Worker(target=sleepy)
        p.start()

        with self.assertRaisesRegex(ValueError, "coroutine not completed"):
            _ = p.result

        await p.join()

        self.assertFalse(p.is_alive())
        self.assertEqual(p.result, p.native_id)

    @async_test
    async def test_worker_join(self):
        # test results from join
        p = ath.Worker(target=sleepy)
        p.start()
        self.assertEqual(await p.join(), p.native_id)

        # test awaiting p directly, no need to start
        p = ath.Worker(target=sleepy)
        self.assertEqual(await p, p.native_id)

    @async_test
    async def test_initializer(self):
        result = await ath.Worker(
            target=get_dummy_constant,
            name="test_process",
            initializer=initializer,
            initargs=(10,),
        )
        self.assertEqual(result, 10)

    @async_test
    async def test_async_initializer(self):
        with self.assertRaises(ValueError) as _:
            p = ath.Thread(target=sleepy, name="test_process", initializer=sleepy)
            p.start()

    @async_test
    async def test_raise(self):
        result = await ath.Worker(
            target=raise_fn, name="test_process", initializer=do_nothing
        )    
        self.assertIsInstance(result, RuntimeError)

    @async_test
    async def test_sync_target(self):
        with self.assertRaises(ValueError) as _:
            p = ath.Thread(
                target=do_nothing, name="test_process", initializer=do_nothing
            )
            p.start()

    @async_test
    async def test_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await ath.core.not_implemented()


if __name__ == "__main__":
    import unittest

    unittest.main()
