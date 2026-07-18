# 🖼️ PicConverter

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml/badge.svg)](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-1f538d?style=flat)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🇬🇧 [English version](README.en.md)

Ein **Bild- & PDF-Konvertierungs-Tool** für Python mit moderner GUI (CustomTkinter) und CLI für Automatisierung. Konvertiert einzelne Dateien oder ganze Stapel zwischen allen gängigen Bildformaten und PDF — mit EXIF-Verwaltung, Zielgrößen-Modus und Größenprognose.

![Screenshot](screenshot.png)

---

## ✨ Features

- **Alle gängigen Bildformate**: JPEG, PNG, BMP, TIFF, GIF, WebP, ICO
- **PDF in beide Richtungen**: Bilder als PDF speichern oder PDF-Seiten als Bild exportieren (Seitenauswahl, alle Seiten, DPI-Wahl)
- **Batch-Verarbeitung**: mehrere Dateien per Drag & Drop in die Warteschlange bzw. Globs wie `*.jpg` in der CLI
- **Sammel-PDF**: mehrere Bilder (und PDF-Seiten) zu einer mehrseitigen PDF zusammenfassen
- **EXIF-Metadaten**: automatisch korrekte Bildausrichtung, Metadaten wahlweise übernehmen, komplett entfernen oder gezielt bearbeiten (Autor, Copyright, Datum, …)
- **Zielgröße statt Qualität**: „max. 500 KB“ angeben — die passende Qualität wird automatisch gesucht (JPEG/WebP)
- **Anpassbare Qualität/Kompression**, **Auflösungsänderung** mit Seitenverhältnis-Erhalt und **Größenprognose** vor der Konvertierung
- **Moderne Oberfläche**: folgt dem System-Theme (umschaltbar auf Dunkel/Hell), Live-Vorschau, PDF-Seitennavigation, Ergebnis direkt in der Oberfläche mit „Ordner öffnen“
- **Zwei Modi**: GUI für interaktive Nutzung, CLI für Skripte und Automatisierung

---

## 🚀 Installation

```bash
git clone https://github.com/0xGI0/PicConverter.git
cd PicConverter
pip install -r requirements.txt
```

Das installiert:

| Paket | Zweck |
|-------|-------|
| `Pillow` | Bildverarbeitung |
| `customtkinter` | Moderne GUI |
| `tkinterdnd2` | Drag & Drop (optional — die GUI läuft auch ohne) |
| `PyMuPDF` | PDF → Bild (optional — Bild → PDF geht auch ohne) |

**Als Paket installieren (optional):** Danach stehen die Befehle `picconverter` und `picconverter-gui` systemweit zur Verfügung:

```bash
pip install .[all]        # oder: pipx install .[all]
```

**Startmenü-Eintrag (Linux, nach Paketinstallation):**

```bash
cp picconverter.desktop ~/.local/share/applications/
```

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
python picconverter_gui.py        # oder: picconverter-gui
```

1. Bilder oder PDFs **per Drag & Drop** ins Fenster ziehen oder über **„Dateien auswählen"** laden — mehrere Dateien bilden eine Warteschlange, bei PDFs erscheint eine **Seitennavigation**
2. **Ausgabeformat** wählen (inkl. PDF); bei Zielformat PDF lassen sich alle Eingaben zu **einer PDF zusammenfassen**
3. **Qualität** anpassen — oder eine **Zielgröße in KB** festlegen (JPEG/WebP)
4. **EXIF-Metadaten** wahlweise entfernen oder über **„Anzeigen / Bearbeiten"** einzelne Felder ändern
5. Optional: neue **Auflösung** eingeben, **„Größe schätzen"** für eine Prognose
6. **„Konvertieren starten"** — das Ergebnis erscheint direkt in der Oberfläche, **„📂 Ordner öffnen"** führt zu den Dateien

Über den Schalter oben rechts lässt sich zwischen **System**, **Dunkel** und **Hell** umschalten.

### ⌨️ CLI

```bash
python picconverter_cli.py <eingaben...> -f <format> [optionen]
```

**Beispiele:**

```bash
# JPG zu PNG
python picconverter_cli.py foto.jpg -f png

# Batch: alle JPGs zu WebP in einen Ausgabeordner
python picconverter_cli.py *.jpg -f webp -q 85 -o ausgabe/

