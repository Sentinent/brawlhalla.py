from brawlhalla import BrawlhallaClient
import asyncio

async def main():
    with open("key.txt", "r") as f:
        client = BrawlhallaClient(f.read())
    page = await client.get_ranked_page("1v1", "all", 3)
    print(page)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

