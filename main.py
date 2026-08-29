import ctypes
import os
import sys

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox
except ImportError:  # pragma: no cover - allows unit tests on headless hosts
    tk = None
    ttk = None
    messagebox = None

import mac_utils


NETWORK_INTERFACE = "Wi-Fi"

THEME_CONFIG = {
    "font_family": "Segoe UI",
    "font_size_title": 22,
    "font_size_large": 16,
    "font_size_medium": 12,
    "font_size_small": 11,
    "font_size_tiny": 9,
    "button_padding": (16, 8),
    "entry_padding": (10, 8),
    "card_padding": 16,
    "button_spacing": 8,
    "section_spacing": 14,
    "element_spacing": 8,
    "window_width": 560,
    "window_height": 720,
    "min_width": 480,
    "min_height": 560,
}


def should_wait_for_input():
    stdin = getattr(sys, "stdin", None)
    if stdin is None:
        return False
    try:
        return bool(stdin.isatty())
    except Exception:
        return False


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin():
    if getattr(sys, "frozen", False):
        params = " ".join('"%s"' % arg for arg in sys.argv[1:])
    else:
        params = " ".join('"%s"' % arg for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)


class ScrollableFrame(ttk.Frame):
    """A vertical scrolling container so the form fits on smaller screens."""

    def __init__(self, container):
        super().__init__(container)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda _event: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda _event: self._unbind_mousewheel())

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_linux_scroll_up)
        self.canvas.bind_all("<Button-5>", self._on_linux_scroll_down)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta, "units")

    def _on_linux_scroll_up(self, _event):
        self.canvas.yview_scroll(-1, "units")

    def _on_linux_scroll_down(self, _event):
        self.canvas.yview_scroll(1, "units")


