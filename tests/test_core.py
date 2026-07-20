"""Tests für picconverter_core"""

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
import picconverter_core as core

pymupdf = pytest.importorskip("pymupdf", reason="PDF-Tests benötigen PyMuPDF")


@pytest.fixture
def rgba_image():
    img = Image.new('RGBA', (200, 100), (255, 0, 0, 0))
    for x in range(100):
        for y in range(100):
            img.putpixel((x, y), (0, 100, 200, 255))
    return img


@pytest.fixture
def oriented_jpeg(tmp_path):
    """JPEG 200x100 mit Orientation=6 (90° drehen) und EXIF-Daten"""
    img = Image.new('RGB', (200, 100), (10, 20, 30))
    exif = Image.Exif()
    exif[core.ORIENTATION_TAG] = 6
    exif[0x013B] = 'Testautor'
    path = tmp_path / 'orientiert.jpg'
    img.save(path, exif=exif)
    return path


@pytest.fixture
def svg_file(tmp_path):
    """SVG 100x60: blauer Kreis auf transparentem Grund"""
    path = tmp_path / 'kreis.svg'
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" '
        'viewBox="0 0 100 60">'
        '<circle cx="50" cy="30" r="25" fill="#3399ff"/></svg>'
    )
    return path


@pytest.fixture
def fluid_svg(tmp_path):
    """SVG mit Prozent-Maßen -- MuPDF kennt dafür nur eine Letter-Seite"""
    path = tmp_path / 'fluid.svg'
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        'viewBox="0 0 200 100"><rect width="200" height="100" fill="#ee9944"/>'
        '</svg>'
    )
    return path


@pytest.fixture
def two_page_pdf(tmp_path):
    doc = pymupdf.open()
    for i in range(2):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f'Seite {i + 1}', fontsize=36)
    path = tmp_path / 'zwei_seiten.pdf'
    doc.save(path)
    doc.close()
    return path


class TestLoadImage:
    def test_exif_orientierung_wird_eingerechnet(self, oriented_jpeg):
        img = core.load_image(oriented_jpeg)
        assert img.size == (100, 200)

    def test_orientation_tag_wird_entfernt(self, oriented_jpeg):
        img = core.load_image(oriented_jpeg)
        exif = core.build_exif(img, 'keep')
        assert core.ORIENTATION_TAG not in exif
        assert exif[0x013B] == 'Testautor'

    def test_pdf_seite_rendern(self, two_page_pdf):
        img = core.load_image(two_page_pdf, page=1, dpi=72)
        assert img.size == (595, 842)

    def test_pdf_ungueltige_seite(self, two_page_pdf):
        with pytest.raises(RuntimeError, match="Seite 5 existiert nicht"):
            core.load_image(two_page_pdf, page=5)

    def test_pdf_seitenanzahl(self, two_page_pdf):
        assert core.pdf_page_count(two_page_pdf) == 2


class TestSvg:
    def test_svg_wird_erkannt(self, svg_file):
        assert core.is_svg(svg_file)
        assert not core.is_svg('bild.png')

    def test_svg_ist_eingabeformat(self):
        assert 'svg' in core.INPUT_EXTENSIONS

    def test_72_dpi_ergibt_originalgroesse(self, svg_file):
        assert core.load_image(svg_file, dpi=72).size == (100, 60)

    def test_dpi_skaliert_verlustfrei(self, svg_file):
        assert core.load_image(svg_file, dpi=144).size == (200, 120)

    def test_zielbreite_schlaegt_dpi(self, svg_file):
        img = core.load_image(svg_file, dpi=72, svg_width=400)
        assert img.size == (400, 240)

    def test_transparenz_bleibt_erhalten(self, svg_file):
        img = core.load_image(svg_file, dpi=72)
        assert img.mode == 'RGBA'
        assert img.getpixel((0, 0))[3] == 0      # Ecke ist transparent
        assert img.getpixel((50, 30))[3] == 255  # Kreis ist deckend

    def test_kaputtes_svg_meldet_klartext(self, tmp_path):
        bad = tmp_path / 'kaputt.svg'
        bad.write_text('<svg><kein gueltiges svg')
        with pytest.raises(RuntimeError, match="konnte nicht gelesen werden"):
            core.load_image(bad)

    def test_prozentmasse_folgen_der_viewbox(self, fluid_svg):
        img = core.load_image(fluid_svg, svg_width=800)
        assert img.size == (800, 400)

    def test_prozentmasse_ohne_zielbreite_behalten_verhaeltnis(self, fluid_svg):
        w, h = core.load_image(fluid_svg, dpi=72).size
        assert round(w / h, 2) == 2.0

    def test_prozentmasse_lassen_keinen_rand_stehen(self, fluid_svg):
        img = core.load_image(fluid_svg, svg_width=200)
        assert img.size == (200, 100)
        assert img.getpixel((0, 0))[3] == 255      # Inhalt bis in die Ecken
        assert img.getpixel((199, 99))[3] == 255

    def test_svg_zu_jpeg_flacht_transparenz_ab(self, svg_file, tmp_path):
        img = core.load_image(svg_file, dpi=72)
        out = tmp_path / 'kreis.jpg'
        core.convert(img, out, 'JPEG')
        assert Image.open(out).getpixel((0, 0)) == (255, 255, 255)


