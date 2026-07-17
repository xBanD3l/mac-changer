import json
import os
import platform
import random
import re
import subprocess

# Saved MACs are kept in this file.
SAVE_FILE = os.path.join(os.path.dirname(__file__), "saved_mac.json")


def generate_random_mac():
    """Create a random MAC address in the usual XX:XX:XX:XX:XX:XX format."""
    first_octet = random.randint(0x00, 0xFF)
    first_octet = (first_octet | 0x02) & 0xFE  # Locally administered, unicast

    mac = [first_octet] + [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{octet:02X}" for octet in mac)


def save_mac(mac_address, save_file=SAVE_FILE):
    """Save a MAC address to disk."""
    try:
        with open(save_file, "w") as file:
            json.dump({"mac": mac_address}, file)
        return True
    except Exception as e:
        print(f"Error saving MAC: {e}")
        return False


def load_saved_mac(save_file=SAVE_FILE):
    """Load a saved MAC address from disk if one exists."""
    if not os.path.exists(save_file):
        return None
    try:
        with open(save_file, "r") as file:
            data = json.load(file)
            return data.get("mac")
    except Exception as e:
        print(f"Error loading saved MAC: {e}")
        return None


def get_available_interfaces():
    """Return available network interface names for the current OS."""
    system = platform.system()

    try:
        if system == "Windows":
            result = subprocess.run(
                ["wmic", "nic", "where", "NetEnabled=True", "get", "NetConnectionID"],
                capture_output=True,
                text=True,
            )
            interfaces = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip() and not line.lower().startswith("netconnectionid")
            ]
            return [iface for iface in interfaces if iface]

        for command in (["ip", "-o", "link", "show"], ["ip", "link", "show"], ["ifconfig"]):
            try:
                result = subprocess.run(command, capture_output=True, text=True)
            except FileNotFoundError:
                continue

            if result.returncode != 0:
                continue

            if command[0] == "ifconfig":
                interfaces = []
                for line in result.stdout.splitlines():
                    if line.startswith(" ") or not line.strip():
                        continue
                    parts = line.split()
                    if parts and parts[0].endswith(":"):
                        name = parts[0][:-1]
                        if name != "lo":
                            interfaces.append(name)
                return interfaces

            interfaces = []
            for line in result.stdout.splitlines():
                match = re.match(r"^\d+:\s+([^:]+):", line)
                if match:
                    name = match.group(1)
                    if name != "lo":
                        interfaces.append(name)
            return interfaces

    except Exception as e:
        print(f"Error fetching interfaces: {e}")

    return []


def resolve_interface_name(interface_name=None, fallback=None):
    """Pick the best interface name from the available options."""
    available = get_available_interfaces()

    if interface_name and interface_name in available:
        return interface_name

    if fallback and fallback in available:
        return fallback

    if available:
        return available[0]

    return interface_name or fallback or "Wi-Fi"


def get_adapter_description(interface_name):
    try:
        result = subprocess.run(
            ["wmic", "nic", "where", f"NetConnectionID='{interface_name}'", "get", "Name"],
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if len(lines) >= 2:
            return lines[1]
        return None
    except Exception as e:
        print(f"Error getting adapter description: {e}")
        return None


def find_registry_key_by_description(description):
    """
    Searches registry keys under the network adapter class GUID to find the key
    that matches the given adapter description.
    Returns the full registry path of the matching key or None.
    """
    import winreg

    base_key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
    try:
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        class_key = winreg.OpenKey(reg, base_key_path)
        for i in range(0, 1000):
            try:
                subkey_name = winreg.EnumKey(class_key, i)
                subkey = winreg.OpenKey(class_key, subkey_name)
                try:
                    name, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                    if name == description:
                        winreg.CloseKey(subkey)
                        winreg.CloseKey(class_key)
                        reg.Close()
                        return f"{base_key_path}\\{subkey_name}"
                except FileNotFoundError:
                    pass
                winreg.CloseKey(subkey)
            except OSError:
                break
        winreg.CloseKey(class_key)
        reg.Close()
    except Exception as e:
        print(f"Error accessing registry: {e}")
    return None


def apply_mac(interface, new_mac):
    """Change the MAC address on the selected interface."""
    system = platform.system()

    try:
        if system == "Windows":
            description = get_adapter_description(interface)
            if not description:
                print(f"Could not find adapter description for interface '{interface}'")
                return False

            reg_key_path = find_registry_key_by_description(description)
            if not reg_key_path:
                print(f"Could not find registry key for adapter '{description}'")
                return False

            subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=disable"], check=True)
            subprocess.run(
                [
                    "reg",
                    "add",
                    f"HKEY_LOCAL_MACHINE\\{reg_key_path}",
                    "/v",
                    "NetworkAddress",
                    "/d",
                    new_mac.replace(":", ""),
                    "/f",
                ],
                check=True,
            )
            subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=enable"], check=True)

        elif system in ["Linux", "Darwin"]:  # macOS is Darwin
            subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)

        print(f"MAC address changed to {new_mac} on {interface}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error changing MAC: {e}")
        return False


def get_current_mac(interface):
    """Return the current MAC address for the given interface."""
    system = platform.system()

    try:
        if system == "Windows":
            result = subprocess.run(["getmac", "/v", "/fo", "list"], capture_output=True, text=True)
            output = result.stdout
            interfaces = output.split("\n\n")
            for iface in interfaces:
                if interface.lower() in iface.lower():
                    mac_match = re.search(r"([0-9A-F]{2}[:-]){5}([0-9A-F]{2})", iface, re.I)
                    if mac_match:
                        return mac_match.group(0).replace("-", ":").upper()
            return None

        elif system in ["Linux", "Darwin"]:
            result = subprocess.run(["ifconfig", interface], capture_output=True, text=True)
            mac_match = re.search(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", result.stdout, re.I)
            return mac_match.group(0).upper() if mac_match else None

    except Exception as e:
        print(f"Error fetching current MAC: {e}")
        return None


def restore_original_mac_if_enabled(interface, original_mac, enable_restore):
    """Restore the original MAC address if that option is enabled."""
    if not enable_restore or not original_mac:
        return True
    return apply_mac(interface, original_mac)
