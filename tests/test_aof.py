import asyncio
import json
import os
import tempfile
import unittest
from functools import partial
from unittest.mock import call, patch

from models import CommandResults, ExecuteResult
from network import aof, setup
from network.client import handle_client
from network.execute.commands import execute


def encode_command(*arguments: bytes) -> bytes:
    frame = f"*{len(arguments)}\r\n".encode("ascii")
    for argument in arguments:
        frame += f"${len(argument)}\r\n".encode("ascii")
        frame += argument + b"\r\n"
    return frame


class AOFFileTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.aof_path = os.path.join(
            self.temp_directory.name,
            "custom-appendonly.aof",
        )
        self.path_patch = patch.object(aof, "aof_filename", self.aof_path)
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.temp_directory.cleanup()

    def read_records(self):
        if not os.path.exists(self.aof_path):
            return []
        with open(self.aof_path, "r", encoding="utf-8") as file:
            return [json.loads(line) for line in file]

    def write_records(self, *records):
        with open(self.aof_path, "w", encoding="utf-8", newline="\n") as file:
            for record in records:
                json.dump(record, file)
                file.write("\n")

    def test_successful_persistent_set_is_appended(self):
        response = ExecuteResult(response=b"+OK\r\n", command="SET")
        aof.append_to_aof([b"SET", b"name", b"john"], response)
        self.assertEqual(self.read_records(), [["SET", "name", "john"]])

    def test_successful_expiring_set_is_stored_as_absolute_pxat(self):
        response = ExecuteResult(
            response=b"+OK\r\n", command="SET", expires_at=1_010.0
        )
        aof.append_to_aof(
            [b"SET", b"session", b"abc", b"EX", b"10"], response
        )
        self.assertEqual(
            self.read_records(),
            [["SET", "session", "abc", "PXAT", "1010000"]],
        )

    def test_pxat_rounding_produces_an_integer_string(self):
        response = ExecuteResult(
            response=b"+OK\r\n", command="SET", expires_at=1_000.1236
        )
        aof.append_to_aof([b"SET", b"key", b"value"], response)
        expiration = self.read_records()[0][-1]
        self.assertEqual(expiration, "1000124")
        self.assertTrue(expiration.isdecimal())

    def test_failed_set_is_not_appended(self):
        response = ExecuteResult(
            response=b"-ERR Database connection failed\r\n", command="SET"
        )
        aof.append_to_aof([b"SET", b"name", b"john"], response)
        self.assertFalse(os.path.exists(self.aof_path))

    def test_successful_delete_is_appended(self):
        response = ExecuteResult(response=b":1\r\n", command="DEL")
        aof.append_to_aof([b"DEL", b"name"], response)
        self.assertEqual(self.read_records(), [["DEL", "name"]])

    def test_delete_of_missing_key_is_not_appended(self):
        response = ExecuteResult(response=b":0\r\n", command="DEL")
        aof.append_to_aof([b"DEL", b"missing"], response)
        self.assertFalse(os.path.exists(self.aof_path))

    def test_multiple_commands_are_appended_in_order(self):
        set_response = ExecuteResult(response=b"+OK\r\n", command="SET")
        delete_response = ExecuteResult(response=b":1\r\n", command="DEL")
        aof.append_to_aof([b"SET", b"name", b"john"], set_response)
        aof.append_to_aof([b"DEL", b"name"], delete_response)
        self.assertEqual(
            self.read_records(),
            [["SET", "name", "john"], ["DEL", "name"]],
        )

    def test_spaces_newlines_quotes_and_backslashes_are_preserved(self):
        value = 'hello world\r\n"quoted" \\ path'
        response = ExecuteResult(response=b"+OK\r\n", command="SET")
        aof.append_to_aof(
            [b"SET", b"message", value.encode("utf-8")], response
        )
        self.assertEqual(self.read_records(), [["SET", "message", value]])

    def test_unicode_key_and_value_are_stored_as_strings(self):
        response = ExecuteResult(response=b"+OK\r\n", command="SET")
        aof.append_to_aof(
            [
                b"set",
                "caf\u00e9".encode("utf-8"),
                "cr\u00e8me \u2615".encode("utf-8"),
            ],
            response,
        )
        self.assertEqual(
            self.read_records(), [["SET", "caf\u00e9", "cr\u00e8me \u2615"]]
        )

    def test_empty_string_key_and_value_are_preserved(self):
        response = ExecuteResult(response=b"+OK\r\n", command="SET")
        aof.append_to_aof([b"SET", b"", b""], response)
        self.assertEqual(self.read_records(), [["SET", "", ""]])

    def test_empty_file_replays_nothing(self):
        self.write_records()
        with patch("network.aof.execute") as replay_execute:
            result = aof.aof_check(cache_size=2)
        self.assertIsNone(result)
        replay_execute.assert_not_called()

    def test_missing_file_is_treated_as_empty(self):
        with patch("network.aof.execute") as replay_execute:
            result = aof.aof_check(cache_size=2)
        self.assertIsNone(result)
        replay_execute.assert_not_called()

    def test_replay_uses_configured_filename_cache_size_and_order(self):
        self.write_records(
            ["SET", "first", "hello world"],
            ["DEL", "first"],
        )
        with patch("network.aof.execute") as replay_execute:
            replay_execute.return_value = ExecuteResult(b"+OK\r\n")
            aof.aof_check(cache_size=3)
        self.assertEqual(
            replay_execute.call_args_list,
            [
                call(
                    ["SET", "first", "hello world"],
                    cache_size=3,
                    aof=True,
                ),
                call(["DEL", "first"], cache_size=3, aof=True),
            ],
        )

    def test_replay_preserves_unicode_and_control_characters(self):
        value = "cr\u00e8me\nsecond line\tindent"
        self.write_records(["SET", "caf\u00e9", value])
        with patch("network.aof.execute") as replay_execute:
            replay_execute.return_value = ExecuteResult(b"+OK\r\n")
            aof.aof_check(cache_size=None)
        replay_execute.assert_called_once_with(
            ["SET", "caf\u00e9", value], cache_size=None, aof=True
        )

    def test_replay_error_identifies_the_failing_line(self):
        self.write_records(["SET", "first", "1"], ["SET", "broken"])
        with patch("network.aof.execute") as replay_execute:
            replay_execute.side_effect = [
                ExecuteResult(b"+OK\r\n"),
                ExecuteResult(
                    b"-ERR wrong number of arguments for 'set' command\r\n"
                ),
            ]
            with self.assertRaisesRegex(RuntimeError, "line 2"):
                aof.aof_check(cache_size=2)

    def test_malformed_json_stops_replay(self):
        with open(self.aof_path, "w", encoding="utf-8") as file:
            file.write('["SET", "name", "john"\n')
        with self.assertRaises(json.JSONDecodeError):
            aof.aof_check(cache_size=2)


