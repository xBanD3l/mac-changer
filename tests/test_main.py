import unittest
from unittest.mock import patch

import main


class MainStartupTests(unittest.TestCase):
    def test_should_wait_for_input_without_stdin(self):
        with patch("main.sys.stdin", None):
            self.assertFalse(main.should_wait_for_input())


if __name__ == "__main__":
    unittest.main()
