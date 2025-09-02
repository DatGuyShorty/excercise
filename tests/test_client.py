"""
Unit tests for TxtClient class methods.
"""
from tests.test_base import BaseTestCase
from client import TxtClient
from collections import Counter

class ClientUnitTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = TxtClient()

    def test_process_text_chunk_basic(self):
        """Test basic text processing with mixed case and punctuation."""
        text = "Hello world! This is a test."
        result = self.client.process_text_chunk(text)
        expected = Counter({'hello': 1, 'world': 1, 'this': 1, 'is': 1, 'a': 1, 'test': 1})
        self.assertEqual(result, expected)

    def test_process_text_chunk_case_insensitive(self):
        """Test that text processing is case-insensitive."""
        text = "Hello HELLO hello HeLLo"
        result = self.client.process_text_chunk(text)
        expected = Counter({'hello': 4})
        self.assertEqual(result, expected)

    def test_process_text_chunk_with_punctuation(self):
        """Test text processing with various punctuation marks."""
        text = "Hello, world! How are you? I'm fine."
        result = self.client.process_text_chunk(text)
        expected = Counter({'hello': 1, 'world': 1, 'how': 1, 'are': 1, 'you': 1, 'i': 1, 'm': 1, 'fine': 1})
        self.assertEqual(result, expected)

    def test_process_text_chunk_empty(self):
        """Test text processing with empty and None inputs."""
        result = self.client.process_text_chunk("")
        self.assertEqual(result, Counter())
        result = self.client.process_text_chunk(None)
        self.assertEqual(result, Counter())

    def test_process_buffer_complete_words(self):
        """Test buffer processing with complete words ending in space."""
        buffer = "hello world test "
        result = self.client.process_buffer(buffer)
        expected = Counter({'hello': 1, 'world': 1, 'test': 1})
        self.assertEqual(result, expected)

    def test_process_buffer_incomplete_word(self):
        """Test buffer processing with incomplete word at the end."""
        buffer = "hello world incompl"
        result = self.client.process_buffer(buffer)
        expected = Counter({'hello': 1, 'world': 1})
        self.assertEqual(result, expected)

    def test_process_buffer_no_complete_words(self):
        """Test buffer processing when no complete words are found."""
        buffer = "incomplete"
        result = self.client.process_buffer(buffer)
        self.assertEqual(result, Counter())

    def test_get_incomplete_word_with_space(self):
        """Test extracting incomplete word when buffer ends after space."""
        buffer = "hello world incompl"
        result = self.client.get_incomplete_word(buffer)
        self.assertEqual(result, "incompl")

    def test_get_incomplete_word_with_newline(self):
        """Test extracting incomplete word when buffer ends after newline."""
        buffer = "hello world\nincompl"
        result = self.client.get_incomplete_word(buffer)
        self.assertEqual(result, "incompl")

    def test_get_incomplete_word_no_boundary(self):
        """Test extracting incomplete word when no word boundaries exist."""
        buffer = "incomplete"
        result = self.client.get_incomplete_word(buffer)
        self.assertEqual(result, "incomplete")
