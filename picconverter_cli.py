#!/usr/bin/env python3
"""
PicConverter CLI - Bild- & PDF-Konvertierungs-Tool mit Kommandozeilen-Interface
"""

import argparse
import glob
import sys
from pathlib import Path

import picconverter_core as core


def parse_exif_overrides(pairs):
    """Wandelt --exif-set FELD=WERT Argumente in ein Override-Dict um"""
    overrides = {}
    for pair in pairs or []:
        if '=' not in pair:
            raise ValueError(f"Ungültiges Argument '{pair}' — erwartet wird FELD=WERT")
        name, _, value = pair.partition('=')
        name = name.strip()
        if name not in core.EXIF_EDITABLE_TAGS:
            valid = ', '.join(core.EXIF_EDITABLE_TAGS)
            raise ValueError(f"Unbekanntes EXIF-Feld '{name}'. Verfügbar: {valid}")
        overrides[name] = value.strip()
    return overrides


def expand_inputs(patterns):
    """Löst Eingabepfade und Glob-Muster (z.B. '*.jpg') zu einer Dateiliste auf"""
    paths = []
    for pattern in patterns:
        path = Path(pattern)
        if path.exists():
            paths.append(path)
            continue
        matches = sorted(glob.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"Datei '{pattern}' existiert nicht")
        paths.extend(Path(m) for m in matches)
    return paths


def build_jobs(inputs, page_arg):
    """Erstellt die Liste der Konvertierungsaufträge: (Pfad, Seite-oder-None)"""
    jobs = []
    for path in inputs:
        if core.is_pdf(path):
            if page_arg == 'all':
                count = core.pdf_page_count(path)
                jobs.extend((path, page) for page in range(1, count + 1))
            else:
                jobs.append((path, int(page_arg)))
        else:
            jobs.append((path, None))
    return jobs


def resolve_output(out_arg, single_job):
    """Interpretiert -o als Zieldatei oder Zielordner.

    Ein Ordner liegt vor, wenn mehrere Aufträge anstehen, der Pfad bereits als
    Ordner existiert oder mit einem Pfadtrenner endet. Gibt (datei, ordner) zurück.
    """
    if not out_arg:
        return None, None
    out = Path(out_arg)
    if not single_job or out.is_dir() or out_arg.endswith(('/', '\\')):
        out.mkdir(parents=True, exist_ok=True)
        return None, out
    return out, None


def output_path_for(input_path, page, extension, out_file, out_dir, page_all):
    """Bestimmt den Ausgabepfad eines Auftrags.

    PDF-Seiten erhalten ab Seite 2 (bzw. bei --page all immer) ein _seiteN-Suffix.
    """
    if out_file:
        return out_file

    stem = core.output_stem(input_path, page, page_all)
    directory = out_dir if out_dir else input_path.parent
    return directory / f"{stem}.{extension}"


def resolve_resolution(img, width_arg, height_arg):
    """Ermittelt die Zielauflösung; eine fehlende Dimension wird
    seitenverhältnistreu aus der anderen berechnet."""
    if not width_arg and not height_arg:
        return None, None
    if width_arg and height_arg:
        return width_arg, height_arg
    ratio = img.size[0] / img.size[1]
    if width_arg:
        return width_arg, round(width_arg / ratio)
    return round(height_arg * ratio), height_arg


