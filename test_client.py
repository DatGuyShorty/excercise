from client import TxtClient
from collections import Counter
import pytest
import subprocess
import time
import os
import socket
import sys

def get_coverage_env():
    """Get environment variables for coverage in subprocesses"""
    env = os.environ.copy()
    env['COVERAGE_PROCESS_START'] = '.coveragerc'
    env['PYTHONPATH'] = os.getcwd()
    return env

@pytest.mark.parametrize("text,expected", [
    ("hello world hello test", Counter({'hello': 2, 'world': 1, 'test': 1})),
    ("Hello WORLD hello", Counter({'hello': 2, 'world': 1})),
    ("café café naïve façade", Counter({'café': 2, 'naïve': 1, 'façade': 1})),
    ("héllo wörld tëst résumé", Counter({'héllo': 1, 'wörld': 1, 'tëst': 1, 'résumé': 1})),
    ("hello café world naïve", Counter({'hello': 1, 'café': 1, 'world': 1, 'naïve': 1})),
    ("München München", Counter({'münchen': 2})),  # Fixed: should be lowercase
    ("Vysoké tatry sú krásné", Counter({'vysoké': 1, 'tatry': 1, 'sú': 1, 'krásné': 1})),  # Fixed: should be lowercase
    ("Praha je hlavní město a současně největší město Česka.", Counter({'praha': 1, 'je': 1, 'hlavní': 1, 'město': 2, 'a': 1, 'současně': 1, 'největší': 1, 'česka': 1}))  # Fixed: should be lowercase
])
def test_client_text_processing(text, expected):
    """Test client text processing functions with various inputs"""
    client = TxtClient()
    
    # Test basic text processing
    result = client.process_text_chunk(text)
    assert result == expected

@pytest.mark.parametrize("text,expected_buffer,expected_incomplete", [
    ("hello world incomplete", Counter({'hello': 1, 'world': 1}), "incomplete"),
    ("test buffer word", Counter({'test': 1, 'buffer': 1}), "word"),
    ("single", Counter(), "single"),
    ("café naïve incomplete", Counter({'café': 1, 'naïve': 1}), "incomplete"),
    ("", Counter(), "")
])
def test_client_buffer_processing(text, expected_buffer, expected_incomplete):
    """Test client buffer processing and incomplete word extraction"""
    client = TxtClient()
    
    # Test buffer processing (should only process complete words)
    result = client.process_buffer(text)
    assert result == expected_buffer
    
    # Test incomplete word extraction
    incomplete = client.get_incomplete_word(text)
    assert incomplete == expected_incomplete

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

# Fixtures for server setup
@pytest.fixture
def host():
    """Fixture to provide the server host"""
    return "localhost"

