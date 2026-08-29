import os
import subprocess
import unittest


SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "next_version_tag.sh")


class NextVersionTagTests(unittest.TestCase):
    def _next(self, *tags):
        result = subprocess.run(
            ["bash", SCRIPT, *tags],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_increments_three_part_tag(self):
        # This is the case that failed on windows-latest Git Bash:
        # v1.2.4 padded as 1.2.4.0.0 used to put "4.0.0" into patch.
        self.assertEqual(
            self._next("v1.0", "v1.1", "v1.2", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"),
            "v1.2.5",
        )

    def test_increments_two_part_tag(self):
        self.assertEqual(self._next("v1.2"), "v1.2.1")

    def test_increments_one_part_tag(self):
        self.assertEqual(self._next("v1"), "v1.0.1")

    def test_skips_existing_next_tag(self):
        self.assertEqual(self._next("v1.2.4", "v1.2.5"), "v1.2.6")

    def test_defaults_when_no_version_tags(self):
        self.assertEqual(self._next("latest"), "v1.0.0")


if __name__ == "__main__":
    unittest.main()
