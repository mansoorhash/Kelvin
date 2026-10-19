import asyncio
import time

from network.aof import append_to_aof
from network.execute.commands import execute
from network.resp2 import (
    RESPProtocolError,
    error_response,
    parse_request,
)
from models import WriteRequest

last_aof = time.time()
write_lock = asyncio.Lock()

async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    cache_size: int | None,
    aof_type: str = "no",
    write_queue: asyncio.Queue
):
    buffer = b""
    try:
        while True:
            data = await reader.read(4096)
            if not data: 
                break
            buffer += data

            while buffer:
                try:
                    parsed = parse_request(buffer)
                except RESPProtocolError as error:
                    writer.write(error_response(f"Protocol error: {error}"))
                    await writer.drain()
                    return

                if parsed is None:
                    break

                command, buffer = parsed
                operation = command[0].decode(
                    "utf-8",
                    errors="ignore",
                ).upper()

                if operation in ("SET", "DEL") and write_queue is not None:
                    loop = asyncio.get_running_loop()
                    future = loop.create_future()

                    request = WriteRequest(
                        command=command,
                        cache_size=cache_size,
                        future=future,
                    )
                    
                    await write_queue.put(request)

                    resp = await future
                else:
                    resp = execute(command, cache_size=cache_size)
                    if aof_type != "no" and resp.command is not None:
                        asyncio.to_thread(
                            append_to_aof,
                            [(command, resp)],
                            aof_type == "always"
                        )
                writer.write(resp.response)
                await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()