# available port fixture
@pytest.fixture
def available_port():
    """Find an available port for testing"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
    
@pytest.fixture
def chunk_size():
    """Fixture to provide the default chunk size"""
    return 1024

#server creation fixture
@pytest.fixture
def start_server(host, available_port, chunk_size):
    """Fixture to start server process with coverage"""
    sample_file = "data/test.txt"
    env = get_coverage_env()
    server_process = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(available_port), str(chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env)
    time.sleep(1)   # Give server time to start
    yield host, available_port, chunk_size  # Yield the host, port, and chunk size for the test to use

    # Cleanup: terminate the server process
    server_process.terminate()
    server_process.wait()
    time.sleep(0.5)

@pytest.mark.asyncio
async def test_real_client_server_interaction(start_server):
    """Test real client-server interaction"""
    addr, available_port, chunk_size = start_server
    client = TxtClient()
    servers = [(addr, available_port, chunk_size)]
    results = await client.run_analysis(servers)
    aggregation_counter = client.aggregate_results(results)
    expected = Counter({'test': 4, 'this': 3, 'is': 3, 'a': 3, 'txt': 1})
    assert aggregation_counter == expected

@pytest.mark.asyncio
async def test_multi_server_interaction():
    """Tests client interaction with 2 servers on different ports"""
    # Get two different available ports
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.bind(('', 0))
        port1 = s1.getsockname()[1]
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        s2.bind(('', 0))
        port2 = s2.getsockname()[1]
    
    host = "localhost"
    chunk_size = 1024
    sample_file = "data/test.txt"
    env = get_coverage_env()
    
    # Start two server processes on different ports
    server_process1 = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(port1), str(chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env)
    
    server_process2 = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(port2), str(chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env)
    
    try:
        time.sleep(1)  # Give servers time to start
        
        client = TxtClient()
        servers = [(host, port1, chunk_size), (host, port2, chunk_size)]
        results = await client.run_analysis(servers)
        aggregation_counter = client.aggregate_results(results)
        
        # Since we're connecting to two servers with the same file, we get double the counts
        expected = Counter({'test': 8, 'this': 6, 'is': 6, 'a': 6, 'txt': 2})
        assert aggregation_counter == expected
        
    finally:
        # Cleanup: terminate both server processes
        server_process1.terminate()
        server_process2.terminate()
        server_process1.wait()
        server_process2.wait()
        time.sleep(0.5)

@pytest.fixture(params=[64, 128, 256, 512, 2048, 4096, 8192])
def valid_chunk_size(request):
    """Fixture to provide valid chunk sizes (64-8192)"""
    return request.param

@pytest.fixture
def valid_chunk_server(host, available_port, valid_chunk_size):
    """Fixture to start server with valid chunk size"""
    sample_file = "data/test.txt"
    env = get_coverage_env()
    server_process = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(available_port), str(valid_chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env)
    time.sleep(1)   # Give server time to start
    yield host, available_port, valid_chunk_size

    # Cleanup: terminate the server process
    server_process.terminate()
    server_process.wait()
    time.sleep(0.5)

@pytest.mark.asyncio
async def test_valid_chunk_sizes(valid_chunk_server):
    """Tests client interaction with valid chunk sizes (64-8192)"""
    addr, available_port, chunk_size = valid_chunk_server
    client = TxtClient()
    servers = [(addr, available_port, chunk_size)]
    results = await client.run_analysis(servers)
    aggregation_counter = client.aggregate_results(results)
    expected = Counter({'test': 4, 'this': 3, 'is': 3, 'a': 3, 'txt': 1})
    assert aggregation_counter == expected

# chunk size tests - invalid range (should fail)
@pytest.fixture(params=[0, 1, 16, 32, 63, 16384, 32768, 9999999])
def invalid_chunk_size(request):
    """Fixture to provide invalid chunk sizes (outside 64-8192 range)"""
    return request.param

@pytest.mark.asyncio
async def test_invalid_chunk_sizes_fail(host, available_port, invalid_chunk_size):
    """Tests that server rejects invalid chunk sizes"""
    sample_file = "data/test.txt"
    env = get_coverage_env()
    
    # This should fail - server should exit with non-zero code
    with pytest.raises(subprocess.CalledProcessError):
        result = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
            host, str(available_port), str(invalid_chunk_size), str(sample_file)
        ], cwd=os.getcwd(), env=env, check=True, capture_output=True, timeout=5)
    
    # Alternative: Check that server process exits quickly with error
    server_process = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(available_port), str(invalid_chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Server should exit quickly due to validation error
        return_code = server_process.wait(timeout=3)
        assert return_code != 0, f"Server should have failed with invalid chunk_size {invalid_chunk_size}"
    except subprocess.TimeoutExpired:
        server_process.kill()
        pytest.fail(f"Server did not exit quickly with invalid chunk_size {invalid_chunk_size}")

#valid port tests
@pytest.fixture(params=[2100,4286, 5563, 4200, 9000, 25565, 65000])
def valid_port(request):
    """Fixture to provide valid port numbers (1-65535)"""
    return request.param

def test_valid_ports(valid_port):
    """Tests that server accepts valid port numbers"""
    host = "localhost"
    chunk_size = 1024
    sample_file = "data/test.txt"
    env = get_coverage_env()
    
    # This should succeed - server should start and then be terminated
    server_process = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(valid_port), str(chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        time.sleep(2)  # Give server time to start
        # Check if the server is still running
        assert server_process.poll() is None, f"Server should be running on valid port {valid_port}"
    finally:
        server_process.terminate()
        server_process.wait()
        time.sleep(0.5)

# invalid port tests
@pytest.fixture(params=[-1, 0, 65536, 70000, 80000])
def invalid_port(request):
    """Fixture to provide invalid port numbers (outside 1-65535 range)"""
    return request.param

@pytest.mark.asyncio
async def test_invalid_ports_fail(host, invalid_port, chunk_size):
    """Tests that server rejects invalid port numbers"""
    sample_file = "data/test.txt"
    env = get_coverage_env()
    
    # This should fail - server should exit with non-zero code
    with pytest.raises(subprocess.CalledProcessError):
        result = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
            host, str(invalid_port), str(chunk_size), str(sample_file)
        ], cwd=os.getcwd(), env=env, check=True, capture_output=True, timeout=5)
    
    # Alternative: Check that server process exits quickly with error
    server_process = subprocess.Popen([
        sys.executable, "-m", "coverage", "run", "--parallel-mode", "server.py",
        host, str(invalid_port), str(chunk_size), str(sample_file)
    ], cwd=os.getcwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Server should exit quickly due to validation error
        return_code = server_process.wait(timeout=3)
        assert return_code != 0, f"Server should have failed with invalid port {invalid_port}"
    except subprocess.TimeoutExpired:
        server_process.kill()
        pytest.fail(f"Server did not exit quickly with invalid port {invalid_port}")