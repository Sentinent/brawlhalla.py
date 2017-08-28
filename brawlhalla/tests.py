from brawlhalla import BrawlhallaClient
import asyncio

async def main():
    with open("key.txt", "r") as f:
        client = BrawlhallaClient(f.read())
    legend = await client.get_legend_info(23)
    print(legend)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

