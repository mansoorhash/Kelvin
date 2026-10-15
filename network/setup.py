import socket as sk

store = {}

def run(ip: str = "127.0.0.1", port: int = 6379):
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.bind((ip, port))
    server.listen()

    while True:
        conn, addr = server.accept()
        with conn:
            data = conn.recv(1024).decode()
            print('recieved ', data)
            print('addr ', addr)

