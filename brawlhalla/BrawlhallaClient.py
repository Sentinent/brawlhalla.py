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

    requests_per_second : int
        Requests allowed per second, default value is 10.
        
    use_internal_ratelimiter : bool
        Whether or not to use the client's internal ratelimiter. Before hitting a ratelimit, the client will wait
        until it can make more requests. Default value is True.

    max_timeout_time : int
        Max amount of time to wait (in seconds) for a request, default value is 10. If the connection timeout is hit, 
        the corooutine will return None.
        
    propagate_exceptions : bool
        If True, exceptions will be propagated to the caller, :attr:`ClientOptions.swallow_429` overrides this setting. 
        If set to false, errors will return None instead of raising an exception. Default value is True.
        
    swallows_429 : bool
        If True, rate limit exceptions will not be propagated to the caller, instead, None will be returned. Default 
        value is True.
        
    retry_on_429 : bool
        If true, rate limited requests will automatically be retried in :attr:`ClientOptions.retry_delay`. Default 
        value is False.
        
    retry_delay : int
        The amount of time (in seconds) to wait before retrying a rate limited request. Default value is 60.
        
    """

    requests_per_15_minutes: int = 180
    requests_per_second: int = 10
    use_internal_ratelimiter: bool = True
    max_timeout_time: int = 10
    propagate_exceptions: bool = True
    swallow_429: bool = True
    retry_on_429: bool = False
    retry_delay = 60


class BrawlhallaClient:
    """
    The client used to make requests to the Brawlhalla API. An optional :class:`ClientOptions` may be 
    passed to the constructor for more customization of the client's behavior. For example, 
    ``client = BrawlhallaClient(api_key, client_options: opts)``.
    """

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
        for key in [x for x in kvargs if kvargs[x]]:  # Filter out Nones
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
        """
        Sends a request to get a player's Brawlhalla ID from a Steam ID.
        
        :param int steam_id:
            The Steam ID of the player to get the Brawlhalla ID for.
        :return: 
            A :class:`API.Response` object with the attributes ``brawlhalla_id`` and ``name``, or ``None`` if the 
            request timed out.
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
        """
        return await self.__send_request("search", steamid=steam_id)

    async def get_ranked_page(self, bracket, region, page=1, name=None):
        """
        Sends a request to get a ranked page.
        :param str bracket:
            The ranked bracket to get, one of ``1v1`` or ``2v2``.
        :param str region: 
            The region to get, one of ``us-w``, ``us-e``, ``eu``, ``brz``, ``aus``, ``sea``, or ``all`` for all.
        :param int page: 
            The page number to get, minimum (and default) value is 1.
        :param str name: The (optional) name to search for.
        :return: 
            A ``list`` of ``Response`` objects, each with the following attributes: 
            ``rank`` (int) - The rank of the player relative to the ``region``.
            ``name``, ``brawlhalla_id``, ``best_legend``, ``a``, ``a``, 
            ``a``, ``a``, ``a``, ``a``, ``a``, ``a``, ``a``, ``a``, ``a``.
        """
        responses = await self.__send_request("rankings/{}/{}/{}", bracket, region, page, name=name)

        #  Post processing, convert the string "rank" attribute into an integer.
        if responses:
            for response in responses.responses:
                response.rank = int(response.rank)

        return responses

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
