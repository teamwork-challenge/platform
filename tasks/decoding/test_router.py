import unittest
from datetime import datetime, timedelta
import pytz  # type: ignore[import-untyped]
import re

from decoding.router import get_random_sentence
from tasks.right_time.router import generate_time_for_level


class TestGenerateTimeForLevel(unittest.TestCase):
    """Test cases for the generate_time_for_level function."""
    def test_correct_taken_sentence(self):
        sentence = get_random_sentence()
        print(sentence)


if __name__ == "__main__":
    unittest.main()