import sys
import os
import json
from unittest.mock import patch, mock_open

# Add scripts directory to sys.path to import routine_engine
scripts_dir = os.path.join(os.path.dirname(__file__), '../scripts')
sys.path.append(scripts_dir)

import routine_engine

def test_save_db():
    test_db = {"task1": {"primary_period": 5, "deadline_period": 1}}

    # Mock open and os.makedirs
    m = mock_open()
    with patch("builtins.open", m), \
         patch("os.makedirs") as mock_makedirs:

        routine_engine.save_db(test_db)

        # Verify os.makedirs was called for the directory of DB_PATH
        expected_dir = os.path.dirname(routine_engine.DB_PATH)
        mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)

        # Verify open was called with DB_PATH and 'w' mode
        m.assert_called_once_with(routine_engine.DB_PATH, 'w')

        # Verify that json.dump was called correctly
        # We can verify this by checking the content written to the file
        handle = m()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written_content) == test_db
