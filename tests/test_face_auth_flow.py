import tempfile
import unittest
from pathlib import Path

from engine import config


class FaceAuthFlowTests(unittest.TestCase):
    def test_admin_password_is_valid(self):
        self.assertTrue(config.ADMIN_PASSWORD)

    def test_registered_users_list_uses_directory_names(self):
        from engine.auth import recoganize

        with tempfile.TemporaryDirectory() as tmpdir:
            samples_dir = Path(tmpdir) / "samples"
            (samples_dir / "Alice").mkdir(parents=True)
            (samples_dir / "Bob").mkdir(parents=True)

            original = recoganize.SAMPLES_DIR
            recoganize.SAMPLES_DIR = str(samples_dir)
            try:
                names = recoganize.get_registered_users()
            finally:
                recoganize.SAMPLES_DIR = original

        self.assertEqual(names, ["", "Alice", "Bob"])


if __name__ == "__main__":
    unittest.main()