class TestPrepareForFormat:
    def test_rgba_wird_fuer_pdf_abgeflacht(self, rgba_image):
        result = core.prepare_for_format(rgba_image, 'PDF')
        assert result.mode == 'RGB'
        # Transparenter Bereich wird weiß
        assert result.getpixel((150, 50)) == (255, 255, 255)
        assert result.getpixel((50, 50)) == (0, 100, 200)

    def test_rgba_bleibt_fuer_png(self, rgba_image):
        assert core.prepare_for_format(rgba_image, 'PNG').mode == 'RGBA'


class TestConvert:
    def test_bild_zu_pdf(self, rgba_image, tmp_path):
        out = tmp_path / 'out.pdf'
        core.convert(rgba_image, out, 'PDF')
        doc = pymupdf.open(out)
        assert doc.page_count == 1
        doc.close()

    def test_pdf_seite_zu_png(self, two_page_pdf, tmp_path):
        img = core.load_image(two_page_pdf, page=2, dpi=100)
        out = tmp_path / 'seite2.png'
        core.convert(img, out, 'PNG')
        assert Image.open(out).size == img.size

    def test_resize(self, rgba_image, tmp_path):
        out = tmp_path / 'klein.png'
        core.convert(rgba_image, out, 'PNG', width=100, height=50)
        assert Image.open(out).size == (100, 50)


class TestExif:
    def test_strip(self, oriented_jpeg, tmp_path):
        img = core.load_image(oriented_jpeg)
        out = tmp_path / 'ohne.jpg'
        core.convert(img, out, 'JPEG', exif_mode='strip')
        assert len(Image.open(out).getexif()) == 0

    def test_keep(self, oriented_jpeg, tmp_path):
        img = core.load_image(oriented_jpeg)
        out = tmp_path / 'mit.jpg'
        core.convert(img, out, 'JPEG', exif_mode='keep')
        exif = Image.open(out).getexif()
        assert exif[0x013B] == 'Testautor'
        assert core.ORIENTATION_TAG not in exif

    def test_override_setzen_und_loeschen(self, oriented_jpeg, tmp_path):
        img = core.load_image(oriented_jpeg)
        out = tmp_path / 'geaendert.jpg'
        core.convert(img, out, 'JPEG', exif_mode='keep',
                     exif_overrides={'Copyright': 'CC-BY', 'Artist': ''})
        exif = Image.open(out).getexif()
        assert exif[0x8298] == 'CC-BY'
        assert 0x013B not in exif

    def test_strip_mit_override(self, oriented_jpeg, tmp_path):
        """strip + override = nur die gesetzten Felder bleiben"""
        img = core.load_image(oriented_jpeg)
        out = tmp_path / 'nur_artist.jpg'
        core.convert(img, out, 'JPEG', exif_mode='strip',
                     exif_overrides={'Artist': 'Neu'})
        exif = Image.open(out).getexif()
        assert dict(exif) == {0x013B: 'Neu'}

    def test_unbekanntes_feld(self, rgba_image):
        with pytest.raises(ValueError, match="Unbekanntes EXIF-Feld"):
            core.build_exif(rgba_image, 'keep', {'Quatsch': 'x'})


class TestTargetSize:
    def test_zielgroesse_wird_eingehalten(self, tmp_path):
        import random
        random.seed(42)
        img = Image.new('RGB', (500, 400))
        img.putdata([(random.randrange(256),) * 3 for _ in range(500 * 400)])
        quality, size_mb = core.quality_for_target(img, 'JPEG', target_kb=50)
        assert 1 <= quality <= 100
        assert size_mb * 1024 <= 50

    def test_nur_jpeg_webp(self, rgba_image):
        with pytest.raises(ValueError, match="Zielgröße"):
            core.quality_for_target(rgba_image, 'PNG', target_kb=50)


class TestImagesToPdf:
    def test_mehrere_bilder_eine_pdf(self, rgba_image, tmp_path):
        images = [rgba_image, Image.new('RGB', (300, 300), 'white'),
                  Image.new('L', (100, 100), 128)]
        out = tmp_path / 'gesamt.pdf'
        core.images_to_pdf(images, out)
        doc = pymupdf.open(out)
        assert doc.page_count == 3
        doc.close()

    def test_leere_liste(self, tmp_path):
        with pytest.raises(ValueError):
            core.images_to_pdf([], tmp_path / 'leer.pdf')


class TestEstimate:
    def test_schaetzung_nah_an_realitaet(self, rgba_image, tmp_path):
        estimated = core.estimate_size(rgba_image, 'PNG', quality=6)
        out = tmp_path / 'echt.png'
        core.convert(rgba_image, out, 'PNG', quality=6)
        real = out.stat().st_size / (1024 * 1024)
        assert abs(estimated - real) < 0.01


