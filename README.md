# Redis-Inspired Key-Value Server

A small, dependency-free key-value server written in Python. It accepts commands over a TCP socket and persists data in a local SQLite database.

The server uses the Redis Serialization Protocol version 2 (RESP2) for client requests and responses.

## Features

- TCP server listening on `127.0.0.1:6379` by default
- Persistent key-value storage with SQLite
- Multiple commands can be sent over one connection
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
Redis Starting
Server listening on 127.0.0.1:6379. Press Ctrl+C to exit instantly.
```

The server creates `kelvin.db` in the current working directory when it starts. This file stores all keys and values and is excluded from Git.

## Usage

Commands are sent as RESP2 arrays of bulk strings. Command names are case-insensitive, while keys and values are case-sensitive.

| Command | Description | Example response |
| --- | --- | --- |
| `PING` | Check that the server is available | `PONG` |
| `SET <key> <value>` | Create or replace a value | `OK` |
| `GET <key>` | Retrieve a value | The stored value |
| `DEL <key>` | Delete a key | `OK` |
| `EXISTS <key>` | Check if key exists |  |
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

## Running the examples

Start the server in one terminal, then run an example client in another:

```bash
python tests/buffer.py
python tests/fetchafterset.py
```

These files are simple integration examples rather than an automated test suite. They connect to a server already running on `127.0.0.1:6379` and may read or modify the local database.

## Project structure

```text
.
|-- main.py                     # Application entry point
|-- database/
|   |-- model.py                # SQLite connection and operation wrapper
|   `-- commands/               # GET, SET, and DEL database operations
|-- network/
|   |-- setup.py                # TCP server and request buffering
|   `-- execute/commands.py     # Command parsing and dispatch
`-- tests/                      # Socket client examples
```

## Current limitations

- Only RESP2 arrays containing bulk-string command arguments are accepted.
- Command arguments must contain valid UTF-8 text; arbitrary binary values are not yet supported.
- Only string values and five commands are supported.
- Connections are handled synchronously, one client at a time.
- The bind address and port can be changed through `network.setup.run()`, but there are no command-line flags yet.

## Stopping the server

Press `Ctrl+C` in the server terminal. The listening socket will be closed cleanly.
