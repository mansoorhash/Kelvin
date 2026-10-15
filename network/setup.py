import socket as sk
from network.execute.commands import execute

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
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data: 
                            break
                        buffer += data

                        while b"\r\n" in buffer:
                            command, buffer = buffer.split(b"\r\n", 1)
                            response = execute(command.decode('utf-8', errors='ignore'))
                            conn.sendall((response + "\n").encode('utf-8'))
                    except sk.timeout:
                        continue
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing server socket...")
    finally:
        server.close()
        print("[+] Server stopped cleanly.")