import socket
import asyncio
from collections import Counter
import re
import logging
import sys
import os

class TxtClient:    
    async def read_from_server(self, addr, port, chunk_size):
        """
        Read text data from server and count word occurrences
        Args: addr (str): server address
              port (int): server port
              chunk_size (int): size of data chunks to read
        Returns: Counter of words
        """
        client_socket = None
        word_counter = Counter()  # Counter to aggregate word counts
        text_buffer = ""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
            client_socket.connect((addr, port))  # Connect to server

            # Receive file size first, sockets need to know expected size before transfer
            size_data = b""
            while True:
                char = client_socket.recv(1)
                if char == b"\n":
                    break
                size_data += char
  
            file_size = int(size_data.decode())
            logging.info(f"{addr}:{port}: Expected {file_size} bytes")

            # Stream and process data in chunks with a buffer
            total_received = 0
            while total_received < file_size:
                chunk = client_socket.recv(min(chunk_size, file_size - total_received))
                if not chunk:
                    break

                total_received += len(chunk)
                # decoding and adding to a buffer
                try:
                    text_chunk = chunk.decode("utf-8")
                except UnicodeDecodeError:
                    # Handle partial UTF-8 characters at chunk boundaries
                    text_chunk = chunk.decode("utf-8", errors="replace")
                text_buffer += text_chunk

                # process complete words from buffer
                word_counter.update(self.process_buffer(text_buffer))
                # Keep incomplete word at end of buffer
                text_buffer = self.get_incomplete_word(text_buffer)

            # Process any remaining text in buffer
            if text_buffer.strip():
                word_counter.update(self.process_text_chunk(text_buffer))
            logging.info(f"{addr}:{port}: {total_received} bytes processed")
            return word_counter
        

        except Exception as e:
            logging.error(f"Error reading from {addr}:{port}: {e}")
            return Counter()
        finally:
            if client_socket:
                client_socket.close()
                
    def process_buffer(self, buffer):
        """
        Process complete words from buffer, return word counter
        Args: buffer (str): text buffer to process
        Returns: Counter of words
        """
        # Find last complete word boundary
        last_space = buffer.rfind(' ')
        last_newline = buffer.rfind('\n')
        last_boundary = max(last_space, last_newline)
        
        if last_boundary == -1:
            return Counter()  # No complete words
        
        # Process text up to last word boundary
        complete_text = buffer[:last_boundary]
        return self.process_text_chunk(complete_text)
    
    def get_incomplete_word(self, buffer):
        """Return the incomplete word at the end of buffer"""
        last_space = buffer.rfind(' ')
        last_newline = buffer.rfind('\n')
        last_boundary = max(last_space, last_newline)
        
        if last_boundary == -1:
            return buffer  # Entire buffer is incomplete word
        
        return buffer[last_boundary + 1:]
    
    def process_text_chunk(self, text):
        """
        Process a chunk of text and return word counter.

        Args: text (str): text chunk to process

        Returns: Counter of words
        """
        # Process a chunk of text and return word counter
        if not text:
            return Counter()
        
        # Convert to lowercase and extract words to count them
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return Counter(words)
    
    async def run_analysis(self, servers):
        """
        Run analysis on multiple servers in parallel using async.

        Args: servers (list): List of tuples (addr, port, chunk_size).

        Returns: list: List of results from each server, in the same order as the input tasks.
        """
        # Start connections in parallel
        tasks = []
        for addr, port, chunk_size in servers:
            tasks.append(asyncio.create_task(self.read_from_server(addr, port, chunk_size)))

        # Wait for all tasks to complete
        return await asyncio.gather(*tasks)
        
async def main(servers=None):

    if servers is None:
        logging.info("No servers provided, using default localhost servers.")
        servers = [("localhost", 9001, 8192), ("localhost", 9002, 8192)]  # Default servers

    # Create client instance
    client = TxtClient()
    try:
        # Run parallel analysis
        results = await client.run_analysis(servers)

        # Aggregate results from all servers
        aggregation_counter = Counter()
        for result in results:
            aggregation_counter.update(result)

        # Print aggregated results
        print(f"Top 5 words across {len(servers)} file{'s' if len(servers) != 1 else ''}:")
        for word, count in aggregation_counter.most_common(5):
            print(f"  {word}: {count}")

    except Exception as e:
        logging.error(f"Client error: {e}")


if __name__ == "__main__":
    # Ensure 'logs/' directory exists
    os.makedirs("logs", exist_ok=True)
    # Setup logging to file and console
    logging.basicConfig(level=logging.INFO, filename="logs/client.log", filemode="a",
                        format="%(asctime)s - %(levelname)s - %(message)s")
    #logging.getLogger().addHandler(logging.StreamHandler(sys.stdout)) # Uncomment to also log to console

    asyncio.run(main(servers=None)) # Use default servers if none provided

