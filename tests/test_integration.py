"""
Integration tests for client-server communication.
"""
from tests.test_base import BaseTestCase
from client import TxtClient
from collections import Counter
import subprocess, sys, time, asyncio

class IntegrationTests(BaseTestCase):
    def start_test_server(self, port, file_path):
        server_proc = subprocess.Popen([
            sys.executable, "server.py", 
            "localhost", str(port), "1024", file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.servers.append(server_proc)
        time.sleep(2)  # Give more time for async server startup
        return server_proc

    def test_client_server_integration_single(self):
        test_content = "hello world test hello"
        test_file = self.create_test_file("test.txt", test_content)
        self.start_test_server(9003, test_file)
        async def run_test():
            client = TxtClient()
            result = await client.read_from_server('localhost', 9003, 1024)
            return result
        result = asyncio.run(run_test())
        expected = Counter({'hello': 2, 'world': 1, 'test': 1})
        self.assertEqual(result, expected)

    def test_client_server_integration_multiple(self):
        test_content1 = "hello world"
        test_content2 = "world test"
        test_file1 = self.create_test_file("test1.txt", test_content1)
        test_file2 = self.create_test_file("test2.txt", test_content2)
        self.start_test_server(9004, test_file1)
        self.start_test_server(9005, test_file2)
        async def run_test():
            client = TxtClient()
            servers = [("localhost", 9004, 1024), ("localhost", 9005, 1024)]
            results = await client.run_analysis(servers)
            total_counter = Counter()
            for result in results:
                total_counter.update(result)
            return total_counter
        result = asyncio.run(run_test())
        expected = Counter({'world': 2, 'hello': 1, 'test': 1})
        self.assertEqual(result, expected)
