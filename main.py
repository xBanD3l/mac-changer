import ctypes
import os
import re
import subprocess
import sys
import tkinter as tk

# Check and install ttkbootstrap if not available
try:
    import ttkbootstrap as ttk
except ImportError:
    print("Installing ttkbootstrap...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ttkbootstrap"])
    import ttkbootstrap as ttk

import pyperclip

import mac_utils


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


THEME_CONFIG = {
    "font_family": "Segoe UI",
    "font_size_title": 32,
    "font_size_large": 24,
    "font_size_medium": 16,
    "font_size_small": 12,
    "font_size_tiny": 10,
    "button_padding": (30, 16),
    "entry_padding": (16, 12),
    "card_padding": 28,
    "button_spacing": 16,
    "section_spacing": 28,
    "element_spacing": 12,
    "window_width": 650,
    "window_height": 900,
    "min_width": 620,
    "min_height": 780,
}

NETWORK_INTERFACE = "Wi-Fi"
try:
    DEFAULT_MAC = mac_utils.get_current_mac(NETWORK_INTERFACE)
except Exception:
    DEFAULT_MAC = "98-8D-46-FB-64-45"


def normalize_mac(mac_str):
    """Remove all non-hex characters, then format as XX:XX:XX:XX:XX:XX"""
    mac = re.sub(r"[^0-9A-Fa-f]", "", mac_str)
    if len(mac) != 12:
        return None
    mac = mac.upper()
    return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAC Address Changer")
        self.current_mac = None
        self.current_interface = mac_utils.resolve_interface_name(NETWORK_INTERFACE)

        self.setup_theme()
        self.setup_window()
        self.create_ui()

    def setup_theme(self):
        """Set up the app theme."""
        self.style = ttk.Style(theme="darkly")
        self.configure_custom_styles()

    def configure_custom_styles(self):
        """Set a few simple widget styles."""
        config = THEME_CONFIG

        self.style.configure(
            "Custom.TButton",
            font=(config["font_family"], config["font_size_medium"]),
            padding=config["button_padding"],
        )
        self.style.configure(
            "Custom.TEntry",
            font=(config["font_family"], config["font_size_medium"]),
            padding=config["entry_padding"],
        )
        self.style.configure(
            "Title.TLabel",
            font=(config["font_family"], config["font_size_title"], "bold"),
        )
        self.style.configure(
            "Large.TLabel",
            font=(config["font_family"], config["font_size_large"], "bold"),
        )
        self.style.configure(
            "Medium.TLabel",
            font=(config["font_family"], config["font_size_medium"]),
        )
        self.style.configure(
            "Small.TLabel",
            font=(config["font_family"], config["font_size_small"]),
        )
        self.style.configure(
            "Tiny.TLabel",
            font=(config["font_family"], config["font_size_tiny"]),
        )
        self.style.configure(
            "Status.TLabel",
            font=(config["font_family"], config["font_size_small"]),
            justify="center",
        )

    def setup_window(self):
        """Size the window for the current screen."""
        config = THEME_CONFIG

        window_width = config["window_width"]
        window_height = config["window_height"]
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(config["min_width"], config["min_height"])
        self.root.resizable(True, True)

    def create_ui(self):
        """Build the main window UI."""
        config = THEME_CONFIG

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = ttk.Label(self.main_frame, text="MAC Address Changer", style="Title.TLabel")
        self.title_label.pack(pady=(0, config["section_spacing"]))

        self.mac_card = ttk.LabelFrame(
            self.main_frame,
            text="Current MAC Address",
            padding=config["card_padding"],
            bootstyle="info",
        )
        self.mac_card.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.mac_label = ttk.Label(self.mac_card, text="Click Generate to start", style="Large.TLabel")
        self.mac_label.pack()

        self.interface_frame = ttk.LabelFrame(
            self.main_frame,
            text="Network Interface",
            padding=config["card_padding"],
            bootstyle="secondary",
        )
        self.interface_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.interface_var = tk.StringVar(value=self.current_interface)
        self.interface_combo = ttk.Combobox(
            self.interface_frame,
            textvariable=self.interface_var,
            state="readonly",
            bootstyle="rounded",
        )
        self.interface_combo.pack(fill="x")
        self.interface_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_original_mac())
        self.refresh_interface_options()

        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.generate_btn = ttk.Button(
            self.buttons_frame,
            text="Generate New MAC",
            command=self.generate_mac,
            style="Custom.TButton",
            bootstyle="primary-rounded",
        )
        self.generate_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.check_btn = ttk.Button(
            self.buttons_frame,
            text="Check Current MAC",
            command=self.check_current_mac,
            style="Custom.TButton",
            bootstyle="info-rounded",
        )
        self.check_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.copy_btn = ttk.Button(
            self.buttons_frame,
            text="Copy MAC to Clipboard",
            command=self.copy_mac,
            style="Custom.TButton",
            bootstyle="success-rounded",
        )
        self.copy_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.set_mac_btn = ttk.Button(
            self.buttons_frame,
            text="Apply Current MAC",
            command=self.set_mac_address,
            style="Custom.TButton",
            bootstyle="warning-rounded",
        )
        self.set_mac_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.reset_btn = ttk.Button(
            self.buttons_frame,
            text="Reset to Default MAC",
            command=self.reset_to_default_mac,
            style="Custom.TButton",
            bootstyle="danger-rounded",
        )
        self.reset_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.save_btn = ttk.Button(
            self.buttons_frame,
            text="Save Current MAC",
            command=self.save_current_mac,
            style="Custom.TButton",
            bootstyle="success-rounded",
        )
        self.save_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.restore_btn = ttk.Button(
            self.buttons_frame,
            text="Restore Saved MAC",
            command=self.restore_saved_mac,
            style="Custom.TButton",
            bootstyle="secondary-rounded",
        )
        self.restore_btn.pack(pady=(0, config["section_spacing"]), fill="x")

        self.exit_restore_var = tk.BooleanVar(value=False)
        self.exit_restore_frame = ttk.LabelFrame(
            self.main_frame,
            text="Exit Behavior",
            padding=config["card_padding"],
            bootstyle="secondary",
        )
        self.exit_restore_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.exit_restore_box = ttk.Checkbutton(
            self.exit_restore_frame,
            text="Restore original MAC on exit",
            variable=self.exit_restore_var,
            style="Custom.TButton",
        )
        self.exit_restore_box.pack(anchor="w")

        self.custom_mac_frame = ttk.LabelFrame(
            self.main_frame,
            text="Custom MAC Address",
            padding=config["card_padding"],
            bootstyle="secondary",
        )
        self.custom_mac_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.custom_mac_entry = ttk.Entry(
            self.custom_mac_frame,
            style="Custom.TEntry",
            justify="center",
            font=(config["font_family"], config["font_size_medium"]),
            bootstyle="rounded",
        )
        self.custom_mac_entry.pack(pady=(0, config["button_spacing"]), fill="x")

        self.custom_mac_btn = ttk.Button(
            self.custom_mac_frame,
            text="Use Custom Address",
            command=self.add_custom_mac,
            style="Custom.TButton",
            bootstyle="secondary-rounded",
        )
        self.custom_mac_btn.pack(fill="x")

        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            style="Status.TLabel",
            wraplength=400,
            justify="center",
        )
        self.status_label.pack(pady=(0, config["section_spacing"]))

        self.author_label = ttk.Label(self.root, text="by xBanD3l", style="Tiny.TLabel")
        self.author_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self.original_mac = None
        self.refresh_original_mac()

    def refresh_interface_options(self):
        interfaces = mac_utils.get_available_interfaces()
        self.interface_combo["values"] = interfaces
        if interfaces:
            selected = mac_utils.resolve_interface_name(self.current_interface, fallback=interfaces[0])
            self.current_interface = selected
            self.interface_var.set(selected)
        else:
            self.interface_var.set(self.current_interface)

    def get_selected_interface(self):
        selected = self.interface_var.get().strip()
        if selected:
            self.current_interface = selected
            return selected
        return self.current_interface

    def set_status(self, message, duration=4000):
        """Set status message with optional color and duration"""
        if hasattr(self, "_status_timeout"):
            self.root.after_cancel(self._status_timeout)

        self.status_label.configure(text=message)
        self._status_timeout = self.root.after(duration, lambda: self.status_label.configure(text=""))

    def refresh_original_mac(self):
        interface = self.get_selected_interface()
        self.original_mac = mac_utils.get_current_mac(interface)

    def generate_mac(self):
        """Generate a new random MAC address"""
        self.current_mac = mac_utils.generate_random_mac()
        self.mac_label.configure(text=self.current_mac)
        self.set_status("✓ Generated new MAC address")

    def check_current_mac(self):
        """Check and display current MAC address"""
        interface = self.get_selected_interface()
        mac = mac_utils.get_current_mac(interface)
        if mac:
            self.mac_label.configure(text=mac)
            self.current_mac = mac
            self.original_mac = mac
            self.set_status(f"✓ Current MAC on {interface}: {mac}")
        else:
            self.set_status(f"✗ Could not get current MAC for {interface}")

    def copy_mac(self):
        """Copy current MAC to clipboard"""
        if self.current_mac:
            pyperclip.copy(self.current_mac)
            self.set_status("✓ MAC copied to clipboard")
        else:
            self.set_status("✗ No MAC to copy")

    def set_mac_address(self):
        """Apply the current MAC address"""
        if not self.current_mac:
            self.set_status("✗ No MAC to apply")
            return

        interface = self.get_selected_interface()
        if mac_utils.apply_mac(interface, self.current_mac):
            self.set_status(f"✓ Applied MAC: {self.current_mac} on {interface}")
        else:
            self.set_status(f"✗ Could not apply MAC on {interface}")

    def reset_to_default_mac(self):
        """Reset to default MAC address"""
        interface = self.get_selected_interface()
        if not DEFAULT_MAC:
            self.set_status("✗ No default MAC available")
            return

        if mac_utils.apply_mac(interface, DEFAULT_MAC):
            self.current_mac = DEFAULT_MAC
            self.mac_label.configure(text=self.current_mac)
            self.set_status(f"✓ Reset MAC to {DEFAULT_MAC} on {interface}")
        else:
            self.set_status(f"✗ Could not reset MAC on {interface}")

    def add_custom_mac(self):
        """Add and validate custom MAC address"""
        mac_input = self.custom_mac_entry.get()
        normalized = normalize_mac(mac_input)
        if not normalized:
            self.set_status("✗ Invalid MAC address format")
            return
        self.current_mac = normalized
        self.mac_label.configure(text=self.current_mac)
        self.set_status(f"✓ Custom MAC set: {self.current_mac}")

    def save_current_mac(self):
        """Save the currently displayed MAC address."""
        if not self.current_mac:
            self.set_status("✗ No MAC to save")
            return
        if mac_utils.save_mac(self.current_mac):
            self.set_status("✓ Saved current MAC")
        else:
            self.set_status("✗ Could not save MAC")

    def restore_saved_mac(self):
        """Restore a previously saved MAC address and apply it."""
        saved_mac = mac_utils.load_saved_mac()
        if not saved_mac:
            self.set_status("✗ No saved MAC found")
            return

        self.current_mac = saved_mac
        self.mac_label.configure(text=self.current_mac)
        interface = self.get_selected_interface()
        if mac_utils.apply_mac(interface, self.current_mac):
            self.set_status(f"✓ Restored MAC {self.current_mac} on {interface}")
        else:
            self.set_status(f"✗ Could not restore MAC on {interface}")

    def on_close(self):
        """Restore the original MAC if that option is enabled."""
        if self.exit_restore_var.get():
            interface = self.get_selected_interface()
            if mac_utils.restore_original_mac_if_enabled(interface, self.original_mac, True):
                self.set_status(f"✓ Restored original MAC for {interface}")
        self.root.destroy()


if __name__ == "__main__":
    try:
        if os.name == "nt":
            if not is_admin():
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    " ".join(['"%s"' % arg for arg in sys.argv]),
                    None,
                    1,
                )
                sys.exit(0)

        root = ttk.Window(themename="darkly")
        app = MacChangerApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()

    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback

        traceback.print_exc()
        input("Press Enter to exit...")