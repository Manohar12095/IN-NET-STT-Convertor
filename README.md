Visit at : https://in-net-stt-convertor.vercel.app

# IN NET STT Convertor

**IN NET STT Convertor** is a powerful Text-to-Speech (TTS) application that transforms any text into natural, expressive speech. Built using Microsoft Edge Neural TTS voices, this tool supports 70+ languages and offers a simple, beautiful desktop interface.

---

## 🌟 Features

- **70+ Languages & Hundreds of Voices:** Access high-quality Microsoft Edge Neural TTS voices.
- **Adjustable Speech Parameters:** Customize the reading speed and pitch to fit your needs.
- **Beautiful Glassmorphism UI:** Features a sleek dark theme, animated gradient backgrounds, and intuitive micro-interactions.
- **Native Desktop App:** Runs as a standalone Windows desktop app without needing a web browser tab (powered by `pywebview`).
- **One-Click Download:** Download generated audio as an `.mp3` file instantly.
- **Free Forever:** No API keys or subscriptions required.

---

## 🚀 Getting Started

### Option 1: Run the Pre-built Windows Application
For standard users, there is no need to install Python or use the command line!

**System Requirements:**
- **OS:** Windows 10 or Windows 11 (64-bit)
- **Internet:** Required (to access the Microsoft Edge TTS servers)
- **Dependencies:** Microsoft Edge WebView2 (Built into Windows 11 and modern Windows 10). *Note: If WebView2 is missing, the app will gracefully fall back to opening in your default web browser.*

**How it works:**
The `InNetSTT.exe` is a fully portable, single-file executable built using PyInstaller. It bundles the Python runtime, the local Flask server, and all frontend UI assets. When launched, it spins up the server in the background and opens a native desktop window—meaning you get a full software experience without needing to install anything!

1. Download the pre-built `InNetSTT.exe` from the `dist/` folder.
2. Double-click the file to open the native desktop application instantly.
3. Type your text, select a voice, and hit **Generate & Play**!

### Option 2: Run from Source (For Developers)

**Prerequisites:**
- Python 3.8 or higher installed on your system.

**Installation & Execution:**
1. Clone or download this repository.
2. Run the included `run.bat` script. This will automatically check for Python, install dependencies, and launch the application.

*Alternatively, to run manually in your terminal:*
```cmd
pip install -r requirements.txt
python app.py
```

### Option 3: Deploy to Vercel (Web Version)
This project comes with a `vercel.json` file ready for serverless deployment on Vercel.
1. Install the Vercel CLI.
2. Run `vercel deploy` in the root folder.
3. Access your web-hosted TTS app from anywhere!

---

## 🛠 Building the EXE from Source
If you make changes to the code and want to rebuild the standalone `.exe`:
1. Double-click `build.bat`
2. Wait 1-3 minutes while PyInstaller compiles the app.
3. The new executable will be available at `dist/InNetSTT.exe`.

---

## 📞 About the Creator

**Created by:** Manohar
**Powered by:** IN NET CREATIONS

Building smart, accessible tools for everyone. Crafting the future, one app at a time.

📧 **Contact:** innetcreations@gmail.com

---

© 2026 IN NET CREATIONS · All rights reserved.