class AOFReplayExecutionTests(unittest.TestCase):
    @patch("network.execute.commands.Operation.set")
    def test_replayed_pxat_is_forwarded_as_absolute_expiration(self, set_item):
        set_item.return_value = CommandResults("OK", 1_010.0)
        result = execute(
            ["SET", "session", "abc", "PXAT", "1010000"],
            cache_size=2,
            aof=True,
        )
        self.assertEqual(result.response, b"+OK\r\n")
        set_item.assert_called_once_with(
            key="session",
            value="abc",
            cache_size=2,
            exp_type="PXAT",
            exp_time=1_010_000,
        )

    def test_replay_rejects_non_integer_pxat(self):
        result = execute(
            ["SET", "session", "abc", "PXAT", "1010.0"],
            cache_size=2,
            aof=True,
        )
        self.assertTrue(result.response.startswith(b"-ERR"))

    @patch("network.execute.commands.Operation.set")
    def test_replayed_expired_pxat_returns_ok_without_crashing(self, set_item):
        set_item.return_value = CommandResults()

        result = execute(
            ["SET", "expired", "value", "PXAT", "1000"],
            cache_size=2,
            aof=True,
        )

        self.assertEqual(result.response, b"+OK\r\n")
        self.assertIsNone(result.command)
        self.assertIsNone(result.expires_at)


class AOFClientIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        handler = partial(handle_client, cache_size=None)
        self.server = await asyncio.start_server(handler, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()

    async def send_command(self, frame):
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        try:
            writer.write(frame)
            await writer.drain()
            return await asyncio.wait_for(reader.readline(), timeout=1)
        finally:
            writer.close()
            await writer.wait_closed()

    @patch("network.client.append_to_aof")
    @patch("network.client.execute")
    async def test_successful_set_is_appended_with_its_result(
        self, client_execute, append_to_aof
    ):
        result = ExecuteResult(
            response=b"+OK\r\n", command="SET", expires_at=1_010.0
        )
        client_execute.return_value = result
        command = [b"SET", b"session", b"abc", b"EX", b"10"]
        response = await self.send_command(encode_command(*command))
        self.assertEqual(response, b"+OK\r\n")
        append_to_aof.assert_called_once_with(command, result)

    @patch("network.client.append_to_aof")
    @patch("network.client.execute")
    async def test_successful_delete_is_appended(
        self, client_execute, append_to_aof
    ):
        result = ExecuteResult(response=b":1\r\n", command="DEL")
        client_execute.return_value = result
        command = [b"DEL", b"name"]
        response = await self.send_command(encode_command(*command))
        self.assertEqual(response, b":1\r\n")
        append_to_aof.assert_called_once_with(command, result)

    @patch("network.client.append_to_aof")
    @patch("network.client.execute")
    async def test_read_only_command_is_not_appended(
        self, client_execute, append_to_aof
    ):
        client_execute.return_value = ExecuteResult(b"$4\r\njohn\r\n")
        response = await self.send_command(encode_command(b"GET", b"name"))
        self.assertEqual(response, b"$4\r\n")
        append_to_aof.assert_not_called()

    @patch("network.client.append_to_aof")
    @patch("network.client.execute")
    async def test_rejected_command_is_not_appended(
        self, client_execute, append_to_aof
    ):
        client_execute.return_value = ExecuteResult(
            b"-ERR invalid expiration time (time>0)\r\n"
        )
        response = await self.send_command(
            encode_command(b"SET", b"name", b"john", b"EX", b"0")
        )
        self.assertTrue(response.startswith(b"-ERR"))
        append_to_aof.assert_not_called()


class AOFStartupTests(unittest.IsolatedAsyncioTestCase):
    @patch("network.setup.aof_check")
    async def test_server_replays_aof_before_listening(self, aof_check):
        class StopStartup(Exception):
            pass

        aof_check.side_effect = StopStartup
        with self.assertRaises(StopStartup):
            await setup.serve("127.0.0.1", 0, cache_size=7)
        aof_check.assert_called_once_with(cache_size=7)


if __name__ == "__main__":
    unittest.main()
