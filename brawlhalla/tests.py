from brawlhalla import BrawlhallaClient
import asyncio

async def main():
    with open("key.txt", "r") as f:
        client = BrawlhallaClient(f.read())
    player = await client.get_player_ranked_stats(1312150)
    print(player["2v2"])


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

