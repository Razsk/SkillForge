import unittest
from unittest.mock import patch
from datetime import datetime
import sys
import os

# Ensure routine_engine can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import routine_engine

class TestCalculateNextRun(unittest.TestCase):

    @patch('routine_engine.datetime')
    def test_calculate_next_run_basic(self, mock_datetime):
        # Setup mock
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        # We need to make sure other methods behave like the real datetime class
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.combine.side_effect = datetime.combine

        # Call the function
        result = routine_engine.calculate_next_run("14:30", 1)

        # Verify
        expected = datetime(2023, 1, 2, 14, 30)
        self.assertEqual(result, expected)

    @patch('routine_engine.datetime')
    def test_calculate_next_run_month_rollover(self, mock_datetime):
        # Setup mock
        mock_now = datetime(2023, 1, 31, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.combine.side_effect = datetime.combine

        # Call the function
        result = routine_engine.calculate_next_run("09:00", 1)

        # Verify
        expected = datetime(2023, 2, 1, 9, 0)
        self.assertEqual(result, expected)

    @patch('routine_engine.datetime')
    def test_calculate_next_run_year_rollover(self, mock_datetime):
        # Setup mock
        mock_now = datetime(2023, 12, 31, 23, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.combine.side_effect = datetime.combine

        # Call the function
        result = routine_engine.calculate_next_run("00:00", 1)

        # Verify
        expected = datetime(2024, 1, 1, 0, 0)
        self.assertEqual(result, expected)

    @patch('routine_engine.datetime')
    def test_calculate_next_run_leap_year(self, mock_datetime):
        # Setup mock: Feb 28th 2024 (Leap year)
        mock_now = datetime(2024, 2, 28, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.combine.side_effect = datetime.combine

        # Call the function: 1 day ahead should be Feb 29th
        result = routine_engine.calculate_next_run("10:00", 1)

        # Verify
        expected = datetime(2024, 2, 29, 10, 0)
        self.assertEqual(result, expected)

    @patch('routine_engine.datetime')
    def test_calculate_next_run_zero_days(self, mock_datetime):
        # Setup mock
        mock_now = datetime(2023, 6, 15, 8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.combine.side_effect = datetime.combine

        # Call the function
        result = routine_engine.calculate_next_run("18:00", 0)

        # Verify
        expected = datetime(2023, 6, 15, 18, 0)
        self.assertEqual(result, expected)

    def test_calculate_next_run_invalid_time_format(self):
        # Verify that invalid time format raises ValueError
        # Note: We don't necessarily need to mock datetime here if we expect strptime to fail first,
        # but since calculate_next_run calls now() first, we might want to mock it to be safe
        # or just let it use real now() since we only care about the exception.
        # However, strptime is a method on the datetime class (or instance?), wait.
        # In routine_engine: datetime.strptime(time_str, "%H:%M")
        # If we don't patch, it uses real datetime.

        with self.assertRaises(ValueError):
            routine_engine.calculate_next_run("25:00", 1)

        with self.assertRaises(ValueError):
            routine_engine.calculate_next_run("invalid", 1)

if __name__ == '__main__':
    unittest.main()
