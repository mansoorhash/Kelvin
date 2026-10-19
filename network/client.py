import asyncio

from network.aof import append_to_aof
from network.execute.commands import execute
from network.resp2 import (
    RESPProtocolError,
    error_response,
    parse_request,
)

async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    cache_size: int | None,
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
                resp = execute(command, cache_size=cache_size)

                writer.write(resp.response)
                if resp.command is not None:
                    append_to_aof(command, resp)

                await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()