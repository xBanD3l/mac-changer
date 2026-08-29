import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys

# Saved MACs live next to the app, or in a user data folder when that path is not writable.
def _app_dir():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        if os.access(exe_dir, os.W_OK):
            return exe_dir
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(appdata, "mac-changer")
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.dirname(os.path.abspath(__file__))


SAVE_FILE = os.path.join(_app_dir(), "saved_mac.json")
_MAC_RE = re.compile(r"([0-9A-F]{2}[:-]){5}[0-9A-F]{2}", re.I)


def normalize_mac(mac_str):
    """Return a MAC as XX:XX:XX:XX:XX:XX, or None if the input is invalid."""
    if not mac_str:
        return None
    mac = re.sub(r"[^0-9A-Fa-f]", "", str(mac_str))
    if len(mac) != 12:
        return None
    mac = mac.upper()
    return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


def mac_digits(mac_str):
    """Return the 12 hex digits of a MAC, or None if invalid."""
    normalized = normalize_mac(mac_str)
    return None if normalized is None else normalized.replace(":", "")


def generate_random_mac():
    """Create a random locally administered, unicast MAC address."""
    first_octet = random.randint(0x00, 0xFF)
    first_octet = (first_octet | 0x02) & 0xFE

    mac = [first_octet] + [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{octet:02X}" for octet in mac)


def save_mac(mac_address, save_file=SAVE_FILE):
    """Save a MAC address to disk."""
    try:
        parent = os.path.dirname(save_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
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
            return normalize_mac(data.get("mac")) or data.get("mac")
    except Exception as e:
        print(f"Error loading saved MAC: {e}")
        return None


def _run(command, **kwargs):
    run_kwargs = {"capture_output": True, "text": True}
    if os.name == "nt":
        run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    run_kwargs.update(kwargs)
    try:
        return subprocess.run(command, **run_kwargs)
    except FileNotFoundError:
        return None


def _clean_interface_name(name):
    name = name.strip()
    if "@" in name:
        name = name.split("@", 1)[0]
    return name


def _unix_interfaces_from_sysfs():
    net_dir = "/sys/class/net"
    if not os.path.isdir(net_dir):
        return []
    return [name for name in os.listdir(net_dir) if name and name != "lo"]


def _unix_interfaces_from_commands():
    for command in (["ip", "-o", "link", "show"], ["ip", "link", "show"], ["ifconfig"]):
        result = _run(command)
        if result is None or result.returncode != 0:
            continue

        if command[0] == "ifconfig":
            interfaces = []
            for line in result.stdout.splitlines():
                if line.startswith(" ") or not line.strip():
                    continue
                parts = line.split()
                if parts and parts[0].endswith(":"):
                    name = _clean_interface_name(parts[0][:-1])
                    if name and name != "lo":
                        interfaces.append(name)
            return interfaces

        interfaces = []
        for line in result.stdout.splitlines():
            match = re.match(r"^\d+:\s+([^:]+):", line)
            if match:
                name = _clean_interface_name(match.group(1))
                if name and name != "lo":
                    interfaces.append(name)
        if interfaces:
            return interfaces
    return []


def _windows_interfaces():
    result = _run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetAdapter | Select-Object -ExpandProperty Name",
        ]
    )
    if result and result.returncode == 0 and result.stdout.strip():
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    result = _run(["wmic", "nic", "where", "NetEnabled=True", "get", "NetConnectionID"])
    if result and result.stdout:
        interfaces = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip() and not line.lower().startswith("netconnectionid")
        ]
        return [iface for iface in interfaces if iface]
    return []


def get_available_interfaces():
    """Return available network interface names for the current OS."""
    system = platform.system()

    try:
        if system == "Windows":
            return _windows_interfaces()

        interfaces = _unix_interfaces_from_sysfs()
        if interfaces:
            return interfaces
        return _unix_interfaces_from_commands()

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
    result = _run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"Get-NetAdapter -Name '{interface_name}' | Select-Object -ExpandProperty InterfaceDescription",
        ]
    )
    if result and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().splitlines()[0].strip()

    result = _run(
        ["wmic", "nic", "where", f"NetConnectionID='{interface_name}'", "get", "Name"]
    )
    if not result:
        return None
    try:
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
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


