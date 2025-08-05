import random
import os
import json
import platform
import subprocess
import re

# File to store the saved MAC address
SAVE_FILE = "saved_mac.json"


def generate_random_mac():
    """
    Generates a random MAC address in the format XX:XX:XX:XX:XX:XX.
    The first octet is set to avoid multicast and ensure it's a locally administered address.
    """
    first_octet = random.randint(0x00, 0xFF)
    first_octet = (first_octet | 0x02) & 0xFE  # Locally administered, unicast

    mac = [first_octet] + [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{octet:02X}" for octet in mac)


def save_mac(mac_address):
    """
    Saves the given MAC address to a JSON file.
    """
    try:
        with open(SAVE_FILE, "w") as file:
            json.dump({"mac": mac_address}, file)
    except Exception as e:
        print(f"Error saving MAC: {e}")


def load_saved_mac():
    """
    Loads and returns the saved MAC address from the JSON file.
    Returns None if no saved MAC is found or if an error occurs.
    """
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r") as file:
            data = json.load(file)
            return data.get("mac")
    except Exception as e:
        print(f"Error loading saved MAC: {e}")
        return None


import subprocess

def get_adapter_description(interface_name):
    try:
        result = subprocess.run(
            ["wmic", "nic", "where", f"NetConnectionID='{interface_name}'", "get", "Name"],
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        print(f"WMIC output for '{interface_name}':\n{output}")  # Debug print

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        # The first line is the header, second line is the description
        if len(lines) >= 2:
            description = lines[1]
            return description
        else:
            print("WMIC output does not have expected lines.")
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
    """
    Changes the MAC address of the given network interface.
    Requires administrative/root privileges.
    """
    system = platform.system()

    try:
        if system == "Windows":
            description = get_adapter_description(interface)
            if not description:
                print(f"Could not find adapter description for interface '{interface}'")
                return

            reg_key_path = find_registry_key_by_description(description)
            if not reg_key_path:
                print(f"Could not find registry key for adapter '{description}'")
                return

            # Disable interface
            subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=disable"], check=True)

            # Set the new MAC address in registry
            subprocess.run([
                "reg", "add",
                f"HKEY_LOCAL_MACHINE\\{reg_key_path}",
                "/v", "NetworkAddress", "/d", new_mac.replace(":", ""), "/f"
            ], check=True)

            # Enable interface
            subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=enable"], check=True)

        elif system in ["Linux", "Darwin"]:  # macOS is Darwin
            subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)

        print(f"MAC address changed to {new_mac} on {interface}")

    except subprocess.CalledProcessError as e:
        print(f"Error changing MAC: {e}")


def get_current_mac(interface):
    """
    Returns the current MAC address of the specified network interface.
    """
    system = platform.system()

    try:
        if system == "Windows":
            # Use 'getmac' and parse output for the specific interface if possible
            result = subprocess.run(["getmac", "/v", "/fo", "list"], capture_output=True, text=True)
            output = result.stdout
            # Extract MACs and their interface names
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
