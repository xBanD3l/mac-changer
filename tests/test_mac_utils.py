import os
import tempfile
import unittest
from unittest.mock import mock_open, patch

import mac_utils


class MacUtilsInterfaceTests(unittest.TestCase):
    def test_get_available_interfaces_uses_sysfs(self):
        with patch("platform.system", return_value="Linux"), patch(
            "os.path.isdir", return_value=True
        ), patch("os.listdir", return_value=["lo", "eth0", "wlan0"]):
            interfaces = mac_utils.get_available_interfaces()

        self.assertEqual(interfaces, ["eth0", "wlan0"])

    def test_get_available_interfaces_parses_ip_output(self):
        fake_result = type(
            "Result",
            (),
            {
                "stdout": "1: lo: <LOOPBACK>\n2: eth0: <BROADCAST,MULTICAST>\n3: wlan0@if2: <BROADCAST,MULTICAST>\n",
                "returncode": 0,
            },
        )()

        with patch("platform.system", return_value="Linux"), patch(
            "os.path.isdir", return_value=False
        ), patch("mac_utils._run", return_value=fake_result):
            interfaces = mac_utils.get_available_interfaces()

        self.assertIn("eth0", interfaces)
        self.assertIn("wlan0", interfaces)
        self.assertNotIn("lo", interfaces)
        self.assertNotIn("wlan0@if2", interfaces)

    def test_get_available_interfaces_parses_windows_powershell(self):
        fake_result = type("Result", (), {"stdout": "Wi-Fi\r\nEthernet\r\n", "returncode": 0})()

        with patch("platform.system", return_value="Windows"), patch(
            "mac_utils._run", return_value=fake_result
        ):
            interfaces = mac_utils.get_available_interfaces()

        self.assertEqual(interfaces, ["Wi-Fi", "Ethernet"])

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


class MacUtilsFormatTests(unittest.TestCase):
    def test_normalize_mac_accepts_common_formats(self):
        self.assertEqual(mac_utils.normalize_mac("aa-bb-cc-dd-ee-ff"), "AA:BB:CC:DD:EE:FF")
        self.assertEqual(mac_utils.normalize_mac("AABBCCDDEEFF"), "AA:BB:CC:DD:EE:FF")
        self.assertEqual(mac_utils.normalize_mac("aa:bb:cc:dd:ee:ff"), "AA:BB:CC:DD:EE:FF")
        self.assertIsNone(mac_utils.normalize_mac("not-a-mac"))
        self.assertIsNone(mac_utils.normalize_mac(""))

    def test_mac_digits(self):
        self.assertEqual(mac_utils.mac_digits("aa:bb:cc:dd:ee:ff"), "AABBCCDDEEFF")
        self.assertIsNone(mac_utils.mac_digits("bad"))

    def test_generate_random_mac_format_and_bits(self):
        mac = mac_utils.generate_random_mac()
        self.assertRegex(mac, r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")
        first = int(mac.split(":")[0], 16)
        self.assertEqual(first & 0x01, 0)
        self.assertEqual(first & 0x02, 0x02)

    def test_save_and_load_mac(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "saved_mac.json")
            self.assertTrue(mac_utils.save_mac("AA:BB:CC:DD:EE:FF", save_file=path))
            self.assertEqual(mac_utils.load_saved_mac(save_file=path), "AA:BB:CC:DD:EE:FF")

    def test_get_current_mac_reads_sysfs(self):
        with patch("platform.system", return_value="Linux"), patch(
            "os.path.isfile", return_value=True
        ), patch("builtins.open", mock_open(read_data="82:2b:38:3d:bc:d0\n")):
            self.assertEqual(mac_utils.get_current_mac("eth0"), "82:2B:38:3D:BC:D0")

    def test_apply_mac_rejects_invalid_address(self):
        self.assertFalse(mac_utils.apply_mac("eth0", "not-a-mac"))


if __name__ == "__main__":
    unittest.main()
