import tempfile
import unittest
from pathlib import Path

from core.storage import SQLiteDataStore


class SQLiteDataStoreTest(unittest.TestCase):
    def test_replace_and_read_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDataStore(Path(tmp) / "app.sqlite")
            rows = [{"id": "one", "username": "alice", "symbol": "002982"}]

            store.replace_dataset("alice", "alerts", rows)
            loaded = store.read_dataset("alice", "alerts")

            self.assertEqual(loaded, rows)


if __name__ == "__main__":
    unittest.main()
