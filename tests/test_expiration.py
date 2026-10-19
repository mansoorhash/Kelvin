import sqlite3
import unittest
from unittest.mock import patch

from database import model
from network.execute.commands import execute


class ExpirationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE TABLE kv("
            "key TEXT PRIMARY KEY, "
            "value TEXT, "
            "expires_at REAL DEFAULT NULL"
            ")"
        )
        self.connection_patch = patch.object(
            model,
            "connection",
            self.connection,
        )
        self.connection_patch.start()
        model.cache.clear()

    def tearDown(self):
        model.cache.clear()
        self.connection_patch.stop()
        self.connection.close()

    def set_clock(self, timestamp):
        patches = [
            patch("database.model.time.time", return_value=timestamp),
            patch("database.commands.set.time.time", return_value=timestamp),
            patch("database.commands.ttl.time.time", return_value=timestamp),
        ]
        for clock_patch in patches:
            clock_patch.start()
            self.addCleanup(clock_patch.stop)

    def test_ex_stores_absolute_expiration_in_cache_and_database(self):
        self.set_clock(1_000.0)

        model.Operation.set(
            key="session",
            value="abc",
            exp_type="EX",
            exp_time=10,
            cache_size=2,
        )

        self.assertEqual(model.cache["session"], ("abc", 1_010.0))
        row = self.connection.execute(
            "SELECT value, expires_at FROM kv WHERE key = ?",
            ("session",),
        ).fetchone()
        self.assertEqual(row, ("abc", 1_010.0))

    def test_px_stores_millisecond_expiration(self):
        self.set_clock(1_000.0)

        model.Operation.set(
            key="short",
            value="value",
            exp_type="PX",
            exp_time=250,
            cache_size=2,
        )

        self.assertEqual(model.cache["short"], ("value", 1_000.25))

    def test_ttl_is_recalculated_from_cached_expiration(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="session",
                value="abc",
                exp_type="EX",
                exp_time=10,
                cache_size=2,
            )

        with (
            patch("database.model.time.time", return_value=1_002.0),
            patch("database.commands.ttl.time.time", return_value=1_002.0),
        ):
            first_ttl = model.Operation.ttl(key="session", cache_size=2)

        with (
            patch("database.model.time.time", return_value=1_006.0),
            patch("database.commands.ttl.time.time", return_value=1_006.0),
        ):
            second_ttl = model.Operation.ttl(key="session", cache_size=2)

        self.assertEqual(first_ttl.return_value, 8)
        self.assertEqual(second_ttl.return_value, 4)
        self.assertIsInstance(first_ttl.return_value, int)
        self.assertIsInstance(second_ttl.return_value, int)
        self.assertEqual(first_ttl.expires_at, 1_010.0)
        self.assertEqual(second_ttl.expires_at, 1_010.0)
        self.assertEqual(model.cache["session"], ("abc", 1_010.0))

    def test_expired_cache_hit_is_lazily_deleted(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="short",
                value="value",
                exp_type="PX",
                exp_time=100,
                cache_size=2,
            )

        with patch("database.model.time.time", return_value=1_000.2):
            result = model.Operation.get(key="short", cache_size=2)

        self.assertIsNone(result.return_value)
        self.assertIsNone(result.expires_at)
        self.assertNotIn("short", model.cache)
        row = self.connection.execute(
            "SELECT key FROM kv WHERE key = ?",
            ("short",),
        ).fetchone()
        self.assertIsNone(row)

    def test_exists_returns_zero_after_lazy_expiration(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="short",
                value="value",
                exp_type="PX",
                exp_time=100,
                cache_size=2,
            )

        with patch("database.model.time.time", return_value=1_000.2):
            response = execute([b"EXISTS", b"short"], cache_size=2)

        self.assertEqual(response.response, b":0\r\n")

    def test_ttl_returns_minus_two_after_lazy_expiration(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="short",
                value="value",
                exp_type="PX",
                exp_time=100,
                cache_size=2,
            )

        with (
            patch("database.model.time.time", return_value=1_000.2),
            patch("database.commands.ttl.time.time", return_value=1_000.2),
        ):
            response = execute([b"TTL", b"short"], cache_size=2)

        self.assertEqual(response.response, b":-2\r\n")

    def test_delete_returns_zero_for_expired_key(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="short",
                value="value",
                exp_type="PX",
                exp_time=100,
                cache_size=2,
            )

        model.cache.clear()

        with patch("database.model.time.time", return_value=1_000.2):
            response = execute([b"DEL", b"short"], cache_size=2)

        self.assertEqual(response.response, b":0\r\n")

    def test_persistent_key_has_minus_one_ttl(self):
        model.Operation.set(
            key="permanent",
            value="value",
            cache_size=2,
        )

        response = execute([b"TTL", b"permanent"], cache_size=2)

        self.assertEqual(response.response, b":-1\r\n")

    def test_set_without_expiration_clears_previous_ttl(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="name",
                value="old",
                exp_type="EX",
                exp_time=10,
                cache_size=2,
            )

        model.Operation.set(
            key="name",
            value="new",
            cache_size=2,
        )

        self.assertEqual(model.cache["name"], ("new", None))
        result = model.Operation.ttl(key="name", cache_size=2)
        self.assertEqual(result.return_value, -1)
        self.assertIsNone(result.expires_at)

    def test_get_unexpired_value_preserves_expiration_metadata(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="session",
                value="abc",
                exp_type="EX",
                exp_time=10,
                cache_size=2,
            )

        with patch("database.model.time.time", return_value=1_005.0):
            result = model.Operation.get(key="session", cache_size=2)

        self.assertEqual(result.return_value, "abc")
        self.assertEqual(result.expires_at, 1_010.0)

    def test_key_expires_exactly_at_deadline(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="session",
                value="abc",
                exp_type="EX",
                exp_time=10,
                cache_size=2,
            )

        with patch("database.model.time.time", return_value=1_010.0):
            result = model.Operation.get(key="session", cache_size=2)

        self.assertIsNone(result.return_value)
        self.assertNotIn("session", model.cache)
        row = self.connection.execute(
            "SELECT key FROM kv WHERE key = ?",
            ("session",),
        ).fetchone()
        self.assertIsNone(row)

    def test_ttl_missing_key_returns_empty_command_result(self):
        result = model.Operation.ttl(key="missing", cache_size=2)

        self.assertIsNone(result.return_value)
        self.assertIsNone(result.expires_at)

    def test_exists_before_expiration_returns_one(self):
        with patch("database.commands.set.time.time", return_value=1_000.0):
            model.Operation.set(
                key="session",
                value="abc",
                exp_type="EX",
                exp_time=10,
                cache_size=2,
            )

        with patch("database.model.time.time", return_value=1_009.0):
            result = model.Operation.exists(key="session", cache_size=2)

        self.assertEqual(result.return_value, 1)
        self.assertEqual(result.expires_at, 1_010.0)


if __name__ == "__main__":
    unittest.main()
