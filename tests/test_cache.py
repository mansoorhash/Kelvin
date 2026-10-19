import sqlite3
import unittest
from unittest.mock import patch

from database import model


class CacheTests(unittest.TestCase):
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

    def test_cache_is_not_populated_when_disabled(self):
        model.Operation.set(key="first", value="1", cache_size=None)

        self.assertEqual(model.cache, {})
        result = model.Operation.get(key="first", cache_size=None)
        self.assertEqual(result.return_value, "1")
        self.assertIsNone(result.expires_at)
        self.assertEqual(model.cache, {})

    def test_cache_never_exceeds_configured_size(self):
        model.Operation.set(key="first", value="1", cache_size=2)
        model.Operation.set(key="second", value="2", cache_size=2)
        model.Operation.set(key="third", value="3", cache_size=2)

        self.assertEqual(len(model.cache), 2)
        self.assertNotIn("first", model.cache)
        self.assertEqual(list(model.cache), ["second", "third"])

    def test_get_updates_lru_order(self):
        model.Operation.set(key="first", value="1", cache_size=2)
        model.Operation.set(key="second", value="2", cache_size=2)

        result = model.Operation.get(key="first", cache_size=2)
        self.assertEqual(result.return_value, "1")
        model.Operation.set(key="third", value="3", cache_size=2)

        self.assertEqual(list(model.cache), ["first", "third"])
        self.assertNotIn("second", model.cache)

    def test_overwriting_key_makes_it_most_recently_used(self):
        model.Operation.set(key="first", value="1", cache_size=2)
        model.Operation.set(key="second", value="2", cache_size=2)
        model.Operation.set(key="first", value="updated", cache_size=2)
        model.Operation.set(key="third", value="3", cache_size=2)

        self.assertEqual(list(model.cache), ["first", "third"])
        self.assertEqual(model.cache["first"], ("updated", None))

    def test_delete_invalidates_cached_value(self):
        model.Operation.set(key="name", value="john", cache_size=2)

        deleted = model.Operation.delete(key="name", cache_size=2)

        self.assertEqual(deleted.return_value, 1)
        self.assertNotIn("name", model.cache)
        result = model.Operation.get(key="name", cache_size=2)
        self.assertIsNone(result.return_value)

    def test_exists_populates_cache_with_database_value(self):
        self.connection.execute(
            "INSERT INTO kv(key, value) VALUES (?, ?)",
            ("name", "john"),
        )
        self.connection.commit()

        result = model.Operation.exists(key="name", cache_size=2)
        self.assertEqual(result.return_value, 1)
        self.assertEqual(model.cache["name"], ("john", None))

    def test_eviction_does_not_delete_persistent_value(self):
        model.Operation.set(key="first", value="1", cache_size=1)
        model.Operation.set(key="second", value="2", cache_size=1)

        self.assertNotIn("first", model.cache)
        result = model.Operation.get(key="first", cache_size=1)
        self.assertEqual(result.return_value, "1")

    def test_get_missing_key_returns_empty_command_result(self):
        result = model.Operation.get(key="missing", cache_size=2)

        self.assertIsNone(result.return_value)
        self.assertIsNone(result.expires_at)
        self.assertNotIn("missing", model.cache)

    def test_exists_cache_hit_updates_lru_order(self):
        model.Operation.set(key="first", value="1", cache_size=2)
        model.Operation.set(key="second", value="2", cache_size=2)

        result = model.Operation.exists(key="first", cache_size=2)
        model.Operation.set(key="third", value="3", cache_size=2)

        self.assertEqual(result.return_value, 1)
        self.assertEqual(list(model.cache), ["first", "third"])
        self.assertNotIn("second", model.cache)

    def test_delete_missing_key_returns_zero(self):
        result = model.Operation.delete(key="missing", cache_size=2)

        self.assertEqual(result.return_value, 0)
        self.assertIsNone(result.expires_at)

    def test_cache_size_one_keeps_only_most_recent_key(self):
        model.Operation.set(key="first", value="1", cache_size=1)
        model.Operation.set(key="second", value="2", cache_size=1)
        model.Operation.get(key="first", cache_size=1)

        self.assertEqual(list(model.cache), ["first"])
        self.assertEqual(model.cache["first"], ("1", None))


if __name__ == "__main__":
    unittest.main()