@pytest.fixture
def animated_gif(tmp_path):
    frames = [Image.new('RGB', (80, 60), c) for c in ('red', 'green', 'blue')]
    path = tmp_path / 'anim.gif'
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=200, loop=0)
    return path


class TestAnimation:
    def test_gif_zu_gif_behaelt_frames(self, animated_gif, tmp_path):
        img = core.load_image(animated_gif)
        assert core.is_animated(img)
        out = tmp_path / 'out.gif'
        core.convert(img, out, 'GIF')
        assert Image.open(out).n_frames == 3

    def test_gif_zu_webp_behaelt_frames(self, animated_gif, tmp_path):
        img = core.load_image(animated_gif)
        out = tmp_path / 'out.webp'
        core.convert(img, out, 'WebP', quality=80)
        assert Image.open(out).n_frames == 3

    def test_gif_zu_png_nimmt_erstes_frame(self, animated_gif, tmp_path):
        img = core.load_image(animated_gif)
        out = tmp_path / 'out.png'
        core.convert(img, out, 'PNG')
        result = Image.open(out)
        assert getattr(result, 'n_frames', 1) == 1

    def test_animation_mit_resize(self, animated_gif, tmp_path):
        img = core.load_image(animated_gif)
        out = tmp_path / 'klein.gif'
        core.convert(img, out, 'GIF', width=40, height=30)
        result = Image.open(out)
        assert result.size == (40, 30) and result.n_frames == 3


class TestWatermark:
    def test_text_wasserzeichen(self):
        img = Image.new('RGB', (400, 300), 'black')
        marked = core.apply_watermark(img, text='Test', opacity=100)
        assert marked.size == img.size
        assert marked.getpixel((10, 10)) == (0, 0, 0)  # oben links unberührt
        # Unten rechts muss sich etwas verändert haben
        region = marked.crop((200, 200, 400, 300))
        assert region.getextrema() != ((0, 0), (0, 0), (0, 0))

    def test_bild_wasserzeichen(self, tmp_path):
        logo = tmp_path / 'logo.png'
        Image.new('RGBA', (50, 50), (255, 255, 255, 255)).save(logo)
        img = Image.new('RGB', (400, 300), 'black')
        marked = core.apply_watermark(img, image_path=logo,
                                      position='mitte', opacity=100)
        assert marked.getpixel((200, 150)) != (0, 0, 0)

    def test_ohne_angaben_unveraendert(self):
        img = Image.new('RGB', (10, 10), 'red')
        assert core.apply_watermark(img) is img


class TestUniquePath:
    def test_frei_bleibt_gleich(self, tmp_path):
        p = tmp_path / 'neu.png'
        assert core.unique_path(p) == p

    def test_zaehlt_hoch(self, tmp_path):
        p = tmp_path / 'da.png'
        p.write_bytes(b'x')
        assert core.unique_path(p) == tmp_path / 'da (1).png'
        (tmp_path / 'da (1).png').write_bytes(b'x')
        assert core.unique_path(p) == tmp_path / 'da (2).png'


@pytest.mark.skipif(not core.HEIF_AVAILABLE, reason="pillow-heif fehlt")
class TestHeic:
    def test_heic_laden_und_konvertieren(self, tmp_path):
        src = tmp_path / 'foto.heic'
        Image.new('RGB', (120, 90), (10, 120, 200)).save(src, format='HEIF')
        img = core.load_image(src)
        assert img.size == (120, 90)
        out = tmp_path / 'foto.jpg'
        core.convert(img, out, 'JPEG', quality=90)
        assert Image.open(out).format == 'JPEG'

    def test_heic_in_input_extensions(self):
        assert 'heic' in core.INPUT_EXTENSIONS

    @pytest.mark.skipif(not core.AVIF_AVAILABLE, reason="AVIF nicht verfügbar")
    def test_avif_laden(self, tmp_path):
        src = tmp_path / 'foto.avif'
        Image.new('RGB', (60, 40), (200, 30, 30)).save(src)
        assert core.load_image(src).size == (60, 40)


class TestPresets:
    def test_builtin_presets_vorhanden(self):
        presets = core.load_presets()
        assert 'web' in presets and 'email' in presets

    def test_nutzer_preset_speichern(self, tmp_path, monkeypatch):
        monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
        core.save_user_preset('mein', {'format': 'jpg', 'quality': 70,
                                       'unbekannt': 'wird verworfen'})
        presets = core.load_presets()
        assert presets['mein'] == {'format': 'jpg', 'quality': 70}


class TestOutputStem:
    def test_ohne_seite(self):
        assert core.output_stem(Path('foto.jpg')) == 'foto'

    def test_seite_eins_ohne_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=1) == 'doc'

    def test_seite_zwei_mit_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=2) == 'doc_seite2'

    def test_alle_seiten_immer_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=1, all_pages=True) == 'doc_seite1'
