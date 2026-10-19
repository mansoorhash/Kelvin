from database.model import Operation
from network.resp2 import bulk_string, error_response, integer, simple_string
from models import ExecuteResult

def argumentCount(opr: str) -> bytes:
    return error_response(f"wrong number of arguments for '{opr.lower()}' command")

def execute(
        commands: list[bytes | str], 
        cache_size: int | None, 
        aof: bool = False, 
        auto_commit: bool = True
    ) -> ExecuteResult:

    try:
        if not aof:
            try:
                operation = commands[0].decode("utf-8").upper()
                arguments = [part.decode("utf-8") for part in commands[1:]]
            except UnicodeDecodeError:
                return ExecuteResult(error_response("command arguments must be valid UTF-8"))
        else:
            operation = commands[0]
            arguments = commands[1:]

        commit_options = {}

        if not auto_commit:
            commit_options["auto_commit"] = False
        
        if operation == "PING":
            if len(arguments) == 0:
                return ExecuteResult(simple_string("PONG"))
            if len(arguments) == 1:
                return ExecuteResult(bulk_string(arguments[0]))
            return ExecuteResult(argumentCount(operation))
        
        elif operation == "SET":
            if len(arguments) == 2:
                key, value = arguments
                result = Operation.set(key=key, value=value, cache_size=cache_size, auto_commit=auto_commit,)
            elif len(arguments) == 4:
                key, value, exp_type, expiration_value = arguments
                valid_exp_types = {"PX", "EX"}
                if aof:
                    valid_exp_types.add("PXAT")

                if exp_type not in valid_exp_types:
                    return ExecuteResult(error_response(f"invalid expiration type, use PX (milliseconds) or EX (seconds)"))
                if not expiration_value.isdecimal() or int(expiration_value) <= 0:
                    return ExecuteResult(error_response(f"invalid expiration time (time>0)"))
                
                result = Operation.set(
                    key=key, value=value, 
                    cache_size=cache_size, 
                    exp_type=exp_type, 
                    exp_time=int(expiration_value), 
                    **commit_options
                )
            else:
                return ExecuteResult(argumentCount(operation))            
            
            if result.return_value is None:
                return ExecuteResult(response=simple_string("OK"))
            
            return ExecuteResult(
                response=simple_string(result.return_value),
                command=operation,
                expires_at=result.expires_at
            )
        
        elif operation == "GET":
            if len(arguments) != 1:
                return ExecuteResult(argumentCount(operation))
            result = Operation.get(key=arguments[0], cache_size=cache_size)
            return ExecuteResult(bulk_string(result.return_value))
    
        elif operation == "DEL":
            if len(arguments) != 1:
                return ExecuteResult(argumentCount(operation))
            result = Operation.delete(key=arguments[0], cache_size=cache_size)
            return ExecuteResult(
                integer(result.return_value),
                command=operation,
            )
        
        elif operation == "EXISTS":
            if len(arguments) != 1:
                return ExecuteResult(argumentCount(operation))
            result = Operation.exists(key=arguments[0], cache_size=cache_size)
            return ExecuteResult(integer(0 if result.return_value is None else result.return_value))
                

        elif operation == "TTL":
            if len(arguments) != 1:
                return ExecuteResult(argumentCount(operation))
            result = Operation.ttl(key=arguments[0], cache_size=cache_size)
            return ExecuteResult(integer(-2 if result.return_value is None else result.return_value))

        return ExecuteResult(error_response(f"unknown command '{operation.lower()}'"))
    except ConnectionError as e:
        return ExecuteResult(error_response(str(e)))
