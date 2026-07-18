#!/usr/bin/env python3
"""
PicConverter Core - gemeinsame Konvertierungslogik für CLI und GUI
"""

import io
from pathlib import Path

from PIL import Image, ImageOps, ExifTags

# PDF-Eingabe ist optional -- ohne PyMuPDF bleiben alle Bildformate nutzbar
try:
    import pymupdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Render-Auflösung für PDF-Seiten, wenn nichts anderes angegeben ist
PDF_RENDER_DPI = 150

# PIL-Formatname je Dateiendung
FORMAT_BY_EXT = {
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'png': 'PNG',
    'bmp': 'BMP',
    'tiff': 'TIFF',
    'tif': 'TIFF',
    'gif': 'GIF',
    'webp': 'WebP',
    'ico': 'ICO',
    'pdf': 'PDF',
}

# Qualitäts-/Kompressionseinstellungen je Format
QUALITY_SETTINGS = {
    'JPEG': {'min': 1, 'max': 100, 'default': 85, 'name': 'Qualität'},
    'PNG': {'min': 0, 'max': 9, 'default': 6, 'name': 'Kompression'},
    'WebP': {'min': 0, 'max': 100, 'default': 80, 'name': 'Qualität'},
    'TIFF': {'min': 0, 'max': 9, 'default': 6, 'name': 'Kompression'},
}

# Formate, in die EXIF-Metadaten geschrieben werden können
EXIF_FORMATS = {'JPEG', 'PNG', 'WebP', 'TIFF'}

# Formate, für die eine Zielgröße per Qualitätssuche erreichbar ist
TARGET_SIZE_FORMATS = {'JPEG', 'WebP'}

# Bearbeitbare EXIF-Felder (Basis-IFD): CLI-/GUI-Name -> (Tag-ID, deutsches Label)
EXIF_EDITABLE_TAGS = {
    'ImageDescription': (0x010E, 'Beschreibung'),
    'Artist': (0x013B, 'Künstler'),
    'Copyright': (0x8298, 'Copyright'),
    'Software': (0x0131, 'Software'),
    'DateTime': (0x0132, 'Datum (JJJJ:MM:TT HH:MM:SS)'),
    'Make': (0x010F, 'Kamera-Hersteller'),
    'Model': (0x0110, 'Kamera-Modell'),
}

ORIENTATION_TAG = 0x0112


def is_pdf(path):
    return Path(path).suffix.lower() == '.pdf'


def _require_pymupdf():
    if not PDF_AVAILABLE:
        raise RuntimeError(
            "PDF-Eingabe benötigt PyMuPDF. Installation: pip install pymupdf"
        )


def pdf_page_count(path):
    """Gibt die Seitenanzahl einer PDF zurück"""
    _require_pymupdf()
    doc = pymupdf.open(path)
    try:
        return doc.page_count
    finally:
        doc.close()


def render_pdf_page(path, page=1, dpi=PDF_RENDER_DPI):
    """Rendert eine PDF-Seite (1-basiert) als PIL-Bild"""
    _require_pymupdf()
    doc = pymupdf.open(path)
    try:
        if not (1 <= page <= doc.page_count):
            raise RuntimeError(
                f"Seite {page} existiert nicht — die PDF hat {doc.page_count} Seite(n)"
            )
        pix = doc[page - 1].get_pixmap(dpi=dpi)
        return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    finally:
        doc.close()


def load_image(path, page=1, dpi=PDF_RENDER_DPI):
    """Öffnet ein Bild oder rendert eine PDF-Seite.

    Bei Bildern wird die EXIF-Orientierung direkt eingerechnet (Hochkant-Fotos
    bleiben hochkant); das Orientierungs-Tag ist danach aus den EXIF-Daten entfernt.
    """
    path = Path(path)
    if is_pdf(path):
        return render_pdf_page(path, page, dpi)
    img = Image.open(path)
    return ImageOps.exif_transpose(img)


def prepare_for_format(img, output_format):
    """Passt den Bildmodus ans Zielformat an (Transparenz wird durch Weiß ersetzt)"""
    if output_format in ('JPEG', 'BMP', 'PDF') and img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode not in ('RGB', 'RGBA', 'L', 'P'):
        img = img.convert('RGB')
    return img


def build_exif(image, mode='keep', overrides=None):
    """Stellt die EXIF-Daten für die Ausgabe zusammen.

    mode='keep'  übernimmt die EXIF-Daten des Bildes,
    mode='strip' beginnt mit leeren EXIF-Daten.
    overrides ist ein Dict Feldname -> Wert (leerer Wert löscht das Feld);
    zulässige Feldnamen: EXIF_EDITABLE_TAGS.
    Gibt ein Image.Exif-Objekt oder None (= keine EXIF-Daten schreiben) zurück.
    """
    exif = Image.Exif()
    if mode == 'keep':
        source = image.getexif()
        if len(source):
            exif.load(source.tobytes())

    for name, value in (overrides or {}).items():
        if name not in EXIF_EDITABLE_TAGS:
            valid = ', '.join(EXIF_EDITABLE_TAGS)
            raise ValueError(f"Unbekanntes EXIF-Feld '{name}'. Verfügbar: {valid}")
        tag = EXIF_EDITABLE_TAGS[name][0]
        if value:
            exif[tag] = value
        else:
            exif.pop(tag, None)

    # Orientierung ist beim Laden bereits eingerechnet -- ein verbliebenes
    # Tag würde Betrachter das Bild doppelt drehen lassen
    exif.pop(ORIENTATION_TAG, None)

    return exif if len(exif) else None


