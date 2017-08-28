.. brawlhalla documentation master file, created by
   sphinx-quickstart on Sat Aug 26 22:19:34 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
	:hidden:
	
	self
	BrawlhallaPy
   
Welcome to BrawlhallaPy's documentation!
===========================================
This is the homepage for the documentation for `BrawlhallaPy <https://github.com/Sentinent/brawlhalla.py/>`_, an asynchronous Python wrapper for the Brawlhalla API.

Requirements
======================
* Python 3.6 (or higher)
* `Asyncio <https://docs.python.org/3/library/asyncio.html/>`_
* A Brawlhalla API key - email api@brawlhalla.com to request an API key.

Quick Start
======================
First, we have to create an asynchronous context to create requests with, the most common way is by using the asyncio event loop like so: 

.. code-block:: python

	import asyncio

	async def main():
	    pass

	if __name__ == "__main__":
	    loop = asyncio.get_event_loop()
	    loop.run_until_complete(main())

Then, we need to import the necessary classes with ``from brawlhalla import BrawlhallaClient``. After that, we can initialize our client with ``client = new BrawlhallaClient("API_KEY_HERE")``. Now we are ready to make requests.

Let's get a player's ranked stats with :func:`~BrawlhallaClient.BrawlhallaClient.get_player_ranked_stats`.

.. code-block:: python

	import asyncio
	from brawlhalla import BrawlhallaClient

	async def main():
	    client = BrawlhallaClient("API_KEY_HERE")
		
	    player = await client.get_player_ranked_stats(1297647)
	    print(player.name)  # ߷w߷e߷e߷b߷u߷


	if __name__ == "__main__":
	    loop = asyncio.get_event_loop()
	    loop.run_until_complete(main())

All of the :class:`~BrawlhallaClient.BrawlhallaClient`'s methods return a :class:`API.Response` object, whose attributes directly corrospond to the response returned by the `Brawlhalla API <http://dev.brawlhalla.com/>`_.

For more information, read the documentation on the :class:`~BrawlhallaClient.BrawlhallaClient`.

Useful Links
======================

* `Discord Channel <https://discord.gg/UK5uKFy/>`_
* `Brawlhalla API Documentation <http://dev.brawlhalla.com/>`_
* `Github Repository <https://github.com/Sentinent/brawlhalla.py/>`_
* `BrawlhallaClient Page <BrawlhallaClient.html>`_

