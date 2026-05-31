# Autonomous installers (no Python required)

These launchers install a **private copy** of Python and all app libraries on **first run**, then start the Streamlit UI in your browser. You do **not** need Python, pip, or conda on your computer.

**Requirements:** Internet on first run (~150–250 MB download). Disk space ~500 MB after install. Windows 10/11, macOS 11+, or a recent Linux (x86_64 or arm64).

---

## Windows 10 / 11

1. Open the project folder (or your ZIP after unpacking).
2. Double-click:

   **`installers\windows\Install and Run.bat`**

3. Wait for the first-time setup to finish (several minutes).
4. Your browser should open at `http://localhost:8501`. Keep the black window open while you use the app.

To stop the app: close the browser tab and press **Ctrl+C** in the window, or close the window.

---

## macOS

1. In Terminal, make the launcher executable (once):

   ```bash
   chmod +x "installers/macos/Install and Run.command"
   chmod +x installers/macos/setup-runtime.sh
   ```

2. Double-click **`installers/macos/Install and Run.command`**  
   (If macOS blocks it: **System Settings → Privacy & Security → Open Anyway**.)

3. First run downloads portable Python; then the browser opens.

Alternatively from Terminal:

```bash
bash "installers/macos/Install and Run.command"
```

---

## Linux

1. Make the script executable (once):

   ```bash
   chmod +x installers/linux/install-and-run.sh installers/linux/setup-runtime.sh
   ```

2. Run:

   ```bash
   ./installers/linux/install-and-run.sh
   ```

   Or: `bash installers/linux/install-and-run.sh`

---

## What gets installed?

| Location | Contents |
|----------|----------|
| `installers/runtime/` | Private Python + pip packages (not shared with the system) |
| Browser | App at **http://localhost:8501** |

This folder is **gitignored**; each machine builds its own copy.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| “Setup failed” / download error | Check internet; corporate proxy may block GitHub or python.org |
| Browser does not open | Open **http://localhost:8501** manually |
| Port already in use | Close other Streamlit apps; or set `STREAMLIT_SERVER_PORT=8502` before launch |
| macOS “damaged” / unsigned | `chmod +x` the `.command` file; allow in Privacy & Security |
| Reinstall from scratch | Delete the folder `installers/runtime/` and run the launcher again |

Diagnostics (if you have any Python 3.10+):

```bash
python installers/common/bootstrap.py doctor
```

---

## For maintainers

- **Windows** uses the official **embeddable** CPython zip from python.org.
- **macOS / Linux** use **python-build-standalone** install-only tarballs (no compiler, no root).
- After portable Python exists, `installers/common/bootstrap.py` runs `pip install -e .` on the project root and `streamlit run app.py`.

Do not commit `installers/runtime/` to git (see `.gitignore`).