# Auf maximal 500 KB komprimieren (Qualität wird automatisch gesucht)
python picconverter_cli.py foto.jpg -f jpg --target-size 500

# Bild als PDF speichern
python picconverter_cli.py foto.jpg -f pdf

# Alle Seiten einer PDF als PNG exportieren (300 DPI)
python picconverter_cli.py dokument.pdf -f png --page all --dpi 300

# Mehrere Scans zu einer mehrseitigen PDF zusammenfassen
python picconverter_cli.py scan1.png scan2.png -f pdf --merge -o dokument.pdf

# EXIF-Metadaten entfernen bzw. bearbeiten
python picconverter_cli.py foto.jpg -f jpg --strip-exif
python picconverter_cli.py foto.jpg -f jpg --exif-set "Artist=Max Mustermann" --exif-set Copyright=

# Nur Größenprognose (ohne zu konvertieren)
python picconverter_cli.py bild.jpg -f webp -q 85 --estimate
```

**Optionen:**

| Option | Kürzel | Beschreibung | Beispiel |
|--------|--------|--------------|----------|
| `--format` | `-f` | Zielformat (erforderlich) | `-f png` |
| `--output` | `-o` | Ausgabedatei oder -ordner | `-o bild.jpg` |
| `--quality` | `-q` | Qualität/Kompression | `-q 90` |
| `--target-size` | | Zielgröße in KB (JPEG/WebP) | `--target-size 500` |
| `--width` | `-w` | Breite in Pixeln¹ | `-w 1920` |
| `--height` | | Höhe in Pixeln¹ | `--height 1080` |
| `--page` | | PDF-Seite oder `all` (Standard: 1) | `--page all` |
| `--dpi` | | PDF-Render-DPI (Standard: 150) | `--dpi 300` |
| `--merge` | | Alles in eine PDF (nur `-f pdf`) | `--merge` |
| `--strip-exif` | | EXIF-Metadaten entfernen | `--strip-exif` |
| `--exif-set` | | EXIF-Feld setzen/löschen | `--exif-set Artist=Ich` |
| `--estimate` | | Nur Größe schätzen | `--estimate` |

¹ Wird nur eine Dimension angegeben, wird die andere seitenverhältnistreu ergänzt.
**Hinweis:** `-h` ist für `--help` reserviert, daher `--height` für die Höhe.

**EXIF-Felder für `--exif-set`:** `ImageDescription`, `Artist`, `Copyright`, `Software`, `DateTime`, `Make`, `Model` — ein leerer Wert (`--exif-set Copyright=`) löscht das Feld.

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
| **PDF** | ✅ (benötigt PyMuPDF) | ✅ | – | – |

- **JPEG/WebP**: Höhere Werte = bessere Qualität (Standard: 85 bzw. 80)
- **PNG**: Niedrigere Werte = bessere Qualität (Standard: 6)
- **TIFF**: LZW-Kompression wird automatisch angewendet
- **Transparenz**: JPEG, BMP und PDF unterstützen keine Transparenz — sie wird automatisch durch Weiß ersetzt
- **EXIF**: wird in JPEG, PNG, WebP und TIFF übernommen; die Bildausrichtung (Orientation) wird beim Laden eingerechnet, damit Hochkant-Fotos korrekt bleiben

---

## 🛠️ Technische Details

| Komponente | Details |
|-----------|---------|
| **Python-Version** | 3.9+ |
| **Architektur** | `picconverter_core` (gemeinsame Logik) + CLI + GUI |
| **Bildverarbeitung** | Pillow (PIL) |
| **PDF-Rendering** | PyMuPDF (optional, nur für PDF → Bild) |
| **GUI-Framework** | CustomTkinter |
| **Drag & Drop** | tkinterdnd2 (optional) |
| **Tests** | pytest (`pytest tests/`), CI via GitHub Actions |

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

**„PDF-Eingabe benötigt PyMuPDF"**

PDF → Bild braucht den PDF-Renderer PyMuPDF (Bild → PDF geht auch ohne):

```bash
pip install pymupdf
```

---

## 🤝 Beitragen

Beiträge sind willkommen! Fork das Repository, erstelle einen Feature-Branch und öffne einen Pull Request. Tests laufen mit `pytest tests/`.

**Feature-Ideen:** Export-Presets (z.B. „Web optimiert"), Wasserzeichen, animierte GIFs/WebPs vollständig übernehmen

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
