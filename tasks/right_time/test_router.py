import unittest
from datetime import datetime, timedelta
import pytz
import re
from router import generate_time_for_level

class TestGenerateTimeForLevel(unittest.TestCase):
    """Test cases for the generate_time_for_level function."""

    def test_level_1(self):
        """Test level 1: Time is always 1 minute in the future with ISO 8601 format."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 1
        future_time, time_str = generate_time_for_level(1)
        
        # Check that future_time is about 1 minute in the future
        time_diff = (future_time - now).total_seconds()
        self.assertGreaterEqual(time_diff, 55)  # Allow for slight execution time differences
        self.assertLessEqual(time_diff, 65)
        
        # Check the format of time_str (ISO 8601)
        self.assertTrue(re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', time_str))
        
        # Parse the time_str and check it matches future_time
        parsed_time = datetime.fromisoformat(time_str)
        self.assertAlmostEqual(parsed_time.timestamp(), future_time.timestamp(), delta=1)

    def test_level_2(self):
        """Test level 2: Time is in the range of 1-20 minutes in the future with ISO 8601 format."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 2
        future_time, time_str = generate_time_for_level(2)
        
        # Check that future_time is between 1 and 20 minutes in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 20)
        
        # Check the format of time_str (ISO 8601)
        self.assertTrue(re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', time_str))
        
        # Parse the time_str and check it matches future_time
        parsed_time = datetime.fromisoformat(time_str)
        self.assertAlmostEqual(parsed_time.timestamp(), future_time.timestamp(), delta=1)

    def test_level_3(self):
        """Test level 3: Time with specified timezone."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 3
        future_time, time_str = generate_time_for_level(3)
        
        # Check that future_time is between 1 and 20 minutes in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 20)
        
        # Check the format of time_str (includes timezone name)
        self.assertTrue(any(tz in time_str for tz in ["CEST", "CET", "MSK", "UTC"]))
        
        # Check that the time string contains a valid date and time
        self.assertTrue(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', time_str))

    def test_level_4(self):
        """Test level 4: Time with strange timezones."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 4
        future_time, time_str = generate_time_for_level(4)
        
        # Check that future_time is between 1 minute and 2 hours in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 120)
        
        # Check that the time string contains a valid date and time
        self.assertTrue(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', time_str))
        
        # Check that the time string contains one of the strange timezones
        strange_timezones = ["NST", "IRST", "AFT", "IST", "NPT", "MMT", "ACWST", "ACST", "LHST", "CHAST"]
        self.assertTrue(any(tz in time_str for tz in strange_timezones))

    def test_level_5(self):
        """Test level 5: Different time formats."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 5
        future_time, time_str = generate_time_for_level(5)
        
        # Check that future_time is between 1 minute and 2 hours in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 120)
        
        # Check that the time string is in one of the expected formats
        is_iso = re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', time_str) is not None
        is_rfc = re.match(r'[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{2}:\d{2}', time_str) is not None
        is_unix = re.match(r'^\d{10}$', time_str) is not None
        is_duration = re.match(r'Now\+PT\d+M', time_str) is not None
        
        self.assertTrue(is_iso or is_rfc or is_unix or is_duration)

    def test_level_6(self):
        """Test level 6: Summation of time and duration."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 6
        future_time, time_str = generate_time_for_level(6)
        
        # Check that future_time is between 1 and 60 minutes in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 60)
        
        # Check that the time string contains a + for summation
        self.assertIn("+", time_str)
        
        # Check that the time string contains PT for duration
        self.assertIn("PT", time_str)

    def test_level_7(self):
        """Test level 7: Expression with summation and subtraction."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 7
        future_time, time_str = generate_time_for_level(7)
        
        # Check that future_time is between 1 and 60 minutes in the future
        time_diff_minutes = (future_time - now).total_seconds() / 60
        self.assertGreaterEqual(time_diff_minutes, 1)
        self.assertLessEqual(time_diff_minutes, 60)
        
        # Check that the time string contains both + and - for summation and subtraction
        self.assertIn("+", time_str)
        self.assertIn("-", time_str)
        
        # Check that the time string contains PT for duration
        self.assertIn("PT", time_str)

    def test_level_8(self):
        """Test level 8: Natural language."""
        # Get the current time for comparison
        now = datetime.now(pytz.UTC)
        
        # Generate time for level 8
        future_time, time_str = generate_time_for_level(8)
        
        # Check that future_time is in the future
        self.assertGreater(future_time, now)
        
        # Check that the time string is in natural language
        natural_language_patterns = [
            "minutes from now",
            "hours and", "minutes from now",
            "Half past",
            "Quarter past",
            "Quarter to",
            "o'clock"
        ]
        self.assertTrue(any(pattern in time_str for pattern in natural_language_patterns))

if __name__ == "__main__":
    unittest.main()