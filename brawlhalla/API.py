from enum import Enum

"""
This module contains all the components that brawlhalla.py uses. Useful classes to import include 
:class:`Legends`, :class:`Response`, and :class:`BrawlhallaPyException`.
"""


class Legends(Enum):
    """
    An Enum representing all current legends in the game to be passed to 
    :func:`BrawlhallaClient.get_legend_info`. If the legend is not in this Enum, 
    :func:`BrawlhallaClient.get_legend_info` has an overload that takes an integer.
    """

    BODVAR = 3,
    CASSIDY = 4,
    ORION = 5,
    LORDVRAXX = 6,
    GNASH = 7,
    QUEENNAI = 8,
    LUCIEN = 9,
    HATTORI = 10,
    SIRROLAND = 11,
    SCARLET = 12,
    THATCH = 13,
    ADA = 14,
    SENTINEL = 15,
    TEROS = 16,  # 17 does not exist
    EMBER = 18,
    BRYNN = 19,
    ASURI = 20,
    BARRAZA = 21,
    ULGRIM = 22,  # God = 22
    AZOTH = 23,
    KOJI = 24,
    DIANA = 25,
    JHALA = 26,  # 27 doesn't exist either
    KOR = 28,
    WUSHANG = 29,
    VAL = 30,
    RAGNIR = 31,
    CROSS = 32,
    MIRAGE = 33,
    NIX = 34,
    MORDEX = 35,
    YUMIKO = 36,
    ARTEMIS = 37,
    CASPIAN = 38,

    NONEXISTANT = 9001  # for tests


class Response:
    """
    Represents a response whose attributes are as returned by Brawlhalla API.
    Read the `Brawlhalla documentation <http://dev.brawlhalla.com/>`_ for the name of attributes.
    
    .. note::
        Single object responses (e.g. from :func:`brawlhalla.BrawlhallaClient.get_player_from_steam_id`) will be 
        returned as an object whose attributes are 1:1 with the api.
        For example, if the response was::

            {
                "brawlhalla_id": 2,
                "name": "bmg | dan"
            }
            
        , ``response_object.brawlhalla_id`` would be 2.
        
    .. note::
        For endpoints that return a JSON array, such as :func:`brawlhalla.BrawlhallaClient.get_ranked_page`, you will 
        have to access the data from ``response_object.responses``, which will be a ``list`` of ``Response`` objects.
    """
    def __init__(self, data):
        if type(data) is list:
            self.responses = [Response(x) for x in data]
        elif type(data) is dict:
            #  Fix emojis in name
            if "name" in data.keys():
                data["name"] = data["name"].encode("raw_unicode_escape").decode("utf-8")
            elif "teamname" in data.keys():
                data["teamname"] = data["teamname"].encode("raw_unicode_escape").decode("utf-8")

            for key in data:
                if type(data[key]) is list:
                    data[key] = [Response(x) for x in data[key]]

            self.__dict__ = data
        else:
            raise NotImplementedError(f"Unsupported data type: {type(data)}")

    def __getitem__(self, item):
        return self.__dict__[item]


class BrawlhallaPyException(Exception):
    """
    An exception that signifies something went wrong when sending a request.
    
    status_code : int
        The HTTP status code of the failure.
    reason : str
        The HTTP header reason for the failure.
    detailed_reason : str
        The detailed reason returned by the Brawlhalla API (if available).      
    """
    def __init__(self, status_code: int, reason: str, detailed_reason: str):
        self.status_code = status_code
        self.reason = reason
        self.detailed_reason = detailed_reason
