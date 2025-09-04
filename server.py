import socket # For TCP socket operations used previously, replaced by asyncio streams
import os
import sys
import asyncio 
import logging

async def server(host, port, chunk_size, file_path):
    """Starts a socket server using asyncio streams"""
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, file_path, chunk_size),
        host, port
    )
    logging.info(f"Server started on {host}:{port}, serving file '{file_path}' in chunks of {chunk_size} bytes")
    try:
        await server.serve_forever()
    except KeyboardInterrupt:
        logging.info(f"\nServer on port {port} shutting down...")
    finally:
        server.close()
        await server.wait_closed()

async def handle_client(reader, writer, file_path, chunk_size):
    """Handle a client connection, sending the file in chunks"""
    try:
        # Send file size first
        file_size = os.path.getsize(file_path)
        writer.write(f"{file_size}\n".encode())
        await writer.drain()

        # Stream file content in chunks
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                writer.write(chunk)
                await writer.drain()
        logging.info(f"Server sent {file_size} bytes to {writer.get_extra_info('peername')}")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    # Ensure 'logs/' directory exists
    os.makedirs("logs", exist_ok=True)
    # Setup logging to file and console
    logging.basicConfig(level=logging.INFO, filename="logs/server.log", filemode="a",
                        format="%(asctime)s - %(levelname)s - %(message)s")
    #logging.getLogger().addHandler(logging.StreamHandler(sys.stdout)) # Uncomment to also log to console

    # Simple command line argument parsing
    if len(sys.argv) != 5:
        logging.warning("Usage: python server.py <host> <port> <chunk_size> <file_path>")
        logging.warning("Example: python server.py localhost 9001 8192 data/frankenstein.txt")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    chunk_size = int(sys.argv[3])
    file_path = sys.argv[4]

    if not os.path.exists(file_path):
        logging.error(f"Error: File '{file_path}' not found")
        sys.exit(1)

    asyncio.run(server(host, port, chunk_size, file_path))