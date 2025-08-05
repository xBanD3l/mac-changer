import sys
import os
import tkinter as tk
import pyperclip
import mac_utils
import re

import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# Unified dark mode background color
DARK_BG = "#181a20"
WHITE = "#f3f4f6"
BLUE = "#2563eb"
BUTTON_ACTIVE = "#1e40af"
BUTTON_HOVER = "#334155"
STATUS_GREEN = "#22c55e"
STATUS_RED = "#ef4444"
STATUS_BLUE = "#3b82f6"
ACCENT = "#38bdf8"

# Use a modern, highly readable font stack
FONT_FAMILY = "Segoe UI, Helvetica Neue, Arial, sans-serif"
FONT_LARGE = (FONT_FAMILY, 22, "bold")
FONT_MEDIUM = (FONT_FAMILY, 15, "bold")
FONT_SMALL = (FONT_FAMILY, 12)

BUTTON_WIDTH = 26  # in text units

NETWORK_INTERFACE = "Wi-Fi"
try:
    DEFAULT_MAC = mac_utils.get_current_mac(NETWORK_INTERFACE)
except Exception:
    DEFAULT_MAC = "98-8D-46-FB-64-45"

def normalize_mac(mac_str):
    # Remove all non-hex characters, then format as XX:XX:XX:XX:XX:XX
    mac = re.sub(r'[^0-9A-Fa-f]', '', mac_str)
    if len(mac) != 12:
        return None
    mac = mac.upper()
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2))

