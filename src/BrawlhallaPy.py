import aiohttp
import async_timeout
from enum import Enum


class Legends(Enum):
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


class ClientOptions:
    requests_per_15_minutes: int = 180
    requests_per_60_seconds: int = 10
    max_timeout_time: int = 10
    swallow_429: bool = True
    propagate_exceptions: bool = True


class Response:
    def __init__(self, data):
        if type(data) is list:
            self.responses = data
        elif type(data) is dict:
            self.__dict__ = data
        else:
            raise NotImplementedError(f"Unsupported data type: {type(data)}")


class BrawlhallaPyException(Exception):
    def __init__(self, status_code: int, reason: str, detailed_reason: str):
        self.status_code = status_code
        self.reason = reason
        self.detailed_reason = detailed_reason


class BrawlhallaClient:
    def __init__(self, api_key: str, client_options: ClientOptions = ClientOptions()):
        self.api_key = api_key
        self.options = client_options

        self.session = aiohttp.ClientSession()

    def __del__(self):
        self.session.close()

    def __resolve_query_params(self, **kvargs) -> str:
        query_params = ""
        kvargs["api_key"] = self.api_key
        for key in kvargs:
            if len(query_params) == 0:
                query_params += f"?{key}={kvargs[key]}"
            else:
                query_params += f"&{key}={kvargs[key]}"

        return query_params

    def __resolve_endpoint(self, endpoint: str, *args, **kvargs) -> str:
        return f"https://api.brawlhalla.com/{endpoint.format(*args)}/{self.__resolve_query_params(**kvargs)}"

    async def __send_request(self, endpoint, *args, **kvargs):
        endpoint = self.__resolve_endpoint(endpoint, *args, **kvargs)

        try:
            with async_timeout.timeout(self.options.max_timeout_time):

                    async with self.session.get(endpoint) as response:
                        if response.status != 200:
                            data = await response.json()
                            detailed_error = "No further details."
                            if data:
                                detailed_error = data["error"]["message"]

                            raise BrawlhallaPyException(response.status, response.reason, detailed_error)
                        else:  # success
                            return Response(await response.json())
        except TimeoutError:
            return None

    async def get_player_from_steam_id(self, steam_id: int):
        return await self.__send_request("search", steamid=steam_id)

    async def get_ranked_page(self, bracket, region, page, name=None):
        return await self.__send_request("rankings/{}/{}/{}", bracket, region, page, name=name)

    async def get_player_stats(self, brawlhalla_id: int):
        return await self.__send_request("player/{}/stats", brawlhalla_id)

    async def get_player_ranked_stats(self, brawlhalla_id: int):
        return await self.__send_request("player/{}/stats", brawlhalla_id)

    async def get_clan(self, clan_id: int):
        return await self.__send_request("clan/{}", clan_id)

    async def get_legend_info(self, legend: Legends):
        return await self.__send_request("legend/{}", legend.value)

    async def get_legend_info(self, legend: int):
        return await self.__send_request("legend/{}", legend)
