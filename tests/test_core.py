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


class TestOutputStem:
    def test_ohne_seite(self):
        assert core.output_stem(Path('foto.jpg')) == 'foto'

    def test_seite_eins_ohne_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=1) == 'doc'

    def test_seite_zwei_mit_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=2) == 'doc_seite2'

    def test_alle_seiten_immer_suffix(self):
        assert core.output_stem(Path('doc.pdf'), page=1, all_pages=True) == 'doc_seite1'
