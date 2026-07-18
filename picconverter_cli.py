#!/usr/bin/env python3
"""
PicConverter CLI - Bild- & PDF-Konvertierungs-Tool mit Kommandozeilen-Interface
"""

import argparse
import glob
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import picconverter_core as core
from picconverter_i18n import tr


def parse_exif_overrides(pairs):
    """Wandelt --exif-set FELD=WERT Argumente in ein Override-Dict um"""
    overrides = {}
    for pair in pairs or []:
        if '=' not in pair:
            raise ValueError(
                tr("Ungültiges Argument '{pair}' — erwartet wird FELD=WERT")
                .format(pair=pair))
        name, _, value = pair.partition('=')
        name = name.strip()
        if name not in core.EXIF_EDITABLE_TAGS:
            raise ValueError(
                tr("Unbekanntes EXIF-Feld '{name}'. Verfügbar: {valid}")
                .format(name=name, valid=', '.join(core.EXIF_EDITABLE_TAGS)))
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
            raise FileNotFoundError(
                tr("Datei '{pattern}' existiert nicht").format(pattern=pattern))
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


def reserve_outputs(jobs, extension, out_file, out_dir, page_all, overwrite):
    """Bestimmt vorab alle Ausgabepfade; ohne --overwrite wird auf 'name (N).ext'
    ausgewichen — auch gegen Kollisionen innerhalb desselben Laufs."""
    reserved = set()
    outputs = []
    for path, page in jobs:
        if out_file:
            out = out_file
        else:
            stem = core.output_stem(path, page, page_all)
            directory = out_dir if out_dir else path.parent
            out = directory / f"{stem}.{extension}"
        if not overwrite:
            candidate = out
            i = 1
            while candidate.exists() or candidate in reserved:
                candidate = out.with_name(f"{out.stem} ({i}){out.suffix}")
                i += 1
            out = candidate
        reserved.add(out)
        outputs.append(out)
    return outputs


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


def apply_preset(args, parser):
    """Füllt nicht gesetzte Argumente aus dem gewählten Preset auf"""
    presets = core.load_presets()
    if args.preset not in presets:
        parser.error(tr("Unbekanntes Preset '{name}'. Verfügbar: {valid}")
                     .format(name=args.preset, valid=', '.join(sorted(presets))))
    preset = presets[args.preset]
    if args.format is None:
        args.format = preset.get('format')
    if args.quality is None and args.target_size is None:
        args.quality = preset.get('quality')
        args.target_size = preset.get('target_kb')
    if args.width is None:
        args.width = preset.get('width')
    if args.height is None:
        args.height = preset.get('height')
    if not args.strip_exif:
        args.strip_exif = bool(preset.get('strip_exif'))


def build_watermark(args, parser):
    """Erstellt das Wasserzeichen-Dict aus den CLI-Argumenten"""
    if not args.watermark_text and not args.watermark_image:
        return None
    if args.watermark_image and not Path(args.watermark_image).is_file():
        parser.error(tr("Wasserzeichen-Bild '{path}' existiert nicht")
                     .format(path=args.watermark_image))
    return {
        'text': args.watermark_text,
        'image_path': args.watermark_image,
        'position': args.watermark_pos,
        'opacity': args.watermark_opacity,
    }


