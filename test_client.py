from client import TxtClient
from collections import Counter
import pytest
import subprocess
import time
import os
import socket
import sys


def test_client_text_processing():
    """Test client text processing functions directly (no server needed)"""
    client = TxtClient()
    
    # Test basic text processing
    result = client.process_text_chunk("hello world hello test")
    expected = Counter({'hello': 2, 'world': 1, 'test': 1})
    assert result == expected
    
    # Test case insensitive
    result = client.process_text_chunk("Hello WORLD hello")
    expected = Counter({'hello': 2, 'world': 1})
    assert result == expected
    
    # Test buffer processing
    result = client.process_buffer("hello world incomplete")
    expected = Counter({'hello': 1, 'world': 1})  # 'incomplete' should not be counted
    assert result == expected
    
    # Test incomplete word extraction
    incomplete = client.get_incomplete_word("hello world incomplete")
    assert incomplete == "incomplete"

def test_client_utf8_handling():
    """Test client handles UTF-8 characters correctly"""
    client = TxtClient()
    
    # Test with accented characters
    result = client.process_text_chunk("café café naïve façade")
    expected = Counter({'café': 2, 'naïve': 1, 'façade': 1})
    assert result == expected
    
    # Test with various Unicode letters
    result = client.process_text_chunk("héllo wörld tëst résumé")
    expected = Counter({'héllo': 1, 'wörld': 1, 'tëst': 1, 'résumé': 1})
    assert result == expected

    # Test with mixed ASCII and Unicode
    result = client.process_text_chunk("hello café world naïve")
    expected = Counter({'hello': 1, 'café': 1, 'world': 1, 'naïve': 1})
    assert result == expected

# available port fixture
@pytest.fixture
def available_port():
    """Find an available port for testing"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
    
#server creation fixture
@pytest.fixture
def start_server(available_port):
    """Fixture to start server process"""
    sample_file = "data/test.txt"

    server_process = subprocess.Popen([ 
        sys.executable, "server.py", 
        "localhost", str(available_port), "1024", str(sample_file)
    ], cwd=os.getcwd())
    time.sleep(1)   # Give server time to start
    yield available_port  # Yield the port for the test to use
    
    # Cleanup: terminate the server process
    server_process.terminate()
    server_process.wait()
    time.sleep(0.5)

@pytest.mark.asyncio
async def test_real_client_server_interaction(start_server):
    """Test real client-server interaction"""
    available_port = start_server
    client = TxtClient()
    servers = [("localhost", available_port, 1024)]
    results = await client.run_analysis(servers)
    aggregation_counter = client.aggregate_results(results)
    expected = Counter({'test': 4, 'this': 3, 'is': 3, 'a': 3, 'txt': 1})
    assert aggregation_counter == expected

@pytest.mark.asyncio
async def test_multi_server_interaction(start_server):
    """Tests client interaction with 2 servers"""
    first_server = start_server
    second_server = start_server
    client = TxtClient()
    servers = [("localhost", first_server, 1024), ("localhost", second_server, 1024)]
    results = await client.run_analysis(servers)
    aggregation_counter = client.aggregate_results(results)
    expected = Counter({'test': 8, 'this': 6, 'is': 6, 'a': 6, 'txt': 2})
    assert aggregation_counter == expected
