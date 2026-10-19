from dataclasses import dataclass

@dataclass
class CommandResults:
    return_value: str | int | None = None
    expires_at: float | None = None

@dataclass
class ExecuteResult:
    response: bytes
    command: str | None = None
    expires_at: float | None = None