def read_exif(image):
    """Liest die EXIF-Daten als Liste (Tag-Name, Wert) für die Anzeige"""
    entries = []
    exif = image.getexif()
    for tag, value in exif.items():
        name = ExifTags.TAGS.get(tag, f"0x{tag:04X}")
        entries.append((name, str(value)))
    # Aufnahme-Infos liegen im Exif-Unterverzeichnis (Belichtung, Original-Datum, ...)
    try:
        for tag, value in exif.get_ifd(ExifTags.IFD.Exif).items():
            name = ExifTags.TAGS.get(tag, f"0x{tag:04X}")
            entries.append((name, str(value)))
    except Exception:
        pass
    return entries


def build_save_kwargs(output_format, quality=None, exif=None):
    """Erstellt die Pillow-Speicherparameter für das Zielformat"""
    save_kwargs = {}
    if output_format == 'JPEG':
        save_kwargs['quality'] = quality if quality is not None else 85
        save_kwargs['optimize'] = True
    elif output_format == 'PNG':
        if quality is not None:
            save_kwargs['compress_level'] = 9 - quality
    elif output_format == 'WebP':
        save_kwargs['quality'] = quality if quality is not None else 80
    elif output_format == 'TIFF':
        save_kwargs['compression'] = 'tiff_lzw'
    if exif is not None and output_format in EXIF_FORMATS:
        save_kwargs['exif'] = exif
    return save_kwargs


def _prepare_output_image(image, output_format, width=None, height=None):
    img = prepare_for_format(image, output_format)
    if width and height and (width, height) != img.size:
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    return img


def convert(image, output_path, output_format, quality=None, width=None, height=None,
            exif_mode='keep', exif_overrides=None):
    """Konvertiert ein geladenes Bild und schreibt es nach output_path (wirft bei Fehlern)"""
    img = _prepare_output_image(image, output_format, width, height)
    exif = build_exif(image, exif_mode, exif_overrides)
    img.save(output_path, format=output_format,
             **build_save_kwargs(output_format, quality, exif))


def estimate_size(image, output_format, quality=None, width=None, height=None,
                  exif_mode='keep', exif_overrides=None):
    """Schätzt die Ausgabegröße in MB durch eine Probe-Speicherung im Speicher"""
    img = _prepare_output_image(image, output_format, width, height)
    exif = build_exif(image, exif_mode, exif_overrides)
    buffer = io.BytesIO()
    img.save(buffer, format=output_format,
             **build_save_kwargs(output_format, quality, exif))
    return buffer.tell() / (1024 * 1024)


def quality_for_target(image, output_format, target_kb, width=None, height=None,
                       exif_mode='keep', exif_overrides=None):
    """Sucht per Binärsuche die höchste Qualität, mit der die Zielgröße gehalten wird.

    Nur für JPEG/WebP sinnvoll. Gibt (Qualität, geschätzte Größe in MB) zurück;
    ist selbst Qualität 1 zu groß, wird (1, Größe) zurückgegeben.
    """
    if output_format not in TARGET_SIZE_FORMATS:
        raise ValueError(
            f"Zielgröße wird nur für {', '.join(sorted(TARGET_SIZE_FORMATS))} unterstützt"
        )
    target_mb = target_kb / 1024

    low, high = 1, 100
    best = None
    while low <= high:
        mid = (low + high) // 2
        size = estimate_size(image, output_format, mid, width, height,
                             exif_mode, exif_overrides)
        if size <= target_mb:
            best = (mid, size)
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        return 1, estimate_size(image, output_format, 1, width, height,
                                exif_mode, exif_overrides)
    return best


def output_stem(input_path, page=None, all_pages=False):
    """Ausgabe-Dateiname ohne Endung; PDF-Seiten erhalten ab Seite 2
    (bzw. beim Alle-Seiten-Export immer) ein _seiteN-Suffix"""
    stem = Path(input_path).stem
    if page is not None and (page > 1 or all_pages):
        stem += f"_seite{page}"
    return stem


def images_to_pdf(images, output_path):
    """Speichert mehrere Bilder als eine mehrseitige PDF"""
    if not images:
        raise ValueError("Keine Bilder zum Zusammenfassen übergeben")
    pages = [prepare_for_format(img, 'PDF') for img in images]
    pages[0].save(output_path, format='PDF', save_all=True,
                  append_images=pages[1:])
