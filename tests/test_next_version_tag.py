import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.next_version_tag import next_version_tag


class NextVersionTagTests(unittest.TestCase):
    def test_increments_three_part_tag(self):
        # This is the case that failed on windows-latest Git Bash:
        # v1.2.4 padded as 1.2.4.0.0 used to put "4.0.0" into patch.
        self.assertEqual(
            next_version_tag(["v1.0", "v1.1", "v1.2", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"]),
            "v1.2.5",
        )

    def test_increments_two_part_tag(self):
        self.assertEqual(next_version_tag(["v1.2"]), "v1.2.1")

    def test_increments_one_part_tag(self):
        self.assertEqual(next_version_tag(["v1"]), "v1.0.1")

    def test_skips_existing_next_tag(self):
        self.assertEqual(next_version_tag(["v1.2.4", "v1.2.5"]), "v1.2.6")

    def test_defaults_when_no_version_tags(self):
        self.assertEqual(next_version_tag(["latest"]), "v1.0.0")


if __name__ == "__main__":
    unittest.main()
