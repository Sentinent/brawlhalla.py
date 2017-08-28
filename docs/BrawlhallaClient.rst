.. currentmodule:: BrawlhallaClient

BrawlhallaClient Module
=========================
The core of BrawlhallaPy.

BrawlhallaClient
------------------
.. autoclass:: BrawlhallaClient
	:members:
	
Notes
~~~~~~~

Tiers are represented by a string in the format: ``[RANK] [DIVISION]``, except for ``Diamond``, which is just represented as ``Diamond``. Excluding diamond, [RANK] is one of ``Platinum``, ``Gold``, ``Silver``, ``Bronze``, or ``Tin``. [DIVISION] is an integer 0-5, inclusive. For example, all of the following are valid::

	Diamond
	Gold 4
	Platinum 0
	Tin 2
	
	
ClientOptions
-----------------
.. autoclass:: ClientOptions
	:members:
	
