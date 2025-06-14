# AioThreading

A Fork of aiomultiprocess built around threading for enhancing performance whenever processes can't be used


[![PyPI version](https://badge.fury.io/py/aiomultithreading.svg)](https://badge.fury.io/py/aiothreading)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/aiothreading)](https://badge.fury.io/py/aiothreading)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


__After 6 years of waiting, it finally exists.__ This library was inspired by the amazing work of Amyreese and the other contributors of [aiomultiprocess](https://github.com/omnilib/aiomultiprocess) as well as the original ThreadPoolExecutor apart of the python standard library, originally my plan was to write my own threadpool that could do this and many different versions were attempted by me over the past 2 years which all of them had problems of their own such as workers failing to exit propperly and more. Eventlually I had decided to fork this branch off instead with the goal of implementing this feature that I have long wanted which was asyncio but with threads. There are some occasions where this can be useful such as running a discord bot and http server at the same time when you only have so many computer cpu cores to work with. This can come in handy when you do not need to spawn or fork in a process but at the same time you need to reduce the main loop's overall workload which can be helpful if your goal is to send multiple http requests for instance as sometimes some things can block that you didn't indend or expect to be blocked that shouldn't, aiothreading attemps solve these problems and more of them. The best part of all, no more having to ask on sites like stackoverflow about how to run a thread with an asyncio eventloop, I have just solved that problem.



## Installation

``` 
pip install aiothreading
```



## Examples 

### Threads
```python
from aiothreading import Thread, Worker
from aiohttp import request


async def do_request(link:str) -> str:
    async with request("GET", link) as resp:
        # get data before closing
        data = await resp.json()
    print(f"Your IP address is: {data['origin']}") 
    return data['origin']

async def main():
    thread = Thread(target=do_request, args="https://httpbin.org/ip")
    thread.start()
    # to join the thread you can either await it or join it 
    await thread.join()

    # This will also work...
    await thread



async def worker():
    # Wokers have the ability to return items after execution completes...
    # NOTE: Workers will be renamed to ThreadWorker in a future update so aiomutliprocess doesn't collide with this class object
    worker = Worker(target=do_request, args="https://httpbin.org/ip")
    worker.start()

    await worker.join()
    ip = worker.result
    print(ip)

```

## Integrating with Uvloop or Winloop

A Faster eventloop such as __uvloop__ or __winloop__ have been programmed to have better performance than python's stdlib asyncio 
The ThreadPool and Threads and Workers can be used to make your threads run a bit faster.

```python
# Import uvloop if your not on windows
import platform 
if platform.platform == "Windows":
    import winloop as uvloop
else:
    import uvloop

from aiothreading import Thread, Worker, ThreadPool

await Thread(
    target=some_coro, loop_initializer=uvloop.new_event_loop
)
result = await Worker(
    target=other_coro, loop_initializer=uvloop.new_event_loop
)

async with ThreadPool(loop_initalizer=uvloop.new_event_loop) as pool:
    ...

```



## ThreadPool
__ThreadPool__ is a renamed version of `aiomultiprocess.Pool` so that if you were to import and use both of them at the same time for whatever reasons the names don't overlap

```python
# Incase you need to use both of them at the same time
from aiomultiprocess import Pool
from aiothreading import ThreadPool
```

This example was taken from aiomultiprocess

```python
from asyncio import gather
from aiothreading import ThreadPool

async def get(url):
    async with request("GET", url) as response:
        return await response.text("utf-8")

# the threadpool works the same as aiomultiprocess.Pool 
async with ThreadPool() as pool:
    a, b, c, d = gather(
        pool.apply(get, "https://github.com"),
        pool.apply(get, "https://noswap.com"),
        pool.apply(get, "https://omnilib.dev"),
        pool.apply(get, "https://github.com/Vizonex")
    )

```



## When to Use Aiothreading Over AioMultiprocessing

- High task consumption over a single loop on a lower-end device

- Networking or loading takes longer than usual in cases such as webscraping over the Tor Network

- Your writing an application via excutable such as compiling with pyinstaller which is Notorious
for not working with multiprocessing but you don't want something that will wind up acting too slow

- When you need to run something such as a discord bot and http server over the same process
examples of when you would do this would be when running a health check on the discord bot.

- When you don't need something fancy or grandiose.

- Your working with a potato operating system, rasberrypi, libre-computer, etc...

- When you need to combine aiomultiprocess library with this one. 

- Low CPU overall



If none of these fit your criteria I highly encourage you to use the aiomultiprocessing library, it's way faster and has smarter exiting techniques.

## TODOS
- [ ] add aiologic to fix responsiveness of some threads to fix speeds and performance.
- [ ] Youtube Video about how to use

