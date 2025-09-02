"""
Base test case with common setup/teardown and utilities.
"""
import unittest
import tempfile
import os
import subprocess
import shutil

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # Create test directory in the program's working directory instead of system temp
        program_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_dir_name = f"test_temp_{id(self)}"  # Use object id for uniqueness
        self.test_data_dir = os.path.join(program_dir, test_dir_name)
        os.makedirs(self.test_data_dir, exist_ok=True)
        self.test_files = {}
        self.servers = []

    def tearDown(self):
        for server_proc in self.servers:
            if server_proc and server_proc.poll() is None:
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    server_proc.kill()
        
        # Clean up test files and directory
        if os.path.exists(self.test_data_dir):
            try:
                shutil.rmtree(self.test_data_dir)
            except Exception as e:
                # If directory removal fails, try to remove individual files
                for file_path in self.test_files.values():
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                # Try to remove directory again
                try:
                    os.rmdir(self.test_data_dir)
                except Exception:
                    pass

    def create_test_file(self, name, content):
        file_path = os.path.join(self.test_data_dir, name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.test_files[name] = file_path
        return file_path