def _sudo_prefix():
    if os.name == "nt":
        return []
    try:
        if os.geteuid() == 0:
            return []
    except AttributeError:
        pass
    return ["sudo"] if shutil.which("sudo") else []


def apply_mac(interface, new_mac):
    """Change the MAC address on the selected interface."""
    system = platform.system()
    normalized = normalize_mac(new_mac)
    if not normalized:
        print(f"Invalid MAC address: {new_mac}")
        return False

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

            digits = mac_digits(normalized)
            subprocess.run(
                ["netsh", "interface", "set", "interface", interface, "admin=disable"],
                check=True,
            )
            subprocess.run(
                [
                    "reg",
                    "add",
                    f"HKEY_LOCAL_MACHINE\\{reg_key_path}",
                    "/v",
                    "NetworkAddress",
                    "/d",
                    digits,
                    "/f",
                ],
                check=True,
            )
            subprocess.run(
                ["netsh", "interface", "set", "interface", interface, "admin=enable"],
                check=True,
            )

        elif system in ["Linux", "Darwin"]:
            sudo = _sudo_prefix()
            ip_cmd = shutil.which("ip")
            if system == "Linux" and ip_cmd:
                subprocess.run(sudo + [ip_cmd, "link", "set", "dev", interface, "down"], check=True)
                subprocess.run(
                    sudo + [ip_cmd, "link", "set", "dev", interface, "address", normalized],
                    check=True,
                )
                subprocess.run(sudo + [ip_cmd, "link", "set", "dev", interface, "up"], check=True)
            else:
                subprocess.run(sudo + ["ifconfig", interface, "down"], check=True)
                subprocess.run(sudo + ["ifconfig", interface, "hw", "ether", normalized], check=True)
                subprocess.run(sudo + ["ifconfig", interface, "up"], check=True)

        print(f"MAC address changed to {normalized} on {interface}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error changing MAC: {e}")
        return False


def _extract_mac(text):
    match = _MAC_RE.search(text or "")
    if not match:
        return None
    return normalize_mac(match.group(0))


def get_current_mac(interface):
    """Return the current MAC address for the given interface."""
    if not interface:
        return None
    system = platform.system()

    try:
        if system == "Windows":
            result = _run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    f"Get-NetAdapter -Name '{interface}' | Select-Object -ExpandProperty MacAddress",
                ]
            )
            if result and result.returncode == 0:
                mac = _extract_mac(result.stdout)
                if mac:
                    return mac

            result = _run(["getmac", "/v", "/fo", "list"])
            if result:
                for iface in result.stdout.split("\n\n"):
                    if interface.lower() in iface.lower():
                        mac = _extract_mac(iface)
                        if mac:
                            return mac
            return None

        sysfs_path = os.path.join("/sys/class/net", interface, "address")
        if os.path.isfile(sysfs_path):
            try:
                with open(sysfs_path, "r") as file:
                    mac = normalize_mac(file.read().strip())
                    if mac:
                        return mac
            except OSError:
                pass

        result = _run(["ifconfig", interface])
        if result:
            mac = _extract_mac(result.stdout)
            if mac:
                return mac

        ip_cmd = shutil.which("ip")
        if ip_cmd:
            result = _run([ip_cmd, "link", "show", interface])
            if result:
                return _extract_mac(result.stdout)
        return None

    except Exception as e:
        print(f"Error fetching current MAC: {e}")
        return None


def restore_original_mac_if_enabled(interface, original_mac, enable_restore):
    """Restore the original MAC address if that option is enabled."""
    if not enable_restore or not original_mac:
        return True
    return apply_mac(interface, original_mac)
