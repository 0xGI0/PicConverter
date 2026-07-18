#!/usr/bin/env python3
"""
PicConverter Core - gemeinsame Konvertierungslogik für CLI und GUI
"""

import io
import json
import os
from itertools import count
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence, ExifTags

from picconverter_i18n import tr

__version__ = "3.0.0"

# PDF-Eingabe ist optional -- ohne PyMuPDF bleiben alle Bildformate nutzbar
try:
    import pymupdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# HEIC/HEIF-Eingabe ist optional (iPhone-Fotos u.ä.)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

# AVIF: ab Pillow 11 nativ; ältere pillow-heif-Versionen liefern einen Opener
try:
    from PIL import features as _pil_features
    AVIF_AVAILABLE = bool(_pil_features.check('avif'))
except Exception:
    AVIF_AVAILABLE = False
if not AVIF_AVAILABLE and HEIF_AVAILABLE and hasattr(pillow_heif, 'register_avif_opener'):
    pillow_heif.register_avif_opener()
    AVIF_AVAILABLE = True

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

# Formate, die Animationen speichern können
ANIMATED_FORMATS = {'GIF', 'WebP'}

# Akzeptierte Eingabe-Endungen (ohne Punkt)
INPUT_EXTENSIONS = set(FORMAT_BY_EXT)
if HEIF_AVAILABLE:
    INPUT_EXTENSIONS |= {'heic', 'heif'}
if AVIF_AVAILABLE:
    INPUT_EXTENSIONS.add('avif')

# Positionen für Wasserzeichen
WATERMARK_POSITIONS = ('unten-rechts', 'unten-links', 'oben-rechts',
                       'oben-links', 'mitte')

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
            tr("PDF-Eingabe benötigt PyMuPDF. Installation: pip install pymupdf")
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
                tr("Seite {page} existiert nicht — die PDF hat {count} Seite(n)")
                .format(page=page, count=doc.page_count)
            )
        pix = doc[page - 1].get_pixmap(dpi=dpi)
        return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    finally:
        doc.close()


def is_animated(image):
    """True, wenn das Bild mehrere Frames hat (animiertes GIF/WebP)"""
    return getattr(image, 'n_frames', 1) > 1


def load_image(path, page=1, dpi=PDF_RENDER_DPI):
    """Öffnet ein Bild oder rendert eine PDF-Seite.

    Bei Bildern wird die EXIF-Orientierung direkt eingerechnet (Hochkant-Fotos
    bleiben hochkant); das Orientierungs-Tag ist danach aus den EXIF-Daten
    entfernt. Animierte Bilder werden unverändert zurückgegeben, damit die
    Frames erhalten bleiben.
    """
    path = Path(path)
    if is_pdf(path):
        return render_pdf_page(path, page, dpi)
    img = Image.open(path)
    if is_animated(img):
        return img
    return ImageOps.exif_transpose(img)


def unique_path(path):
    """Weicht auf 'name (1).ext', 'name (2).ext' … aus, falls path existiert"""
    path = Path(path)
    if not path.exists():
        return path
    for i in count(1):
        candidate = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not candidate.exists():
            return candidate


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
            raise ValueError(
                tr("Unbekanntes EXIF-Feld '{name}'. Verfügbar: {valid}")
                .format(name=name, valid=', '.join(EXIF_EDITABLE_TAGS)))
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


