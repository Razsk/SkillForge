
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import shlex
from datetime import datetime

# Add script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

import routine_engine

class TestRoutineEngine(unittest.TestCase):

    def test_add_routine_validation(self):
        # Valid name
        with patch('routine_engine.save_db'), patch('routine_engine.update_crontab'):
            result = routine_engine.add_routine("Valid Name", 1, 1, "07:00")
            self.assertIn("oprettet", result)

        # Invalid name with newline
        result = routine_engine.add_routine("Invalid\nName", 1, 1, "07:00")
        self.assertIn("Fejl", result)
        self.assertIn("linjeskift", result)

        # Invalid name with percent
        result = routine_engine.add_routine("100% Name", 1, 1, "07:00")
        self.assertIn("Fejl", result)
        self.assertIn("procent", result)

    @patch('subprocess.check_output')
    @patch('subprocess.Popen')
    def test_update_crontab_quoting(self, mock_popen, mock_check_output):
        mock_check_output.return_value = b""
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        name = "Routine with 'quotes' and ; semicolon"
        run_dt = datetime(2023, 1, 1, 12, 30)

        routine_engine.update_crontab(name, run_dt)

        # Verify the command sent to crontab
        args, _ = mock_proc.communicate.call_args
        new_cron = args[0].decode('utf-8')

        expected_name_quoted = shlex.quote(name)
        self.assertIn(f"--name {expected_name_quoted}", new_cron)
        self.assertTrue(new_cron.endswith(f"# OPENCLAW_ROUTINE:{name}\n"))

    @patch('subprocess.check_output')
    @patch('subprocess.Popen')
    def test_update_crontab_marker_isolation(self, mock_popen, mock_check_output):
        # Existing crontab with a routine that has a name which is a prefix of our new routine
        marker_existing = "# OPENCLAW_ROUTINE:wash"
        current_cron = f"0 7 * * * some_cmd {marker_existing}\n"
        mock_check_output.return_value = current_cron.encode('utf-8')

        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        # New routine 'wash_car'
        name = "wash_car"
        run_dt = datetime(2023, 1, 1, 7, 0)

        routine_engine.update_crontab(name, run_dt)

        args, _ = mock_proc.communicate.call_args
        new_cron = args[0].decode('utf-8')

        # Both should be present
        self.assertIn(marker_existing, new_cron)
        self.assertIn("# OPENCLAW_ROUTINE:wash_car", new_cron)

    @patch('subprocess.check_output')
    def test_check_routines_marker_isolation(self, mock_check_output):
        # DB has 'wash'
        with patch('routine_engine.load_db') as mock_load_db:
            mock_load_db.return_value = {
                "wash": {"primary_period": 1, "deadline_period": 1, "time_of_day": "07:00"}
            }

            # Crontab only has 'wash_car'
            marker_other = "# OPENCLAW_ROUTINE:wash_car"
            current_cron = f"0 7 * * * some_cmd {marker_other}\n"
            mock_check_output.return_value = current_cron.encode('utf-8')

            report = routine_engine.check_routines()

            # 'wash' should be reported as missing (FEJL) because its marker is NOT exactly at the end of 'wash_car' line
            self.assertIn("[FEJL] wash", report)

if __name__ == "__main__":
    unittest.main()
