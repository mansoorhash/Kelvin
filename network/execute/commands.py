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
            if len(arguments) == 2:
                key, value = arguments
                Operation.set(key=key, value=value, cache_size=cache_size)
            elif len(arguments) == 4:
                key, value, exp_type, expiration_value = arguments
                if exp_type != "PX" and exp_type != "EX":
                    return error_response(f"invalid expiration type, use PX (milliseconds) or EX (seconds)")
                if not expiration_value.isdecimal() or int(expiration_value) <= 0:
                    return error_response(f"invalid expiration time (time>0)")
                Operation.set(key=key, value=value, cache_size=cache_size, exp_type=exp_type, exp_time=int(expiration_value))
            else:
                return argumentCount(operation)            
            return simple_string("OK")
        
        elif operation == "GET":
            if len(arguments) != 1:
                return argumentCount(operation)
            result = Operation.get(key=arguments[0], cache_size=cache_size)
            return bulk_string(result)
    
        elif operation == "DEL":
            if len(arguments) != 1:
                return argumentCount(operation)
            return integer(Operation.delete(key=arguments[0], cache_size=cache_size))
    
        elif operation == "EXISTS":
            if len(arguments) != 1:
                return argumentCount(operation)
            result = Operation.exists(key=arguments[0], cache_size=cache_size)
            if result is None: result = 0
            return integer(result)

        elif operation == "TTL":
            if len(arguments) != 1:
                return argumentCount(operation)
            result = Operation.ttl(key=arguments[0], cache_size=cache_size)
            if result is None: result = -2
            else: result = int(result)
            return integer(result)

        return error_response(f"unknown command '{operation.lower()}'")
    except ConnectionError as e:
        return error_response(str(e))
