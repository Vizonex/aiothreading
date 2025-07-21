aiothreading documentation
==========================


aiothreading is a modified version of aiomultiprocess with the added 
benefit of giving users more power over limited numbers of cpus or cores
as well as providing safer exiting alternatives. This library currently
is more maintained than it's brother and those who want to have a different
experince than aiomultiprocess but still are looking for pleanty of juice 
should give this library a try.


Philsophy
---------

The weak guy deserves to have the bigger stick and having to run code 
with just a cheap laptop is no exception. Not all of us have
Quantum Computers or PCs that produce glowing rainbows in our 
basements ready to compute heavy loads. Your computer
deserves to reach it's limits no matter how big or small it is.

Aiothreading was meant to fill in these gaps as well as working around 
the speed-caps in the concurrent futures module. 
Event-loops can only take in so many tasks at a given time and having a second 
one in a separate thread can greatly lift it's burden. 
Maybe you just want to run something in the background of your 
fastapi or aiohttp server while minimizing the load-times in the 
front-end. 






Contents
--------
.. toctree::
   aiothreading


Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`