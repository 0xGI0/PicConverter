# 🖼️ PicConverter

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml/badge.svg)](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-1f538d?style=flat)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🇩🇪 [Deutsche Version](README.md)

An **image & PDF conversion tool** for Python with a modern GUI (CustomTkinter) and a CLI for automation. Converts single files or whole batches between all common image formats and PDF — with EXIF management, target-size mode, and size estimation.

> **Note:** The user interface and CLI output are currently in German.

![Screenshot](screenshot.png)

---

## ✨ Features

- **All common image formats**: JPEG, PNG, BMP, TIFF, GIF, WebP, ICO
- **PDF in both directions**: save images as PDF or export PDF pages as images (page selection, all pages, DPI choice)
- **Batch processing**: queue multiple files via drag & drop, or use globs like `*.jpg` in the CLI
- **Combined PDF**: merge multiple images (and PDF pages) into one multi-page PDF
- **EXIF metadata**: automatic correct image orientation; keep, strip, or edit metadata fields (artist, copyright, date, …)
- **Target size instead of quality**: specify "max. 500 KB" — the matching quality is found automatically (JPEG/WebP)
- **Adjustable quality/compression**, **resizing** with aspect-ratio preservation, and **size estimation** before converting
- **Modern interface**: follows the system theme (switchable to dark/light), live preview, PDF page navigation, inline results with "open folder"
- **Two modes**: GUI for interactive use, CLI for scripts and automation

---

## 🚀 Installation

```bash
git clone https://github.com/0xGI0/PicConverter.git
cd PicConverter
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| `Pillow` | Image processing |
| `customtkinter` | Modern GUI |
| `tkinterdnd2` | Drag & drop (optional — the GUI works without it) |
| `PyMuPDF` | PDF → image (optional — image → PDF works without it) |

**Install as a package (optional):** afterwards the commands `picconverter` and `picconverter-gui` are available system-wide:

```bash
pip install .[all]        # or: pipx install .[all]
```

**Application menu entry (Linux, after package installation):**

```bash
cp picconverter.desktop ~/.local/share/applications/
```

**Note (Linux):** tkinter itself is installed via the package manager if missing:

```bash
sudo apt-get install python3-tk    # Ubuntu/Debian
sudo dnf install python3-tkinter   # Fedora/RHEL
sudo pacman -S tk                  # Arch Linux
```

---

## 💻 Usage

### 🎨 GUI

```bash
python picconverter_gui.py        # or: picconverter-gui
```

1. Drag images or PDFs into the window or load them via **"Dateien auswählen"** (select files) — multiple files form a queue; for PDFs a **page navigation** appears
2. Choose the **output format** (including PDF); with PDF as target, all inputs can be **merged into one PDF**
3. Adjust the **quality** — or set a **target size in KB** (JPEG/WebP)
4. Optionally **strip EXIF metadata** or edit individual fields via **"Anzeigen / Bearbeiten"** (view / edit)
5. Optionally enter a new **resolution**, use **"Größe schätzen"** (estimate size) for a forecast
6. Hit **"Konvertieren starten"** (start conversion) — results appear inline, **"📂 Ordner öffnen"** (open folder) takes you to the files

The switch in the top right corner toggles between **system**, **dark**, and **light** mode.

### ⌨️ CLI

```bash
python picconverter_cli.py <inputs...> -f <format> [options]
```

**Examples:**

```bash
# JPG to PNG
python picconverter_cli.py photo.jpg -f png

# Batch: all JPGs to WebP into an output directory
python picconverter_cli.py *.jpg -f webp -q 85 -o output/

# Compress to at most 500 KB (quality is found automatically)
python picconverter_cli.py photo.jpg -f jpg --target-size 500

# Save an image as PDF
python picconverter_cli.py photo.jpg -f pdf

# Export all pages of a PDF as PNG (300 DPI)
python picconverter_cli.py document.pdf -f png --page all --dpi 300

# Merge multiple scans into one multi-page PDF
python picconverter_cli.py scan1.png scan2.png -f pdf --merge -o document.pdf

# Strip or edit EXIF metadata
python picconverter_cli.py photo.jpg -f jpg --strip-exif
python picconverter_cli.py photo.jpg -f jpg --exif-set "Artist=Jane Doe" --exif-set Copyright=

# Size estimate only (without converting)
python picconverter_cli.py image.jpg -f webp -q 85 --estimate
```

**Options:**

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--format` | `-f` | Target format (required) | `-f png` |
| `--output` | `-o` | Output file or directory | `-o image.jpg` |
| `--quality` | `-q` | Quality/compression | `-q 90` |
| `--target-size` | | Target size in KB (JPEG/WebP) | `--target-size 500` |
| `--width` | `-w` | Width in pixels¹ | `-w 1920` |
| `--height` | | Height in pixels¹ | `--height 1080` |
| `--page` | | PDF page or `all` (default: 1) | `--page all` |
| `--dpi` | | PDF render DPI (default: 150) | `--dpi 300` |
| `--merge` | | Everything into one PDF (`-f pdf` only) | `--merge` |
| `--strip-exif` | | Remove EXIF metadata | `--strip-exif` |
| `--exif-set` | | Set/delete an EXIF field | `--exif-set Artist=Me` |
| `--estimate` | | Estimate size only | `--estimate` |

¹ If only one dimension is given, the other is derived preserving the aspect ratio.
**Note:** `-h` is reserved for `--help`, hence `--height` for the height.

**EXIF fields for `--exif-set`:** `ImageDescription`, `Artist`, `Copyright`, `Software`, `DateTime`, `Make`, `Model` — an empty value (`--exif-set Copyright=`) deletes the field.

---

## 📊 Supported formats

| Format | Input | Output | Quality setting | Range |
|--------|-------|--------|-----------------|-------|
| **JPEG** | ✅ | ✅ | Quality | 1–100 |
| **PNG** | ✅ | ✅ | Compression | 0–9 |
| **WebP** | ✅ | ✅ | Quality | 0–100 |
| **BMP** | ✅ | ✅ | – | – |
| **TIFF** | ✅ | ✅ | Compression | 0–9 |
| **GIF** | ✅ | ✅ | – | – |
| **ICO** | ✅ | ✅ | – | – |
| **PDF** | ✅ (requires PyMuPDF) | ✅ | – | – |

- **JPEG/WebP**: higher values = better quality (default: 85 / 80)
- **PNG**: lower values = better quality (default: 6)
- **TIFF**: LZW compression is applied automatically
- **Transparency**: JPEG, BMP, and PDF do not support transparency — it is automatically replaced with white
- **EXIF**: carried over to JPEG, PNG, WebP, and TIFF; the orientation tag is applied on load so portrait photos stay upright

---

## 🛠️ Technical details

| Component | Details |
|-----------|---------|
| **Python version** | 3.9+ |
| **Architecture** | `picconverter_core` (shared logic) + CLI + GUI |
| **Image processing** | Pillow (PIL) |
| **PDF rendering** | PyMuPDF (optional, PDF → image only) |
| **GUI framework** | CustomTkinter |
| **Drag & drop** | tkinterdnd2 (optional) |
| **Tests** | pytest (`pytest tests/`), CI via GitHub Actions |

---

## 🤝 Contributing

Contributions are welcome! Fork the repository, create a feature branch, and open a pull request. Run the tests with `pytest tests/`.

**Feature ideas:** export presets (e.g. "web optimized"), watermarks, full support for animated GIFs/WebPs

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
