import unittest
from unittest.mock import patch

from network.execute.commands import execute

CACHE_SIZE = 2


class CommandTests(unittest.TestCase):
    def test_ping(self):
        self.assertEqual(execute([b"PING"], CACHE_SIZE), b"+PONG\r\n")

    def test_ping_with_message(self):
        self.assertEqual(
            execute([b"PING", b"hello world"], CACHE_SIZE),
            b"$11\r\nhello world\r\n",
        )

    @patch("network.execute.commands.Operation.set", return_value="OK")
    def test_set(self, set_item):
        self.assertEqual(
            execute([b"SET", b"name", b"john"], CACHE_SIZE),
            b"+OK\r\n",
        )
        set_item.assert_called_once_with(
            key="name",
            value="john",
            cache_size=CACHE_SIZE,
        )

    @patch("network.execute.commands.Operation.get", return_value="john")
    def test_get(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"], CACHE_SIZE),
            b"$4\r\njohn\r\n",
        )
        get_item.assert_called_once_with(key="name", cache_size=CACHE_SIZE)

    @patch("network.execute.commands.Operation.get", return_value=None)
    def test_get_missing_key(self, get_item):
        self.assertEqual(
            execute([b"GET", b"missing"], CACHE_SIZE),
            b"$-1\r\n",
        )

    @patch("network.execute.commands.Operation.delete", return_value=1)
    def test_delete_existing_key(self, delete_item):
        self.assertEqual(execute([b"DEL", b"name"], CACHE_SIZE), b":1\r\n")
        delete_item.assert_called_once_with(key="name", cache_size=CACHE_SIZE)

    @patch("network.execute.commands.Operation.exists", return_value=0)
    def test_exists_missing_key(self, exists_item):
        self.assertEqual(
            execute([b"EXISTS", b"missing"], CACHE_SIZE),
            b":0\r\n",
        )
        exists_item.assert_called_once_with(key="missing", cache_size=CACHE_SIZE)

    def test_wrong_number_of_arguments(self):
        self.assertEqual(
            execute([b"SET", b"name"], CACHE_SIZE),
            b"-ERR wrong number of arguments for 'set' command\r\n",
        )

    def test_unknown_command(self):
        self.assertEqual(
            execute([b"NOPE"], CACHE_SIZE),
            b"-ERR unknown command 'nope'\r\n",
        )

    @patch(
        "network.execute.commands.Operation.get",
        side_effect=ConnectionError("Database connection failed"),
    )
    def test_database_exception_becomes_resp_error(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"], CACHE_SIZE),
            b"-ERR Database connection failed\r\n",
        )


if __name__ == "__main__":
    unittest.main()
