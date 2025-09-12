import sys
import os
import tkinter as tk
import subprocess
import re
import ctypes

# Check and install ttkbootstrap if not available
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
except ImportError:
    print("Installing ttkbootstrap...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ttkbootstrap"])
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *

import pyperclip
import mac_utils

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# =============================================================================
# THEME CONFIGURATION - ttkbootstrap compatible settings only
# =============================================================================
THEME_CONFIG = {
    # Typography - Larger fonts for better readability
    'font_family': 'Segoe UI',
    'font_size_title': 32,      # Increased from 24
    'font_size_large': 24,      # Increased from 18
    'font_size_medium': 16,     # Increased from 12
    'font_size_small': 12,      # Increased from 10
    'font_size_tiny': 10,       # Increased from 8
    
    # Layout and Spacing - Larger padding and spacing
    'button_padding': (30, 16), # Increased from (20, 10)
    'entry_padding': (16, 12),  # Increased from (12, 8)
    'card_padding': 28,         # Increased from 20
    'button_spacing': 16,       # Increased from 12
    'section_spacing': 28,      # Increased from 20
    'element_spacing': 12,      # Increased from 8
    
    # Window Configuration - Larger window to accommodate bigger elements
    'window_width': 600,        # Increased from 500
    'window_height': 850,       # Increased from 700
    'min_width': 600,           # Increased from 500
    'min_height': 750,          # Increased from 600
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
NETWORK_INTERFACE = "Wi-Fi"
try:
    DEFAULT_MAC = mac_utils.get_current_mac(NETWORK_INTERFACE)
except Exception:
    DEFAULT_MAC = "98-8D-46-FB-64-45"

def normalize_mac(mac_str):
    """Remove all non-hex characters, then format as XX:XX:XX:XX:XX:XX"""
    mac = re.sub(r'[^0-9A-Fa-f]', '', mac_str)
    if len(mac) != 12:
        return None
    mac = mac.upper()
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2))

# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================
class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAC Address Changer")
        self.current_mac = None
        
        # Configure theme and styling
        self.setup_theme()
        
        # Setup window
        self.setup_window()
        
        # Create the UI
        self.create_ui()

    def setup_theme(self):
        """Configure ttkbootstrap theme and custom styles"""
        # Set the theme
        self.style = ttk.Style(theme='darkly')
        
        # Configure custom styles using only supported ttkbootstrap options
        self.configure_custom_styles()

    def configure_custom_styles(self):
        """Configure custom styles with ttkbootstrap compatible options only"""
        config = THEME_CONFIG
        
        # Configure custom button style - simple and compatible
        self.style.configure(
            'Custom.TButton',
            font=(config['font_family'], config['font_size_medium']),
            padding=config['button_padding'],
        )
        
        # Configure custom entry style - basic styling only
        self.style.configure(
            'Custom.TEntry',
            font=(config['font_family'], config['font_size_medium']),
            padding=config['entry_padding'],
        )
        
        # Configure custom label styles - simple and clean
        self.style.configure(
            'Title.TLabel',
            font=(config['font_family'], config['font_size_title'], 'bold'),
        )
        
        self.style.configure(
            'Large.TLabel',
            font=(config['font_family'], config['font_size_large'], 'bold'),
        )
        
        self.style.configure(
            'Medium.TLabel',
            font=(config['font_family'], config['font_size_medium']),
        )
        
        self.style.configure(
            'Small.TLabel',
            font=(config['font_family'], config['font_size_small']),
        )
        
        self.style.configure(
            'Tiny.TLabel',
            font=(config['font_family'], config['font_size_tiny']),
        )
        
        # Configure status label
        self.style.configure(
            'Status.TLabel',
            font=(config['font_family'], config['font_size_small']),
            justify='center',
        )

    def setup_window(self):
        """Configure window properties"""
        config = THEME_CONFIG
        
        # Set window size and position
        window_width = config['window_width']
        window_height = config['window_height']
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(config['min_width'], config['min_height'])
        self.root.resizable(True, True)

    def create_ui(self):
        """Create the user interface with clean ttkbootstrap styling and rounded corners"""
        config = THEME_CONFIG
        
        # Main container frame - Frame does not support rounded corners
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title - Label does not support rounded corners
        self.title_label = ttk.Label(
            self.main_frame,
            text="MAC Address Changer",
            style='Title.TLabel'
        )
        self.title_label.pack(pady=(0, config['section_spacing']))

        # MAC display card with rounded corners
        self.mac_card = ttk.LabelFrame(
            self.main_frame,
            text="Current MAC Address",
            padding=config['card_padding'],
            bootstyle="info"  # LabelFrame supports rounded styling through bootstyle
        )
        self.mac_card.pack(pady=(0, config['section_spacing']), padx=config['card_padding'], fill="x")

        # MAC display label - Label does not support rounded corners
        self.mac_label = ttk.Label(
            self.mac_card,
            text="Click Generate to start",
            style='Large.TLabel'
        )
        self.mac_label.pack()

        # Buttons container - Frame does not support rounded corners
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(pady=(0, config['section_spacing']), padx=config['card_padding'], fill="x")

        # Action buttons with rounded corners using rounded bootstyles
        self.generate_btn = ttk.Button(
            self.buttons_frame,
            text="Generate New MAC",
            command=self.generate_mac,
            style='Custom.TButton',
            bootstyle='primary-rounded'
        )
        self.generate_btn.pack(pady=(0, config['button_spacing']), fill="x")

        self.check_btn = ttk.Button(
            self.buttons_frame,
            text="Check Current MAC",
            command=self.check_current_mac,
            style='Custom.TButton',
            bootstyle='info-rounded'
        )
        self.check_btn.pack(pady=(0, config['button_spacing']), fill="x")

        self.copy_btn = ttk.Button(
            self.buttons_frame,
            text="Copy MAC to Clipboard",
            command=self.copy_mac,
            style='Custom.TButton',
            bootstyle='success-rounded'
        )
        self.copy_btn.pack(pady=(0, config['button_spacing']), fill="x")

        self.set_mac_btn = ttk.Button(
            self.buttons_frame,
            text="Apply Current MAC",
            command=self.set_mac_address,
            style='Custom.TButton',
            bootstyle='warning-rounded'
        )
        self.set_mac_btn.pack(pady=(0, config['button_spacing']), fill="x")

        self.reset_btn = ttk.Button(
            self.buttons_frame,
            text="Reset to Default MAC",
            command=self.reset_to_default_mac,
            style='Custom.TButton',
            bootstyle='danger-rounded'
        )
        self.reset_btn.pack(pady=(0, config['section_spacing']), fill="x")

        # Custom MAC section with rounded corners
        self.custom_mac_frame = ttk.LabelFrame(
            self.main_frame,
            text="Custom MAC Address",
            padding=config['card_padding'],
            bootstyle="secondary"  # LabelFrame supports rounded styling through bootstyle
        )
        self.custom_mac_frame.pack(pady=(0, config['section_spacing']), padx=config['card_padding'], fill="x")

        # Custom MAC entry with rounded corners
        self.custom_mac_entry = ttk.Entry(
            self.custom_mac_frame,
            style='Custom.TEntry',
            justify="center",
            font=(config['font_family'], config['font_size_medium']),
            bootstyle="rounded"  # Entry supports rounded styling
        )
        self.custom_mac_entry.pack(pady=(0, config['button_spacing']), fill="x")

        # Custom MAC button with rounded corners
        self.custom_mac_btn = ttk.Button(
            self.custom_mac_frame,
            text="Use Custom Address",
            command=self.add_custom_mac,
            style='Custom.TButton',
            bootstyle='secondary-rounded'
        )
        self.custom_mac_btn.pack(fill="x")

        # Status label - Label does not support rounded corners
        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            style='Status.TLabel',
            wraplength=400,
            justify="center"
        )
        self.status_label.pack(pady=(0, config['section_spacing']))

        # Author label - Label does not support rounded corners
        self.author_label = ttk.Label(
            self.root,
            text="Made With Hate by xBanD3l",
            style='Tiny.TLabel'
        )
        self.author_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    # =========================================================================
    # EVENT HANDLERS - Keep all existing logic exactly the same
    # =========================================================================
    def set_status(self, message, color=None, duration=4000):
        """Set status message with optional color and duration"""
        # Clear any existing status timeout
        if hasattr(self, '_status_timeout'):
            self.root.after_cancel(self._status_timeout)
        
        # Set the status message
        self.status_label.configure(text=message)
        
        # Auto-clear after specified duration
        self._status_timeout = self.root.after(duration, lambda: self.status_label.configure(text=""))

    def generate_mac(self):
        """Generate a new random MAC address"""
        self.current_mac = mac_utils.generate_random_mac()
        self.mac_label.configure(text=self.current_mac)
        self.set_status("✓ Generated new MAC address")

    def check_current_mac(self):
        """Check and display current MAC address"""
        mac = mac_utils.get_current_mac(NETWORK_INTERFACE)
        if mac:
            self.mac_label.configure(text=mac)
            self.current_mac = mac
            self.set_status(f"✓ Current MAC: {mac}")
        else:
            self.set_status("✗ Could not get current MAC")

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
        mac_utils.apply_mac(NETWORK_INTERFACE, self.current_mac)
        self.set_status(f"✓ Applied MAC: {self.current_mac}")

    def reset_to_default_mac(self):
        """Reset to default MAC address"""
        mac_utils.apply_mac(NETWORK_INTERFACE, DEFAULT_MAC)
        self.current_mac = DEFAULT_MAC
        self.mac_label.configure(text=self.current_mac)
        self.set_status(f"✓ Reset MAC to {DEFAULT_MAC}")

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

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    try:
        if os.name == 'nt':
            if not is_admin():
                # Relaunch as admin
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(['"%s"' % arg for arg in sys.argv]), None, 1
                )
                sys.exit(0)
        
        # Create and run the application
        root = ttk.Window(themename='darkly')
        
        app = MacChangerApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")