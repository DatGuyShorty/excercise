"""
Stress tests for performance and reliability.
"""
from tests.test_base import BaseTestCase
from client import TxtClient
from collections import Counter

class StressTests(BaseTestCase):
    def test_large_file_processing(self):
        """Test processing large text content efficiently without memory issues."""
        large_content = "word " * 10000
        client = TxtClient()
        result = client.process_text_chunk(large_content)
        self.assertEqual(result['word'], 10000)
        self.assertEqual(len(result), 1)

    def test_unicode_handling(self):
        """Test proper handling of Unicode characters from various languages."""
        unicode_content = "café naïve résumé 测试 こんにちは"
        client = TxtClient()
        result = client.process_text_chunk(unicode_content)
        self.assertIsInstance(result, Counter)
