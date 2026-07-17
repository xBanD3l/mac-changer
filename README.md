# MAC Address Changer

This is a small desktop app for changing the MAC address on a network interface. I built it while learning Python and working with low-level networking tools. It is handy for quick experiments and local testing.

## What it does

- show the current MAC address
- generate a random MAC address
- apply a new MAC to a selected interface
- save and restore a MAC later
- optionally restore the original MAC when the app closes

## How to run

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   python main.py
   ```

On Windows, the app may ask for administrator access when changing the MAC address.

## Build a Windows executable

A GitHub Action is included at [.github/workflows/build-exe.yml](.github/workflows/build-exe.yml). It builds a Windows EXE from the current repository contents and updates the latest GitHub release with the newest build.

To run it:
1. Open the Actions tab on GitHub.
2. Select "Build Windows EXE".
3. Click "Run workflow".

The built file will be available as a workflow artifact.

## Limits

- This needs admin or root privileges to actually change the address.
- It depends on the system tools available on your machine.
- This is a simple tool for learning and local testing, not a full network management app.

## ⚠️ Disclaimer

This tool is provided for educational purposes only.
I am not responsible for any misuse, damage, or legal issues caused by using this program.
Use it at your own risk and only on networks you own or have permission to modify.

**Important Notes:**
- Changing MAC addresses may violate terms of service
- Some networks track devices by MAC address
- Always ensure you have permission before changing MAC addresses
- MAC address changes may affect network connectivity

## License

This project is licensed under the **MIT License** with an attribution clause.  
You are free to use, modify, and distribute this software (even commercially), but you must **give proper credit to "xBanD3l"** in your project or distribution.
