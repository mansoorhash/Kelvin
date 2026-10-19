import asyncio
from contextlib import suppress
from functools import partial

from network.client import handle_client
from network.aof import aof_check, sync_aof
from network.execute.worker import write

TIMEOUT = .5

async def sync_every_second():
    while True:
        await asyncio.sleep(3)
        await asyncio.to_thread(sync_aof)

async def serve(ip: str, port: int, cache_size: int, aof_type: str):
    if aof_type != "no":
        failed = aof_check(cache_size=cache_size)
        if failed is not None: return (print(failed))

    sync_task = None
    write_queue = asyncio.Queue(maxsize=10000)

    if aof_type == "everysec":
        sync_task = asyncio.create_task(sync_every_second())
    
    handler = partial(
        handle_client,
        cache_size=cache_size,
        aof_type=aof_type,
        write_queue=write_queue
    )

    worker_task = asyncio.create_task(
        write(
            write_queue,
            aof_type=aof_type,
            batch_size=50,
            batch_delay=0.002
        ),
        name="write-worker"
    )

    if aof_type == "everysec":
        sync_task = asyncio.create_task(sync_every_second(),name="aof-sync")

    server = await asyncio.start_server(
        handler,
        ip,
        port,
    )

    addresses = ", ".join(
        str(sock.getsockname()) for sock in server.sockets
    )
    print(f"Server listening on: {addresses} \nPress Ctrl+C to exit instantly.")
    try:
        async with server:
            await server.serve_forever()
    finally:
        await write_queue.join()

        worker_task.cancel()

        with suppress(asyncio.CancelledError):
            await worker_task

        if sync_task is not None:
            sync_task.cancel()

            with suppress(asyncio.CancelledError):
                await sync_task
            await asyncio.to_thread(sync_aof)

def run(ip: str, port: int, cache_size: int, aof_type: str):
    try:
        asyncio.run(serve(ip, port, cache_size, aof_type))
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing server socket...")
    finally:
        print("[+] Server stopped cleanly.")
