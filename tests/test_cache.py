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
        self.assertEqual(model.Operation.get(key="first", cache_size=None), "1")
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

        self.assertEqual(model.Operation.get(key="first", cache_size=2), "1")
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

        self.assertEqual(deleted, 1)
        self.assertNotIn("name", model.cache)
        self.assertIsNone(model.Operation.get(key="name", cache_size=2))

    def test_exists_populates_cache_with_database_value(self):
        self.connection.execute(
            "INSERT INTO kv(key, value) VALUES (?, ?)",
            ("name", "john"),
        )
        self.connection.commit()

        self.assertEqual(model.Operation.exists(key="name", cache_size=2), 1)
        self.assertEqual(model.cache["name"], ("john", None))

    def test_eviction_does_not_delete_persistent_value(self):
        model.Operation.set(key="first", value="1", cache_size=1)
        model.Operation.set(key="second", value="2", cache_size=1)

        self.assertNotIn("first", model.cache)
        self.assertEqual(model.Operation.get(key="first", cache_size=1), "1")


if __name__ == "__main__":
    unittest.main()
