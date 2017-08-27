import asyncio
import aiohttp
import async_timeout

from brawlhalla.RateBucket import RateBucket
from brawlhalla.API import BrawlhallaPyException, Response, Legends


class ClientOptions:
    """
    Optional configurations to be used by the :class:`BrawlhallaClient`.


    requests_per_15_minutes : int
        Requests allowed per 15 minutes, default value is 180.


    """

    requests_per_15_minutes: int = 180  #: aaaaaa

    requests_per_second: int = 10
    """Requests allowed per second, default value is 10."""

    use_internal_ratelimiter: bool = True
    """
    Whether or not to use the client's internal ratelimiter. Before hitting a ratelimit, the client will wait
    until it can make more requests. Default value is True.
    """

    max_timeout_time: int = 10
    """Max amount of time to wait (in seconds) for a request, default value is 10."""

    propagate_exceptions: bool = True
    """
    If True, exceptions will be propagated to the caller, :attr:`ClientOptions.swallow_429` overrides this setting. 
    Default value is True.
    """

    swallow_429: bool = True
    """
    If True, rate limit exceptions will not be propagated to the caller, instead, None will be returned. Default 
    value is True.
    """

    retry_on_429: bool = True
    """
    If true, rate limited requests will automatically be retried in :attr:`ClientOptions.retry_delay`. Default 
    value is False.
    """

    retry_delay = 60
    """The amount of time (in seconds) to wait before retrying a rate limited request. Default value is 60."""


class BrawlhallaClient:
    def __init__(self, api_key: str, client_options: ClientOptions = ClientOptions()):
        self.api_key = api_key
        self.options = client_options
        self.bucket = RateBucket(self.options.requests_per_15_minutes, self.options.requests_per_second)

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
        except asyncio.TimeoutError:
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