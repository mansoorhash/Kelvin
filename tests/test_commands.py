import unittest
from unittest.mock import patch

from models import CommandResults, ExecuteResult
from network.execute.commands import execute

CACHE_SIZE = 2


class CommandTests(unittest.TestCase):
    def test_ping(self):
        result = execute([b"PING"], CACHE_SIZE)
        self.assertEqual(result.response, b"+PONG\r\n")

    def test_ping_with_message(self):
        self.assertEqual(
            execute([b"PING", b"hello world"], CACHE_SIZE).response,
            b"$11\r\nhello world\r\n",
        )

    @patch(
        "network.execute.commands.Operation.set",
        return_value=CommandResults("OK"),
    )
    def test_set(self, set_item):
        self.assertEqual(
            execute([b"SET", b"name", b"john"], CACHE_SIZE).response,
            b"+OK\r\n",
        )
        set_item.assert_called_once_with(
            key="name",
            value="john",
            cache_size=CACHE_SIZE,
        )

    @patch(
        "network.execute.commands.Operation.get",
        return_value=CommandResults("john"),
    )
    def test_get(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"], CACHE_SIZE).response,
            b"$4\r\njohn\r\n",
        )
        get_item.assert_called_once_with(key="name", cache_size=CACHE_SIZE)

    @patch(
        "network.execute.commands.Operation.get",
        return_value=CommandResults(),
    )
    def test_get_missing_key(self, get_item):
        self.assertEqual(
            execute([b"GET", b"missing"], CACHE_SIZE).response,
            b"$-1\r\n",
        )

    @patch(
        "network.execute.commands.Operation.delete",
        return_value=CommandResults(1),
    )
    def test_delete_existing_key(self, delete_item):
        result = execute([b"DEL", b"name"], CACHE_SIZE)
        self.assertEqual(result.response, b":1\r\n")
        delete_item.assert_called_once_with(key="name", cache_size=CACHE_SIZE)

    @patch(
        "network.execute.commands.Operation.exists",
        return_value=CommandResults(0),
    )
    def test_exists_missing_key(self, exists_item):
        self.assertEqual(
            execute([b"EXISTS", b"missing"], CACHE_SIZE).response,
            b":0\r\n",
        )
        exists_item.assert_called_once_with(key="missing", cache_size=CACHE_SIZE)

    def test_wrong_number_of_arguments(self):
        self.assertEqual(
            execute([b"SET", b"name"], CACHE_SIZE).response,
            b"-ERR wrong number of arguments for 'set' command\r\n",
        )

    def test_unknown_command(self):
        self.assertEqual(
            execute([b"NOPE"], CACHE_SIZE).response,
            b"-ERR unknown command 'nope'\r\n",
        )

    @patch(
        "network.execute.commands.Operation.get",
        side_effect=ConnectionError("Database connection failed"),
    )
    def test_database_exception_becomes_resp_error(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"], CACHE_SIZE).response,
            b"-ERR Database connection failed\r\n",
        )

    def test_command_names_are_case_insensitive(self):
        result = execute([b"ping"], CACHE_SIZE)

        self.assertEqual(result.response, b"+PONG\r\n")

    def test_invalid_utf8_returns_resp_error(self):
        result = execute([b"GET", b"\xff"], CACHE_SIZE)

        self.assertIsInstance(result, ExecuteResult)
        self.assertEqual(
            result.response,
            b"-ERR command arguments must be valid UTF-8\r\n",
        )

    def test_ping_rejects_more_than_one_message(self):
        result = execute([b"PING", b"one", b"two"], CACHE_SIZE)

        self.assertEqual(
            result.response,
            b"-ERR wrong number of arguments for 'ping' command\r\n",
        )

    def test_get_rejects_wrong_number_of_arguments(self):
        result = execute([b"GET"], CACHE_SIZE)

        self.assertEqual(
            result.response,
            b"-ERR wrong number of arguments for 'get' command\r\n",
        )

    def test_delete_rejects_wrong_number_of_arguments(self):
        result = execute([b"DEL", b"one", b"two"], CACHE_SIZE)

        self.assertEqual(
            result.response,
            b"-ERR wrong number of arguments for 'del' command\r\n",
        )

    def test_exists_rejects_wrong_number_of_arguments(self):
        result = execute([b"EXISTS"], CACHE_SIZE)

        self.assertEqual(
            result.response,
            b"-ERR wrong number of arguments for 'exists' command\r\n",
        )

    def test_ttl_rejects_wrong_number_of_arguments(self):
        result = execute([b"TTL", b"one", b"two"], CACHE_SIZE)

        self.assertEqual(
            result.response,
            b"-ERR wrong number of arguments for 'ttl' command\r\n",
        )

    def test_set_rejects_unknown_expiration_type(self):
        result = execute(
            [b"SET", b"name", b"john", b"NX", b"10"],
            CACHE_SIZE,
        )

        self.assertIsInstance(result, ExecuteResult)
        self.assertEqual(
            result.response,
            b"-ERR invalid expiration type, use PX (milliseconds) or EX (seconds)\r\n",
        )

    def test_set_rejects_non_numeric_expiration(self):
        result = execute(
            [b"SET", b"name", b"john", b"EX", b"later"],
            CACHE_SIZE,
        )

        self.assertIsInstance(result, ExecuteResult)
        self.assertEqual(
            result.response,
            b"-ERR invalid expiration time (time>0)\r\n",
        )

    def test_set_rejects_zero_expiration(self):
        result = execute(
            [b"SET", b"name", b"john", b"PX", b"0"],
            CACHE_SIZE,
        )

        self.assertIsInstance(result, ExecuteResult)
        self.assertEqual(
            result.response,
            b"-ERR invalid expiration time (time>0)\r\n",
        )

    @patch(
        "network.execute.commands.Operation.set",
        return_value=CommandResults("OK", 110.0),
    )
    def test_set_with_expiration_returns_metadata(self, set_item):
        result = execute(
            [b"SET", b"name", b"john", b"EX", b"10"],
            CACHE_SIZE,
        )

        self.assertEqual(result.response, b"+OK\r\n")
        self.assertEqual(result.expires_at, 110.0)
        set_item.assert_called_once_with(
            key="name",
            value="john",
            cache_size=CACHE_SIZE,
            exp_type="EX",
            exp_time=10,
        )

    @patch(
        "network.execute.commands.Operation.ttl",
        return_value=CommandResults(),
    )
    def test_ttl_missing_key_returns_minus_two(self, ttl_item):
        result = execute([b"TTL", b"missing"], CACHE_SIZE)

        self.assertEqual(result.response, b":-2\r\n")
        ttl_item.assert_called_once_with(key="missing", cache_size=CACHE_SIZE)


if __name__ == "__main__":
    unittest.main()
