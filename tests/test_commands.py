import unittest
from unittest.mock import patch

from network.execute.commands import execute


class CommandTests(unittest.TestCase):
    def test_ping(self):
        self.assertEqual(execute([b"PING"]), b"+PONG\r\n")

    def test_ping_with_message(self):
        self.assertEqual(
            execute([b"PING", b"hello world"]),
            b"$11\r\nhello world\r\n",
        )

    @patch("network.execute.commands.Operation.set", return_value="OK")
    def test_set(self, set_item):
        self.assertEqual(execute([b"SET", b"name", b"john"]), b"+OK\r\n")
        set_item.assert_called_once_with(key="name", value="john")

    @patch("network.execute.commands.Operation.get", return_value="john")
    def test_get(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"]),
            b"$4\r\njohn\r\n",
        )
        get_item.assert_called_once_with(key="name")

    @patch("network.execute.commands.Operation.get", return_value=None)
    def test_get_missing_key(self, get_item):
        self.assertEqual(execute([b"GET", b"missing"]), b"$-1\r\n")

    @patch("network.execute.commands.Operation.delete", return_value=1)
    def test_delete_existing_key(self, delete_item):
        self.assertEqual(execute([b"DEL", b"name"]), b":1\r\n")

    @patch("network.execute.commands.Operation.exists", return_value=0)
    def test_exists_missing_key(self, exists_item):
        self.assertEqual(execute([b"EXISTS", b"missing"]), b":0\r\n")

    def test_wrong_number_of_arguments(self):
        self.assertEqual(
            execute([b"SET", b"name"]),
            b"-ERR wrong number of arguments for 'set' command\r\n",
        )

    def test_unknown_command(self):
        self.assertEqual(
            execute([b"NOPE"]),
            b"-ERR unknown command 'nope'\r\n",
        )

    @patch(
        "network.execute.commands.Operation.get",
        side_effect=ConnectionError("Database connection failed"),
    )
    def test_database_exception_becomes_resp_error(self, get_item):
        self.assertEqual(
            execute([b"GET", b"name"]),
            b"-ERR Database connection failed\r\n",
        )


if __name__ == "__main__":
    unittest.main()
