import socket
import asyncio
from collections import Counter
import re

class TxtClient:    
    async def read_from_server(self, addr, port):
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

            # Receive data in chunks
            received_data = b""
            chunk_size = 8192
            
            while len(received_data) < file_size:
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    break
                received_data += chunk
            
            count = len(received_data)  # Count bytes
            print(f"{addr}:{port}: {count} bytes read")

            client_socket.close()
            return count, received_data.decode("utf-8", errors="ignore")

        except Exception as e:
            print(f"Error reading from {addr}:{port}: {e}")
            return 0, ""
        
    async def run_analysis(self, servers):
        # Start both connections in parallel
        tasks = []
        for addr, port in servers:
            tasks.append(asyncio.create_task(self.analyze(addr, port)))

        # Wait for all tasks to complete
        return await asyncio.gather(*tasks)

    def process_text(self, text):
        # Process text to count words
        if not text:
            return Counter()
        
        # Convert to lowercase and extract words
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return Counter(words)
    
    def get_top_words(self, counter, n=10):
        # Get top N most common words
        return counter.most_common(n)
    
    async def analyze(self, addr, port):
        top_words = []
        try:
            count, text = await self.read_from_server(addr, port)
            if text:
                word_count = self.process_text(text)
                top_words = self.get_top_words(word_count, 5)   
                    
        except Exception as e:
            print(f"Error analyzing {addr}:{port}: {e}")
        return top_words
    
async def main():
    # Create client instance
    client = TxtClient()
    servers = [("localhost", 9001), ("localhost", 9002)] # Addresses and ports to servers
    try:
        # Run parallel analysis
        results = await client.run_analysis(servers)

        # Aggregate results from all servers
        aggregation_counter = Counter()
        for result in results:
            for word, count in result:
                aggregation_counter[word] += count

        # Print aggregated results
        print("Top 5 words across both files:")
        for word, count in aggregation_counter.most_common(5):
            print(f"  {word}: {count}")

    except Exception as e:
        print(f"Client error: {e}")


if __name__ == "__main__":
    asyncio.run(main())


