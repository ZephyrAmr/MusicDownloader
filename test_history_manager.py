import sys
from unittest.mock import MagicMock

# Mock dependencies before importing downloader
for mod in ['yt_dlp', 'requests', 'bs4', 'spotipy', 'spotipy.oauth2', 'SpotAPI', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.simpledialog']:
    sys.modules[mod] = MagicMock()

import unittest
from unittest.mock import patch, mock_open
import json
import os

# Import the class and constant to test
from downloader import HistoryManager, HISTORY_FILE

class TestHistoryManager(unittest.TestCase):
    @patch('os.path.exists')
    @patch('downloader.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_entry(self, mock_file, mock_json_dump, mock_exists):
        # Setup: history file does not exist
        mock_exists.return_value = False

        hm = HistoryManager()

        test_entry = {
            "date": "2023-10-27 12:00:00",
            "title": "Test Song",
            "url": "https://youtube.com/test",
            "format": "mp3",
            "path": "/downloads"
        }

        # Action
        hm.add_entry(test_entry)

        # Assertions
        # 1. Check if entry was added to the history list
        self.assertEqual(len(hm.history), 1)
        self.assertEqual(hm.history[0], test_entry)

        # 2. Check if it was added at the beginning
        second_entry = {"title": "Second Song"}
        hm.add_entry(second_entry)
        self.assertEqual(hm.history[0], second_entry)
        self.assertEqual(hm.history[1], test_entry)

        # 3. Verify save_history was called (via json.dump)
        # json.dump should have been called twice (once for each add_entry)
        self.assertEqual(mock_json_dump.call_count, 2)

        # The last call to json.dump should have the full history
        expected_history = [second_entry, test_entry]
        mock_json_dump.assert_called_with(expected_history, mock_file(), indent=4)

if __name__ == '__main__':
    unittest.main()
