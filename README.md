
![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Production--ready-brightgreen)
![Made by Bernard Ennis](https://img.shields.io/badge/made%20by-Bernard%20Ennis-blueviolet)

# 🖼️ ImageIP

**A smart, cross-platform image metadata and signature tool by Bernard Ennis**

ImageIP allows you to digitally sign, license, and embed author and copyright metadata into your images—powered by GPG, Creative Commons, and intelligent automation. Whether you're preserving rights or enabling sharing, ImageIP has your creative back.

---

## ✨ Features

- 📁 **Batch-tag entire folders** of images
- 🔍 **Detects transparency**: preserves PNG/WebP or converts to JPEG
- 🔐 **GPG signature support** per profile
- 🧾 **Creative Commons licensing** with embedded license URLs
- 🪪 **Profile manager**: name, license, and signing key
- 🧠 **EXIF and filesystem tagging**, OS-aware
- 🪟 **Simple GUI** using Tkinter
- 🧰 **Cross-platform** (Windows, macOS, Linux)

---

## 📦 Installation

### Requirements

- Python 3.7+
- GPG installed and configured
- Dependencies:
  
```bash
pip install -r requirements.txt

ImageIP/
├── main.py
├── gui.py
├── profile_manager.py
├── signing_engine.py
├── utils.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── profiles/
│   └── profiles.json  (auto-created)
├── assets/
│   └── icon.png       (your beautiful logo)
├── dist/
│   └── imageip.exe or ImageIP.app (after packaging)
