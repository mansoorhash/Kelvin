import asyncio

from network.client import handle_client

TIMEOUT = .5

async def serve(ip: str, port: int):
    server = await asyncio.start_server(
        handle_client,
        ip,
        port
    )

    addresses = ", ".join(
        str(sock.getsockname()) for sock in server.sockets
    )
    print(f"Server listening on: {addresses} \nPress Ctrl+C to exit instantly.")

    async with server:
        await server.serve_forever()

def run(ip: str = "127.0.0.1", port: int = 6379):
    try:
        asyncio.run(serve(ip, port))
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing server socket...")
    finally:
        print("[+] Server stopped cleanly.")
