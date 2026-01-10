"""
Standalone Tests for Architectural Guardrails.
"""
import unittest
from pathlib import Path

from guardrails import check_file


class TestGuardrails(unittest.TestCase):

    def test_cross_service_import_detection(self):
        # Create a temporary violating file content

        # We need to mock how check_file reads content or refactor check_file to accept content.
        # For simplicity, let's just write to a temp file or refactor guardrails.py slightly?
        # Actually, let's refactor guardrails.py to be more testable first (Separation of IO)
        pass

    def test_check_file_logic(self):
         # Since check_file reads from disk, I will create a temp file
         import tempfile

         with tempfile.TemporaryDirectory() as tmpdirname:
             # Create a fake structure
             ms_dir = Path(tmpdirname) / "microservices" / "order_service"
             ms_dir.mkdir(parents=True)

             violating_file = ms_dir / "bad.py"
             with open(violating_file, "w") as f:
                 f.write("from microservices.user_service import models\n")

             # Check it
             errors = check_file(violating_file)
             self.assertTrue(any("Cross-service import forbidden" in e for e in errors))

    def test_adhoc_db_engine(self):
         import tempfile
         with tempfile.TemporaryDirectory() as tmpdirname:
             p = Path(tmpdirname) / "some_service.py"
             with open(p, "w") as f:
                 f.write("engine = create_async_engine('sqlite://')\n")

             errors = check_file(p)
             self.assertTrue(any("Direct use of 'create_async_engine' is forbidden" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
