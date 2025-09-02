"""
Legacy integration test for backward compatibility.
"""
import subprocess, sys, time

class LegacyIntegrationTest:
    """
    Legacy integration test for backward compatibility verification.
    
    Performs end-to-end testing using the original test methodology,
    ensuring that new changes don't break existing functionality.
    Starts real servers and client processes to test actual system behavior.
    """
    def __init__(self):
        self.server_processes = []
    def run_legacy_test(self):
        print("\n" + "=" * 60)
        print("RUNNING LEGACY INTEGRATION TEST")
        print("=" * 60)
        server1_process = None
        server2_process = None
        try:
            print("Starting Frankenstein server...")
            server1_process = subprocess.Popen([
                sys.executable, "server.py", 
                "localhost", "9001", "8192", "data/frankenstein.txt"
            ])
            self.server_processes.append(server1_process)
            print("Starting Dracula server...")
            server2_process = subprocess.Popen([
                sys.executable, "server.py", 
                "localhost", "9002", "8192", "data/dracula.txt"
            ])
            self.server_processes.append(server2_process)
            print("Waiting for servers to start up...")
            time.sleep(5)  # More time for async servers
            print("Starting Client...")
            client_result = subprocess.run([
                sys.executable, "client.py"
            ], capture_output=True, text=True, timeout=30)
            print("Client Output:")
            print(client_result.stdout)
            if client_result.stderr:
                print("Client Errors:")
                print(client_result.stderr)
            return client_result.returncode == 0
        except subprocess.TimeoutExpired:
            print("ERROR: Client timed out!")
            return False
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            return False
        except Exception as e:
            print(f"ERROR: Error during test: {e}")
            return False
        finally:
            self._cleanup_servers()

    def _cleanup_servers(self):
        print("Stopping servers...")
        for i, server_proc in enumerate(self.server_processes, 1):
            if server_proc:
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=5)
                    print(f"Server {i} stopped")
                except subprocess.TimeoutExpired:
                    server_proc.kill()
                    print(f"WARNING: Server {i} forcefully stopped")
        print("Legacy test completed!")
