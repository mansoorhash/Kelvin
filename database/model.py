import sqlite3
import time
from functools import wraps
from collections import OrderedDict

from database.result import CommandResults
from database.commands.get import getItem
from database.commands.set import setItem
from database.commands.delete import delItem
from database.commands.exist import existItem
from database.commands.ttl import ttlItem

connection = sqlite3.connect("kelvin.db")

connection.execute(
    "CREATE TABLE IF NOT EXISTS kv(" \
    "key TEXT PRIMARY KEY," \
    "value TEXT," \
    "expires_at REAL DEFAULT NULL"
    ")"
)

cache = OrderedDict()

def databaseContext(func):
    @wraps(func)
    def wrapper(*args, cache_size: int | None = None, **kwargs):
        active_cache = cache if cache_size is not None else None
        with connection:
            result = func(connection, active_cache, *args, **kwargs)
            if result.expires_at is not None:
                if time.time() >= result.expires_at:
                    delItem(connection, active_cache, kwargs["key"])
                    return None

        if active_cache is not None:
            while len(active_cache) > cache_size:
                active_cache.popitem(last=False)
        return result.return_value
    return wrapper

class Operation:
    get = staticmethod(databaseContext(getItem))
    set = staticmethod(databaseContext(setItem))
    delete = staticmethod(databaseContext(delItem))
    exists = staticmethod(databaseContext(existItem))
    ttl = staticmethod(databaseContext(ttlItem))
