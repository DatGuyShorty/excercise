import socket
import os
import sys

def server(addr, port, file_path):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((addr, port))
    server_socket.listen(5)
    print(f"Server for {file_path} listening on {addr}:{port}")

    while True:
        client_socket, address = server_socket.accept()
        try:
            # Send file size first
            file_size = os.path.getsize(file_path)
            client_socket.send(str(file_size).encode() + b"\n")

            # Stream file content in chunks, handles larger files better.
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks, might increase later
                    if not chunk:
                        break
                    client_socket.send(chunk)
            
            print(f"Server sent {file_size} bytes to {address}")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    
    if len(sys.argv) != 4:
        print("Usage: python server.py <host> <port> <file_path>")
        print("Example: python server.py localhost 9001 frankenstein.txt")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    file_path = sys.argv[3]
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    server(host, port, file_path)