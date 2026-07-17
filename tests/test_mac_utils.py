import unittest
from unittest.mock import patch

import mac_utils


class MacUtilsInterfaceTests(unittest.TestCase):
    def test_get_available_interfaces_parses_ip_output(self):
        fake_result = type("Result", (), {"stdout": "1: lo: <LOOPBACK>\n2: eth0: <BROADCAST,MULTICAST>\n3: wlan0: <BROADCAST,MULTICAST>\n", "returncode": 0})()

        with patch("subprocess.run", return_value=fake_result):
            interfaces = mac_utils.get_available_interfaces()

        self.assertIn("eth0", interfaces)
        self.assertIn("wlan0", interfaces)
        self.assertNotIn("lo", interfaces)

    def test_resolve_interface_name_prefers_requested_interface(self):
        with patch.object(mac_utils, "get_available_interfaces", return_value=["eth0", "wlan0"]):
            self.assertEqual(mac_utils.resolve_interface_name("wlan0"), "wlan0")
            self.assertEqual(mac_utils.resolve_interface_name(None, fallback="Wi-Fi"), "eth0")

    def test_restore_original_mac_only_when_enabled(self):
        with patch.object(mac_utils, "apply_mac", return_value=True) as apply_mock:
            self.assertTrue(mac_utils.restore_original_mac_if_enabled("eth0", "AA:BB:CC:DD:EE:FF", False))
            apply_mock.assert_not_called()

            self.assertTrue(mac_utils.restore_original_mac_if_enabled("eth0", "AA:BB:CC:DD:EE:FF", True))
            apply_mock.assert_called_once_with("eth0", "AA:BB:CC:DD:EE:FF")


if __name__ == "__main__":
    unittest.main()
