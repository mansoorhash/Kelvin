import sqlite3
from functools import wraps

from database.commands.get import getItem
from database.commands.set import setItem
from database.commands.delete import delItem

connection = sqlite3.connect("kelvin.db")

connection.execute(
    "CREATE TABLE IF NOT EXISTS kv(" \
    "key string PRIMARY KEY," \
    "value string" \
    ")"
)

def databaseContext(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with connection:
            return func(connection, *args, **kwargs)
    return wrapper

class Operation:
    get = staticmethod(databaseContext(getItem))
    set = staticmethod(databaseContext(setItem))
    delete = staticmethod(databaseContext(delItem))