# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/), die
Versionierung [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert
- **GUI von CustomTkinter auf PySide6 (Qt 6) portiert** — komplett neues,
  flaches Design mit eigenem hellen/dunklen Theme (folgt weiterhin dem
  System), Logo-Wortmarke im Header, dezente Sektionstitel statt Emojis,
  ein einheitlicher Azur-Akzent
- Drag & Drop jetzt nativ über Qt (tkinterdnd2 entfällt), native
  Dateidialoge (KDE/GNOME-Portale)
- HiDPI-Skalierung übernimmt Qt automatisch — unter Wayland pro Monitor;
  die manuelle DPI-Erkennung (`detect_ui_scale`) entfällt,
  `PICCONVERTER_SCALE` funktioniert weiterhin als Override
- Abhängigkeiten: `customtkinter` und `tkinterdnd2` ersetzt durch `PySide6`

## [2.0.0] - 2026-07-18

### Hinzugefügt
- **PDF-Unterstützung in beide Richtungen**: Bilder als PDF speichern,
  PDF-Seiten als Bild exportieren (Seitenauswahl, `--page all`, DPI-Wahl)
- **Batch-Verarbeitung**: mehrere Dateien/Globs in der CLI, Warteschlange
  mit Dateiliste, Mini-Vorschauen und Einzel-Entfernen in der GUI
- **Sammel-PDF** (`--merge`): mehrere Bilder und PDF-Seiten zu einer
  mehrseitigen PDF zusammenfassen
- **EXIF-Verwaltung**: Metadaten behalten (Standard), komplett entfernen
  (`--strip-exif`) oder gezielt bearbeiten (`--exif-set`, GUI-Editor)
- **HEIC/HEIF- und AVIF-Eingabe** (optional via pillow-heif; iPhone-Fotos)
- **Zielgröße statt Qualität** (`--target-size`): automatische Qualitätssuche
- **Wasserzeichen**: Text (GUI + CLI) oder Logo-Bild (CLI) mit Position
  und Deckkraft
- **Presets**: mitgeliefert (`web`, `email`, `archiv`) und selbst speicherbar
  (`--preset`, `--save-preset`, GUI-Dropdown)
- **Überschreibschutz**: Ausgaben weichen auf `name (1).ext` aus
  (`--overwrite` zum bewussten Ersetzen)
- **Animierte GIFs/WebPs** behalten ihre Frames bei GIF↔WebP-Konvertierung
- **Parallele Batch-Konvertierung** in der CLI (`--jobs`)
- **Zweisprachige Oberfläche** (Deutsch/Englisch, automatisch nach
  Systemsprache, Override: `PICCONVERTER_LANG`)
- GUI merkt sich die Einstellungen zwischen Sitzungen; Ergebnis inline
  mit „Ordner öffnen“ statt Popups; System/Dunkel/Hell-Theme
- `--version`, `--quiet`; App-Icon; `.desktop`-Datei
- Packaging via `pyproject.toml` (`picconverter`, `picconverter-gui`)
- Testsuite (pytest), CI mit Lint (ruff) und Tests, Release-Workflow mit
  Windows-/Linux-Binaries (PyInstaller), Dependabot

### Behoben
- EXIF-Orientierung wird beim Laden eingerechnet — Hochkant-Fotos wurden
  bisher liegend gespeichert
- Größenschätzung schlug bei transparenten Bildern für JPEG/BMP fehl

### Geändert
- Gemeinsame Logik von CLI und GUI in `picconverter_core.py` zusammengeführt
- GUI von Tkinter/ttk auf CustomTkinter migriert (bereits Juli 2026)

## [1.0.0] - 2025-06-17

- Erste Version: Bildkonvertierung (JPEG, PNG, BMP, TIFF, GIF, WebP, ICO)
  mit Tkinter-GUI und CLI, Qualitätsregelung, Auflösungsänderung,
  Größenprognose
