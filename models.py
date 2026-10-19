from dataclasses import dataclass
import asyncio

@dataclass
class CommandResults:
    return_value: str | int | None = None
    expires_at: float | None = None

@dataclass
class ExecuteResult:
    response: bytes
    command: str | None = None
    expires_at: float | None = None

@dataclass
class WriteRequest:
    command: list[bytes]
    cache_size: int | None
    future: asyncio.Future