class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAC Address Changer")
        self.current_mac = None
        self.original_macs = {}
        self.current_interface = mac_utils.resolve_interface_name(NETWORK_INTERFACE)
        self._status_timeout = None

        self.setup_theme()
        self.setup_window()
        self.create_ui()

    def setup_theme(self):
        """Set up the app theme."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
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

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(config["window_width"], max(config["min_width"], screen_width - 80))
        window_height = min(config["window_height"], max(config["min_height"], screen_height - 80))
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(config["min_width"], min(config["min_height"], screen_height - 40))
        self.root.resizable(True, True)

    def create_ui(self):
        """Build the main window UI."""
        config = THEME_CONFIG

        self.scrollable = ScrollableFrame(self.root)
        self.scrollable.pack(fill="both", expand=True)
        self.main_frame = self.scrollable.inner

        self.title_label = ttk.Label(self.main_frame, text="MAC Address Changer", style="Title.TLabel")
        self.title_label.pack(pady=(config["section_spacing"], config["section_spacing"]))

        self.mac_card = ttk.LabelFrame(
            self.main_frame,
            text="Current MAC Address",
        )
        self.mac_card.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.mac_label = ttk.Label(self.mac_card, text="Click Generate to start", style="Large.TLabel")
        self.mac_label.pack(pady=8)

        self.interface_frame = ttk.LabelFrame(
            self.main_frame,
            text="Network Interface",
        )
        self.interface_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.interface_var = tk.StringVar(value=self.current_interface)
        self.interface_combo = ttk.Combobox(
            self.interface_frame,
            textvariable=self.interface_var,
            state="readonly",
        )
        self.interface_combo.pack(fill="x", pady=8)
        self.interface_combo.bind("<<ComboboxSelected>>", lambda _event: self.on_interface_changed())
        self.refresh_interface_options()

        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.generate_btn = ttk.Button(
            self.buttons_frame,
            text="Generate New MAC",
            command=self.generate_mac,
            style="Custom.TButton",
        )
        self.generate_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.check_btn = ttk.Button(
            self.buttons_frame,
            text="Check Current MAC",
            command=self.check_current_mac,
            style="Custom.TButton",
        )
        self.check_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.copy_btn = ttk.Button(
            self.buttons_frame,
            text="Copy MAC to Clipboard",
            command=self.copy_mac,
            style="Custom.TButton",
        )
        self.copy_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.set_mac_btn = ttk.Button(
            self.buttons_frame,
            text="Apply Current MAC",
            command=self.set_mac_address,
            style="Custom.TButton",
        )
        self.set_mac_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.reset_btn = ttk.Button(
            self.buttons_frame,
            text="Reset to Original MAC",
            command=self.reset_to_original_mac,
            style="Custom.TButton",
        )
        self.reset_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.save_btn = ttk.Button(
            self.buttons_frame,
            text="Save Current MAC",
            command=self.save_current_mac,
            style="Custom.TButton",
        )
        self.save_btn.pack(pady=(0, config["button_spacing"]), fill="x")

        self.restore_btn = ttk.Button(
            self.buttons_frame,
            text="Restore Saved MAC",
            command=self.restore_saved_mac,
            style="Custom.TButton",
        )
        self.restore_btn.pack(pady=(0, config["section_spacing"]), fill="x")

        self.exit_restore_var = tk.BooleanVar(value=False)
        self.exit_restore_frame = ttk.LabelFrame(
            self.main_frame,
            text="Exit Behavior",
        )
        self.exit_restore_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.exit_restore_box = ttk.Checkbutton(
            self.exit_restore_frame,
            text="Restore original MAC on exit",
            variable=self.exit_restore_var,
        )
        self.exit_restore_box.pack(anchor="w", pady=8)

        self.custom_mac_frame = ttk.LabelFrame(
            self.main_frame,
            text="Custom MAC Address",
        )
        self.custom_mac_frame.pack(pady=(0, config["section_spacing"]), padx=config["card_padding"], fill="x")

        self.custom_mac_entry = ttk.Entry(
            self.custom_mac_frame,
            style="Custom.TEntry",
            justify="center",
            font=(config["font_family"], config["font_size_medium"]),
        )
        self.custom_mac_entry.pack(pady=(8, config["button_spacing"]), fill="x")

        self.custom_mac_btn = ttk.Button(
            self.custom_mac_frame,
            text="Use Custom Address",
            command=self.add_custom_mac,
            style="Custom.TButton",
        )
        self.custom_mac_btn.pack(fill="x", pady=(0, 8))

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

        self.remember_original_mac()

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

    def remember_original_mac(self, interface=None):
        interface = interface or self.get_selected_interface()
        if interface not in self.original_macs:
            self.original_macs[interface] = mac_utils.get_current_mac(interface)
        return self.original_macs.get(interface)

    def on_interface_changed(self):
        interface = self.get_selected_interface()
        self.remember_original_mac(interface)

    def set_status(self, message, duration=4000):
        """Set status message with optional duration."""
        if self._status_timeout is not None:
            self.root.after_cancel(self._status_timeout)
            self._status_timeout = None

        self.status_label.configure(text=message)
        self._status_timeout = self.root.after(duration, lambda: self.status_label.configure(text=""))

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
            self.remember_original_mac(interface)
            self.set_status(f"✓ Current MAC on {interface}: {mac}")
        else:
            self.set_status(f"✗ Could not get current MAC for {interface}")

    def copy_mac(self):
        """Copy current MAC to clipboard"""
        if not self.current_mac:
            self.set_status("✗ No MAC to copy")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_mac)
            self.root.update_idletasks()
            self.set_status("✓ MAC copied to clipboard")
        except tk.TclError:
            self.set_status("✗ Could not copy MAC to clipboard")

    def set_mac_address(self):
        """Apply the current MAC address"""
        if not self.current_mac:
            self.set_status("✗ No MAC to apply")
            return

        interface = self.get_selected_interface()
        self.remember_original_mac(interface)
        if mac_utils.apply_mac(interface, self.current_mac):
            self.set_status(f"✓ Applied MAC: {self.current_mac} on {interface}")
        else:
            self.set_status(f"✗ Could not apply MAC on {interface}")

    def reset_to_original_mac(self):
        """Reset to the MAC that was present when this interface was first selected."""
        interface = self.get_selected_interface()
        original = self.remember_original_mac(interface)
        if not original:
            self.set_status("✗ No original MAC available")
            return

        if mac_utils.apply_mac(interface, original):
            self.current_mac = original
            self.mac_label.configure(text=self.current_mac)
            self.set_status(f"✓ Reset MAC to {original} on {interface}")
        else:
            self.set_status(f"✗ Could not reset MAC on {interface}")

    def add_custom_mac(self):
        """Add and validate custom MAC address"""
        mac_input = self.custom_mac_entry.get()
        normalized = mac_utils.normalize_mac(mac_input)
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
        self.remember_original_mac(interface)
        if mac_utils.apply_mac(interface, self.current_mac):
            self.set_status(f"✓ Restored MAC {self.current_mac} on {interface}")
        else:
            self.set_status(f"✗ Could not restore MAC on {interface}")

    def on_close(self):
        """Restore the original MAC if that option is enabled."""
        if self.exit_restore_var.get():
            interface = self.get_selected_interface()
            original = self.remember_original_mac(interface)
            if mac_utils.restore_original_mac_if_enabled(interface, original, True):
                self.set_status(f"✓ Restored original MAC for {interface}")
        self.root.destroy()


def _show_startup_error(error):
    print(f"Error starting application: {error}")
    import traceback

    traceback.print_exc()
    if tk is not None:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("MAC Address Changer", f"Error starting application:\n{error}")
            root.destroy()
            return
        except Exception:
            pass
    if should_wait_for_input():
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass


if __name__ == "__main__":
    try:
        if os.name == "nt" and not is_admin():
            _relaunch_as_admin()
            sys.exit(0)

        if tk is None:
            raise RuntimeError("tkinter is not installed")

        root = tk.Tk()
        app = MacChangerApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()

    except Exception as e:
        _show_startup_error(e)
