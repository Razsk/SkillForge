import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the script directory to the python path to allow importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routine_engine import calculate_next_run

def test_calculate_next_run_basic():
    # Mock datetime.now to a fixed time
    fixed_now = datetime(2023, 10, 27, 12, 0, 0)
    with patch('routine_engine.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.strptime = datetime.strptime
        mock_datetime.combine = datetime.combine

        # Test 1 day ahead
        time_str = "14:00"
        days_ahead = 1
        expected = datetime(2023, 10, 28, 14, 0, 0)
        result = calculate_next_run(time_str, days_ahead)
        assert result == expected

def test_calculate_next_run_same_day():
    # Mock datetime.now to a fixed time
    fixed_now = datetime(2023, 10, 27, 12, 0, 0)
    with patch('routine_engine.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.strptime = datetime.strptime
        mock_datetime.combine = datetime.combine

        # Test 0 days ahead (today)
        time_str = "14:00"
        days_ahead = 0
        expected = datetime(2023, 10, 27, 14, 0, 0)
        result = calculate_next_run(time_str, days_ahead)
        assert result == expected

def test_calculate_next_run_future_days():
    # Mock datetime.now to a fixed time
    fixed_now = datetime(2023, 10, 27, 12, 0, 0)
    with patch('routine_engine.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.strptime = datetime.strptime
        mock_datetime.combine = datetime.combine

        # Test 5 days ahead
        time_str = "09:30"
        days_ahead = 5
        expected = datetime(2023, 11, 1, 9, 30, 0)
        result = calculate_next_run(time_str, days_ahead)
        assert result == expected
