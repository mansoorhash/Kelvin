import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 6379))

client.sendall(b"*1\r\n$4\r\nPING\r\n")

client.close()
