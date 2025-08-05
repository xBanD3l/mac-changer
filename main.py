import tkinter as tk
import pyperclip
import mac_utils

# Color and font constants for dark mode
DARK_BG = "#23272f"
WHITE = "#ffffff"
BLUE = "#2563eb"
BUTTON_ACTIVE = "#1e40af"
STATUS_GREEN = "#22c55e"
STATUS_RED = "#ef4444"
STATUS_BLUE = "#3b82f6"
FONT_LARGE = ("Arial", 20, "bold")
FONT_MEDIUM = ("Arial", 16, "bold")
FONT_SMALL = ("Arial", 13)

BUTTON_WIDTH = 26  # in text units

NETWORK_INTERFACE = "Wi-Fi"
DEFAULT_MAC = "98-8D-46-FB-64-45"


class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAC Address Changer")
        self.root.configure(bg=DARK_BG)
        self.current_mac = None

        window_width = 600
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(440, 400)
        self.root.resizable(True, True)

        # Main frame centered
        self.main_frame = tk.Frame(root, bg=DARK_BG)
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
        self.mac_label.pack(pady=(0, 28))

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

        # Buttons
        self.generate_btn = tk.Button(self.main_frame, text="Generate New MAC", command=self.generate_mac, **self.button_opts)
        self.generate_btn.pack(pady=(0, 14))

        self.check_btn = tk.Button(self.main_frame, text="Check Current MAC", command=self.check_current_mac, **self.button_opts)
        self.check_btn.pack(pady=(0, 14))

        self.copy_btn = tk.Button(self.main_frame, text="Copy MAC to Clipboard", command=self.copy_mac, **self.button_opts)
        self.copy_btn.pack(pady=(0, 14))

        self.set_mac_btn = tk.Button(self.main_frame, text="Apply Current MAC", command=self.set_mac_address, **self.button_opts)
        self.set_mac_btn.pack(pady=(0, 14))

        self.reset_btn = tk.Button(self.main_frame, text="Reset to Default MAC", command=self.reset_to_default_mac, **self.button_opts)
        self.reset_btn.pack(pady=(0, 24))

        # Status label
        self.status_label = tk.Label(self.main_frame, text="", font=FONT_SMALL, bg=DARK_BG, fg=STATUS_GREEN, pady=8)
        self.status_label.pack()

        # Author label in bottom-right corner
        self.author_label = tk.Label(
            root,
            text="Made With ❤️by xBanD3l",
            font=("Consolas", 10, "italic"),
            bg=DARK_BG,
            fg="#888888"
        )
        self.author_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def set_status(self, message, color=STATUS_GREEN):
        self.status_label.config(text=message, fg=color)
        self.root.after(3000, lambda: self.status_label.config(text=""))

    def generate_mac(self):
        self.current_mac = mac_utils.generate_random_mac()
        self.mac_label.config(text=self.current_mac)
        self.set_status("Generated new MAC.", STATUS_BLUE)

    def check_current_mac(self):
        mac = mac_utils.get_current_mac(NETWORK_INTERFACE)
        if mac:
            self.mac_label.config(text=mac)
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
        self.mac_label.config(text=self.current_mac)
        self.set_status(f"Reset MAC to {DEFAULT_MAC}", STATUS_BLUE)


if __name__ == "__main__":
    root = tk.Tk()
    app = MacChangerApp(root)
    root.mainloop()
