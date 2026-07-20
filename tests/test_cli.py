"""Tests für picconverter_cli (End-to-End über subprocess)"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
import picconverter_core as core  # noqa: E402

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


def test_version():
    result = run_cli('--version')
    assert result.returncode == 0
    assert f'PicConverter {core.__version__}' in result.stdout


def test_ueberschreibschutz(sample_jpg, tmp_path):
    out = tmp_path / 'bild.png'
    out.write_bytes(b'bestehende datei')
    result = run_cli(sample_jpg, '-f', 'png', '-o', out)
    assert result.returncode == 0, result.stderr
    assert out.read_bytes() == b'bestehende datei'  # Original unangetastet
    assert (tmp_path / 'bild (1).png').exists()


def test_overwrite_flag(sample_jpg, tmp_path):
    out = tmp_path / 'bild.png'
    out.write_bytes(b'bestehende datei')
    result = run_cli(sample_jpg, '-f', 'png', '-o', out, '--overwrite')
    assert result.returncode == 0, result.stderr
    assert Image.open(out).format == 'PNG'
    assert not (tmp_path / 'bild (1).png').exists()


def test_preset(sample_jpg, tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'conf'))
    result = run_cli(sample_jpg, '--preset', 'web', '-o', tmp_path / 'aus.webp')
    assert result.returncode == 0, result.stderr
    assert Image.open(tmp_path / 'aus.webp').format == 'WEBP'


def test_preset_speichern_und_nutzen(sample_jpg, tmp_path):
    env = dict(os.environ, XDG_CONFIG_HOME=str(tmp_path / 'conf'))
    saved = subprocess.run(
        [sys.executable, str(CLI), '--save-preset', 'klein', '-f', 'jpg', '-q', '30'],
        capture_output=True, text=True, env=env)
    assert saved.returncode == 0, saved.stderr
    used = subprocess.run(
        [sys.executable, str(CLI), str(sample_jpg), '--preset', 'klein',
         '-o', str(tmp_path / 'klein.jpg')],
        capture_output=True, text=True, env=env)
    assert used.returncode == 0, used.stderr
    assert (tmp_path / 'klein.jpg').exists()


def test_wasserzeichen_text(sample_jpg, tmp_path):
    out = tmp_path / 'marke.png'
    result = run_cli(sample_jpg, '-f', 'png', '--watermark-text', 'Demo',
                     '--watermark-opacity', '100', '-o', out)
    assert result.returncode == 0, result.stderr
    assert Image.open(out).size == (120, 80)


def test_quiet(sample_jpg, tmp_path):
    result = run_cli(sample_jpg, '-f', 'png', '-o', tmp_path / 'q.png', '--quiet')
    assert result.returncode == 0
    assert result.stdout.strip() == ''


def test_animierte_gif_batch(tmp_path):
    frames = [Image.new('RGB', (40, 30), c) for c in ('red', 'blue')]
    src = tmp_path / 'anim.gif'
    frames[0].save(src, save_all=True, append_images=frames[1:], duration=100)
    result = run_cli(src, '-f', 'webp', '-o', tmp_path / 'anim.webp')
    assert result.returncode == 0, result.stderr
    assert Image.open(tmp_path / 'anim.webp').n_frames == 2


def test_englische_ausgabe(sample_jpg, tmp_path):
    env = dict(os.environ, PICCONVERTER_LANG='en')
    result = subprocess.run(
        [sys.executable, str(CLI), '--help'],
        capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert 'Target format' in result.stdout


def test_estimate_schreibt_nichts(sample_jpg, tmp_path):
    out = tmp_path / 'nie.png'
    result = run_cli(sample_jpg, '-f', 'png', '--estimate', '-o', out)
    assert result.returncode == 0, result.stderr
    assert not out.exists()
    assert 'geschätzt' in result.stdout


@pytest.fixture
def sample_svg(tmp_path):
    path = tmp_path / 'kreis.svg'
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" '
        'viewBox="0 0 100 60">'
        '<circle cx="50" cy="30" r="25" fill="#3399ff"/></svg>'
    )
    return path


def test_svg_zu_png(sample_svg, tmp_path):
    pytest.importorskip("pymupdf")
    out = tmp_path / 'kreis.png'
    result = run_cli(sample_svg, '-f', 'png', '-o', out, '--dpi', '72')
    assert result.returncode == 0, result.stderr
    assert Image.open(out).size == (100, 60)


def test_svg_zielbreite(sample_svg, tmp_path):
    pytest.importorskip("pymupdf")
    out = tmp_path / 'gross.png'
    result = run_cli(sample_svg, '-f', 'png', '-o', out, '--svg-width', '500')
    assert result.returncode == 0, result.stderr
    assert Image.open(out).size == (500, 300)


def test_svg_breite_muss_positiv_sein(sample_svg, tmp_path):
    result = run_cli(sample_svg, '-f', 'png', '-o', tmp_path / 'x.png',
                     '--svg-width', '0')
    assert result.returncode != 0
    assert 'größer als 0' in result.stderr
