import asyncio
from brawlhalla import BrawlhallaClient

async def main():
    with open("key.txt", "r") as f:
        client = BrawlhallaClient(f.read())

    player = await client.get_player_ranked_stats(1297647)
    print(player.name)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
