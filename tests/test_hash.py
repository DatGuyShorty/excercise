"""
Tests for data integrity and hash verification.
"""
from tests.test_base import BaseTestCase
import hashlib

class HashVerificationTests(BaseTestCase):
    def test_hash_calculation_consistency(self):
        """
        Test that rolling hash calculation produces the same result as single hash.
        
        Verifies that processing data in chunks produces identical hash values
        to processing the entire content at once, ensuring data integrity
        verification works correctly during streaming.
        """
        test_content = "This is a test file for hash verification."
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        rolling_hash = hashlib.sha256()
        chunk_size = 10
        for i in range(0, len(test_content), chunk_size):
            chunk = test_content[i:i+chunk_size].encode()
            rolling_hash.update(chunk)
        calculated_hash = rolling_hash.hexdigest()
        self.assertEqual(calculated_hash, expected_hash)
