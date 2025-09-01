import socket
import asyncio
from collections import Counter
import re

class TxtClient:    
    async def read_from_server(self, addr, port, chunk_size):
        client_socket = None
        word_counter = Counter()
        text_buffer = ""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((addr, port))

            # Receive file size first, sockets need to know expected size before
            size_data = b""
            while True:
                char = client_socket.recv(1)
                if char == b"\n":
                    break
                size_data += char
            
            file_size = int(size_data.decode())
            print(f"{addr}:{port}: Expected {file_size} bytes")

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
                    text_chunk = chunk.decode("utf-8", errors="ignore")
                
                text_buffer += text_chunk

                # process complete words from buffer
                word_counter.update(self.process_buffer(text_buffer))
                # Keep incomplete word at end of buffer
                text_buffer = self.get_incomplete_word(text_buffer)

            # Process any remaining text in buffer
            if text_buffer.strip():
                word_counter.update(self.process_text_chunk(text_buffer))
            print(f"{addr}:{port}: {total_received} bytes processed")
            return word_counter
        

        except Exception as e:
            print(f"Error reading from {addr}:{port}: {e}")
            return Counter()
        finally:
            if client_socket:
                client_socket.close()
                
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
        # Start both connections in parallel
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


