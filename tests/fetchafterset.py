import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 6379))

    reader = client.makefile("rb")

    client.sendall(
        b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"
        b"*2\r\n$3\r\nDEL\r\n$4\r\nname\r\n"
        b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"
    )

    response1 = reader.readline()
    print(f"GET response: {response1.decode().strip()}")
    if response1 != b"$-1\r\n":
        print(reader.readline().decode().strip())

    response2 = reader.readline()
    print(f"DEL response: {response2.decode().strip()}")

    response3 = reader.readline()
    print(f"GET response: {response3.decode().strip()}")