def main():
    parser = argparse.ArgumentParser(
        description='PicConverter CLI - Konvertiert Bilder und PDFs zwischen Formaten',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Unterstützte Formate: {', '.join(core.FORMAT_BY_EXT.keys())}
EXIF-Felder für --exif-set: {', '.join(core.EXIF_EDITABLE_TAGS.keys())}

Beispiele:
  %(prog)s bild.jpg -f png -o ausgabe.png
  %(prog)s *.jpg -f webp -q 85                      # Batch
  %(prog)s foto.jpg -f jpg --target-size 500        # max. 500 KB
  %(prog)s dokument.pdf -f png --page all --dpi 300 # alle Seiten
  %(prog)s scan1.png scan2.png -f pdf --merge -o dokument.pdf
  %(prog)s foto.jpg -f jpg --strip-exif             # Metadaten entfernen
  %(prog)s foto.jpg -f jpg --exif-set "Artist=Max Mustermann" --exif-set Copyright=CC-BY
        """
    )

    parser.add_argument('inputs', nargs='+', metavar='EINGABE',
                        help='Eingabedateien (auch mehrere oder Glob-Muster wie *.jpg)')
    parser.add_argument('-f', '--format', '--to', dest='format',
                        choices=list(core.FORMAT_BY_EXT.keys()),
                        required=True,
                        help='Zielformat für die Konvertierung')
    parser.add_argument('-o', '--output', dest='output',
                        help='Ausgabedatei (bei einer Eingabe) oder Ausgabeordner (bei mehreren)')
    parser.add_argument('-q', '--quality', type=int,
                        help='Qualität/Kompression (JPEG/WebP: 1-100, PNG: 0-9)')
    parser.add_argument('--target-size', type=int, metavar='KB',
                        help='Zielgröße in KB — sucht die passende Qualität (nur JPEG/WebP)')
    parser.add_argument('-w', '--width', type=int,
                        help='Breite in Pixeln (Höhe wird ggf. seitenverhältnistreu ergänzt)')
    parser.add_argument('--height', type=int,
                        help='Höhe in Pixeln (Breite wird ggf. seitenverhältnistreu ergänzt)')
    parser.add_argument('--estimate', action='store_true',
                        help='Zeigt geschätzte Ausgabegröße ohne zu konvertieren')
    parser.add_argument('--page', default='1',
                        help="PDF-Eingabe: Seitennummer oder 'all' für alle Seiten (Standard: 1)")
    parser.add_argument('--dpi', type=int, default=core.PDF_RENDER_DPI,
                        help=f'PDF-Eingabe: Render-Auflösung in DPI (Standard: {core.PDF_RENDER_DPI})')
    parser.add_argument('--merge', action='store_true',
                        help='Alle Eingaben in eine mehrseitige PDF zusammenfassen (nur -f pdf)')
    parser.add_argument('--strip-exif', action='store_true',
                        help='EXIF-Metadaten nicht in die Ausgabe übernehmen')
    parser.add_argument('--exif-set', action='append', metavar='FELD=WERT',
                        help='EXIF-Feld setzen (leerer Wert löscht das Feld); mehrfach nutzbar')

    args = parser.parse_args()

    # Argumente validieren
    if args.page != 'all':
        try:
            if int(args.page) < 1:
                raise ValueError
        except ValueError:
            parser.error(f"--page erwartet eine Seitennummer >= 1 oder 'all', nicht '{args.page}'")

    if args.quality is not None and args.target_size is not None:
        parser.error("--quality und --target-size schließen sich gegenseitig aus")

    output_format = core.FORMAT_BY_EXT[args.format.lower()]

    if args.target_size is not None and output_format not in core.TARGET_SIZE_FORMATS:
        parser.error(f"--target-size wird nur für "
                     f"{', '.join(sorted(core.TARGET_SIZE_FORMATS))} unterstützt")

    if args.merge and output_format != 'PDF':
        parser.error("--merge funktioniert nur mit -f pdf")

    try:
        exif_overrides = parse_exif_overrides(args.exif_set)
        inputs = expand_inputs(args.inputs)
        jobs = build_jobs(inputs, args.page)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    exif_mode = 'strip' if args.strip_exif else 'keep'

    # Qualität validieren
    quality = args.quality
    if quality is None and args.target_size is None:
        if output_format in core.QUALITY_SETTINGS:
            quality = core.QUALITY_SETTINGS[output_format]['default']
    elif quality is not None and output_format in core.QUALITY_SETTINGS:
        q_min = core.QUALITY_SETTINGS[output_format]['min']
        q_max = core.QUALITY_SETTINGS[output_format]['max']
        if not (q_min <= quality <= q_max):
            print(f"Warnung: Qualität {quality} außerhalb des Bereichs [{q_min}-{q_max}]. "
                  f"Verwende Standardwert.", file=sys.stderr)
            quality = core.QUALITY_SETTINGS[output_format]['default']

    # Sonderfall: alles in eine PDF zusammenfassen
    if args.merge:
        try:
            images = [core.load_image(path, page or 1, args.dpi) for path, page in jobs]
            out = Path(args.output) if args.output else \
                inputs[0].parent / f"{inputs[0].stem}_gesamt.pdf"
            core.images_to_pdf(images, out)
            size_mb = out.stat().st_size / (1024 * 1024)
            print(f"✓ {len(images)} Seite(n) zusammengefasst in: {out} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"✗ Fehler beim Zusammenfassen: {e}", file=sys.stderr)
            sys.exit(1)
        return

    out_file, out_dir = resolve_output(args.output, len(jobs) == 1)

    extension = args.format.lower()
    failures = 0

    for path, page in jobs:
        label = path.name if page is None else f"{path.name} (Seite {page})"
        out = output_path_for(path, page, extension, out_file, out_dir,
                              args.page == 'all')
        try:
            img = core.load_image(path, page or 1, args.dpi)
            width, height = resolve_resolution(img, args.width, args.height)

            job_quality = quality
            if args.target_size is not None:
                job_quality, est = core.quality_for_target(
                    img, output_format, args.target_size, width, height,
                    exif_mode, exif_overrides)
                print(f"  Zielgröße {args.target_size} KB → Qualität {job_quality} "
                      f"(≈ {est * 1024:.0f} KB)")

            if args.estimate:
                est = core.estimate_size(img, output_format, job_quality,
                                         width, height, exif_mode, exif_overrides)
                original_mb = path.stat().st_size / (1024 * 1024)
                print(f"~ {label}: geschätzt {est:.2f} MB (Original: {original_mb:.2f} MB)")
                continue

            core.convert(img, out, output_format, job_quality, width, height,
                         exif_mode, exif_overrides)
            size_mb = out.stat().st_size / (1024 * 1024)
            print(f"✓ {label} → {out} ({size_mb:.2f} MB)")
        except Exception as e:
            failures += 1
            print(f"✗ {label}: {e}", file=sys.stderr)

    if args.estimate and not failures:
        print("\nNur Schätzung angefordert. Keine Konvertierung durchgeführt.")

    if failures:
        print(f"\n{failures} von {len(jobs)} Auftrag/Aufträgen fehlgeschlagen.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
