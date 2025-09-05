import socket # For TCP socket operations used previously, replaced by asyncio streams
import os
import sys
import asyncio 
import logging

class TxtServer:
    async def startup_server(self, host: str, port: int, chunk_size: int, file_path: str):
        """
        Starts a socket server using asyncio streams
        Args: host (str): server host ('' or '0.0.0.0' for all interfaces)
              port (int): server port (e.g. 1024-65535)
              chunk_size (int): size of data chunks to send (e.g. 256-8192)
              file_path (str): path to the text file to send (e.g. 'data/frankenstein.txt')
        Returns: None
        """
        if port < 1 or port > 65535:
            logging.error("Error: Port must be in range 1-65535")
            raise ValueError("Port must be in range 1-65535")
        elif chunk_size < 256 or chunk_size > 8192:
            logging.error("Error: chunk_size must be in range 256-8192")
            raise ValueError("chunk_size must be in range 256-8192")
        elif not os.path.exists(file_path):
            logging.error(f"Error: File '{file_path}' not found")
            raise ValueError(f"File '{file_path}' not found")

        server = await asyncio.start_server(
            lambda r, w: self.handle_client(r, w, file_path, chunk_size),
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

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, file_path: str, chunk_size: int):
        """
        Handle a client connection, sending the file in chunks
        Args: reader (StreamReader): asyncio stream reader
              writer (StreamWriter): asyncio stream writer
              file_path (str): path to the text file to send
              chunk_size (int): size of data chunks to send
        Returns: None
        """
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
    # Setup logging
    # Ensure 'logs/' directory exists
    os.makedirs("logs", exist_ok=True)
    # Setup logging to file and console
    logging.basicConfig(level=logging.INFO, filename="logs/server.log", filemode="a",
                        format="%(asctime)s - %(levelname)s - %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout)) # Also logs to console
    
    # Simple command line argument parsing and validation for host, port, chunk_size, file_path
    if len(sys.argv) != 5 or sys.argv[1] in ('-h', '--help'): # Expecting 4 args: host, port, chunk_size, file_path
        logging.warning("Usage: python server.py <host> <port> <chunk_size> <file_path>")
        logging.warning("Example: python server.py localhost 9001 8192 data/frankenstein.txt")
        sys.exit(1)
    elif sys.argv[2].isalpha() or sys.argv[3].isalpha(): # Check if port and chunk_size are integers
        logging.error("Error: Port and chunk_size must be integers")
        sys.exit(1)


    host = sys.argv[1]
    port = int(sys.argv[2])
    chunk_size = int(sys.argv[3])
    file_path = sys.argv[4]

    server = TxtServer()
    asyncio.run(server.startup_server(host, port, chunk_size, file_path))