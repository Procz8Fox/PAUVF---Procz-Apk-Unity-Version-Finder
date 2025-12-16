# 🎮 PAUVF – Procz APK Unity Version Finder

PAUVF is a desktop GUI tool written in **Python (Tkinter)** that analyzes Android APK files and detects the **Unity engine version** used to build them.

It features a modern animated UI, real-time progress updates, and deep scanning of Unity asset files to reliably extract version information—even from partially obfuscated APKs.

---

## 🚀 Features

- 🔍 Detects whether an APK is built using **Unity**
- 🎯 Extracts the **exact Unity version** (e.g. `2021.3.1f1`)
- 📦 Scans common Unity files:
  - `globalgamemanagers`
  - `data.unity3d`
  - `level0`
  - `mainData`
  - `libunity.so` (ARM / ARM64 / x86)
- 🔬 Performs **deep asset scanning** if primary files fail
- 📊 Animated progress bar with real-time status updates
- 🎨 Custom neon-themed UI with animations and scaling
- 🧵 Multithreaded scanning (UI never freezes)

---

