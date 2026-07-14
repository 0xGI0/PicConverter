# 🖼️ PicConverter

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-1f538d?style=flat)](https://github.com/TomSchimansky/CustomTkinter)
[![Pillow](https://img.shields.io/badge/Pillow-10.0+-92C83E?style=flat)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ein **Bildkonvertierungs-Tool** für Python mit moderner GUI (CustomTkinter) und CLI für Automatisierung. Konvertiert zwischen allen gängigen Bildformaten, mit Qualitätsregelung, Größenänderung und Größenprognose.

![Screenshot](screenshot.png)

---

## ✨ Features

- **Alle gängigen Bildformate**: JPEG, PNG, BMP, TIFF, GIF, WebP, ICO
- **Moderne Oberfläche**: CustomTkinter mit Dark Mode (Standard) und umschaltbarem Light Mode
- **Drag & Drop**: Bilddateien einfach ins Fenster ziehen
- **Live-Vorschau** und detaillierte Bildinformationen
- **Anpassbare Qualität/Kompression** je nach Zielformat
- **Auflösungsänderung** mit optionalem Erhalt des Seitenverhältnisses
- **Größenprognose** vor der Konvertierung
- **Fortschrittsanzeige und Statusleiste**: Jeder Schritt und jeder Fehler wird sichtbar gemeldet
- **Zwei Modi**: GUI für interaktive Nutzung, CLI für Skripte und Automatisierung

---

## 🚀 Installation

```bash
git clone https://github.com/QG1o/PicConverter.git
cd PicConverter
pip install -r requirements.txt
```

Das installiert:

| Paket | Zweck |
|-------|-------|
| `Pillow` | Bildverarbeitung |
| `customtkinter` | Moderne GUI |
| `tkinterdnd2` | Drag & Drop (optional — die GUI läuft auch ohne) |

**Hinweis (Linux):** tkinter selbst wird über den Paketmanager installiert, falls es fehlt:

```bash
sudo apt-get install python3-tk    # Ubuntu/Debian
sudo dnf install python3-tkinter   # Fedora/RHEL
sudo pacman -S tk                  # Arch Linux
```

---

## 💻 Verwendung

### 🎨 GUI

```bash
python picconverter_gui.py
```

1. Bild **per Drag & Drop** ins Fenster ziehen oder über **„Datei auswählen"** laden
2. **Ausgabeformat** wählen
3. **Qualität/Kompression** anpassen (falls das Format es unterstützt)
4. Optional: neue **Auflösung** eingeben
5. Optional: **„Größe schätzen"** für eine Prognose
6. **„Konvertieren starten"** — Fortschritt und Ergebnis erscheinen direkt in der GUI

Über den Schalter oben rechts lässt sich zwischen **Dunkel** und **Hell** umschalten.

### ⌨️ CLI

```bash
python picconverter_cli.py <eingabedatei> -f <format> [optionen]
```

**Beispiele:**

```bash
# JPG zu PNG
python picconverter_cli.py foto.jpg -f png

# WebP mit 85% Qualität
python picconverter_cli.py bild.png -f webp -q 85

# Auf 1920x1080 skalieren, Ausgabedatei festlegen
python picconverter_cli.py foto.png -f jpg -q 95 -w 1920 --height 1080 -o ergebnis.jpg

# Nur Größenprognose (ohne zu konvertieren)
python picconverter_cli.py bild.jpg -f webp -q 85 --estimate
```

**Optionen:**

| Option | Kürzel | Beschreibung | Beispiel |
|--------|--------|--------------|----------|
| `--format` | `-f` | Zielformat (erforderlich) | `-f png` |
| `--output` | `-o` | Ausgabedatei (optional) | `-o bild.jpg` |
| `--quality` | `-q` | Qualität/Kompression | `-q 90` |
| `--width` | `-w` | Breite in Pixeln | `-w 1920` |
| `--height` | | Höhe in Pixeln | `--height 1080` |
| `--estimate` | | Nur Größe schätzen | `--estimate` |

**Hinweis:** `-h` ist für `--help` reserviert, daher `--height` für die Höhe.

---

## 📊 Unterstützte Formate

| Format | Eingabe | Ausgabe | Qualitätseinstellung | Bereich |
|--------|---------|---------|---------------------|---------|
| **JPEG** | ✅ | ✅ | Qualität | 1–100 |
| **PNG** | ✅ | ✅ | Kompression | 0–9 |
| **WebP** | ✅ | ✅ | Qualität | 0–100 |
| **BMP** | ✅ | ✅ | – | – |
| **TIFF** | ✅ | ✅ | Kompression | 0–9 |
| **GIF** | ✅ | ✅ | – | – |
| **ICO** | ✅ | ✅ | – | – |

- **JPEG/WebP**: Höhere Werte = bessere Qualität (Standard: 85 bzw. 80)
- **PNG**: Niedrigere Werte = bessere Qualität (Standard: 6)
- **TIFF**: LZW-Kompression wird automatisch angewendet
- **Transparenz**: JPEG und BMP unterstützen keine Transparenz — sie wird automatisch durch Weiß ersetzt

---

## 🛠️ Technische Details

| Komponente | Details |
|-----------|---------|
| **Python-Version** | 3.8+ |
| **Bildverarbeitung** | Pillow (PIL) |
| **GUI-Framework** | CustomTkinter |
| **Drag & Drop** | tkinterdnd2 (optional) |
| **Resampling** | LANCZOS (höchste Qualität) |

---

## 🐛 Fehlerbehebung

**`ModuleNotFoundError: No module named 'customtkinter'` (oder `'PIL'`)**

```bash
pip install -r requirements.txt
```

**„ImageTk konnte nicht importiert werden"**

```bash
sudo apt-get install python3-tk   # Ubuntu/Debian
sudo dnf install python3-tkinter  # Fedora/RHEL
# oder: pip install --ignore-installed Pillow
```

**GUI ist zu klein oder zu groß (HiDPI)**

Die Skalierung wird unter Linux automatisch aus der System-DPI erkannt. Falls das Ergebnis nicht passt, lässt sich der Faktor manuell setzen:

```bash
PICCONVERTER_SCALE=1.5 python picconverter_gui.py
```

**Drag & Drop funktioniert nicht**

Die GUI läuft auch ohne — für Drag & Drop `tkinterdnd2` installieren:

```bash
pip install tkinterdnd2
```

---

## 🤝 Beitragen

Beiträge sind willkommen! Fork das Repository, erstelle einen Feature-Branch und öffne einen Pull Request.

**Feature-Ideen:** Batch-Verarbeitung, Export-Presets (z.B. „Web optimiert"), Metadaten-Erhaltung

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
