# Redis-Inspired Key-Value Server

A small, dependency-free key-value server written in Python. It accepts commands over a TCP socket and persists data in a local SQLite database.

This project is inspired by Redis, but it is **not compatible with the Redis protocol (RESP)** and is intended for learning and experimentation.

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

Commands are plain UTF-8 text terminated by `\r\n`. Command names are case-insensitive, while keys and values are case-sensitive.

| Command | Description | Example response |
| --- | --- | --- |
| `PING` | Check that the server is available | `PONG` |
| `SET <key> <value>` | Create or replace a value | `OK` |
| `GET <key>` | Retrieve a value | The stored value |
| `DEL <key>` | Delete a key | `OK` |

Here is a minimal Python client:

```python
import socket

with socket.create_connection(("127.0.0.1", 6379)) as client:
    reader = client.makefile("rb")

    client.sendall(b"SET name Kelvin\r\n")
    print(reader.readline().decode().strip())  # OK

    client.sendall(b"GET name\r\n")
    print(reader.readline().decode().strip())  # Kelvin

    client.sendall(b"DEL name\r\n")
    print(reader.readline().decode().strip())  # OK
```

You can also send pipelined commands in one write:

```python
client.sendall(b"SET name Kelvin\r\nGET name\r\n")
```

The server sends one newline-terminated response for each command.

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

- The wire format is custom plain text, not Redis RESP.
- Keys and values cannot contain whitespace.
- Only string values and four commands are supported.
- A missing key returns `Couldn't find item` rather than a Redis-style null value.
- Connections are handled synchronously, one client at a time.
- The bind address and port can be changed through `network.setup.run()`, but there are no command-line flags yet.

## Stopping the server

Press `Ctrl+C` in the server terminal. The listening socket will be closed cleanly.
