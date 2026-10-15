from database.model import Operation

def argumentCount(opr: str) -> str:
    return f"{opr} wrong number of arguments"

def execute(commands: str) -> str:
    parts = commands.strip().split()

    if not parts:
        return "ERR empty command"

    operation = parts[0].upper()

    if operation == "PING":
        return "PONG"
    
    elif operation == "SET":
        if len(parts) != 3:
            return argumentCount(operation)

        key, value = parts[1], parts[2]
        
        return Operation.set(key=key, value=value)
    
    elif operation == "GET":
        if len(parts) != 2:
            return argumentCount(operation)
        key = parts[1]
        return Operation.get(key=key)

    elif operation == "DEL":
        if len(parts) != 2:
            return argumentCount(operation)
        key = parts[1]
        return Operation.delete(key=key)

    return "ERR invalid command"
        
