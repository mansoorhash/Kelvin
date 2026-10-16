from database.model import Operation
from network.resp2 import bulk_string, error_response, integer, simple_string

def argumentCount(opr: str) -> bytes:
    return error_response(f"wrong number of arguments for '{opr.lower()}' command")

def execute(commands: list[bytes], cache_size: int | None) -> bytes:
    try:
        try:
            operation = commands[0].decode("utf-8").upper()
            arguments = [part.decode("utf-8") for part in commands[1:]]
        except UnicodeDecodeError:
            return error_response("command arguments must be valid UTF-8")
        
        if operation == "PING":
            if len(arguments) == 0:
                return simple_string("PONG")
            if len(arguments) == 1:
                return bulk_string(arguments[0])
            return argumentCount(operation)
        
        elif operation == "SET":
            if len(arguments) != 2:
                return argumentCount(operation)
    
            key, value = arguments
            Operation.set(key=key, value=value, cache_size=cache_size)
            return simple_string("OK")
        
        elif operation == "GET":
            if len(arguments) != 1:
                return argumentCount(operation)
            return bulk_string(Operation.get(key=arguments[0], cache_size=cache_size))
    
        elif operation == "DEL":
            if len(arguments) != 1:
                return argumentCount(operation)
            return integer(Operation.delete(key=arguments[0], cache_size=cache_size))
    
        elif operation == "EXISTS":
            if len(arguments) != 1:
                return argumentCount(operation)
            return integer(Operation.exists(key=arguments[0], cache_size=cache_size))
    
        return error_response(f"unknown command '{operation.lower()}'")
    except ConnectionError as e:
        return error_response(str(e))
