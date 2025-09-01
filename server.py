import socket
import os
import sys

def server(host, port, chunk_size, file_path):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server for {file_path} listening on {host}:{port}") 
        while True:
            client_socket, addr = server_socket.accept()
            try:
                # Send file size first
                file_size = os.path.getsize(file_path)
                client_socket.send(str(file_size).encode() + b"\n")

                # Stream file content in chunks, handles larger files better.
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)  # Use the specified chunk size
                        if not chunk:
                            break
                        client_socket.send(chunk)

                print(f"Server sent {file_size} bytes to {addr}")
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                if client_socket:
                    client_socket.close()
    except KeyboardInterrupt:
        print(f"\nServer on port {port} shutting down...")
    finally:
        if server_socket:
            server_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python server.py <host> <port> <chunk_size> <file_path>")
        print("Example: python server.py localhost 9001 8192 frankenstein.txt")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    chunk_size = int(sys.argv[3])
    file_path = sys.argv[4]

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)

    server(host, port, chunk_size, file_path)