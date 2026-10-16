import asyncio
from functools import partial

from network.client import handle_client

TIMEOUT = .5

async def serve(ip: str, port: int, cache_size: int):
    handler = partial(
        handle_client,
        cache_size=cache_size
    )

    server = await asyncio.start_server(
        handler,
        ip,
        port,
    )

    addresses = ", ".join(
        str(sock.getsockname()) for sock in server.sockets
    )
    print(f"Server listening on: {addresses} \nPress Ctrl+C to exit instantly.")

    async with server:
        await server.serve_forever()

def run(ip: str, port: int, cache_size: int):
    try:
        asyncio.run(serve(ip, port, cache_size))
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing server socket...")
    finally:
        print("[+] Server stopped cleanly.")
