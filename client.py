import socket
import asyncio
from collections import Counter
import re
import logging
import sys
import os

class TxtClient:    
    async def read_from_server(self, addr: str, port: int, chunk_size: int):
        """
        Read text data from server and count word occurrences
        Args: addr (str): server address (e.g. 'localhost' or '0.0.0.0')
              port (int): server port (e.g. 1024-65535)
              chunk_size (int): size of data chunks to read (e.g. 256-8192)
        Returns: Counter of words  (Counter)
        """
        if port < 1 or port > 65535:
            logging.error("Error: Port must be in range 1-65535")
            raise ValueError("Port must be in range 1-65535")
        elif chunk_size < 256 or chunk_size > 8192:
            logging.error("Error: chunk_size must be in range 256-8192")
            raise ValueError("chunk_size must be in range 256-8192")
        
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

    def process_buffer(self, buffer: str):
        """
        Process complete words from buffer, return word counter
        Args: buffer (str): text buffer to process
        Returns: Counter of words (Counter)
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

    def get_incomplete_word(self, buffer: str):
        """
        Return the incomplete word at the end of buffer
        Args: buffer (str): text buffer
        Returns: str: incomplete word at end of buffer
        """
        last_space = buffer.rfind(' ')
        last_newline = buffer.rfind('\n')
        last_boundary = max(last_space, last_newline)
        
        if last_boundary == -1:
            return buffer  # Entire buffer is incomplete word
        
        return buffer[last_boundary + 1:]

    def process_text_chunk(self, text: str):
        """
        Process a chunk of text and return word counter.
        Args: text (str): text chunk to process
        Returns: Counter of words (Counter)
        """
        # Process a chunk of text and return word counter
        if not text:
            return Counter()
        
        # Convert to lowercase and extract words to count them
        # Use \w+ to match Unicode word characters (includes accented letters)
        # \w matches [a-zA-Z0-9_] plus Unicode letter categories
        words = re.findall(r"\b\w+\b", text.lower())
        return Counter(words)

    async def run_analysis(self, servers: list[tuple[str, int, int]]):
        """
        Run analysis on multiple servers in parallel using async.
        Args: servers (list): List of tuples (addr, port, chunk_size, e.g. ('localhost', 9001, 8192)).
        Returns: list: List of results from each server, in the same order as the input tasks.
        """
        # Start connections in parallel
        tasks = []
        for addr, port, chunk_size in servers:
            tasks.append(asyncio.create_task(self.read_from_server(addr, port, chunk_size)))

        # Wait for all tasks to complete
        return await asyncio.gather(*tasks)
    
    def aggregate_results(self, results: list[Counter]):
        """
        Aggregate word counts from multiple server results.
        Args: results (list): List of Counter objects from each server.
        Returns: Counter: Aggregated word counts.
        """
        aggregation_counter = Counter()
        for result in results:
            aggregation_counter.update(result)
        return aggregation_counter

    def print_results(self, aggregation_counter: Counter, num_servers: int):
        """
        Print the top 5 words from the aggregated results.
        Args: aggregation_counter (Counter): Aggregated word counts.
              num_servers (int): Number of servers processed.
        """
        print(f"Top 5 words across {num_servers} file{'s' if num_servers != 1 else ''}:")
        for word, count in aggregation_counter.most_common(5):
            print(f"  {word}: {count}")

async def main(servers: list[tuple[str, int, int]] = None):

    if servers is None:
        logging.info("No servers provided, using default localhost servers.")
        servers = [("localhost", 9001, 8192), ("localhost", 9002, 8192)]  # Default servers

    # Create client instance
    client = TxtClient()
    
    try:
        results = await client.run_analysis(servers)
        aggregation_counter = client.aggregate_results(results)
        client.print_results(aggregation_counter, len(servers))
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