class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAC Address Changer")
        self.root.configure(bg=DARK_BG)
        self.current_mac = None

        # Make the window larger to fit everything comfortably
        window_width = 500
        window_height = 750
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(580, 500)
        self.root.resizable(True, True)

        # Main frame centered, use unified background
        self.main_frame = tk.Frame(root, bg=DARK_BG, bd=0, highlightthickness=0)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # MAC display label
        self.mac_label = tk.Label(
            self.main_frame,
            text="Click Generate to start",
            font=FONT_LARGE,
            bg=DARK_BG,
            fg=WHITE,
            pady=18
        )
        self.mac_label.pack(pady=(0, 36))

        # Button style
        self.button_opts = {
            "font": FONT_MEDIUM,
            "bg": BLUE,
            "fg": WHITE,
            "activebackground": BUTTON_ACTIVE,
            "activeforeground": WHITE,
            "relief": "flat",
            "bd": 0,
            "highlightthickness": 0,
            "height": 2,
            "width": BUTTON_WIDTH,
            "cursor": "hand2"
        }

        # Buttons with more vertical spacing
        self.generate_btn = tk.Button(self.main_frame, text="Generate New MAC", command=self.generate_mac, **self.button_opts)
        self.generate_btn.pack(pady=(0, 22))
        self._add_hover(self.generate_btn)

        self.check_btn = tk.Button(self.main_frame, text="Check Current MAC", command=self.check_current_mac, **self.button_opts)
        self.check_btn.pack(pady=(0, 22))
        self._add_hover(self.check_btn)

        self.copy_btn = tk.Button(self.main_frame, text="Copy MAC to Clipboard", command=self.copy_mac, **self.button_opts)
        self.copy_btn.pack(pady=(0, 22))
        self._add_hover(self.copy_btn)

        self.set_mac_btn = tk.Button(self.main_frame, text="Apply Current MAC", command=self.set_mac_address, **self.button_opts)
        self.set_mac_btn.pack(pady=(0, 22))
        self._add_hover(self.set_mac_btn)

        self.reset_btn = tk.Button(self.main_frame, text="Reset to Default MAC", command=self.reset_to_default_mac, **self.button_opts)
        self.reset_btn.pack(pady=(0, 32))
        self._add_hover(self.reset_btn)

        # --- Custom MAC Entry and Button ---
        self.custom_mac_frame = tk.Frame(self.main_frame, bg=DARK_BG)
        self.custom_mac_frame.pack(pady=(0, 32))

        self.custom_mac_entry = tk.Entry(
            self.custom_mac_frame,
            font=FONT_MEDIUM,
            bg=WHITE,
            fg="#222",
            width=20,
            relief="flat",
            bd=2,
            highlightthickness=1,
            highlightbackground=ACCENT,
            highlightcolor=ACCENT,
            insertbackground="#222"
        )
        self.custom_mac_entry.pack(side="top", padx=(0, 0), pady=(0, 12))

        self.custom_mac_btn = tk.Button(
            self.custom_mac_frame,
            text="Use Custom Address",
            command=self.add_custom_mac,
            font=FONT_MEDIUM,
            bg=ACCENT,
            fg=WHITE,
            activebackground=BUTTON_ACTIVE,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            highlightthickness=0,
            height=2,
            width=20,
            cursor="hand2"
        )
        self.custom_mac_btn.pack(side="top")
        self._add_hover(self.custom_mac_btn, hover_bg=BUTTON_HOVER, normal_bg=ACCENT)
        # --- End Custom MAC ---

        # Status label
        self.status_label = tk.Label(self.main_frame, text="", font=FONT_SMALL, bg=DARK_BG, fg=WHITE, pady=8)
        self.status_label.pack(pady=(0, 0))

        # Author label in bottom-right corner
        self.author_label = tk.Label(
            root,
            text="Made With Hate by xBanD3l",
            font=(FONT_FAMILY, 10, "italic"),
            bg=DARK_BG,
            fg=WHITE
        )
        self.author_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def _add_hover(self, button, hover_bg=BUTTON_HOVER, normal_bg=BLUE):
        # Add a hover effect for better UX
        def on_enter(e):
            button.config(bg=hover_bg)
        def on_leave(e):
            button.config(bg=normal_bg)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def set_status(self, message, color=WHITE):
        self.status_label.config(text=message, fg=color)
        self.root.after(3000, lambda: self.status_label.config(text=""))

    def generate_mac(self):
        self.current_mac = mac_utils.generate_random_mac()
        self.mac_label.config(text=self.current_mac, fg=WHITE)
        self.set_status("Generated new MAC.", STATUS_BLUE)

    def check_current_mac(self):
        mac = mac_utils.get_current_mac(NETWORK_INTERFACE)
        if mac:
            self.mac_label.config(text=mac, fg=WHITE)
            self.current_mac = mac
            self.set_status(f"Current MAC: {mac}", STATUS_BLUE)
        else:
            self.set_status("Could not get current MAC.", STATUS_RED)

    def copy_mac(self):
        if self.current_mac:
            pyperclip.copy(self.current_mac)
            self.set_status("Copied!", STATUS_GREEN)
        else:
            self.set_status("No MAC to copy.", STATUS_RED)

    def set_mac_address(self):
        if not self.current_mac:
            self.set_status("No MAC to apply.", STATUS_RED)
            return
        mac_utils.apply_mac(NETWORK_INTERFACE, self.current_mac)
        self.set_status(f"Applied MAC: {self.current_mac}", STATUS_BLUE)

    def reset_to_default_mac(self):
        mac_utils.apply_mac(NETWORK_INTERFACE, DEFAULT_MAC)
        self.current_mac = DEFAULT_MAC
        self.mac_label.config(text=self.current_mac, fg=WHITE)
        self.set_status(f"Reset MAC to {DEFAULT_MAC}", STATUS_BLUE)

    def add_custom_mac(self):
        mac_input = self.custom_mac_entry.get()
        normalized = normalize_mac(mac_input)
        if not normalized:
            self.set_status("Invalid MAC address format.", STATUS_RED)
            return
        self.current_mac = normalized
        self.mac_label.config(text=self.current_mac, fg=WHITE)
        self.set_status(f"Custom MAC set: {self.current_mac}", STATUS_GREEN)

if __name__ == "__main__":
    if os.name == 'nt':
        if not is_admin():
            # Relaunch as admin
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(['"%s"' % arg for arg in sys.argv]), None, 1
            )
            sys.exit(0)
    root = tk.Tk()
    app = MacChangerApp(root)
    root.mainloop()
