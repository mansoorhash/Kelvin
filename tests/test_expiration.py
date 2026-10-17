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

        self.assertEqual(first_ttl, 8)
        self.assertEqual(second_ttl, 4)
        self.assertIsInstance(first_ttl, int)
        self.assertIsInstance(second_ttl, int)
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

        self.assertIsNone(result)
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

        self.assertEqual(response, b":0\r\n")

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

        self.assertEqual(response, b":-2\r\n")

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

        self.assertEqual(response, b":0\r\n")

    def test_persistent_key_has_minus_one_ttl(self):
        model.Operation.set(
            key="permanent",
            value="value",
            cache_size=2,
        )

        response = execute([b"TTL", b"permanent"], cache_size=2)

        self.assertEqual(response, b":-1\r\n")

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
        self.assertEqual(model.Operation.ttl(key="name", cache_size=2), -1)


if __name__ == "__main__":
    unittest.main()
