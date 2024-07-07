# AioThreading

A Fork of aiomultiprocess built around threading for enhancing performance whenever processes can't be used


[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


After 6 years of waiting, it finally exists. This library was inspired by the amazing work of Amyreese and the other contributors of aiomultiprocess as well as the original ThreadPoolExecutor, originally my plan was to write my own threadpool that could do this and many different versions were attempted by me over the past 2 years which all of them had problems of their own such as workers failing to exit propperly and more. Eventlually I had decided to fork this branch off instead with the goal of implementing this feature that I have long wanted which was asyncio but with threads. There are some occasions where this can be useful such as running a discord bot and http server at the same time when you only have so many computer cpu cores to work with. This can come in handy when you do not need to spawn or fork in a process but at the same time you need to reduce the main loop's overall workload which can be helpful if your goal is to send multiple http requests for instance as sometimes some things can block that you didn't indend or expect to be blocked that shouldn't, aiothreading attemps solve these problems and more of them. 


## When to Use Aiothreading Over AioMultiprocessing

- High task consumption over a single loop on a lower-end device

- Networking or loading takes longer than usual in cases such as webscraping over the Tor Network 

- Your writing an application via excutable such as compiling with pyinstaller which is Notorious for not working with multiprocessing but you don't want something that will wind up acting too slow

- When you need to run something such as a discord bot and http server over the same process examples of when you would do this would be when running a health check on the discord bot.

- You don't want something fancy or grandiose but your still trying to find the best possible outcome.

- Your working with a potato operating system, rasberrypi, libre-computer, etc...

- Low CPU overall


If none of these fit your criteria I highly encourage you to use the aiomultiprocessing library, it's way faster and has smarter exiting techniques.

## TODOS
- [x] Youtube Video about how to use
- [x] Pypi pakage (Hopefully the name has not been claimed yet by anyone)
