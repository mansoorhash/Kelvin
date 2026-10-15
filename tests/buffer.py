import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 6379))
    reader = client.makefile("rb")

    client.sendall(
        b"*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$4\r\njohn\r\n"
        b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"
        b"*2\r\n$3\r\nDEL\r\n$4\r\nname\r\n"
        b"*2\r\n$6\r\nEXISTS\r\n$4\r\nname\r\n"
    )

    set_response = reader.readline()
    print(f"SET response: {set_response.decode().strip()}")

    get_header = reader.readline()
    get_value = reader.readline()
    print(
        f"GET response: "
        f"{get_header.decode().strip()} "
        f"{get_value.decode().strip()}"
    )

    delete_response = reader.readline()
    print(f"DEL response: {delete_response.decode().strip()}")

    exists_response = reader.readline()
    print(f"EXISTS response: {exists_response.decode().strip()}")