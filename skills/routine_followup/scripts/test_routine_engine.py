import unittest
import sys
import os
import json
from unittest.mock import patch, mock_open

# Ensure routine_engine can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import routine_engine

class TestRoutineEngine(unittest.TestCase):

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test_routine": {"primary_period": 7}}')
    def test_load_db_exists(self, mock_file, mock_exists):
        mock_exists.return_value = True

        result = routine_engine.load_db()

        mock_exists.assert_called_with(routine_engine.DB_PATH)
        mock_file.assert_called_with(routine_engine.DB_PATH, 'r')
        self.assertEqual(result, {"test_routine": {"primary_period": 7}})

    @patch('os.path.exists')
    def test_load_db_not_exists(self, mock_exists):
        mock_exists.return_value = False

        result = routine_engine.load_db()

        mock_exists.assert_called_with(routine_engine.DB_PATH)
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