def apply_watermark(img, text=None, image_path=None, position='unten-rechts',
                    opacity=50):
    """Legt ein Text- oder Bild-Wasserzeichen über das Bild.

    opacity in Prozent (0-100). Bei Bild-Wasserzeichen wird das Logo auf
    ca. 20 % der Bildbreite skaliert.
    """
    if not text and not image_path:
        return img

    base = img.convert('RGBA')
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    alpha = round(255 * max(0, min(100, opacity)) / 100)
    margin = max(12, base.width // 50)

    if text:
        font_size = max(16, base.width // 25)
        font = _watermark_font(font_size)
        draw = ImageDraw.Draw(overlay)
        bbox = draw.textbbox((0, 0), text, font=font)
        mark_w, mark_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = _watermark_xy(base.size, (mark_w, mark_h), position, margin)
        # Leichter Schatten für Lesbarkeit auf hellen Bildern
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))
    else:
        mark = Image.open(image_path).convert('RGBA')
        target_w = max(1, base.width // 5)
        scale = target_w / mark.width
        mark = mark.resize((target_w, max(1, round(mark.height * scale))),
                           Image.Resampling.LANCZOS)
        faded = mark.getchannel('A').point(lambda a: a * alpha // 255)
        mark.putalpha(faded)
        x, y = _watermark_xy(base.size, mark.size, position, margin)
        overlay.paste(mark, (x, y), mark)

    result = Image.alpha_composite(base, overlay)
    return result if img.mode == 'RGBA' else result.convert('RGB')


def _watermark_font(size):
    """Sucht eine fette TrueType-Schrift; fällt auf Pillows Standardschrift zurück"""
    for name in ("DejaVuSans-Bold.ttf", "NotoSans-Bold.ttf", "LiberationSans-Bold.ttf",
                 "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow < 10.1 kennt den size-Parameter nicht
        return ImageFont.load_default()


def _watermark_xy(base_size, mark_size, position, margin):
    bw, bh = base_size
    mw, mh = mark_size
    if position == 'mitte':
        return (bw - mw) // 2, (bh - mh) // 2
    x = margin if 'links' in position else bw - mw - margin
    y = margin if 'oben' in position else bh - mh - margin
    return x, y


def _prepare_output_image(image, output_format, width=None, height=None,
                          watermark=None):
    img = image
    if width and height and (width, height) != img.size:
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    if watermark:
        img = apply_watermark(img, **watermark)
    return prepare_for_format(img, output_format)


def _save_animated(image, target, output_format, quality=None, width=None,
                   height=None, watermark=None, exif=None):
    """Speichert ein animiertes Bild mit allen Frames (GIF/WebP)"""
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(image):
        durations.append(frame.info.get('duration', image.info.get('duration', 100)))
        frames.append(_prepare_output_image(frame.copy(), output_format,
                                            width, height, watermark))
    save_kwargs = build_save_kwargs(output_format, quality, exif)
    save_kwargs.pop('optimize', None)
    frames[0].save(target, format=output_format, save_all=True,
                   append_images=frames[1:], duration=durations,
                   loop=image.info.get('loop', 0), **save_kwargs)


def convert(image, output_path, output_format, quality=None, width=None, height=None,
            exif_mode='keep', exif_overrides=None, watermark=None):
    """Konvertiert ein geladenes Bild und schreibt es nach output_path (wirft bei Fehlern).

    Animierte GIFs/WebPs behalten ihre Frames, wenn das Zielformat Animationen
    unterstützt; andernfalls wird das erste Frame konvertiert.
    """
    exif = build_exif(image, exif_mode, exif_overrides)
    if is_animated(image) and output_format in ANIMATED_FORMATS:
        _save_animated(image, output_path, output_format, quality,
                       width, height, watermark, exif)
        return
    if is_animated(image):
        image.seek(0)
    img = _prepare_output_image(image, output_format, width, height, watermark)
    img.save(output_path, format=output_format,
             **build_save_kwargs(output_format, quality, exif))


def estimate_size(image, output_format, quality=None, width=None, height=None,
                  exif_mode='keep', exif_overrides=None, watermark=None):
    """Schätzt die Ausgabegröße in MB durch eine Probe-Speicherung im Speicher"""
    exif = build_exif(image, exif_mode, exif_overrides)
    buffer = io.BytesIO()
    if is_animated(image) and output_format in ANIMATED_FORMATS:
        _save_animated(image, buffer, output_format, quality,
                       width, height, watermark, exif)
    else:
        img = _prepare_output_image(image, output_format, width, height, watermark)
        img.save(buffer, format=output_format,
                 **build_save_kwargs(output_format, quality, exif))
    return buffer.tell() / (1024 * 1024)


def quality_for_target(image, output_format, target_kb, width=None, height=None,
                       exif_mode='keep', exif_overrides=None, watermark=None):
    """Sucht per Binärsuche die höchste Qualität, mit der die Zielgröße gehalten wird.

    Nur für JPEG/WebP sinnvoll. Gibt (Qualität, geschätzte Größe in MB) zurück;
    ist selbst Qualität 1 zu groß, wird (1, Größe) zurückgegeben.
    """
    if output_format not in TARGET_SIZE_FORMATS:
        raise ValueError(
            tr("Zielgröße wird nur für {formats} unterstützt").format(
                formats=', '.join(sorted(TARGET_SIZE_FORMATS)))
        )
    target_mb = target_kb / 1024

    low, high = 1, 100
    best = None
    while low <= high:
        mid = (low + high) // 2
        size = estimate_size(image, output_format, mid, width, height,
                             exif_mode, exif_overrides, watermark)
        if size <= target_mb:
            best = (mid, size)
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        return 1, estimate_size(image, output_format, 1, width, height,
                                exif_mode, exif_overrides, watermark)
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
        raise ValueError(tr("Keine Bilder zum Zusammenfassen übergeben"))
    pages = [prepare_for_format(img, 'PDF') for img in images]
    pages[0].save(output_path, format='PDF', save_all=True,
                  append_images=pages[1:])


# ---------- Konfiguration & Presets ----------

# Mitgelieferte Presets; Nutzer-Presets aus presets.json überschreiben
# gleichnamige Einträge
BUILTIN_PRESETS = {
    'web': {'format': 'webp', 'quality': 80, 'width': 1920},
    'email': {'format': 'jpg', 'target_kb': 500},
    'archiv': {'format': 'png'},
}

# Felder, die ein Preset setzen darf
PRESET_FIELDS = ('format', 'quality', 'target_kb', 'width', 'height', 'strip_exif')


def config_dir():
    """Konfigurationsordner (~/.config/picconverter bzw. XDG_CONFIG_HOME)"""
    base = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    return Path(base) / 'picconverter'


def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_presets():
    """Alle Presets: mitgelieferte plus Nutzer-Presets aus presets.json"""
    presets = {name: dict(settings) for name, settings in BUILTIN_PRESETS.items()}
    for name, settings in _read_json(config_dir() / 'presets.json').items():
        if isinstance(settings, dict):
            presets[name] = {k: v for k, v in settings.items() if k in PRESET_FIELDS}
    return presets


def save_user_preset(name, settings):
    """Speichert ein Nutzer-Preset in presets.json"""
    path = config_dir() / 'presets.json'
    presets = _read_json(path)
    presets[name] = {k: v for k, v in settings.items()
                     if k in PRESET_FIELDS and v not in (None, '', False)}
    _write_json(path, presets)


def load_gui_settings():
    """Zuletzt gespeicherte GUI-Einstellungen"""
    return _read_json(config_dir() / 'settings.json')


def save_gui_settings(settings):
    """Speichert die GUI-Einstellungen für den nächsten Start"""
    _write_json(config_dir() / 'settings.json', settings)
