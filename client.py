import socket
import asyncio
from collections import Counter
import re
import hashlib
import logging

# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TxtClient:    
    async def read_from_server(self, addr, port, chunk_size):
        client_socket = None
        word_counter = Counter()
        text_buffer = ""
        rolling_hash = hashlib.sha256()  # For data integrity verification
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
            client_socket.connect((addr, port))  # Connect to server

            # Receive file size first, sockets need to know expected size before transfer
            size_data = b""
            while True:
                # Read in small chunks instead of byte-by-byte for better efficiency
                char = client_socket.recv(1)
                if not char or char == b"\n":
                    break
                size_data += char
  
            file_size = int(size_data.decode())
            logger.info(f"{addr}:{port}: Expected {file_size} bytes")

            # Stream and process data in chunks with a buffer
            total_received = 0
            while total_received < file_size:
                remaining = file_size - total_received
                chunk = client_socket.recv(min(chunk_size, remaining))
                if not chunk:
                    break

                rolling_hash.update(chunk)  # Update integrity hash
                total_received += len(chunk)
                
                # decoding and adding to a buffer  
                try:
                    text_chunk = chunk.decode("utf-8")
                except UnicodeDecodeError as e:
                    # Handle partial UTF-8 characters at chunk boundaries more gracefully
                    logger.warning(f"UTF-8 decode warning at {addr}:{port} - using replacement chars")
                    text_chunk = chunk.decode("utf-8", errors="replace")
                
                text_buffer += text_chunk

                # process complete words from buffer
                word_counter.update(self.process_buffer(text_buffer))
                # Keep incomplete word at end of buffer
                text_buffer = self.get_incomplete_word(text_buffer)

            # Process any remaining text in buffer
            if text_buffer.strip():
                word_counter.update(self.process_text_chunk(text_buffer))
                
            # Try to receive hash for integrity verification (optional - server may not send)
            try:
                client_socket.settimeout(1.0)  # Short timeout for hash
                hash_data = self._try_receive_hash(client_socket)
                if hash_data:
                    received_hash = rolling_hash.hexdigest()
                    if received_hash == hash_data:
                        logger.info(f"{addr}:{port}: [OK] Hash verification successful")
                    else:
                        logger.warning(f"{addr}:{port}: [WARNING] Hash mismatch")
            except socket.timeout:
                pass  # No hash sent, continue normally
            except Exception:
                pass  # Hash verification failed, but don't break functionality
            
            logger.info(f"{addr}:{port}: {total_received} bytes processed")
            return word_counter
        

        except Exception as e:
            logger.error(f"Error reading from {addr}:{port}: {e}")
            return Counter()
        finally:
            if client_socket:
                client_socket.close()
    
    def _try_receive_hash(self, sock):
        """Try to receive hash from server if available"""
        try:
            # Look for hash pattern
            data = b""
            while len(data) < 100:  # Reasonable limit
                char = sock.recv(1)
                if not char:
                    break
                data += char
                if b"HASH:" in data and data.endswith(b"\n"):
                    # Found complete hash message
                    hash_line = data.decode('utf-8').strip()
                    if "HASH:" in hash_line:
                        return hash_line.split("HASH:")[1].strip()
            return None
        except Exception:
            return None
                
    def process_buffer(self, buffer):
        """Process complete words from buffer, return word counter"""
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
        # Process a chunk of text and return word counter
        if not text:
            return Counter()
        
        # Convert to lowercase and extract words to count them
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return Counter(words)
    
    async def run_analysis(self, servers):
        """
        Run analysis on multiple servers in parallel.

        Args:
            servers (list): List of tuples (addr, port, chunk_size).

        Returns:
            list: List of results from each server, in the same order as the input tasks.
        """
        # Start connections in parallel
        tasks = []
        for addr, port, chunk_size in servers:
            tasks.append(asyncio.create_task(self.read_from_server(addr, port, chunk_size)))

        # Wait for all tasks to complete
        return await asyncio.gather(*tasks)
        
async def main():
    # Create client instance
    client = TxtClient()
    servers = [("localhost", 9001, 8192), ("localhost", 9002, 8192)] # Addresses, ports, and chunk sizes for servers
    try:
        # Run parallel analysis
        results = await client.run_analysis(servers)

        # Aggregate results from all servers
        aggregation_counter = Counter()
        for result in results:
            aggregation_counter.update(result)

        # Print aggregated results
        print("Top 5 words across both files:")
        for word, count in aggregation_counter.most_common(5):
            print(f"  {word}: {count}")

    except Exception as e:
        print(f"Client error: {e}")


if __name__ == "__main__":
    asyncio.run(main())


