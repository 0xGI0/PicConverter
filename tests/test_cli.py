"""Tests für picconverter_cli (End-to-End über subprocess)"""

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
import picconverter_core as core

CLI = Path(__file__).parent.parent / 'picconverter_cli.py'


def run_cli(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                          capture_output=True, text=True)


@pytest.fixture
def sample_jpg(tmp_path):
    path = tmp_path / 'bild.jpg'
    Image.new('RGB', (120, 80), (200, 50, 50)).save(path)
    return path


def test_einfache_konvertierung(sample_jpg, tmp_path):
    out = tmp_path / 'bild.png'
    result = run_cli(sample_jpg, '-f', 'png', '-o', out)
    assert result.returncode == 0, result.stderr
    assert Image.open(out).format == 'PNG'


def test_batch_in_ordner(tmp_path):
    for name in ('a.jpg', 'b.jpg'):
        Image.new('RGB', (50, 50)).save(tmp_path / name)
    out_dir = tmp_path / 'out'
    result = run_cli(tmp_path / 'a.jpg', tmp_path / 'b.jpg',
                     '-f', 'webp', '-o', str(out_dir) + '/')
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in out_dir.iterdir()) == ['a.webp', 'b.webp']


def test_fehlende_datei(tmp_path):
    result = run_cli(tmp_path / 'gibtsnicht.jpg', '-f', 'png')
    assert result.returncode == 1
    assert 'existiert nicht' in result.stderr


def test_strip_exif(sample_jpg, tmp_path):
    out = tmp_path / 'ohne.jpg'
    exif = Image.Exif()
    exif[0x013B] = 'Wer'
    img = Image.open(sample_jpg)
    img.save(sample_jpg, exif=exif)
    result = run_cli(sample_jpg, '-f', 'jpg', '--strip-exif', '-o', out)
    assert result.returncode == 0, result.stderr
    assert len(Image.open(out).getexif()) == 0


def test_exif_set(sample_jpg, tmp_path):
    out = tmp_path / 'neu.jpg'
    result = run_cli(sample_jpg, '-f', 'jpg', '--exif-set', 'Artist=Testautor',
                     '-o', out)
    assert result.returncode == 0, result.stderr
    assert Image.open(out).getexif()[0x013B] == 'Testautor'


def test_quality_und_target_size_schliessen_sich_aus(sample_jpg):
    result = run_cli(sample_jpg, '-f', 'jpg', '-q', '80', '--target-size', '100')
    assert result.returncode == 2


def test_merge_nur_mit_pdf(sample_jpg):
    result = run_cli(sample_jpg, '-f', 'png', '--merge')
    assert result.returncode == 2


def test_merge(tmp_path):
    pytest.importorskip("pymupdf")
    import pymupdf
    for name in ('a.png', 'b.png'):
        Image.new('RGB', (50, 50)).save(tmp_path / name)
    out = tmp_path / 'gesamt.pdf'
    result = run_cli(tmp_path / 'a.png', tmp_path / 'b.png',
                     '-f', 'pdf', '--merge', '-o', out)
    assert result.returncode == 0, result.stderr
    doc = pymupdf.open(out)
    assert doc.page_count == 2
    doc.close()


def test_pdf_alle_seiten(tmp_path):
    pytest.importorskip("pymupdf")
    import pymupdf
    doc = pymupdf.open()
    for _ in range(3):
        doc.new_page(width=200, height=200)
    pdf = tmp_path / 'drei.pdf'
    doc.save(pdf)
    doc.close()
    out_dir = tmp_path / 'seiten'
    result = run_cli(pdf, '-f', 'png', '--page', 'all', '--dpi', '72',
                     '-o', str(out_dir) + '/')
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in out_dir.iterdir()) == \
        ['drei_seite1.png', 'drei_seite2.png', 'drei_seite3.png']


def test_estimate_schreibt_nichts(sample_jpg, tmp_path):
    out = tmp_path / 'nie.png'
    result = run_cli(sample_jpg, '-f', 'png', '--estimate', '-o', out)
    assert result.returncode == 0, result.stderr
    assert not out.exists()
    assert 'geschätzt' in result.stdout
