import asyncio
import aiohttp
import async_timeout

from datetime import datetime
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
        Max amount of time to wait (in seconds) for a request, default value is None. If the connection timeout is hit, 
        the corooutine will return None. Set to None to specify no timeout.
        
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
    max_timeout_time: int = None
    propagate_exceptions: bool = True
    swallow_429: bool = True
    retry_on_429: bool = False
    retry_delay = 60


class BrawlhallaClient:
    """
    The client used to make requests to the Brawlhalla API. An optional :class:`ClientOptions` may be 
    passed to the constructor for more customization of the client's behavior. For example, 
    ``client = BrawlhallaClient(api_key, client_options: opts)``.
    
    The client has a built-in ratelimiter to prevent you from going over your maximum allotted requests. If you have 
    an elevated ratelimit, you can pass those to the client in the :class:`ClientOptions`.
    
    """

    def __init__(self, api_key: str, client_options: ClientOptions = ClientOptions()):
        self.api_key = api_key
        self.options = client_options

        if self.options.use_internal_ratelimiter:
            self.bucket = RateBucket(self.options.requests_per_15_minutes, self.options.requests_per_second)
        else:
            self.bucket = None

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
        if self.options.use_internal_ratelimiter:
            while not self.bucket.can_request():
                await asyncio.sleep(self.bucket.get_next_request())
            self.bucket.do_request()

        endpoint = self.__resolve_endpoint(endpoint, *args, **kvargs)

        try:
            with async_timeout.timeout(self.options.max_timeout_time):
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        return Response(await response.json())

                    elif response.status == 429:
                        if self.options.swallow_429:
                            if self.options.retry_on_429:
                                await asyncio.sleep(self.options.retry_delay)
                                return await self.__send_request(endpoint, *args, **kvargs)
                            else:
                                print("A")
                                return None

                        raise BrawlhallaPyException(429, "Too Many Requests", "Your API key has hit the rate limit.")

                    else:
                        data = await response.json()
                        detailed_error = "No further details."
                        if data:
                            detailed_error = data["error"]["message"]

                        raise BrawlhallaPyException(response.status, response.reason, detailed_error)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            # If the option to propagate exceptions is True, raise the exception. Else, just return None.
            if self.options.propagate_exceptions:
                raise e
            else:
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
            The region to get, one of ``US-W``, ``US-E``, ``EU``, ``BRZ``, ``AUS``, ``SEA``, or ``ALL`` for all.
        :param int page: 
            The page number to get, minimum (and default) value is 1.
        :param str name: 
            The (optional) name to search for.
        :return: 
            A ``list`` of :class:`API.Response` objects, each with the following attributes: 
            
            ``rank`` (int) - The rank of the player relative to the ``region``.
            
            ``name`` (str) - The name of the player.
            
            ``brawlhalla_id`` (int) - The Brawlhalla ID of the player.
            
            ``best_legend`` (int) - The ID of the player's highest elo legend.
            
            ``best_legend_games`` (int) - The number of games on the player's best legend.
            
            ``best_legend_wins`` (int) - The number of wins on the player's best legend.
            
            ``rating`` (int) - The elo of the playaer.
            
            ``tier`` (str) The tier the player is in, see the :ref:`Notes` section for more information.
            
            ``games`` (int) - The total number of games played.
            
            ``wins`` (int) - The total number of games won.
            
            ``region`` (str) - One of ``US-W``, ``US-E``, ``EU``, ``BRZ``, ``AUS``, or ``SEA``.
            
            ``peak_rating`` (int) - The highest elo the player has achieved this season.
            
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
        """

        responses = await self.__send_request("rankings/{}/{}/{}", bracket, region, page, name=name)

        #  Post processing, convert the string "rank" attribute into an integer.
        if responses:
            for response in responses.responses:
                response.rank = int(response.rank)

        return responses

    async def get_player_stats(self, brawlhalla_id: int):
        """
        Sends a request to get general stats for a player. All values are total from season 2 and onwards.
        
        :param int brawlhalla_id: 
            The Brawlhalla ID of the player to get information for.
        :return: 
            A :class:`API.Response` object of the player, with the following attributes: ``brawlhalla_id`` (int), 
            ``name`` (str), ``xp`` (int), ``level`` (int), ``xp_percentage`` (int), ``games`` (int), 
            ``wins`` (int), ``damagebomb`` (int), ``damagemine`` (int), ``damagespikeball`` (int), 
            ``damagesidekick`` (str), ``hitsnowball`` (int), ``kobomb`` (int), ``komine`` (int), ``kospikeball`` (int), 
            ``kosidekick`` (int), ``kosnowball`` (int), ``legends`` (``list`` of objects, see below), 
            and ``clan`` (see below).
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
        
        .. note::
            A ``legend`` object has the following attributes: ``legend_id`` (int), ``legend_name_key`` (str), 
            ``damagedealt`` (int), ``damagetaken`` (int), ``kos`` (int), ``falls`` (int), ``suicides`` (int), 
            ``teamkos`` (int), ``matchtime`` (int), ``games`` (int), ``wins`` (int), ``damageunarmed`` (int), 
            ``damagethrownitem`` (int), ``damageweaponone`` (int), ``damageweapontwo`` (int), ``damagegadgets`` (int), 
            ``kounarmed`` (int), ``kothrownitem`` (int), ``koweaponone`` (int), ``koweapontwo`` (int), 
            ``kogadgets`` (int), ``timeheldweaponone`` (int), ``timeheldweapontwo`` (int), ``xp`` (int), 
            ``level`` (int), and ``xp_percentage`` (int).
        
        .. note::
            A ``clan`` object has the following attributes: ``clan_name`` (str), ``clan_id`` (int), ``clan_xp`` (int), 
            and ``personal_xp`` (int).
            
        .. note::
            In all the percentage attributes (e.g. ``xp_percentage``), the value is represented as a decimal < 0, 
            e.g. ``0.84918519``.
        """
        response = await self.__send_request("player/{}/stats", brawlhalla_id)

        if response:
            # Convert string values from the API into integer values.
            response.damagebomb = int(response.damagebomb)
            response.damagemine = int(response.damagemine)
            response.damagespikeball = int(response.damagespikeball)
            response.damagesidekick = int(response.damagesidekick)

            keys = ["damagedealt", "damagetaken", "damageunarmed", "damagethrownitem", "damageweaponone",
                    "damageweapontwo", "damagegadgets"]
            for legend in response.legends:
                for key in keys:
                    legend[key] = int(legend[key])

            response.clan["clan_xp"] = int(response.clan["clan_xp"])

        return response

    async def get_player_ranked_stats(self, brawlhalla_id: int):
        """
        Sends a request to get the ranked stats of a player for the current season.
        
        :param int brawlhalla_id: 
            The Brawlhalla ID of the player to get information for.
        :return: 
            A :class:`API.Response` object with the following attributes: ``name`` (str), ``brawlhalla_id`` (int), 
            ``rating`` (int), ``peak_rating`` (int), ``tier`` (str, see the :ref:`Notes` section), ``wins`` (int), 
            ``games`` (int), ``region`` (str), ``global_rank`` (int), ``region_rank`` (int),  
            ``legends`` (``list`` of ``legend`` objects, see below), and ``2v2`` (``list`` of objects, see below).      
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
            
        .. note::
            Unlike the ``legend`` objects from :func:`BrawlhallaClient.get_player_stats`, the ``legend`` objects from 
            this endpoint only has the following attributes: ``legend_id`` (int), ``legend_name_key`` (str), 
            ``rating`` (int), ``peak_rating`` (int), ``tier`` (str, see :ref:`Notes`), ``wins`` (int), 
            and ``games`` (int).
        
        .. note::
            Due to the nature of Python, you will have to use ``response["2v2"]`` to access the player's 2v2 stats.
        
        .. note::
            The ``2v2`` attribute is a list of team objects with the following attributes: ``brawlhalla_id_one`` (int), 
            ``brawlhalla_id_two`` (int), ``rating`` (int), ``peak_rating`` (int), ``tier`` (str, see :ref:`Notes`), 
            ``wins`` (int), ``games`` (int), 
            ``teamname`` (str, [{name of {brawlhalla_id_one}}+{name of {brawlhalla_id_two}}]), ``region`` (str), 
            and ``global_rank`` (int).
        
        .. warning::
            The player MUST have played at least 1 game of both ranked 1v1 and 2v2 for this to return properly. This 
            is a limitation of the Brawlhalla API.
            
        .. warning::
            Currently, the Brawlhalla API always returns ``global_rank`` and ``region_rank`` as 0. This may be fixed 
            in the future.
        """
        response = await self.__send_request("player/{}/ranked", brawlhalla_id)

        if response:
            #  For this endpoint only, region is returned as an integer.
            ints_to_regions = dict([(2, "US-E"), (3, "EU"), (4, "SEA"), (5, "BRZ"), (6, "AUS"), (7, "US-W")])
            for team in response["2v2"]:
                team.region = ints_to_regions[team.region]

        return response

    async def get_clan(self, clan_id: int):
        """
        Sends a request to get information for a clan.
        
        :param int clan_id: 
            The clan ID to get information for.
        :return: 
            A :class:`API.Response` object with the following attributes: ``clan_id`` (int), ``clan_name`` (str), 
            ``clan_create_date`` (datetime), ``clan_xp`` (int), and ``clan`` (``list`` of objects, see below).                
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
            
        .. note::
            The ``clan`` attribute contains a list of all the clan members, each with the following attributes: 
            ``brawlhalla_id`` (int), ``name`` (str), ``rank`` (str, one of ``Leader``, ``Officer``, or ``Recruit``), 
            ``join_date`` (datetime), ``xp`` (int).
                
        .. note::
            ``clan_create_date`` and ``join_date`` are both datetime objects from the built-in Python library in 
             UTC format.

        """
        response = await self.__send_request("clan/{}", clan_id)

        if response:
            response.clan_create_date = datetime.fromtimestamp(response.clan_create_date)
            for member in response.clan:
                member.join_date = datetime.fromtimestamp(member.join_date)

        return response

    async def get_legend_info(self, legend: Legends):
        """
        Sends a request to get static information for a legend.
        
        :param Legends legend: 
            An enum value from :class:`API.Legends`.
        :return: 
            A :class:`API.Response` object containing legend information.
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
            
        .. note::
            This method serves as a wrapper for the other method with the same name, except it takes an enum value 
            instead of an integer value. See the other method for more details.
        """
        return await self.get_legend_info(legend.value)

    async def get_legend_info(self, legend: int):
        """
        Sends a request to get static information for a legend.
        
        :param int legend:
            The ID of the legend to get information for.
        :return: 
            A :class:`API.Response` object with the following attributes:
                
            ``legend_id`` (int) - The ID of the legend.
                
            ``legend_name_key`` (str) - The name of the legend.
                
            ``bio_name`` (str) - The name of the legend as shown in the bio, usually the same as 
            :attr:`legend_name_key` except in the cases of special letters, such as bodvar. In that case, this will 
            be bödvar.
                
            ``bio_aka`` (str) - Alternative titles as shown in the legend bio.
                
            ``bio_quote`` (str) - A quote from the bio.
                
            ``bio_quote_about_attrib`` (str) - 
                
            ``bio_quote_from`` (str) - 
               
            ``bio_quote_from_attrib`` (str) -
                
            ``bio_text`` (str) - Lore for this legend.
                
            ``bot_name`` (str) - Bot name for this legend.
                
            ``weapon_one`` (str) - The legend's first weapon, see note below.
                
            ``weapon_two`` (str) - The legend's second weapon, see note below.
                
            ``strength`` (int) - The legend's strength stat.
                
            ``dexterity`` (int) - The legend's dexterity stat.
                
            ``defense`` (int) - The legend's defense stat.
                
            ``speed`` (int) - The legend's speed stat.
        :raises API.BrawlhallaPyException:
            if something went wrong with the request.
            
        .. note::
            Weapons are one of ``Hammer``, ``Sword``, ``Axe``, ``RocketLance``, ``Pistol``, ``Katar``, ``Bow``,
            ``Fists``, or ``Scythe``
        """

        response = await self.__send_request("legend/{}", legend)

        if response:
            response.strength = int(response.strength)
            response.dexterity = int(response.dexterity)
            response.defense = int(response.defense)
            response.speed = int(response.speed)

        return response
