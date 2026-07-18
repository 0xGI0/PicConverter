<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.png">
    <img src="assets/logo-light.png" alt="PicConverter" width="440">
  </picture>
</p>

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml/badge.svg)](https://github.com/0xGI0/PicConverter/actions/workflows/tests.yml)
[![Qt for Python](https://img.shields.io/badge/GUI-PySide6_(Qt)-2c66a8?style=flat)](https://doc.qt.io/qtforpython-6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🇬🇧 [English version](README.en.md)

Ein **Bild- & PDF-Konvertierungs-Tool** für Python mit moderner GUI (Qt/PySide6) und CLI für Automatisierung. Konvertiert einzelne Dateien oder ganze Stapel zwischen allen gängigen Bildformaten und PDF — mit EXIF-Verwaltung, Zielgrößen-Modus und Größenprognose.

![Screenshot](screenshot.png)

<details>
<summary>📸 Mehr Screenshots</summary>

**EXIF-Editor** — Metadaten ansehen, Felder ändern oder löschen:

![EXIF-Editor](screenshot-exif.png)

</details>

---

## ✨ Features

- **Alle gängigen Bildformate**: JPEG, PNG, BMP, TIFF, GIF, WebP, ICO — plus **HEIC/HEIF und AVIF** als Eingabe (iPhone-Fotos)
- **PDF in beide Richtungen**: Bilder als PDF speichern oder PDF-Seiten als Bild exportieren (Seitenauswahl, alle Seiten, DPI-Wahl)
- **Batch-Verarbeitung**: Warteschlange mit Mini-Vorschauen in der GUI, Globs wie `*.jpg` und parallele Verarbeitung in der CLI
- **Sammel-PDF**: mehrere Bilder (und PDF-Seiten) zu einer mehrseitigen PDF zusammenfassen
- **EXIF-Metadaten**: automatisch korrekte Bildausrichtung, Metadaten wahlweise übernehmen, komplett entfernen oder gezielt bearbeiten (Autor, Copyright, Datum, …)
- **Wasserzeichen**: Text oder Logo-Bild, mit Position und Deckkraft
- **Presets**: mitgeliefert (`web`, `email`, `archiv`) oder eigene speichern — in GUI und CLI
- **Zielgröße statt Qualität**: „max. 500 KB“ angeben — die passende Qualität wird automatisch gesucht (JPEG/WebP)
- **Überschreibschutz**: vorhandene Dateien bleiben erhalten, Ausgaben weichen auf `name (1).ext` aus
- **Animierte GIFs/WebPs** behalten bei GIF↔WebP ihre Animation
- **Anpassbare Qualität/Kompression**, **Auflösungsänderung** mit Seitenverhältnis-Erhalt und **Größenprognose** vor der Konvertierung
- **Moderne Oberfläche**: folgt dem System-Theme (umschaltbar), Live-Vorschau, PDF-Seitennavigation, Ergebnis inline mit „Ordner öffnen“, Einstellungen bleiben zwischen Sitzungen erhalten
- **Zweisprachig**: Deutsch/Englisch — automatisch nach Systemsprache, direkt in der GUI umschaltbar (Auto/DE/EN) oder per `PICCONVERTER_LANG=de|en`
- **Zwei Modi**: GUI für interaktive Nutzung, CLI für Skripte und Automatisierung

---

## 🚀 Installation

**Fertige Programme (ohne Python):** Unter [Releases](https://github.com/0xGI0/PicConverter/releases) liegen Windows-`.exe`- und Linux-Builds zum Direktstart.

**Aus dem Quellcode:**

```bash
git clone https://github.com/0xGI0/PicConverter.git
cd PicConverter
pip install -r requirements.txt
```

Das installiert:

| Paket | Zweck |
|-------|-------|
| `Pillow` | Bildverarbeitung |
| `PySide6` | Moderne GUI (Qt) — Drag & Drop und HiDPI inklusive |
| `PyMuPDF` | PDF → Bild (optional — Bild → PDF geht auch ohne) |
| `pillow-heif` | HEIC/HEIF-Eingabe (optional) |

**Als Paket installieren (optional):** Danach stehen die Befehle `picconverter` und `picconverter-gui` systemweit zur Verfügung:

```bash
pip install .[all]        # oder: pipx install .[all]
```

**Startmenü-Eintrag (Linux, nach Paketinstallation):**

```bash
cp picconverter.desktop ~/.local/share/applications/
mkdir -p ~/.local/share/icons/hicolor/512x512/apps
cp assets/icon.png ~/.local/share/icons/hicolor/512x512/apps/picconverter.png
```

---

## 💻 Verwendung

### 🎨 GUI

```bash
python picconverter_gui.py        # oder: picconverter-gui
```

1. Bilder oder PDFs **per Drag & Drop** ins Fenster ziehen oder über **„Dateien auswählen"** laden — mehrere Dateien bilden eine Warteschlange (mit Mini-Vorschauen und ✕ zum Entfernen), bei PDFs erscheint eine **Seitennavigation**
2. Optional ein **Preset** wählen oder die aktuellen Einstellungen als eigenes Preset **speichern**
3. **Ausgabeformat** wählen (inkl. PDF); bei Zielformat PDF lassen sich alle Eingaben zu **einer PDF zusammenfassen**
4. **Qualität** anpassen — oder eine **Zielgröße in KB** festlegen (JPEG/WebP)
5. Optional: **Wasserzeichen**-Text mit Position und Deckkraft, neue **Auflösung**, **„Größe schätzen"** für eine Prognose
6. **EXIF-Metadaten** wahlweise entfernen oder über **„Anzeigen / Bearbeiten"** einzelne Felder ändern
7. **„Konvertieren starten"** — das Ergebnis erscheint direkt in der Oberfläche, **„📂 Ordner öffnen"** führt zu den Dateien; vorhandene Dateien werden nicht überschrieben (abschaltbar)

Über den Schalter oben rechts lässt sich zwischen **System**, **Dunkel** und **Hell** umschalten. Alle Einstellungen bleiben für den nächsten Start erhalten.

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

# Preset anwenden bzw. eigene speichern
python picconverter_cli.py foto.jpg --preset web
python picconverter_cli.py --save-preset klein -f jpg -q 40 -w 1280

# Wasserzeichen (Text oder Logo)
python picconverter_cli.py foto.jpg -f jpg --watermark-text "© 2026" --watermark-pos unten-links
python picconverter_cli.py foto.jpg -f png --watermark-image logo.png --watermark-opacity 30

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
| `--watermark-text` | | Text-Wasserzeichen | `--watermark-text "© 2026"` |
| `--watermark-image` | | Logo-Wasserzeichen | `--watermark-image logo.png` |
| `--watermark-pos` | | Position (Standard: unten-rechts) | `--watermark-pos mitte` |
| `--watermark-opacity` | | Deckkraft in % (Standard: 50) | `--watermark-opacity 30` |
| `--preset` | | Preset anwenden | `--preset web` |
| `--save-preset` | | Optionen als Preset speichern | `--save-preset klein` |
| `--overwrite` | | Vorhandene Dateien ersetzen | `--overwrite` |
| `--jobs` | | Parallele Konvertierungen | `--jobs 8` |
| `--estimate` | | Nur Größe schätzen | `--estimate` |
| `--quiet` | | Nur Fehler ausgeben | `--quiet` |
| `--version` | | Version anzeigen | `--version` |

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
| **HEIC/HEIF** | ✅ (benötigt pillow-heif) | – | – | – |
| **AVIF** | ✅ (Pillow ≥ 11) | – | – | – |

- **JPEG/WebP**: Höhere Werte = bessere Qualität (Standard: 85 bzw. 80)
- **PNG**: Niedrigere Werte = bessere Qualität (Standard: 6)
- **TIFF**: LZW-Kompression wird automatisch angewendet
- **Transparenz**: JPEG, BMP und PDF unterstützen keine Transparenz — sie wird automatisch durch Weiß ersetzt
- **EXIF**: wird in JPEG, PNG, WebP und TIFF übernommen; die Bildausrichtung (Orientation) wird beim Laden eingerechnet, damit Hochkant-Fotos korrekt bleiben
- **Animation**: GIF↔WebP behält alle Frames; bei anderen Zielformaten wird das erste Frame verwendet (mit Hinweis)

---

## 🛠️ Technische Details

| Komponente | Details |
|-----------|---------|
| **Python-Version** | 3.9+ |
| **Architektur** | `picconverter_core` (gemeinsame Logik) + CLI + GUI + `picconverter_i18n` |
| **Bildverarbeitung** | Pillow (PIL) |
| **PDF-Rendering** | PyMuPDF (optional, nur für PDF → Bild) |
| **HEIC/HEIF** | pillow-heif (optional) |
| **GUI-Framework** | PySide6 (Qt 6) — natives Wayland, Drag & Drop und Per-Monitor-HiDPI inklusive |
| **Konfiguration** | `~/.config/picconverter/` (Presets, GUI-Einstellungen) |
| **Tests & Lint** | pytest + ruff, CI via GitHub Actions |
| **Releases** | PyInstaller-Binaries (Windows/Linux) per Git-Tag |

---

## 🐛 Fehlerbehebung

**`ModuleNotFoundError: No module named 'PySide6'` (oder `'PIL'`)**

```bash
pip install -r requirements.txt
```

**GUI ist zu klein oder zu groß (HiDPI)**

Qt erkennt die Display-Skalierung selbst (unter Wayland sogar pro Monitor). Falls das Ergebnis nicht passt, lässt sich der Faktor manuell setzen:

```bash
PICCONVERTER_SCALE=1.5 python picconverter_gui.py
```

**„PDF-Eingabe benötigt PyMuPDF"**

PDF → Bild braucht den PDF-Renderer PyMuPDF (Bild → PDF geht auch ohne):

```bash
pip install pymupdf
```

**HEIC-Dateien werden nicht erkannt**

```bash
pip install pillow-heif
```

**Falsche Sprache**

Die Oberfläche folgt der Systemsprache; erzwingen lässt sie sich mit:

```bash
PICCONVERTER_LANG=de picconverter-gui   # oder =en
```

---

## 🤝 Beitragen

Beiträge sind willkommen! Fork das Repository, erstelle einen Feature-Branch und öffne einen Pull Request. Tests laufen mit `pytest tests/`.

**Feature-Ideen:** SVG-Eingabe, passwortgeschützte PDFs, Konvertierungs-Verlauf, weitere Sprachen

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
