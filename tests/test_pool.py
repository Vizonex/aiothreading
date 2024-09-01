# Modified by Vizonex

# pylint: disable=import-error,import-outside-toplevel

import asyncio
from unittest import TestCase
from queue import Queue
import aiothreading as ath
from aiothreading.pool import ThreadPoolWorker, ProxyException
from _base import async_test, mapper, raise_fn, starmapper, two


async def check_uvloop():
    import uvloop # type: ignore

    loop = asyncio.get_event_loop()
    return isinstance(loop, uvloop.Loop)


async def check_winloop():
    import winloop # type: ignore

    loop = asyncio.get_event_loop()
    return isinstance(loop, winloop.Loop)


class PoolTest(TestCase):  # pylint: disable=too-many-public-methods
    @async_test
    async def test_pool_worker_max_tasks(self):
        # print("test_pool_worker_max_tasks")
        tx = Queue()
        rx = Queue()
        worker = ThreadPoolWorker(tx, rx, 1)
        worker.start()

        self.assertTrue(worker.is_alive())
        tx.put_nowait((1, mapper, (5,), {}))
        await asyncio.sleep(0.5)
        result = rx.get_nowait()

        self.assertEqual(result, (1, 10, None))
        self.assertFalse(worker.is_alive())  # maxtasks == 1

    @async_test
    async def test_pool_worker_stop(self):
        # print("test_pool_worker_stop")
        tx = Queue()
        rx = Queue()
        worker = ThreadPoolWorker(tx, rx, 2)
        worker.start()

        self.assertTrue(worker.is_alive())
        tx.put_nowait((1, mapper, (5,), {}))
        await asyncio.sleep(0.5)
        result = rx.get_nowait()

        self.assertEqual(result, (1, 10, None))
        self.assertTrue(worker.is_alive())  # maxtasks == 2

        tx.put(None)
        await worker.join(timeout=0.5)
        self.assertFalse(worker.is_alive())

    @async_test
    async def test_pool_worker_exceptions(self):
        # print("test_pool_worker_exceptions")
        tx = Queue()
        rx = Queue()
        worker = ThreadPoolWorker(tx, rx)
        worker.start()

        self.assertTrue(worker.is_alive())
        tx.put_nowait((1, raise_fn, (), {}))
        await asyncio.sleep(0.5)
        tid, result, trace = rx.get_nowait()

        self.assertEqual(tid, 1)
        self.assertIsNone(result)
        self.assertIsInstance(trace, str)
        self.assertIn("RuntimeError: raising", trace)

        tx.put(None)
        await worker.join(timeout=0.5)
        self.assertFalse(worker.is_alive())

    @async_test
    async def test_pool(self):
        # print("test_pool")
        values = list(range(10))
        results = [await mapper(i) for i in values]

        async with ath.ThreadPool(2, maxtasksperchild=5) as pool:
            self.assertEqual(pool.thread_count, 2)
            self.assertEqual(len(pool.threads), 2)

            self.assertEqual(await pool.apply(mapper, (values[0],)), results[0])
            self.assertEqual(await pool.map(mapper, values), results)
            self.assertEqual(
                await pool.starmap(starmapper, [values[:4], values[4:]]),
                [results[:4], results[4:]],
            )

    @async_test
    async def test_pool_map(self):
        # print("test_pool_map")
        values = list(range(0, 20, 2))
        expected = [k * 2 for k in values]

        async with ath.ThreadPool(2) as pool:
            obj = pool.map(mapper, values)
            self.assertIsInstance(obj, ath.ThreadPoolResult)
            results = await obj
            self.assertEqual(results, expected)

            obj = pool.map(mapper, values)
            self.assertIsInstance(obj, ath.ThreadPoolResult)
            idx = 0
            async for result in obj:
                self.assertEqual(result, expected[idx])
                idx += 1

    @async_test
    async def test_pool_starmap(self):
        # print("test_pool_starmap")
        values = list(range(0, 20, 2))
        expected = [k * 2 for k in values]

        async with ath.ThreadPool(2) as pool:
            obj = pool.starmap(starmapper, [values] * 5)
            self.assertIsInstance(obj, ath.ThreadPoolResult)
            results = await obj
            self.assertEqual(results, [expected] * 5)

            obj = pool.starmap(starmapper, [values] * 5)
            self.assertIsInstance(obj, ath.ThreadPoolResult)
            count = 0
            async for results in obj:
                self.assertEqual(results, expected)
                count += 1
            self.assertEqual(count, 5)

    @async_test
    async def test_pool_exception(self):
        # print("test_pool_exception")
        async with ath.ThreadPool(2) as pool:
            with self.assertRaises(ProxyException):
                await pool.apply(raise_fn, args=())

    @async_test
    async def test_pool_exception_handler(self):
        # print("test_pool_exception_handler")
        exc_q = Queue()
        handler = exc_q.put_nowait

        async with ath.ThreadPool(2, exception_handler=handler) as pool:
            with self.assertRaises(ProxyException):
                # print("applying to pool")
                await pool.apply(raise_fn, args=())

            # print("waiting for queue")
            exc = exc_q.get_nowait()
            # print("assering for runitme Err")
            self.assertIsInstance(exc, RuntimeError)
            self.assertEqual(exc.args, ("raising",))

    def test_pool_args(self):
        with self.assertRaisesRegex(ValueError, "queue count must be <= thread"):
            ath.ThreadPool(4, queuecount=9)

    @async_test
    async def test_pool_closed(self):
        # print("test_pool_closed")
        pool = ath.ThreadPool(2)
        pool.close()

        with self.assertRaisesRegex(RuntimeError, "pool is closed"):
            await pool.apply(two)

        with self.assertRaisesRegex(RuntimeError, "pool is closed"):
            await pool.map(mapper, [1, 2, 3])

        with self.assertRaisesRegex(RuntimeError, "pool is closed"):
            await pool.starmap(starmapper, [[1, 2, 3], [1, 2, 3]])

        pool.terminate()

    @async_test
    async def test_pool_early_join(self):
        async with ath.ThreadPool(2) as pool:
            with self.assertRaisesRegex(RuntimeError, "pool is still open"):
                await pool.join()

    @async_test
    async def test_pool_uvloop(self):
        try:
            import uvloop # type: ignore

            async with ath.ThreadPool(
                2, loop_initializer=uvloop.new_event_loop
            ) as pool:
                had_uvloop = await pool.apply(check_uvloop)
                self.assertTrue(had_uvloop)

        except ModuleNotFoundError:
            self.skipTest("uvloop not available")

    @async_test
    async def test_pool_winloop(self):
        try:
            import winloop

            async with ath.ThreadPool(
                2, loop_initializer=winloop.new_event_loop
            ) as pool:
                had_winloop = await pool.apply(check_winloop)
                self.assertTrue(had_winloop)

        except ModuleNotFoundError:
            self.skipTest("winloop not available")
