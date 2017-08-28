from brawlhalla import BrawlhallaClient, ClientOptions
import asyncio

async def main():
    with open("key.txt", "r") as f:
        opts = ClientOptions()
        opts.retry_on_429 = True
        opts.retry_delay = 5
        client = BrawlhallaClient(f.read(), client_options=opts)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