def main():
    parser = argparse.ArgumentParser(
        description=tr('PicConverter CLI - Konvertiert Bilder und PDFs zwischen Formaten'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=tr("""
Unterstützte Formate: {formats}
EXIF-Felder für --exif-set: {exif_fields}
Presets: {presets}

Beispiele:
  %(prog)s bild.jpg -f png -o ausgabe.png
  %(prog)s *.jpg -f webp -q 85                      # Batch
  %(prog)s foto.jpg -f jpg --target-size 500        # max. 500 KB
  %(prog)s dokument.pdf -f png --page all --dpi 300 # alle Seiten
  %(prog)s scan1.png scan2.png -f pdf --merge -o dokument.pdf
  %(prog)s foto.jpg --preset web                    # Preset anwenden
  %(prog)s foto.jpg -f jpg --strip-exif             # Metadaten entfernen
  %(prog)s foto.jpg -f jpg --watermark-text "© 2026"
        """).format(formats=', '.join(core.FORMAT_BY_EXT),
                    exif_fields=', '.join(core.EXIF_EDITABLE_TAGS),
                    presets=', '.join(sorted(core.load_presets())))
    )

    parser.add_argument('inputs', nargs='*', metavar=tr('EINGABE'),
                        help=tr('Eingabedateien (auch mehrere oder Glob-Muster wie *.jpg)'))
    parser.add_argument('-f', '--format', '--to', dest='format',
                        choices=list(core.FORMAT_BY_EXT.keys()),
                        help=tr('Zielformat für die Konvertierung'))
    parser.add_argument('-o', '--output', dest='output',
                        help=tr('Ausgabedatei (bei einer Eingabe) oder Ausgabeordner (bei mehreren)'))
    parser.add_argument('-q', '--quality', type=int,
                        help=tr('Qualität/Kompression (JPEG/WebP: 1-100, PNG: 0-9)'))
    parser.add_argument('--target-size', type=int, metavar='KB',
                        help=tr('Zielgröße in KB — sucht die passende Qualität (nur JPEG/WebP)'))
    parser.add_argument('-w', '--width', type=int,
                        help=tr('Breite in Pixeln (Höhe wird ggf. seitenverhältnistreu ergänzt)'))
    parser.add_argument('--height', type=int,
                        help=tr('Höhe in Pixeln (Breite wird ggf. seitenverhältnistreu ergänzt)'))
    parser.add_argument('--estimate', action='store_true',
                        help=tr('Zeigt geschätzte Ausgabegröße ohne zu konvertieren'))
    parser.add_argument('--page', default='1',
                        help=tr("PDF-Eingabe: Seitennummer oder 'all' für alle Seiten (Standard: 1)"))
    parser.add_argument('--dpi', type=int, default=core.PDF_RENDER_DPI,
                        help=tr('PDF-Eingabe: Render-Auflösung in DPI (Standard: {dpi})')
                        .format(dpi=core.PDF_RENDER_DPI))
    parser.add_argument('--merge', action='store_true',
                        help=tr('Alle Eingaben in eine mehrseitige PDF zusammenfassen (nur -f pdf)'))
    parser.add_argument('--strip-exif', action='store_true',
                        help=tr('EXIF-Metadaten nicht in die Ausgabe übernehmen'))
    parser.add_argument('--exif-set', action='append', metavar=tr('FELD=WERT'),
                        help=tr('EXIF-Feld setzen (leerer Wert löscht das Feld); mehrfach nutzbar'))
    parser.add_argument('--watermark-text', metavar=tr('TEXT'),
                        help=tr('Text-Wasserzeichen einfügen'))
    parser.add_argument('--watermark-image', metavar=tr('DATEI'),
                        help=tr('Bild-Wasserzeichen (z.B. Logo mit Transparenz) einfügen'))
    parser.add_argument('--watermark-pos', choices=core.WATERMARK_POSITIONS,
                        default='unten-rechts',
                        help=tr('Position des Wasserzeichens (Standard: unten-rechts)'))
    parser.add_argument('--watermark-opacity', type=int, default=50, metavar='0-100',
                        help=tr('Deckkraft des Wasserzeichens in Prozent (Standard: 50)'))
    parser.add_argument('--preset', metavar=tr('NAME'),
                        help=tr('Preset anwenden (explizite Optionen haben Vorrang)'))
    parser.add_argument('--save-preset', metavar=tr('NAME'),
                        help=tr('Aktuelle Optionen als Preset speichern'))
    parser.add_argument('--overwrite', action='store_true',
                        help=tr('Vorhandene Dateien überschreiben statt auf "name (1).ext" auszuweichen'))
    parser.add_argument('--jobs', type=int, metavar='N',
                        help=tr('Anzahl paralleler Konvertierungen (Standard: automatisch)'))
    parser.add_argument('--quiet', action='store_true',
                        help=tr('Nur Fehler ausgeben'))
    parser.add_argument('--version', action='version',
                        version=f"PicConverter {core.__version__}")

    args = parser.parse_args()

    def say(message):
        if not args.quiet:
            print(message)

    # Preset speichern (auch ohne Eingaben nutzbar)
    if args.save_preset:
        core.save_user_preset(args.save_preset, {
            'format': args.format, 'quality': args.quality,
            'target_kb': args.target_size, 'width': args.width,
            'height': args.height, 'strip_exif': args.strip_exif,
        })
        say(tr("✓ Preset '{name}' gespeichert").format(name=args.save_preset))
        if not args.inputs:
            return

    if not args.inputs:
        parser.error(tr("Keine Eingabedateien angegeben"))

    if args.preset:
        apply_preset(args, parser)

    if args.format is None:
        parser.error(tr("Kein Zielformat: -f angeben oder ein Preset mit Format wählen"))

    # Argumente validieren
    if args.page != 'all':
        try:
            if int(args.page) < 1:
                raise ValueError
        except ValueError:
            parser.error(
                tr("--page erwartet eine Seitennummer >= 1 oder 'all', nicht '{value}'")
                .format(value=args.page))

    if args.quality is not None and args.target_size is not None:
        parser.error(tr("--quality und --target-size schließen sich gegenseitig aus"))

    output_format = core.FORMAT_BY_EXT[args.format.lower()]

    if args.target_size is not None and output_format not in core.TARGET_SIZE_FORMATS:
        parser.error(tr("--target-size wird nur für {formats} unterstützt")
                     .format(formats=', '.join(sorted(core.TARGET_SIZE_FORMATS))))

    if args.merge and output_format != 'PDF':
        parser.error(tr("--merge funktioniert nur mit -f pdf"))

    watermark = build_watermark(args, parser)

    try:
        exif_overrides = parse_exif_overrides(args.exif_set)
        inputs = expand_inputs(args.inputs)
        jobs = build_jobs(inputs, args.page)
    except Exception as e:
        print(tr("Fehler: {error}").format(error=e), file=sys.stderr)
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
            print(tr("Warnung: Qualität {value} außerhalb des Bereichs [{min}-{max}]. "
                     "Verwende Standardwert.").format(value=quality, min=q_min, max=q_max),
                  file=sys.stderr)
            quality = core.QUALITY_SETTINGS[output_format]['default']

    # Sonderfall: alles in eine PDF zusammenfassen
    if args.merge:
        try:
            images = [core.load_image(path, page or 1, args.dpi) for path, page in jobs]
            if watermark:
                images = [core.apply_watermark(img, **watermark) for img in images]
            out = Path(args.output) if args.output else \
                inputs[0].parent / f"{inputs[0].stem}_gesamt.pdf"
            if not args.overwrite:
                out = core.unique_path(out)
            core.images_to_pdf(images, out)
            size_mb = out.stat().st_size / (1024 * 1024)
            say(tr("✓ {count} Seite(n) zusammengefasst in: {out} ({size:.2f} MB)")
                .format(count=len(images), out=out, size=size_mb))
        except Exception as e:
            print(tr("✗ Fehler beim Zusammenfassen: {error}").format(error=e),
                  file=sys.stderr)
            sys.exit(1)
        return

    out_file, out_dir = resolve_output(args.output, len(jobs) == 1)
    extension = args.format.lower()
    outputs = reserve_outputs(jobs, extension, out_file, out_dir,
                              args.page == 'all', args.overwrite)

    def run_job(path, page, out):
        """Konvertiert einen Auftrag; gibt (ok, Meldung) zurück"""
        label = path.name if page is None else f"{path.name} ({tr('Seite')} {page})"
        try:
            img = core.load_image(path, page or 1, args.dpi)
            width, height = resolve_resolution(img, args.width, args.height)

            job_quality = quality
            note = ''
            if args.target_size is not None:
                job_quality, est = core.quality_for_target(
                    img, output_format, args.target_size, width, height,
                    exif_mode, exif_overrides, watermark)
                note = tr(" [Zielgröße {kb} KB → Qualität {q}]").format(
                    kb=args.target_size, q=job_quality)

            if args.estimate:
                est = core.estimate_size(img, output_format, job_quality,
                                         width, height, exif_mode,
                                         exif_overrides, watermark)
                original_mb = path.stat().st_size / (1024 * 1024)
                return True, tr("~ {label}: geschätzt {est:.2f} MB (Original: {orig:.2f} MB)") \
                    .format(label=label, est=est, orig=original_mb)

            if core.is_animated(img) and output_format not in core.ANIMATED_FORMATS:
                note += tr(" [Hinweis: Animation geht in diesem Format verloren]")

            core.convert(img, out, output_format, job_quality, width, height,
                         exif_mode, exif_overrides, watermark)
            size_mb = out.stat().st_size / (1024 * 1024)
            return True, f"✓ {label} → {out} ({size_mb:.2f} MB){note}"
        except Exception as e:
            return False, f"✗ {label}: {e}"

    workers = args.jobs if args.jobs and args.jobs > 0 else min(4, os.cpu_count() or 1)
    failures = 0

    if workers > 1 and len(jobs) > 1 and not args.estimate:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_job, path, page, out)
                       for (path, page), out in zip(jobs, outputs)]
            for future in as_completed(futures):
                ok, message = future.result()
                if ok:
                    say(message)
                else:
                    failures += 1
                    print(message, file=sys.stderr)
    else:
        for (path, page), out in zip(jobs, outputs):
            ok, message = run_job(path, page, out)
            if ok:
                say(message)
            else:
                failures += 1
                print(message, file=sys.stderr)

    if args.estimate and not failures:
        say(tr("\nNur Schätzung angefordert. Keine Konvertierung durchgeführt."))

    if failures:
        print(tr("\n{failed} von {total} Auftrag/Aufträgen fehlgeschlagen.")
              .format(failed=failures, total=len(jobs)), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
