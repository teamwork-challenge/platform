import unittest
from unittest.mock import patch, mock_open
from math import gcd
from collections import Counter

from decoding.router import (
    get_random_sentence,
    generate_caesar_cipher,
    generate_morse_code,
    generate_affine_cipher,
    generate_reversed_swapped_sentence,
    is_binary_string,
    is_prefix_free,
    huffman_bit_length,
    add_hint_sentence,
    check_student_answer_huffman,
    get_difficulty,
    generate_input,
    STATEMENTS,
    MORSE_CODE
)


class TestDecodingFunctions(unittest.TestCase):
    """Test cases for all decoding functions."""

    def test_generate_caesar_cipher(self):
        # Test basic shift
        self.assertEqual(generate_caesar_cipher("abc", 1), "bcd")
        # Test wrap around
        self.assertEqual(generate_caesar_cipher("xyz", 3), "abc")
        # Test non-alphabetic characters
        self.assertEqual(generate_caesar_cipher("a b c!", 1), "b c d!")
        # Test full rotation (26 chars)
        original = "hello world"
        self.assertEqual(generate_caesar_cipher(generate_caesar_cipher(original, 13), 13), original.lower())

    def test_generate_morse_code(self):
        # Test known conversions
        self.assertEqual(generate_morse_code("sos"), "... --- ...")
        self.assertEqual(generate_morse_code("a b"), ".-  -...")
        # Test non-alphabetic characters
        self.assertEqual(generate_morse_code("a"), ".-")

    def test_generate_reversed_swapped_sentence(self):
        # Test even length
        self.assertEqual(generate_reversed_swapped_sentence("abcd"), "cdab")
        # Test odd length
        self.assertEqual(generate_reversed_swapped_sentence("abc"), "cab")
        # Test with spaces
        self.assertEqual(generate_reversed_swapped_sentence("aaa"), "aaa")

    def test_generate_affine_cipher(self):
        sentence = "test"
        encoded, formula = generate_affine_cipher(sentence)
        # Should be same length
        self.assertEqual(len(encoded), len(sentence))
        # Formula should be in expected format
        self.assertTrue(formula.startswith("f(x) = ("))
        self.assertIn("mod 26", formula)

    def test_is_binary_string(self):
        self.assertTrue(is_binary_string("010101"))
        self.assertFalse(is_binary_string("0101a1"))
        self.assertTrue(is_binary_string(""))

    def test_is_prefix_free(self):
        self.assertTrue(is_prefix_free(["0", "10", "11"]))
        self.assertFalse(is_prefix_free(["0", "01", "11"]))
        self.assertTrue(is_prefix_free(["00", "01", "10", "11"]))

    def test_huffman_bit_length(self):
        # Test uniform distribution
        self.assertEqual(huffman_bit_length("aaaa"), 4)
        # Test varied distribution
        self.assertEqual(huffman_bit_length("aaabbc"), 9)
        # Test single character
        self.assertEqual(huffman_bit_length("a"), 1)

    def test_add_hint_sentence(self):
        original = "decode this"
        result = add_hint_sentence(original)
        self.assertIn("reverse", result)
        self.assertIn("swap", result)
        self.assertIn(original, result)

    def test_check_student_answer_huffman(self):
        # Test valid case
        valid_answer = "2\na 0\nb 1\n01"
        success, msg = check_student_answer_huffman(2, valid_answer)
        self.assertTrue(success)

        # Test invalid binary
        invalid_binary = "2\na 0\nb 2\n01"
        success, msg = check_student_answer_huffman(2, invalid_binary)
        self.assertFalse(success)

        # Test non-prefix-free
        non_prefix_free = "2\na 0\nb 01\n001"
        success, msg = check_student_answer_huffman(3, non_prefix_free)
        self.assertFalse(success)


    def test_generate_input(self):
        sentence = "test sentence"

        # Test level 1 (basic Caesar)
        result, hint = generate_input(1, sentence)
        self.assertEqual(generate_caesar_cipher(result, -1), sentence.lower())

        # Test level 4 (Morse with hint)
        result, hint = generate_input(4, sentence)
        self.assertIn("reverse", hint)

        # Test level 8 (Huffman)
        result, bit_length = generate_input(8, sentence)
        self.assertEqual(result, "testsentence")
        self.assertEqual(bit_length, huffman_bit_length("testsentence"))

    def test_statements(self):
        self.assertIn("v1", STATEMENTS)
        self.assertIn("v8", STATEMENTS)
        self.assertTrue(len(STATEMENTS) >= 8)


if __name__ == "__main__":
    unittest.main()