# MAC Address Changer

This is a small desktop app for changing the MAC address on a network interface. I built it while learning Python and working with low-level networking tools. It is handy for quick experiments and local testing.

## What it does

- show the current MAC address
- generate a random MAC address
- apply a new MAC to a selected interface
- save and restore a MAC later
- optionally restore the original MAC when the app closes

## How to run

Python 3.10+ with tkinter is enough. On Debian/Ubuntu, install tkinter first:

```bash
sudo apt install python3-tk
```

Start the app:

```bash
python main.py
```

On Windows, the app may ask for administrator access when changing the MAC address.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Build a Windows executable

A GitHub Action is included at [.github/workflows/build-exe.yml](.github/workflows/build-exe.yml). It runs the tests, builds a Windows EXE, and (from `main` or a version tag) updates the latest GitHub release.

To run a release build:
1. Open the Actions tab on GitHub.
2. Select "Build Windows EXE".
3. Click "Run workflow" on the `main` branch.

Pull requests also run the tests and publish the EXE as a workflow artifact without creating a release.

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
