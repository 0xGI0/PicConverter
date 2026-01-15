# 🖼️ PicConverter

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Pillow](https://img.shields.io/badge/Pillow-10.0+-92C83E?style=flat)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ein vielseitiges **Bildkonvertierungs-Tool** für Python mit zwei Benutzeroberflächen: CLI für Automatisierung und GUI für einfache Bedienung.

---

## ✨ Features

- ✅ **Alle gängigen Bildformate**: JPEG, PNG, BMP, TIFF, GIF, WebP, ICO
- ✅ **Anpassbare Qualität/Kompression**: Optimieren Sie die Dateigröße nach Ihren Bedürfnissen
- ✅ **Auflösungsänderung**: Passen Sie die Bildgröße präzise an
- ✅ **Größenprognose**: Sehen Sie die geschätzte Ausgabegröße vor der Konvertierung
- ✅ **Modernes dunkles Design**: Angenehme GUI mit Card-basiertem Layout
- ✅ **Zwei Modi**: CLI für Skripte/Automatisierung, GUI für interaktive Nutzung
- ✅ **Bildvorschau**: Sehen Sie Ihr Bild vor der Konvertierung (nur GUI)
- ✅ **Seitenverhältnis**: Optional beibehalten bei Größenänderung

---

## 📋 Voraussetzungen

- **Python 3.7+**
- **Pillow** (Bildverarbeitung)
- **tkinter** (für GUI - meist bereits in Python enthalten)

---

## 🚀 Installation

### 1. Repository klonen

```bash
git clone https://github.com/QG1o/PicConverter.git
cd PicConverter
```

### 2. Pillow installieren

```bash
pip install Pillow
```

### 3. tkinter installieren (falls nicht vorhanden)

**tkinter ist normalerweise bereits in Python enthalten!** Falls es fehlt:

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

**macOS/Windows:**
- Bereits in Python enthalten ✓

---

## 💻 Verwendung

### 🎨 GUI-Version (Grafische Oberfläche)

**Starten:**
```bash
python picconverter_gui.py
```

**Bedienung:**
1. ✅ Klicken Sie auf **"Datei auswählen"** und wählen Sie ein Bild
2. ✅ Wählen Sie das gewünschte **Ausgabeformat**
3. ✅ Passen Sie **Qualität/Kompression** an (falls verfügbar)
4. ✅ Optional: Geben Sie neue **Auflösung** ein
5. ✅ Klicken Sie auf **"Größe schätzen"** für eine Prognose
6. ✅ Klicken Sie auf **"🚀 Konvertieren starten"**

**Design-Highlights:**
- 🎨 Modernes dunkles Theme
- 📱 Card-basiertes Interface
- 👁️ Live-Bildvorschau
- 📊 Detaillierte Bildinformationen
- ⚡ Intuitive Bedienung

---

### ⌨️ CLI-Version (Kommandozeile)

**Grundlegende Syntax:**
```bash
python picconverter_cli.py <eingabedatei> -f <format> [optionen]
```

#### 📚 Beispiele:

**Einfache Konvertierung:**
```bash
# JPG zu PNG
python picconverter_cli.py foto.jpg -f png

# PNG zu WebP
python picconverter_cli.py bild.png -f webp
```

**Mit Qualitätseinstellung:**
```bash
# JPEG mit 90% Qualität
python picconverter_cli.py foto.jpg -f jpg -q 90

# WebP mit 85% Qualität
python picconverter_cli.py bild.png -f webp -q 85
```

**Mit Auflösungsänderung:**
```bash
# Auf 1920x1080 skalieren
python picconverter_cli.py bild.jpg -f png -w 1920 --height 1080

# Nur Breite angeben (Höhe wird berechnet)
python picconverter_cli.py foto.jpg -f jpg -w 800
```

**Nur Größenprognose (ohne zu konvertieren):**
```bash
python picconverter_cli.py bild.jpg -f webp -q 85 --estimate
```

**Ausgabedatei festlegen:**
```bash
python picconverter_cli.py input.png -f jpg -q 90 -o mein_output.jpg
```

**Alles kombiniert:**
```bash
python picconverter_cli.py foto.png -f jpg -q 95 -w 1920 --height 1080 -o ergebnis.jpg
```

#### ⚙️ Verfügbare Optionen:

| Option | Kürzel | Beschreibung | Beispiel |
|--------|--------|--------------|----------|
| `--format` | `-f` | Zielformat (erforderlich) | `-f png` |
| `--output` | `-o` | Ausgabedatei (optional) | `-o bild.jpg` |
| `--quality` | `-q` | Qualität/Kompression | `-q 90` |
| `--width` | `-w` | Breite in Pixeln | `-w 1920` |
| `--height` | | Höhe in Pixeln | `--height 1080` |
| `--estimate` | | Nur Größe schätzen | `--estimate` |

**Hinweis:** `-h` ist für `--help` reserviert, daher verwenden wir `--height` für die Höhe.

---

## 📊 Unterstützte Formate

| Format | Eingabe | Ausgabe | Qualitätseinstellung | Bereich |
|--------|---------|---------|---------------------|---------|
| **JPEG** | ✅ | ✅ | Qualität | 1-100 |
| **PNG** | ✅ | ✅ | Kompression | 0-9 |
| **WebP** | ✅ | ✅ | Qualität | 0-100 |
| **BMP** | ✅ | ✅ | - | - |
| **TIFF** | ✅ | ✅ | Kompression | 0-9 |
| **GIF** | ✅ | ✅ | - | - |
| **ICO** | ✅ | ✅ | - | - |

### 📝 Qualitätshinweise:

- **JPEG/WebP**: Höhere Werte = bessere Qualität (Standard: 85)
- **PNG**: Niedrigere Werte = bessere Qualität (Standard: 6)
- **TIFF**: LZW-Kompression wird automatisch angewendet

---

## 🛠️ Technische Details

| Komponente | Details |
|-----------|---------|
| **Python-Version** | 3.7+ |
| **Hauptbibliothek** | Pillow (PIL) |
| **GUI-Framework** | tkinter |
| **Resampling-Methode** | LANCZOS (höchste Qualität) |
| **Transparenz** | Automatische Konvertierung für JPEG/BMP |

---

## 🎯 Anwendungsfälle

**Perfekt für:**
- 📸 Batch-Konvertierung von Fotos
- 🖼️ Web-Optimierung (PNG → WebP)
- 📱 Größenanpassung für Social Media
- 💾 Komprimierung großer Bildsammlungen
- 🔄 Format-Konvertierung für Kompatibilität
- 📊 Automatisierung in Python-Skripten

---

## 🐛 Fehlerbehebung

### Problem: "ImageTk konnte nicht importiert werden"

**Lösung:**
```bash
# tkinter nachinstallieren (Linux)
sudo apt-get install python3-tk  # Ubuntu/Debian
sudo dnf install python3-tkinter  # Fedora/RHEL
```

### Problem: "ModuleNotFoundError: No module named 'PIL'"

**Lösung:**
```bash
pip install Pillow
```

### Problem: Transparenz wird schwarz dargestellt

**Erklärung:** JPEG und BMP unterstützen keine Transparenz. PicConverter konvertiert transparent automatisch zu weiß.

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

Die MIT-Lizenz erlaubt:
- ✅ Kommerzielle Nutzung
- ✅ Modifikation
- ✅ Verteilung
- ✅ Private Nutzung

---

## 🤝 Beitragen

Beiträge sind willkommen! 

**So kannst du helfen:**
1. 🍴 Fork das Repository
2. 🌿 Erstelle einen Feature-Branch (`git checkout -b feature/NeuesFeature`)
3. ✅ Committe deine Änderungen (`git commit -m 'Neues Feature hinzugefügt'`)
4. 📤 Push zum Branch (`git push origin feature/NeuesFeature`)
5. 🔃 Öffne einen Pull Request

**Feature-Ideen:**
- Batch-Verarbeitung mehrerer Dateien
- Zusätzliche Filter und Effekte
- Export-Presets (z.B. "Web optimiert")
- Metadaten-Erhaltung

---

## 💡 Tipps & Tricks

**Optimale Einstellungen für:**

| Zweck | Format | Qualität | Empfehlung |
|-------|--------|----------|------------|
| Web (klein) | WebP | 75-85 | Beste Balance |
| Web (Standard) | JPEG | 85-90 | Gute Qualität |
| Druck | PNG/TIFF | 9 | Verlustfrei |
| Archivierung | PNG | 6-9 | Verlustfrei |
| Social Media | JPEG | 90-95 | Hohe Qualität |

---

## 👨‍💻 Autor

Erstellt mit ❤️ für die Open-Source-Community

---

## ⭐ Star dieses Repo!

Wenn dir PicConverter gefällt, gib dem Projekt einen Stern! ⭐
