import unittest

from decoding.router import get_random_sentence, generate_caesar_cipher, generate_morse_code, generate_affine_cipher


class TestGenerateTimeForLevel(unittest.TestCase):
    """Test cases for the generate_time_for_level function."""
    def test_correct_taken_sentence_generated(self):
        sentence = get_random_sentence()
        print(sentence)

    def test_correct_caesar_cipher_generated(self):
        sentence = get_random_sentence()
        print('\n', sentence, '\n')
        sentence = generate_caesar_cipher(sentence, 13)
        print(sentence, '\n')
        print(generate_caesar_cipher(sentence, 13))

    def test_correct_morse_code_generated(self):
        sentence = get_random_sentence()
        print('\n', sentence, '\n')
        print(generate_morse_code(sentence))

    def test_correct_affine_cipher_generated(self):
        sentence = get_random_sentence()
        print('\n', sentence, '\n')
        print(generate_affine_cipher(sentence))




if __name__ == "__main__":
    unittest.main()