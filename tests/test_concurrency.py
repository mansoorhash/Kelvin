import asyncio
import unittest
from functools import partial

from network.client import handle_client


PING = b"*1\r\n$4\r\nPING\r\n"


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        handler = partial(handle_client, cache_size=None)
        self.server = await asyncio.start_server(handler, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()

    async def open_client(self):
        return await asyncio.open_connection("127.0.0.1", self.port)

    async def close_client(self, writer):
        writer.close()
        await writer.wait_closed()

    async def test_incomplete_client_does_not_block_another_client(self):
        first_reader, first_writer = await self.open_client()
        second_reader, second_writer = await self.open_client()

        try:
            first_writer.write(PING[:8])
            await first_writer.drain()

            second_writer.write(PING)
            await second_writer.drain()

            second_response = await asyncio.wait_for(
                second_reader.readline(),
                timeout=1,
            )
            self.assertEqual(second_response, b"+PONG\r\n")

            first_writer.write(PING[8:])
            await first_writer.drain()

            first_response = await asyncio.wait_for(
                first_reader.readline(),
                timeout=1,
            )
            self.assertEqual(first_response, b"+PONG\r\n")
        finally:
            await self.close_client(first_writer)
            await self.close_client(second_writer)

    async def test_pipelined_commands_preserve_response_order(self):
        reader, writer = await self.open_client()

        try:
            writer.write(PING + PING)
            await writer.drain()

            first = await asyncio.wait_for(reader.readline(), timeout=1)
            second = await asyncio.wait_for(reader.readline(), timeout=1)

            self.assertEqual(first, b"+PONG\r\n")
            self.assertEqual(second, b"+PONG\r\n")
        finally:
            await self.close_client(writer)


if __name__ == "__main__":
    unittest.main()
