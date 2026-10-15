import socket as sk
from network.execute.commands import execute
from network.resp2 import RESPProtocolError, error_response, parse_request

TIMEOUT = .5

def run(ip: str = "127.0.0.1", port: int = 6379):
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen()
    server.settimeout(TIMEOUT)

    print(f"Server listening on {ip}:{port}. Press Ctrl+C to exit instantly.")

    try:
        while True:
            try:
                conn, addr = server.accept()
            except sk.timeout:
                continue

            buffer = b""
            with conn:
                conn.settimeout(TIMEOUT)
                close_connection = False
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data: 
                            break
                        buffer += data

                        while buffer:
                            try:
                                parsed = parse_request(buffer)
                            except RESPProtocolError as error:
                                conn.sendall(error_response(f"Protocol error: {error}"))
                                close_connection = True
                                break

                            if parsed is None:
                                break

                            command, buffer = parsed
                            conn.sendall(execute(command))

                        if close_connection:
                            break
                    except sk.timeout:
                        continue
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing server socket...")
    finally:
        server.close()
        print("[+] Server stopped cleanly.")
