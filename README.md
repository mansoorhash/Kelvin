# Kelvin

A small, dependency-free, Redis-inspired key-value server written in Python. Kelvin accepts RESP2 commands over TCP, serves multiple clients with `asyncio`, and persists data in SQLite.

The server uses the Redis Serialization Protocol version 2 (RESP2) for client requests and responses.

## Features

- TCP server listening on `127.0.0.1:6379` by default
- Concurrent client connections with `asyncio`
- Redis-compatible RESP2 request and response framing
- Persistent key-value storage with SQLite
- Optional bounded in-memory LRU cache
- Pipelined commands over a single connection
- Configurable IP address, port, and cache size from the command line
- No third-party Python packages required
- Graceful shutdown with `Ctrl+C`

## Requirements

- Python 3.10 or newer

The project uses only modules from the Python standard library.

## Getting started

Clone the repository, move into its directory, and start the server:

```bash
python main.py
```

You should see:

```text
Kelvin Starting
Server listening on: ('127.0.0.1', 6379)
Press Ctrl+C to exit instantly.
```

The server creates `kelvin.db` in the current working directory when it starts. This file stores all keys and values and is excluded from Git.

### Command-line options

```bash
python main.py --help
```

| Option | Description | Default |
| --- | --- | --- |
| `--ip ADDRESS` | Address on which the server listens | `127.0.0.1` |
| `--port PORT` | TCP port on which the server listens | `6379` |
| `--cache [SIZE]` | Enable the in-memory LRU cache | Disabled |

Supplying `--cache` without a size enables a capacity of 100 entries:

```bash
python main.py --cache
```

Provide an explicit positive capacity with:

```bash
python main.py --cache 1000
```

To use a different address and port:

```bash
python main.py --ip 127.0.0.1 --port 6380
```

Cache eviction removes only the in-memory copy. Values remain available in SQLite and can be loaded into the cache again on a later request.

## Usage

Commands are sent as RESP2 arrays of bulk strings. Command names are case-insensitive, while keys and values are case-sensitive.

| Command | Description | Example response |
| --- | --- | --- |
| `PING [message]` | Check availability or echo a message | `+PONG` or a bulk string |
| `SET <key> <value>` | Create or replace a value | `+OK` |
| `GET <key>` | Retrieve a value | Bulk string or `$-1` |
| `DEL <key>` | Delete a key | `:1` or `:0` |
| `EXISTS <key>` | Check whether a key exists | `:1` or `:0` |

Here is a minimal Python client:

```python
import socket

with socket.create_connection(("127.0.0.1", 6379)) as client:
    reader = client.makefile("rb")

    client.sendall(b"*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$6\r\nKelvin\r\n")
    print(reader.readline().decode().strip())  # OK

    client.sendall(b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n")
    print(reader.readline().decode().strip())  # $6
    print(reader.readline().decode().strip())  # Kelvin

    client.sendall(b"*2\r\n$3\r\nDEL\r\n$4\r\nname\r\n")
    print(reader.readline().decode().strip())  # :1
```

You can also send pipelined commands in one write:

```python
client.sendall(
    b"*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$6\r\nKelvin\r\n"
    b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"
)
```

The server returns a complete RESP2 value for each command.

## Tests

> Some tests were generated with AI assistance and subsequently reviewed and validated by the project author.

Run the complete automated test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

The suite covers command dispatch, RESP2 parsing and serialization, fragmented and pipelined requests, concurrent clients, SQLite-backed cache behavior, and LRU eviction.

Run one test module with:

```bash
python -m unittest discover -s tests -p "test_cache.py" -v
python -m unittest discover -s tests -p "test_commands.py" -v
python -m unittest discover -s tests -p "test_concurrency.py" -v
python -m unittest discover -s tests -p "test_resp2.py" -v
```

The current suite contains 30 tests.


## Manual examples

Start the server in one terminal, then run an example client in another:

```bash
python tests/buffer.py
python tests/fetchafterset.py
```

These scripts are manual integration examples. They connect to a server already running on `127.0.0.1:6379` and may read or modify the local database.

## Project structure

```text
.
|-- main.py                     # Application entry point
|-- database/
|   |-- model.py                # SQLite context and shared LRU cache
|   `-- commands/               # SET, GET, DEL, and EXISTS operations
|-- network/
|   |-- setup.py                # Asyncio TCP server setup
|   |-- client.py               # Per-client buffering and request handling
|   |-- resp2.py                # RESP2 parser and response encoders
|   `-- execute/commands.py     # Command validation and dispatch
`-- tests/                      # Automated tests and manual clients
```

## Current limitations

- Only RESP2 arrays containing bulk-string command arguments are accepted.
- Command arguments must contain valid UTF-8 text; arbitrary binary values are not yet supported.
- Only string values and five commands are supported.
- Database operations use synchronous SQLite calls and briefly block the event loop while executing.
- Authentication, encryption, key expiration, transactions, and Redis persistence formats are not yet supported.

## Stopping the server

Press `Ctrl+C` in the server terminal. The listening socket will be closed cleanly.
