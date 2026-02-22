import unittest
import sys
import os
import json
import subprocess
from unittest.mock import patch, mock_open, MagicMock, call
from datetime import datetime, timedelta

# Ensure the module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from skills.routine_followup.scripts import routine_engine

class TestRoutineEngine(unittest.TestCase):
    def setUp(self):
        self.mock_db = {
            "test_routine": {
                "primary_period": 2,
                "deadline_period": 1,
                "time_of_day": "08:00"
            }
        }

    @patch('skills.routine_followup.scripts.routine_engine.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_load_db_exists(self, mock_file, mock_exists):
        mock_exists.return_value = True
        db = routine_engine.load_db()
        self.assertEqual(db, {"test": "data"})
        mock_file.assert_called_once_with(routine_engine.DB_PATH, 'r')

    @patch('skills.routine_followup.scripts.routine_engine.os.path.exists')
    def test_load_db_not_exists(self, mock_exists):
        mock_exists.return_value = False
        db = routine_engine.load_db()
        self.assertEqual(db, {})

    @patch('skills.routine_followup.scripts.routine_engine.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_db(self, mock_file, mock_makedirs):
        db = {"new": "data"}
        routine_engine.save_db(db)
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once_with(routine_engine.DB_PATH, 'w')
        handle = mock_file()
        self.assertTrue(handle.write.called)

    @patch('skills.routine_followup.scripts.routine_engine.datetime')
    @patch('skills.routine_followup.scripts.routine_engine.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_completion(self, mock_file, mock_makedirs, mock_datetime):
        mock_now = datetime(2023, 10, 27, 10, 0, 0)
        mock_datetime.now.return_value = mock_now

        routine_engine.log_completion("test_routine")

        mock_makedirs.assert_called_once()
        mock_file.assert_called_once_with(routine_engine.LOG_PATH, 'a')
        handle = mock_file()
        expected_log = "[2023-10-27 10:00:00] Rutine fuldført: test_routine\n"
        handle.write.assert_called_once_with(expected_log)

    @patch('skills.routine_followup.scripts.routine_engine.datetime')
    def test_calculate_next_run(self, mock_datetime):
        mock_now = datetime(2023, 10, 27, 10, 0, 0) # Friday
        mock_datetime.now.return_value = mock_now
        # Needed because calculate_next_run uses datetime.strptime which is on the class
        mock_datetime.strptime = datetime.strptime
        mock_datetime.combine = datetime.combine

        # Test adding 2 days
        next_dt = routine_engine.calculate_next_run("09:00", 2)
        expected_dt = datetime(2023, 10, 29, 9, 0, 0)
        self.assertEqual(next_dt, expected_dt)

    @patch('skills.routine_followup.scripts.routine_engine.subprocess')
    def test_update_crontab(self, mock_subprocess):
        # Mock check_output to return existing crontab
        mock_subprocess.check_output.return_value = b"# OPENCLAW_ROUTINE:other\n* * * * * other_cmd\n"
        mock_subprocess.Popen.return_value.communicate.return_value = (None, None)

        run_dt = datetime(2023, 10, 28, 9, 0, 0)
        routine_engine.update_crontab("test_routine", run_dt)

        # Verify call to crontab -l
        mock_subprocess.check_output.assert_called_with(['crontab', '-l'], stderr=mock_subprocess.DEVNULL)

        # Verify call to write new crontab
        mock_subprocess.Popen.assert_called_with(['crontab', '-'], stdin=mock_subprocess.PIPE)

        # Check the content written to stdin
        args, _ = mock_subprocess.Popen.return_value.communicate.call_args
        new_cron_bytes = args[0]
        new_cron = new_cron_bytes.decode('utf-8')

        expected_marker = "# OPENCLAW_ROUTINE:test_routine"
        expected_time = "0 9 28 10 *"

        self.assertIn(expected_marker, new_cron)
        self.assertIn(expected_time, new_cron)
        self.assertIn("--action trigger --name 'test_routine'", new_cron)

    @patch('skills.routine_followup.scripts.routine_engine.update_crontab')
    @patch('skills.routine_followup.scripts.routine_engine.save_db')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    @patch('skills.routine_followup.scripts.routine_engine.calculate_next_run')
    def test_add_routine(self, mock_calc, mock_load, mock_save, mock_update):
        mock_load.return_value = {}
        mock_next_dt = datetime(2023, 10, 29, 9, 0, 0)
        mock_calc.return_value = mock_next_dt

        msg = routine_engine.add_routine("new_routine", 2, 1, "09:00")

        self.assertIn("Rutine 'new_routine' oprettet", msg)
        mock_save.assert_called_once()
        saved_db = mock_save.call_args[0][0]
        self.assertEqual(saved_db["new_routine"]["primary_period"], 2)
        mock_update.assert_called_once_with("new_routine", mock_next_dt)

    @patch('skills.routine_followup.scripts.routine_engine.update_crontab')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    @patch('skills.routine_followup.scripts.routine_engine.calculate_next_run')
    def test_trigger_routine(self, mock_calc, mock_load, mock_update):
        mock_load.return_value = self.mock_db
        mock_next_dt = datetime(2023, 10, 28, 8, 0, 0)
        mock_calc.return_value = mock_next_dt

        with patch('builtins.print') as mock_print:
            routine_engine.trigger_routine("test_routine")

            # Should calculate next run based on deadline period (1 day)
            # data['deadline_period'] is 1
            mock_calc.assert_called_with("08:00", 1)
            mock_update.assert_called_with("test_routine", mock_next_dt)
            mock_print.assert_called()
            self.assertIn("SYSTEM PROMPT", mock_print.call_args[0][0])

    @patch('skills.routine_followup.scripts.routine_engine.log_completion')
    @patch('skills.routine_followup.scripts.routine_engine.update_crontab')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    @patch('skills.routine_followup.scripts.routine_engine.calculate_next_run')
    def test_complete_routine(self, mock_calc, mock_load, mock_update, mock_log):
        mock_load.return_value = self.mock_db
        mock_next_dt = datetime(2023, 10, 30, 8, 0, 0)
        mock_calc.return_value = mock_next_dt

        msg = routine_engine.complete_routine("test_routine")

        # Should calculate next run based on primary period (2 days)
        mock_calc.assert_called_with("08:00", 2)
        mock_update.assert_called_with("test_routine", mock_next_dt)
        mock_log.assert_called_with("test_routine")
        self.assertIn("Succes", msg)

    @patch('skills.routine_followup.scripts.routine_engine.subprocess')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    def test_check_routines(self, mock_load, mock_subprocess):
        mock_load.return_value = self.mock_db
        # Mock crontab -l output
        mock_subprocess.check_output.return_value = b"0 8 * * * cmd # OPENCLAW_ROUTINE:test_routine\n"

        report = routine_engine.check_routines()

        self.assertIn("Status rapport", report)
        self.assertIn("[OK]   test_routine", report)

    @patch('skills.routine_followup.scripts.routine_engine.subprocess')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    def test_check_routines_missing(self, mock_load, mock_subprocess):
        mock_load.return_value = self.mock_db
        # Mock crontab -l output empty
        mock_subprocess.check_output.return_value = b""

        report = routine_engine.check_routines()

        self.assertIn("[FEJL] test_routine", report)

    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    def test_check_routines_no_db(self, mock_load):
        mock_load.return_value = {}
        report = routine_engine.check_routines()
        self.assertEqual(report, "Ingen rutiner fundet i databasen.")

    @patch('skills.routine_followup.scripts.routine_engine.subprocess')
    @patch('skills.routine_followup.scripts.routine_engine.load_db')
    def test_check_routines_crontab_missing(self, mock_load, mock_subprocess):
        mock_load.return_value = self.mock_db
        # We need to ensure the mocked module has the real exception class
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError

        mock_subprocess.check_output.side_effect = FileNotFoundError

        report = routine_engine.check_routines()
        self.assertIn("Fejl: 'crontab' kommandoen findes ikke", report)

if __name__ == '__main__':
    unittest.main()
