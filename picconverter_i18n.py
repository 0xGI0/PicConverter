#!/usr/bin/env python3
"""
PicConverter i18n - einfache Übersetzungsschicht.

Deutsch ist die Ausgangssprache (alle Strings im Code sind deutsch);
für andere Sprachen wird über TRANSLATIONS nachgeschlagen. Fehlt ein
Eintrag, bleibt der deutsche Text stehen. Platzhalter ({name}, {size:.2f}, …)
müssen in der Übersetzung identisch erhalten bleiben.

Sprachwahl: Umgebungsvariable PICCONVERTER_LANG (de/en), sonst Systemsprache.
"""

import locale
import os

TRANSLATIONS = {
    'en': {
        # ---------- Core ----------
        "{kind}-Eingabe benötigt PyMuPDF. Installation: pip install pymupdf":
            "{kind} input requires PyMuPDF. Install it with: pip install pymupdf",
        "Seite {page} existiert nicht — die PDF hat {count} Seite(n)":
            "Page {page} does not exist — the PDF has {count} page(s)",
        "SVG konnte nicht gelesen werden: {name}":
            "Could not read SVG: {name}",
        "Unbekanntes EXIF-Feld '{name}'. Verfügbar: {valid}":
            "Unknown EXIF field '{name}'. Available: {valid}",
        "Keine Bilder zum Zusammenfassen übergeben":
            "No images given to merge",
        "Zielgröße wird nur für {formats} unterstützt":
            "Target size is only supported for {formats}",

        # ---------- CLI ----------
        'PicConverter CLI - Konvertiert Bilder und PDFs zwischen Formaten':
            'PicConverter CLI - Converts images and PDFs between formats',
        """
Unterstützte Formate: {formats}
Nur als Eingabe: {input_only}
EXIF-Felder für --exif-set: {exif_fields}
Presets: {presets}

Beispiele:
  %(prog)s bild.jpg -f png -o ausgabe.png
  %(prog)s *.jpg -f webp -q 85                      # Batch
  %(prog)s foto.jpg -f jpg --target-size 500        # max. 500 KB
  %(prog)s dokument.pdf -f png --page all --dpi 300 # alle Seiten
  %(prog)s logo.svg -f png --svg-width 1024         # SVG rastern
  %(prog)s scan1.png scan2.png -f pdf --merge -o dokument.pdf
  %(prog)s foto.jpg --preset web                    # Preset anwenden
  %(prog)s foto.jpg -f jpg --strip-exif             # Metadaten entfernen
  %(prog)s foto.jpg -f jpg --watermark-text "© 2026"
        """:
            """
Supported formats: {formats}
Input only: {input_only}
EXIF fields for --exif-set: {exif_fields}
Presets: {presets}

Examples:
  %(prog)s image.jpg -f png -o output.png
  %(prog)s *.jpg -f webp -q 85                      # batch
  %(prog)s photo.jpg -f jpg --target-size 500       # max. 500 KB
  %(prog)s document.pdf -f png --page all --dpi 300 # all pages
  %(prog)s logo.svg -f png --svg-width 1024         # rasterize SVG
  %(prog)s scan1.png scan2.png -f pdf --merge -o document.pdf
  %(prog)s photo.jpg --preset web                   # apply a preset
  %(prog)s photo.jpg -f jpg --strip-exif            # remove metadata
  %(prog)s photo.jpg -f jpg --watermark-text "© 2026"
        """,
        'EINGABE': 'INPUT',
        'Eingabedateien (auch mehrere oder Glob-Muster wie *.jpg)':
            'Input files (multiple files or glob patterns like *.jpg)',
        'Zielformat für die Konvertierung':
            'Target format for the conversion',
        'Ausgabedatei (bei einer Eingabe) oder Ausgabeordner (bei mehreren)':
            'Output file (single input) or output directory (multiple inputs)',
        'Qualität/Kompression (JPEG/WebP: 1-100, PNG: 0-9)':
            'Quality/compression (JPEG/WebP: 1-100, PNG: 0-9)',
        'Zielgröße in KB — sucht die passende Qualität (nur JPEG/WebP)':
            'Target size in KB — finds the matching quality (JPEG/WebP only)',
        'Breite in Pixeln (Höhe wird ggf. seitenverhältnistreu ergänzt)':
            'Width in pixels (height is derived preserving the aspect ratio)',
        'Höhe in Pixeln (Breite wird ggf. seitenverhältnistreu ergänzt)':
            'Height in pixels (width is derived preserving the aspect ratio)',
        'Zeigt geschätzte Ausgabegröße ohne zu konvertieren':
            'Show the estimated output size without converting',
        "PDF-Eingabe: Seitennummer oder 'all' für alle Seiten (Standard: 1)":
            "PDF input: page number or 'all' for every page (default: 1)",
        'PDF-/SVG-Eingabe: Render-Auflösung in DPI (Standard: {dpi})':
            'PDF/SVG input: render resolution in DPI (default: {dpi})',
        'SVG-Eingabe: auf genau diese Pixelbreite rendern (hat Vorrang vor --dpi)':
            'SVG input: render at exactly this pixel width (takes precedence over --dpi)',
        "--svg-width muss größer als 0 sein":
            "--svg-width must be greater than 0",
        'Alle Eingaben in eine mehrseitige PDF zusammenfassen (nur -f pdf)':
            'Merge all inputs into one multi-page PDF (only with -f pdf)',
        'EXIF-Metadaten nicht in die Ausgabe übernehmen':
            'Do not carry EXIF metadata over to the output',
        'FELD=WERT': 'FIELD=VALUE',
        'EXIF-Feld setzen (leerer Wert löscht das Feld); mehrfach nutzbar':
            'Set an EXIF field (an empty value deletes it); repeatable',
        'TEXT': 'TEXT',
        'Text-Wasserzeichen einfügen':
            'Add a text watermark',
        'DATEI': 'FILE',
        'Bild-Wasserzeichen (z.B. Logo mit Transparenz) einfügen':
            'Add an image watermark (e.g. a logo with transparency)',
        'Position des Wasserzeichens (Standard: unten-rechts)':
            'Watermark position (default: unten-rechts)',
        'Deckkraft des Wasserzeichens in Prozent (Standard: 50)':
            'Watermark opacity in percent (default: 50)',
        'NAME': 'NAME',
        'Preset anwenden (explizite Optionen haben Vorrang)':
            'Apply a preset (explicit options take precedence)',
        'Aktuelle Optionen als Preset speichern':
            'Save the current options as a preset',
        'Vorhandene Dateien überschreiben statt auf "name (1).ext" auszuweichen':
            'Overwrite existing files instead of falling back to "name (1).ext"',
        'Anzahl paralleler Konvertierungen (Standard: automatisch)':
            'Number of parallel conversions (default: automatic)',
        'Nur Fehler ausgeben':
            'Only print errors',
        "Ungültiges Argument '{pair}' — erwartet wird FELD=WERT":
            "Invalid argument '{pair}' — expected FIELD=VALUE",
        "Datei '{pattern}' existiert nicht":
            "File '{pattern}' does not exist",
        "Unbekanntes Preset '{name}'. Verfügbar: {valid}":
            "Unknown preset '{name}'. Available: {valid}",
        "Wasserzeichen-Bild '{path}' existiert nicht":
            "Watermark image '{path}' does not exist",
        "✓ Preset '{name}' gespeichert":
            "✓ Preset '{name}' saved",
        "Keine Eingabedateien angegeben":
            "No input files given",
        "Kein Zielformat: -f angeben oder ein Preset mit Format wählen":
            "No target format: pass -f or choose a preset that sets one",
        "--page erwartet eine Seitennummer >= 1 oder 'all', nicht '{value}'":
            "--page expects a page number >= 1 or 'all', not '{value}'",
        "--quality und --target-size schließen sich gegenseitig aus":
            "--quality and --target-size are mutually exclusive",
        "--target-size wird nur für {formats} unterstützt":
            "--target-size is only supported for {formats}",
        "--merge funktioniert nur mit -f pdf":
            "--merge only works with -f pdf",
        "Fehler: {error}": "Error: {error}",
        "Warnung: Qualität {value} außerhalb des Bereichs [{min}-{max}]. "
        "Verwende Standardwert.":
            "Warning: quality {value} outside the range [{min}-{max}]. "
            "Using the default value.",
        "✓ {count} Seite(n) zusammengefasst in: {out} ({size:.2f} MB)":
            "✓ {count} page(s) merged into: {out} ({size:.2f} MB)",
        "✗ Fehler beim Zusammenfassen: {error}":
            "✗ Merge failed: {error}",
        'Seite': 'page',
        " [Zielgröße {kb} KB → Qualität {q}]":
            " [target size {kb} KB → quality {q}]",
        "~ {label}: geschätzt {est:.2f} MB (Original: {orig:.2f} MB)":
            "~ {label}: estimated {est:.2f} MB (original: {orig:.2f} MB)",
        " [Hinweis: Animation geht in diesem Format verloren]":
            " [note: the animation is lost in this format]",
        "\nNur Schätzung angefordert. Keine Konvertierung durchgeführt.":
            "\nEstimate only. No conversion performed.",
        "\n{failed} von {total} Auftrag/Aufträgen fehlgeschlagen.":
            "\n{failed} of {total} job(s) failed.",

        # ---------- GUI: Fenster & Karten ----------
        "PicConverter - Bild- & PDF-Konverter":
            "PicConverter - Image & PDF Converter",
        "Moderner Bild- & PDF-Konverter":
            "Modern image & PDF converter",
        "System": "System",
        "Dunkel": "Dark",
        "Hell": "Light",
        "Eingabedateien": "Input files",
        "Bilder oder PDFs hierher ziehen\noder klicken zum Auswählen":
            "Drag images or PDFs here\nor click to select",
        "Klicken, um Bilder oder PDFs auszuwählen":
            "Click to select images or PDFs",
        "Keine Dateien ausgewählt": "No files selected",
        "Dateien auswählen": "Select files",
        "Leeren": "Clear",
        "PDF-Seite": "PDF page",
        "von {n}": "of {n}",
        "Alle Seiten exportieren": "Export all pages",
        "Vorschau": "Preview",
        "Warteschlange": "Queue",
        "Sprache geändert": "Language changed",
        "… oder einfach ins Fenster ziehen": "… or simply drag them into the window",
        "Qualität wird automatisch gesucht": "Quality is searched automatically",
        "Vorhandene Dateien überschreiben": "Overwrite existing files",
        "Kein Bild geladen": "No image loaded",
        "Bildinformationen": "Image information",
        "Konvertierungseinstellungen": "Conversion settings",
        "Preset": "Preset",
        "(keins)": "(none)",
        "Speichern": "Save",
        "Ausgabeformat": "Output format",
        "Alle Eingaben in eine PDF zusammenfassen":
            "Merge all inputs into one PDF",
        "Qualität": "Quality",
        "Kompression": "Compression",
        "Zielgröße:": "Target size:",
        "KB (Qualität wird automatisch gesucht)":
            "KB (quality is found automatically)",
        "Auflösung": "Resolution",
        "Seitenverhältnis beibehalten": "Preserve aspect ratio",
        "Wasserzeichen:": "Watermark:",
        "Text, z.B. © 2026": "Text, e.g. © 2026",
        'unten-rechts': 'bottom right',
        'unten-links': 'bottom left',
        'oben-rechts': 'top right',
        'oben-links': 'top left',
        'mitte': 'center',
        "Größe schätzen": "Estimate size",
        "Geschätzte Ausgabegröße: -- MB": "Estimated output size: -- MB",
        "Metadaten entfernen": "Strip metadata",
        "Anzeigen / Bearbeiten": "View / edit",
        "Ausgabe & Konvertierung": "Output & conversion",
        "Automatisch generiert": "Generated automatically",
        "Speicherort wählen": "Choose destination",
        'Vorhandene Dateien überschreiben (sonst "name (1)")':
            'Overwrite existing files (otherwise "name (1)")',
        "Konvertieren starten": "Start conversion",
        "Ordner öffnen": "Open folder",
        "Bereit": "Ready",
        "Bereit — Tipp: 'pip install pymupdf' aktiviert PDF-Eingabe":
            "Ready — tip: 'pip install pymupdf' enables PDF input",

        # ---------- GUI: Meldungen ----------
        "✓ Preset '{name}' angewendet": "✓ Preset '{name}' applied",
        "Name für das Preset:": "Name for the preset:",
        "Preset speichern": "Save preset",
        "✗ Keine unterstützten Dateien dabei":
            "✗ No supported files among them",
        "✓ {added} Datei(en) geladen — {skipped} nicht unterstützte übersprungen":
            "✓ {added} file(s) loaded — skipped {skipped} unsupported",
        "Liste geleert": "List cleared",
        "✓ {n} Dateien in der Warteschlange": "✓ {n} files in the queue",
        "✓ Datei erfolgreich geladen": "✓ File loaded successfully",
        "✗ Fehler beim Laden: {error}": "✗ Failed to load: {error}",
        "PDF · Seite {page} von {count}": "PDF · page {page} of {count}",
        "SVG · gerastert auf {w}×{h}": "SVG · rasterized to {w}×{h}",
        " · animiert ({n} Frames)": " · animated ({n} frames)",
        "{n} Einträge": "{n} entries",
        "keine": "none",
        "Datei:      {name}": "File:       {name}",
        "Größe:      {size:.2f} MB": "Size:       {size:.2f} MB",
        "Auflösung:  {w} × {h} Pixel": "Resolution: {w} × {h} pixels",
        "Format:     {format}": "Format:     {format}",
        "EXIF:       {exif}": "EXIF:       {exif}",
        "✓ Seite {page} geladen": "✓ Page {page} loaded",
        "✗ Fehler beim Laden der Seite: {error}":
            "✗ Failed to load the page: {error}",
        "Qualität (für dieses Format nicht verfügbar)":
            "Quality (not available for this format)",
        "auto": "auto",
        "Ungültige Auflösung — Originalgröße wird verwendet":
            "Invalid resolution — using the original size",
        "Ungültige Zielgröße — bitte KB als Zahl angeben":
            "Invalid target size — please enter KB as a number",
        "Wasserzeichen aktiviert, aber kein Text angegeben":
            "Watermark enabled, but no text given",
        "Bitte zuerst eine Datei laden": "Please load a file first",
        "EXIF-Metadaten": "EXIF metadata",
        "Bearbeitbare Felder": "Editable fields",
        "Beschreibung": "Description",
        "Künstler": "Artist",
        "Copyright": "Copyright",
        "Software": "Software",
        "Datum (JJJJ:MM:TT HH:MM:SS)": "Date (YYYY:MM:DD HH:MM:SS)",
        "Kamera-Hersteller": "Camera make",
        "Kamera-Modell": "Camera model",
        "Alle Metadaten der ausgewählten Datei":
            "All metadata of the selected file",
        "Keine EXIF-Daten vorhanden.": "No EXIF data present.",
        "Abbrechen": "Cancel",
        "Übernehmen": "Apply",
        "✓ {n} EXIF-Feld(er) werden beim Konvertieren angepasst":
            "✓ {n} EXIF field(s) will be adjusted during conversion",
        "EXIF-Änderungen zurückgesetzt": "EXIF changes reset",
        "Wird angepasst: {fields}": "Will be adjusted: {fields}",
        "je Eingabeordner": "each input folder",
        "Mehrere Dateien → {target}": "Multiple files → {target}",
        "Bitte zuerst Dateien auswählen": "Please select files first",
        "Ausgabedatei speichern": "Save output file",
        "Alle Dateien": "All files",
        "Ausgabeordner wählen": "Choose output folder",
        "Alle unterstützten Dateien": "All supported files",
        "Alle Bilder": "All images",
        "Bilder oder PDFs auswählen": "Select images or PDFs",
        "Geschätzt: {size:.2f} MB (Qualität {q})":
            "Estimated: {size:.2f} MB (quality {q})",
        "Zielgröße {kb} KB → Qualität {q}":
            "Target size {kb} KB → quality {q}",
        "Geschätzt: {size:.2f} MB (Original: {orig:.2f} MB)":
            "Estimated: {size:.2f} MB (original: {orig:.2f} MB)",
        "Schätzung: -{value:.1f}% kleiner":
            "Estimate: {value:.1f}% smaller",
        "Schätzung: +{value:.1f}% größer":
            "Estimate: {value:.1f}% larger",
        "Konnte Größe nicht schätzen": "Could not estimate the size",
        "✗ Fehler bei Größenberechnung: {error}":
            "✗ Size estimation failed: {error}",
        "Konvertiere...": "Converting...",
        "{n} Seite(n) → {name} ({size:.2f} MB)":
            "{n} page(s) → {name} ({size:.2f} MB)",
        "S.": "p.",
        " (Animation ging verloren)": " (animation was lost)",
        "✓ {ok} von {total} konvertiert": "✓ {ok} of {total} converted",
        "… und {n} weitere Fehler": "… and {n} more errors",
        "✗ {n} Konvertierung(en) fehlgeschlagen":
            "✗ {n} conversion(s) failed",
        "✓ Konvertierung abgeschlossen": "✓ Conversion finished",
    }
}


def _detect_language():
    override = os.environ.get('PICCONVERTER_LANG', '').lower()
    if override in ('de', 'en'):
        return override
    try:
        lang = locale.getlocale()[0] or os.environ.get('LANG', '')
    except Exception:
        lang = os.environ.get('LANG', '')
    return 'de' if str(lang).lower().startswith('de') else 'en'


LANGUAGE = _detect_language()


def set_language(lang):
    """Setzt die aktive Sprache zur Laufzeit ('de', 'en' oder 'system')"""
    global LANGUAGE
    LANGUAGE = _detect_language() if lang == 'system' else lang


def tr(text):
    """Übersetzt einen deutschen UI-Text in die aktive Sprache"""
    if LANGUAGE == 'de':
        return text
    return TRANSLATIONS.get(LANGUAGE, {}).get(text, text)
