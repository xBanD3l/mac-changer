import unittest
from unittest.mock import MagicMock, patch

import main
import mac_utils


class MainStartupTests(unittest.TestCase):
    def test_should_wait_for_input_without_stdin(self):
        with patch("main.sys.stdin", None):
            self.assertFalse(main.should_wait_for_input())

    def test_should_wait_for_input_when_not_a_tty(self):
        stdin = MagicMock()
        stdin.isatty.return_value = False
        with patch("main.sys.stdin", stdin):
            self.assertFalse(main.should_wait_for_input())

    def test_should_wait_for_input_when_tty(self):
        stdin = MagicMock()
        stdin.isatty.return_value = True
        with patch("main.sys.stdin", stdin):
            self.assertTrue(main.should_wait_for_input())


class MainAppLogicTests(unittest.TestCase):
    def test_check_current_mac_does_not_overwrite_original(self):
        if main.tk is None:
            self.skipTest("tkinter is not available")

        with patch.object(mac_utils, "get_available_interfaces", return_value=["eth0"]), patch.object(
            mac_utils, "resolve_interface_name", return_value="eth0"
        ), patch.object(mac_utils, "get_current_mac", return_value="AA:BB:CC:DD:EE:FF"):
            root = main.tk.Tk()
            root.withdraw()
            try:
                app = main.MacChangerApp(root)
                self.assertEqual(app.original_macs["eth0"], "AA:BB:CC:DD:EE:FF")

                with patch.object(mac_utils, "get_current_mac", return_value="11:22:33:44:55:66"):
                    app.check_current_mac()

                self.assertEqual(app.current_mac, "11:22:33:44:55:66")
                self.assertEqual(app.original_macs["eth0"], "AA:BB:CC:DD:EE:FF")
            finally:
                root.destroy()

    def test_custom_mac_normalizes_input(self):
        if main.tk is None:
            self.skipTest("tkinter is not available")

        with patch.object(mac_utils, "get_available_interfaces", return_value=["eth0"]), patch.object(
            mac_utils, "resolve_interface_name", return_value="eth0"
        ), patch.object(mac_utils, "get_current_mac", return_value="AA:BB:CC:DD:EE:FF"):
            root = main.tk.Tk()
            root.withdraw()
            try:
                app = main.MacChangerApp(root)
                app.custom_mac_entry.insert(0, "aa-bb-cc-dd-ee-00")
                app.add_custom_mac()
                self.assertEqual(app.current_mac, "AA:BB:CC:DD:EE:00")
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
