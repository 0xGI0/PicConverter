#!/usr/bin/env python3
"""
PicConverter GUI - Modernes Bild- & PDF-Konvertierungs-Tool (PySide6/Qt)
"""

import os
import sys
import threading
from pathlib import Path

try:
    from PySide6.QtCore import QObject, QSize, Qt, QUrl, Signal
    from PySide6.QtGui import (QDesktopServices, QFontDatabase, QGuiApplication,
                               QIcon, QImage, QPalette, QColor, QPixmap)
    from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox,
                                   QDialog, QFileDialog, QFrame, QHBoxLayout,
                                   QInputDialog, QLabel, QLineEdit, QListWidget,
                                   QListWidgetItem, QMainWindow, QPlainTextEdit,
                                   QProgressBar, QPushButton, QScrollArea, QSlider,
                                   QStackedWidget, QVBoxLayout, QWidget)
except ImportError:
    print("Fehler: PySide6 konnte nicht importiert werden.", file=sys.stderr)
    print("\nBitte installieren Sie die Abhängigkeiten:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

from PIL import Image

import picconverter_core as core
from picconverter_i18n import tr

ASSETS = Path(__file__).parent / 'assets'

# Anzeigename -> PIL-Formatname
SUPPORTED_FORMATS = {
    'JPEG (.jpg, .jpeg)': 'JPEG',
    'PNG (.png)': 'PNG',
    'BMP (.bmp)': 'BMP',
    'TIFF (.tiff, .tif)': 'TIFF',
    'GIF (.gif)': 'GIF',
    'WebP (.webp)': 'WebP',
    'ICO (.ico)': 'ICO',
    'PDF (.pdf)': 'PDF'
}

# Dateiendung je Anzeigename
EXT_MAP = {
    'JPEG (.jpg, .jpeg)': '.jpg',
    'PNG (.png)': '.png',
    'BMP (.bmp)': '.bmp',
    'TIFF (.tiff, .tif)': '.tiff',
    'GIF (.gif)': '.gif',
    'WebP (.webp)': '.webp',
    'ICO (.ico)': '.ico',
    'PDF (.pdf)': '.pdf'
}

# Formatname (Endung ohne Punkt) -> Anzeigename, für Presets
LABEL_BY_EXT = {ext.lstrip('.'): label for label, ext in EXT_MAP.items()}
LABEL_BY_EXT['jpeg'] = LABEL_BY_EXT['jpg']

# Akzeptierte Eingabedateien (Dialog und Drag & Drop)
SUPPORTED_INPUT_EXTENSIONS = {f'.{ext}' for ext in core.INPUT_EXTENSIONS}

# Maximale Anzahl Mini-Vorschaubilder in der Dateiliste
MAX_THUMBNAILS = 40

PAD = 16  # Einheitlicher Abstand zwischen Sektionen

# Farb-Tokens je Theme; 'system' folgt dem Desktop über Qt-ColorScheme
THEMES = {
    'light': {
        'window': '#f2f3f5',
        'sidebar': '#e9ebef',
        'card': '#ffffff',
        'field': '#f5f6f8',
        'border': '#dfe2e7',
        'border_strong': '#c4c9d1',
        'text': '#1d2129',
        'muted': '#697077',
        'accent': '#2c66a8',
        'accent_soft': '#e4edf7',
        'btn': '#316fb8',
        'btn_hover': '#2a609f',
        'btn_press': '#255489',
        'ghost_hover': '#eceef1',
        'seg_checked': '#ffffff',
        'success': '#1a7a3c',
        'error': '#b3261e',
        'warning': '#8a5a00',
        'chevron': 'chevron-down-light.svg',
    },
    'dark': {
        'window': '#191b1e',
        'sidebar': '#141619',
        'card': '#212428',
        'field': '#2a2e33',
        'border': '#34383e',
        'border_strong': '#4a5058',
        'text': '#e8eaed',
        'muted': '#9aa1ab',
        'accent': '#82b3e8',
        'accent_soft': '#2c3d52',
        'btn': '#3a72b4',
        'btn_hover': '#4681c4',
        'btn_press': '#356399',
        'ghost_hover': '#2e3237',
        'seg_checked': '#3a3f46',
        'success': '#8fd6a4',
        'error': '#ef9a9a',
        'warning': '#e8c47a',
        'chevron': 'chevron-down-dark.svg',
    },
}


def build_stylesheet(t):
    """Erzeugt das QSS-Stylesheet für ein Theme-Token-Set"""
    chevron = (ASSETS / t['chevron']).as_posix()
    return f"""
    QMainWindow, QDialog {{
        background: {t['window']};
    }}
    QLabel {{
        background: transparent;
        color: {t['text']};
    }}
    QLabel#sectionTitle {{
        color: {t['muted']};
    }}
    QLabel#subtitle {{
        color: {t['muted']};
    }}
    QLabel[kind="accent"] {{ color: {t['accent']}; }}
    QLabel[kind="success"] {{ color: {t['success']}; }}
    QLabel[kind="error"] {{ color: {t['error']}; }}
    QLabel[kind="warning"] {{ color: {t['warning']}; }}
    QLabel[kind="muted"] {{ color: {t['muted']}; }}
    QLabel#chip {{
        background: {t['accent_soft']};
        color: {t['accent']};
        border-radius: 4px;
        padding: 0px 5px;
    }}
    QLabel#infoBox, QLabel#previewPanel {{
        background: {t['field']};
        border: 1px solid {t['border']};
        border-radius: 8px;
    }}
    QLabel#infoBox {{ padding: 10px; }}
    QLabel#previewPanel {{ color: {t['muted']}; }}
    QFrame#card {{
        background: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 10px;
    }}
    QFrame#sidebar {{
        background: {t['sidebar']};
        border-right: 1px solid {t['border']};
    }}
    QFrame#divider {{
        background: {t['border']};
        border: none;
    }}
    QScrollArea#panelScroll {{
        background: transparent;
        border: none;
        border-left: 1px solid {t['border']};
    }}
    QScrollArea#panelScroll > QWidget > QWidget {{
        background: transparent;
    }}
    QFrame#dropZone {{
        background: {t['field']};
        border: 1.5px dashed {t['border_strong']};
        border-radius: 8px;
    }}
    QFrame#dropZone[dragOver="true"] {{
        border-color: {t['accent']};
        background: {t['accent_soft']};
    }}
    QFrame#dropZone QLabel {{ color: {t['muted']}; }}
    QFrame#statusBar {{
        background: {t['card']};
        border-top: 1px solid {t['border']};
    }}
    QFrame#segmented {{
        background: {t['field']};
        border: 1px solid {t['border']};
        border-radius: 8px;
    }}
    QPushButton {{
        background: transparent;
        color: {t['text']};
        border: 1px solid {t['border_strong']};
        border-radius: 8px;
        padding: 6px 14px;
    }}
    QPushButton:hover {{ background: {t['ghost_hover']}; }}
    QPushButton:pressed {{ background: {t['border']}; }}
    QPushButton:disabled {{
        color: {t['muted']};
        border-color: {t['border']};
    }}
    QPushButton#primary {{
        background: {t['btn']};
        color: #ffffff;
        border: none;
        font-weight: 600;
    }}
    QPushButton#primary:hover {{ background: {t['btn_hover']}; }}
    QPushButton#primary:pressed {{ background: {t['btn_press']}; }}
    QPushButton#primary:disabled {{
        background: {t['border']};
        color: {t['muted']};
    }}
    QPushButton#toolBtn {{
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 2px 8px;
        color: {t['muted']};
    }}
    QPushButton#toolBtn:hover {{
        background: {t['ghost_hover']};
        color: {t['text']};
    }}
    QPushButton#segItem {{
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 4px 12px;
        color: {t['muted']};
    }}
    QPushButton#segItem:checked {{
        background: {t['seg_checked']};
        color: {t['text']};
    }}
    QLineEdit {{
        background: {t['field']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 5px 8px;
        selection-background-color: {t['btn']};
        selection-color: #ffffff;
    }}
    QLineEdit:focus {{ border-color: {t['accent']}; }}
    QLineEdit:disabled {{
        color: {t['muted']};
        background: {t['window']};
    }}
    QComboBox {{
        background: {t['field']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 5px 10px;
    }}
    QComboBox:hover {{ border-color: {t['border_strong']}; }}
    QComboBox:focus {{ border-color: {t['accent']}; }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox::down-arrow {{
        image: url({chevron});
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background: {t['card']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {t['accent_soft']};
        selection-color: {t['text']};
        outline: none;
    }}
    QCheckBox {{
        spacing: 8px;
        color: {t['text']};
    }}
    QCheckBox:disabled {{ color: {t['muted']}; }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {t['border_strong']};
        border-radius: 4px;
        background: {t['field']};
    }}
    QCheckBox::indicator:hover {{ border-color: {t['muted']}; }}
    QCheckBox::indicator:checked {{
        background: {t['btn']};
        border-color: {t['btn']};
        image: url({(ASSETS / 'check.svg').as_posix()});
    }}
    QCheckBox::indicator:disabled {{
        border-color: {t['border']};
        background: {t['window']};
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: {t['border']};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {t['btn']};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: {t['card']};
        border: 2px solid {t['btn']};
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:disabled {{ border-color: {t['border_strong']}; }}
    QSlider::sub-page:horizontal:disabled {{ background: {t['border_strong']}; }}
    QProgressBar {{
        background: {t['field']};
        border: none;
        border-radius: 4px;
    }}
    QProgressBar::chunk {{
        background: {t['btn']};
        border-radius: 4px;
    }}
    QListWidget#fileList {{
        background: transparent;
        border: none;
        padding: 0px;
        outline: none;
    }}
    QListWidget#fileList::item {{
        border-radius: 6px;
        color: {t['text']};
    }}
    QListWidget#fileList::item:hover {{ background: {t['ghost_hover']}; }}
    QListWidget#fileList::item:selected {{ background: {t['accent_soft']}; }}
    QPlainTextEdit#exifViewer {{
        background: {t['field']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 6px;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border_strong']};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t['muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['border_strong']};
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
    QToolTip {{
        background: {t['card']};
        color: {t['text']};
        border: 1px solid {t['border']};
    }}
    """


def build_palette(t):
    """QPalette passend zum Theme -- steuert Fusion-Indikatoren und Menüs"""
    palette = QPalette()
    groups = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)
    roles = {
        QPalette.ColorRole.Window: t['window'],
        QPalette.ColorRole.WindowText: t['text'],
        QPalette.ColorRole.Base: t['field'],
        QPalette.ColorRole.AlternateBase: t['card'],
        QPalette.ColorRole.Text: t['text'],
        QPalette.ColorRole.Button: t['card'],
        QPalette.ColorRole.ButtonText: t['text'],
        QPalette.ColorRole.Highlight: t['btn'],
        QPalette.ColorRole.HighlightedText: '#ffffff',
        QPalette.ColorRole.ToolTipBase: t['card'],
        QPalette.ColorRole.ToolTipText: t['text'],
        QPalette.ColorRole.PlaceholderText: t['muted'],
    }
    for group in groups:
        for role, value in roles.items():
            palette.setColor(group, role, QColor(value))
    disabled = QPalette.ColorGroup.Disabled
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
                 QPalette.ColorRole.ButtonText):
        palette.setColor(disabled, role, QColor(t['muted']))
    return palette


def pil_to_qimage(img):
    """PIL-Bild -> QImage (RGBA, mit Kopie der Pixeldaten)"""
    rgba = img.convert('RGBA')
    data = rgba.tobytes('raw', 'RGBA')
    qimage = QImage(data, rgba.width, rgba.height,
                    QImage.Format.Format_RGBA8888)
    return qimage.copy()


def repolish(widget):
    """Wendet Style nach Änderung einer dynamischen Property neu an"""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class PreviewLabel(QLabel):
    """Vorschau-Label, das sein Bild seitenverhältnistreu mitskaliert"""

    def __init__(self, placeholder, framed=True):
        super().__init__(placeholder)
        self._source = None
        self.setObjectName("previewPanel" if framed else "stagePreview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)

    def set_image(self, pil_img):
        self._source = pil_to_qimage(pil_img)
        self._update_scaled()

    def clear_image(self, placeholder):
        self._source = None
        self.setPixmap(QPixmap())
        self.setText(placeholder)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()

    def _update_scaled(self):
        if self._source is None:
            return
        dpr = self.devicePixelRatioF()
        avail_w = max(1, int((self.width() - 24) * dpr))
        avail_h = max(1, int((self.height() - 24) * dpr))
        # Nie über die Quellauflösung hinaus vergrößern
        target_w = min(avail_w, self._source.width())
        target_h = min(avail_h, self._source.height())
        pixmap = QPixmap.fromImage(self._source).scaled(
            target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        pixmap.setDevicePixelRatio(dpr)
        self.setText("")
        self.setPixmap(pixmap)


class DropZone(QFrame):
    """Klickbare Drop-Fläche; Datei-Drops nimmt das Hauptfenster entgegen"""

    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("dropZone")
        self.setProperty("dragOver", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_drag_over(self, active):
        self.setProperty("dragOver", active)
        repolish(self)


class _WorkerSignals(QObject):
    """Signale, um Ergebnisse aus dem Worker-Thread in den GUI-Thread zu holen"""
    progress = Signal(float)
    done = Signal(list)


class PicConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("PicConverter - Bild- & PDF-Konverter"))
        icon_path = ASSETS / 'icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.input_paths = []          # Warteschlange aller geladenen Dateien
        self.selected_index = None     # Index der Datei, die Vorschau/Infos zeigt
        self.image = None              # geladenes Bild der ausgewählten Datei
        self.pdf_page_count = 0        # 0 = ausgewählte Datei ist keine PDF
        self.prefilled_size = ('', '') # zuletzt vorbefüllte Auflösungswerte
        self.exif_overrides = {}       # EXIF-Änderungen aus dem Editor
        self.output_file = None        # gewählte Zieldatei (nur Einzelkonvertierung)
        self.output_dir = None         # gewählter Zielordner
        self.last_output_dir = None    # für den "Ordner öffnen"-Button
        self.thumbnails = {}           # Pfad -> QPixmap für die Dateiliste
        self.appearance_mode = 'system'
        self._current_theme = THEMES['dark']

        self._signals = _WorkerSignals()
        self._signals.progress.connect(
            lambda p: self.progress_bar.setValue(round(p * 100)))
        self._signals.done.connect(self._on_convert_done)

        self.setup_fonts()
        self.setup_ui()
        self.apply_theme(self.appearance_mode)
        self.restore_settings()
        self.setAcceptDrops(True)

        # Systemfarbschema-Wechsel live übernehmen
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_scheme_changed)

        # Wunschgröße 1240x820, aber nie größer als der Bildschirm
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(1240, int(screen.width() * 0.92))
        height = min(820, int(screen.height() * 0.90))
        self.resize(width, height)
        self.setMinimumSize(min(1024, width), min(620, height))

    # ---------- Fonts und Grundgerüst ----------

    def setup_fonts(self):
        base = QApplication.font()
        self.font_section = QApplication.font()
        self.font_section.setPointSizeF(max(8.0, base.pointSizeF() * 0.82))
        self.font_section.setWeight(self.font_section.Weight.DemiBold)
        self.font_section.setLetterSpacing(
            self.font_section.SpacingType.PercentageSpacing, 108)
        self.font_bold = QApplication.font()
        self.font_bold.setWeight(self.font_bold.Weight.DemiBold)
        self.font_small = QApplication.font()
        self.font_small.setPointSizeF(max(7.5, base.pointSizeF() * 0.78))
        self.font_mono = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.FixedFont)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main = QHBoxLayout()
        main.setSpacing(0)
        outer.addLayout(main, 1)

        # ---------- Sidebar: Logo, Dateiauswahl, Warteschlange, Theme ----------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(252)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 16, 14, 14)
        side.setSpacing(8)

        self.logo_label = QLabel("PicConverter")
        title_font = QApplication.font()
        title_font.setPointSizeF(title_font.pointSizeF() * 1.5)
        title_font.setWeight(title_font.Weight.Bold)
        self.logo_label.setFont(title_font)
        side.addWidget(self.logo_label)
        subtitle = QLabel(tr("Moderner Bild- & PDF-Konverter"))
        subtitle.setObjectName("subtitle")
        subtitle.setFont(self.font_small)
        side.addWidget(subtitle)
        side.addSpacing(8)

        select_btn = QPushButton(tr("Dateien auswählen"))
        select_btn.clicked.connect(self.select_files)
        side.addWidget(select_btn)
        drop_hint = QLabel(tr("… oder einfach ins Fenster ziehen"))
        drop_hint.setFont(self.font_small)
        self.set_kind(drop_hint, 'muted')
        side.addWidget(drop_hint)
        side.addSpacing(10)

        queue_row = QHBoxLayout()
        queue_row.setSpacing(4)
        queue_row.addWidget(self._section_label(tr("Warteschlange")), 1)
        clear_btn = QPushButton(tr("Leeren"))
        clear_btn.setObjectName("toolBtn")
        clear_btn.clicked.connect(self.clear_files)
        queue_row.addWidget(clear_btn)
        side.addLayout(queue_row)

        self.input_label = QLabel(tr("Keine Dateien ausgewählt"))
        self.input_label.setFont(self.font_small)
        self.set_kind(self.input_label, 'muted')
        side.addWidget(self.input_label)

        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.currentRowChanged.connect(self.on_row_changed)
        side.addWidget(self.file_list, 1)

        # Appearance-Umschalter als Segmented Control
        seg_frame = QFrame()
        seg_frame.setObjectName("segmented")
        seg_layout = QHBoxLayout(seg_frame)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(2)
        self.appearance_group = QButtonGroup(self)
        self.appearance_buttons = {}
        for label, mode in ((tr("System"), 'system'), (tr("Dunkel"), 'dark'),
                            (tr("Hell"), 'light')):
            btn = QPushButton(label)
            btn.setObjectName("segItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mode: self.on_appearance_change(m))
            seg_layout.addWidget(btn, 1)
            self.appearance_group.addButton(btn)
            self.appearance_buttons[mode] = btn
        self.appearance_buttons['system'].setChecked(True)
        side.addWidget(seg_frame)

        main.addWidget(sidebar)

        # ---------- Bühne: Hero-Dropzone (leer) oder Vorschau ----------
        self.stage = QStackedWidget()
        main.addWidget(self.stage, 1)

        hero_page = QWidget()
        hero_layout = QVBoxLayout(hero_page)
        hero_layout.setContentsMargins(48, 48, 48, 48)
        self.drop_zone = DropZone()
        self.drop_zone.clicked.connect(self.select_files)
        self.drop_zone.setMinimumHeight(220)
        self.drop_zone.setMaximumWidth(560)
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setContentsMargins(PAD * 2, PAD * 2, PAD * 2, PAD * 2)
        drop_text = tr("Bilder oder PDFs hierher ziehen\noder klicken zum Auswählen")
        self.drop_label = QLabel(drop_text)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.addWidget(self.drop_label)
        hero_row = QHBoxLayout()
        hero_row.addStretch(1)
        hero_row.addWidget(self.drop_zone, 2)
        hero_row.addStretch(1)
        hero_layout.addStretch(2)
        hero_layout.addLayout(hero_row)
        hero_layout.addStretch(3)
        self.stage.addWidget(hero_page)

        view_page = QWidget()
        view = QVBoxLayout(view_page)
        view.setContentsMargins(24, 24, 24, 16)
        view.setSpacing(12)

        self.preview_label = PreviewLabel(tr("Kein Bild geladen"), framed=False)
        self.set_kind(self.preview_label, 'muted')
        view.addWidget(self.preview_label, 1)

        # PDF-Seitennavigation -- wird nur bei geladener PDF eingeblendet
        self.page_row = QWidget()
        page_layout = QHBoxLayout(self.page_row)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(6)
        page_layout.addStretch(1)
        page_layout.addWidget(QLabel(tr("PDF-Seite")))
        prev_btn = QPushButton("‹")
        prev_btn.setObjectName("toolBtn")
        prev_btn.clicked.connect(lambda: self.step_page(-1))
        page_layout.addWidget(prev_btn)
        self.page_entry = QLineEdit("1")
        self.page_entry.setFixedWidth(52)
        self.page_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_entry.returnPressed.connect(self.on_page_change)
        self.page_entry.editingFinished.connect(self.on_page_change)
        page_layout.addWidget(self.page_entry)
        next_btn = QPushButton("›")
        next_btn.setObjectName("toolBtn")
        next_btn.clicked.connect(lambda: self.step_page(1))
        page_layout.addWidget(next_btn)
        self.page_count_label = QLabel(tr("von {n}").format(n=1))
        self.set_kind(self.page_count_label, 'muted')
        page_layout.addWidget(self.page_count_label)
        self.all_pages_check = QCheckBox(tr("Alle Seiten exportieren"))
        page_layout.addWidget(self.all_pages_check)
        page_layout.addStretch(1)
        view.addWidget(self.page_row)
        self.page_row.hide()

        info_row = QHBoxLayout()
        info_row.addStretch(1)
        self.info_label = QLabel("")
        self.info_label.setObjectName("infoBox")
        self.info_label.setFont(self.font_mono)
        self.info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_label.setMinimumWidth(420)
        info_row.addWidget(self.info_label)
        info_row.addStretch(1)
        view.addLayout(info_row)
        self.stage.addWidget(view_page)

        # ---------- Rechtes Panel: Einstellungen & Konvertierung ----------
        panel_scroll = QScrollArea()
        panel_scroll.setObjectName("panelScroll")
        panel_scroll.setWidgetResizable(True)
        panel_scroll.setFixedWidth(342)
        panel_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(18, 16, 18, 16)
        pv.setSpacing(10)
        panel_scroll.setWidget(panel)
        main.addWidget(panel_scroll)

        pv.addWidget(self._section_label(tr("Preset")))
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        self.preset_menu = QComboBox()
        self.preset_menu.addItems(self._preset_names())
        self.preset_menu.textActivated.connect(self.on_preset_selected)
        preset_row.addWidget(self.preset_menu, 1)
        preset_save_btn = QPushButton(tr("Speichern"))
        preset_save_btn.clicked.connect(self.save_preset)
        preset_row.addWidget(preset_save_btn)
        pv.addLayout(preset_row)

        pv.addWidget(self._divider())

        pv.addWidget(self._section_label(tr("Ausgabeformat")))
        self.format_menu = QComboBox()
        self.format_menu.addItems(list(SUPPORTED_FORMATS.keys()))
        self.format_menu.textActivated.connect(self.on_format_change)
        pv.addWidget(self.format_menu)

        # PDF zusammenfassen -- nur bei Zielformat PDF sichtbar
        self.merge_check = QCheckBox(tr("Alle Eingaben in eine PDF zusammenfassen"))
        self.merge_check.toggled.connect(lambda _: self.update_output_path())
        pv.addWidget(self.merge_check)
        self.merge_check.hide()

        pv.addWidget(self._divider())

        quality_row = QHBoxLayout()
        pv.addLayout(quality_row)
        self.quality_label = QLabel(tr("Qualität"))
        quality_row.addWidget(self.quality_label, 1)
        self.quality_value_label = QLabel("85")
        self.quality_value_label.setFont(self.font_bold)
        self.set_kind(self.quality_value_label, 'accent')
        quality_row.addWidget(self.quality_value_label)

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self.on_quality_change)
        pv.addWidget(self.quality_slider)

        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        pv.addLayout(target_row)
        self.target_check = QCheckBox(tr("Zielgröße:"))
        self.target_check.toggled.connect(lambda _: self.on_target_toggle())
        target_row.addWidget(self.target_check)
        self.target_entry = QLineEdit("500")
        self.target_entry.setFixedWidth(70)
        self.target_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        target_row.addWidget(self.target_entry)
        target_row.addWidget(QLabel("KB"))
        target_row.addStretch(1)
        target_hint = QLabel(tr("Qualität wird automatisch gesucht"))
        target_hint.setFont(self.font_small)
        self.set_kind(target_hint, 'muted')
        pv.addWidget(target_hint)

        pv.addWidget(self._divider())

        pv.addWidget(self._section_label(tr("Auflösung")))
        resolution_row = QHBoxLayout()
        resolution_row.setSpacing(6)
        pv.addLayout(resolution_row)
        self.width_entry = QLineEdit()
        self.width_entry.setFixedWidth(76)
        self.width_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resolution_row.addWidget(self.width_entry)
        resolution_row.addWidget(QLabel("×"))
        self.height_entry = QLineEdit()
        self.height_entry.setFixedWidth(76)
        self.height_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resolution_row.addWidget(self.height_entry)
        resolution_row.addWidget(QLabel("px"))
        resolution_row.addStretch(1)

        self.aspect_check = QCheckBox(tr("Seitenverhältnis beibehalten"))
        self.aspect_check.setChecked(True)
        pv.addWidget(self.aspect_check)

        pv.addWidget(self._divider())

        wm_row1 = QHBoxLayout()
        wm_row1.setSpacing(6)
        pv.addLayout(wm_row1)
        self.watermark_check = QCheckBox(tr("Wasserzeichen:"))
        wm_row1.addWidget(self.watermark_check)
        self.watermark_text_entry = QLineEdit()
        self.watermark_text_entry.setPlaceholderText(tr("Text, z.B. © 2026"))
        wm_row1.addWidget(self.watermark_text_entry, 1)

        wm_row2 = QHBoxLayout()
        wm_row2.setSpacing(6)
        pv.addLayout(wm_row2)
        self.watermark_pos_labels = {tr(p): p for p in core.WATERMARK_POSITIONS}
        self.watermark_pos_menu = QComboBox()
        self.watermark_pos_menu.addItems(list(self.watermark_pos_labels))
        self.watermark_pos_menu.setCurrentText(tr('unten-rechts'))
        wm_row2.addWidget(self.watermark_pos_menu, 1)
        self.watermark_opacity_entry = QLineEdit("50")
        self.watermark_opacity_entry.setFixedWidth(44)
        self.watermark_opacity_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wm_row2.addWidget(self.watermark_opacity_entry)
        wm_row2.addWidget(QLabel("%"))

        pv.addWidget(self._divider())

        pv.addWidget(self._section_label(tr("EXIF-Metadaten")))
        exif_row = QHBoxLayout()
        exif_row.setSpacing(8)
        pv.addLayout(exif_row)
        self.exif_strip_check = QCheckBox(tr("Metadaten entfernen"))
        exif_row.addWidget(self.exif_strip_check, 1)
        exif_btn = QPushButton(tr("Anzeigen / Bearbeiten"))
        exif_btn.clicked.connect(self.open_exif_editor)
        exif_row.addWidget(exif_btn)

        self.exif_hint_label = QLabel("")
        self.exif_hint_label.setFont(self.font_small)
        self.exif_hint_label.setWordWrap(True)
        self.set_kind(self.exif_hint_label, 'accent')
        pv.addWidget(self.exif_hint_label)
        self.exif_hint_label.hide()

        pv.addWidget(self._divider())

        pv.addWidget(self._section_label(tr("Ausgabe & Konvertierung")))
        self.output_label = QLabel(tr("Automatisch generiert"))
        self.output_label.setWordWrap(True)
        self.set_kind(self.output_label, 'muted')
        pv.addWidget(self.output_label)

        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        pv.addLayout(out_row)
        output_btn = QPushButton(tr("Speicherort wählen"))
        output_btn.clicked.connect(self.select_output)
        out_row.addWidget(output_btn)
        estimate_btn = QPushButton(tr("Größe schätzen"))
        estimate_btn.clicked.connect(self.estimate_size)
        out_row.addWidget(estimate_btn)
        out_row.addStretch(1)

        self.estimate_label = QLabel(tr("Geschätzte Ausgabegröße: -- MB"))
        self.estimate_label.setFont(self.font_small)
        self.estimate_label.setWordWrap(True)
        self.set_kind(self.estimate_label, 'muted')
        pv.addWidget(self.estimate_label)

        self.overwrite_check = QCheckBox(tr("Vorhandene Dateien überschreiben"))
        self.overwrite_check.setToolTip(
            tr("Vorhandene Dateien überschreiben (sonst \"name (1)\")"))
        pv.addWidget(self.overwrite_check)

        pv.addStretch(1)

        self.convert_button = QPushButton(tr("Konvertieren starten"))
        self.convert_button.setObjectName("primary")
        self.convert_button.setMinimumHeight(44)
        self.convert_button.setEnabled(False)
        self.convert_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_button.clicked.connect(self.convert)
        pv.addWidget(self.convert_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        pv.addWidget(self.progress_bar)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setFont(self.font_small)
        pv.addWidget(self.result_label)
        self.result_label.hide()
        self.open_folder_button = QPushButton(tr("Ordner öffnen"))
        self.open_folder_button.clicked.connect(self.open_output_folder)
        pv.addWidget(self.open_folder_button)
        self.open_folder_button.hide()

        # ---------- Statusleiste ----------
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(PAD, 7, PAD, 7)
        self.status_label = QLabel(tr("Bereit"))
        self.set_kind(self.status_label, 'accent')
        status_layout.addWidget(self.status_label)
        outer.addWidget(status_bar)

        if not core.PDF_AVAILABLE:
            self.set_status(tr("Bereit — Tipp: 'pip install pymupdf' aktiviert PDF-Eingabe"),
                            'muted')

        # Initiale Format-Einstellung
        self.on_format_change()

    def _section_label(self, text):
        """Kleine VERSALIEN-Überschrift für Panel-Sektionen"""
        label = QLabel(text.upper())
        label.setObjectName("sectionTitle")
        label.setFont(self.font_section)
        return label

    def _divider(self):
        """Feine Trennlinie zwischen Panel-Sektionen"""
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedHeight(1)
        return line

    # ---------- Theme und Status ----------

    def set_kind(self, label, kind):
        """Setzt die semantische Farbe eines Labels (QSS-Property 'kind')"""
        if label.property("kind") != kind:
            label.setProperty("kind", kind)
            repolish(label)

    def set_status(self, message, kind='accent'):
        """Zeigt eine Statusmeldung farbcodiert in der Statusleiste an"""
        self.status_label.setText(message)
        self.set_kind(self.status_label, kind)

    def resolve_theme(self, mode):
        """'system' über das Qt-ColorScheme auflösen"""
        if mode in THEMES:
            return THEMES[mode]
        scheme = QGuiApplication.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Light:
            return THEMES['light']
        return THEMES['dark']

    def apply_theme(self, mode):
        self.appearance_mode = mode
        theme = self.resolve_theme(mode)
        self._current_theme = theme
        app = QApplication.instance()
        app.setPalette(build_palette(theme))
        app.setStyleSheet(build_stylesheet(theme))
        self._update_logo(theme is THEMES['dark'])

    def _update_logo(self, dark):
        """Logo-Wortmarke passend zum Theme in den Header laden"""
        logo = ASSETS / ('logo-dark.png' if dark else 'logo-light.png')
        if not logo.exists():
            return
        dpr = self.devicePixelRatioF()
        pixmap = QPixmap(str(logo)).scaledToHeight(
            int(26 * dpr), Qt.TransformationMode.SmoothTransformation)
        pixmap.setDevicePixelRatio(dpr)
        self.logo_label.setPixmap(pixmap)

    def on_appearance_change(self, mode):
        self.apply_theme(mode)

    def _on_system_scheme_changed(self, _scheme):
        if self.appearance_mode == 'system':
            self.apply_theme('system')

    # ---------- Einstellungen speichern/laden ----------

    def restore_settings(self):
        """Stellt die Einstellungen der letzten Sitzung wieder her"""
        settings = core.load_gui_settings()
        if not settings:
            return
        try:
            mode = settings.get('appearance', 'system')
            if mode in self.appearance_buttons:
                self.appearance_buttons[mode].setChecked(True)
                self.apply_theme(mode)

            fmt_label = settings.get('format')
            if fmt_label in SUPPORTED_FORMATS:
                self.format_menu.setCurrentText(fmt_label)
                self.on_format_change()
            if 'quality' in settings:
                self.quality_slider.setValue(int(settings['quality']))
                self.on_quality_change()
            self.target_check.setChecked(bool(settings.get('use_target', False)))
            self.target_entry.setText(str(settings.get('target_kb', 500)))
            self.aspect_check.setChecked(bool(settings.get('keep_aspect', True)))
            self.exif_strip_check.setChecked(bool(settings.get('strip_exif', False)))
            self.overwrite_check.setChecked(bool(settings.get('overwrite', False)))
            self.watermark_check.setChecked(bool(settings.get('watermark_on', False)))
            self.watermark_text_entry.setText(settings.get('watermark_text', ''))
            pos = settings.get('watermark_pos', 'unten-rechts')
            if pos in core.WATERMARK_POSITIONS:
                self.watermark_pos_menu.setCurrentText(tr(pos))
            self.watermark_opacity_entry.setText(
                str(settings.get('watermark_opacity', 50)))
            self.on_target_toggle()
        except Exception:
            pass  # defekte Einstellungsdatei ignorieren

    def closeEvent(self, event):
        """Speichert die Einstellungen und schließt das Fenster"""
        try:
            core.save_gui_settings({
                'appearance': self.appearance_mode,
                'format': self.format_menu.currentText(),
                'quality': int(self.quality_slider.value()),
                'use_target': self.target_check.isChecked(),
                'target_kb': self.target_entry.text(),
                'keep_aspect': self.aspect_check.isChecked(),
                'strip_exif': self.exif_strip_check.isChecked(),
                'overwrite': self.overwrite_check.isChecked(),
                'watermark_on': self.watermark_check.isChecked(),
                'watermark_text': self.watermark_text_entry.text(),
                'watermark_pos': self.watermark_pos_labels.get(
                    self.watermark_pos_menu.currentText(), 'unten-rechts'),
                'watermark_opacity': self.watermark_opacity_entry.text(),
            })
        except Exception:
            pass
        super().closeEvent(event)

    # ---------- Presets ----------

    def _preset_names(self):
        return [tr("(keins)")] + sorted(core.load_presets())

    def on_preset_selected(self, choice):
        if choice == tr("(keins)"):
            return
        preset = core.load_presets().get(choice, {})
        fmt_label = LABEL_BY_EXT.get(str(preset.get('format', '')).lower())
        if fmt_label:
            self.format_menu.setCurrentText(fmt_label)
            self.on_format_change()
        if preset.get('target_kb'):
            self.target_check.setChecked(True)
            self.target_entry.setText(str(preset['target_kb']))
        else:
            self.target_check.setChecked(False)
            if preset.get('quality') is not None:
                self.quality_slider.setValue(int(preset['quality']))
                self.on_quality_change()
        if preset.get('width'):
            self.width_entry.setText(str(preset['width']))
            self.height_entry.setText('')
        if preset.get('height'):
            self.height_entry.setText(str(preset['height']))
        self.exif_strip_check.setChecked(bool(preset.get('strip_exif', False)))
        self.on_target_toggle()
        self.set_status(tr("✓ Preset '{name}' angewendet").format(name=choice),
                        'success')

    def save_preset(self):
        name, ok = QInputDialog.getText(self, tr("Preset speichern"),
                                        tr("Name für das Preset:"))
        name = (name or '').strip()
        if not ok or not name:
            return
        width, height = self.parse_resolution()
        core.save_user_preset(name, {
            'format': EXT_MAP[self.format_menu.currentText()].lstrip('.'),
            'quality': (int(self.quality_slider.value())
                        if not self.target_check.isChecked() else None),
            'target_kb': self.parse_target_kb(),
            'width': width,
            'height': height,
            'strip_exif': self.exif_strip_check.isChecked(),
        })
        self.preset_menu.clear()
        self.preset_menu.addItems(self._preset_names())
        self.preset_menu.setCurrentText(name)
        self.set_status(tr("✓ Preset '{name}' gespeichert").format(name=name),
                        'success')

    # ---------- Drag & Drop ----------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone.set_drag_over(True)

    def dragLeaveEvent(self, event):
        self.drop_zone.set_drag_over(False)

    def dropEvent(self, event):
        self.drop_zone.set_drag_over(False)
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()
                 if url.isLocalFile()]
        if paths:
            self.add_files(paths)

    # ---------- Dateiauswahl und Laden ----------

    def select_files(self):
        image_exts = sorted(core.INPUT_EXTENSIONS - {'pdf'})
        image_patterns = ' '.join(f'*.{ext}' for ext in image_exts)
        filters = ';;'.join([
            tr("Alle unterstützten Dateien") + f" ({image_patterns} *.pdf)",
            tr("Alle Bilder") + f" ({image_patterns})",
            "PDF (*.pdf)",
            tr("Alle Dateien") + " (*)",
        ])
        filenames, _ = QFileDialog.getOpenFileNames(
            self, tr("Bilder oder PDFs auswählen"), '', filters)
        if filenames:
            self.add_files([Path(f) for f in filenames])

    def add_files(self, paths):
        """Nimmt Dateien in die Warteschlange auf und wählt die erste neue aus"""
        added = 0
        skipped = 0
        for path in paths:
            if not path.is_file():
                skipped += 1
                continue
            if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                skipped += 1
                continue
            if path in self.input_paths:
                continue
            self.input_paths.append(path)
            added += 1

        if not added:
            if skipped:
                self.set_status(tr("✗ Keine unterstützten Dateien dabei"), 'error')
            return

        # Gewählter Speicherort bezieht sich auf die alte Auswahl
        self.output_file = None

        if self.selected_index is None:
            self.selected_index = 0
        self.refresh_file_list()
        self.load_selected()

        if skipped:
            self.set_status(
                tr("✓ {added} Datei(en) geladen — {skipped} nicht unterstützte übersprungen")
                .format(added=added, skipped=skipped), 'warning')

    def clear_files(self):
        self.input_paths = []
        self.selected_index = None
        self.image = None
        self.pdf_page_count = 0
        self.output_file = None
        self.output_dir = None
        self.thumbnails = {}
        self.refresh_file_list()
        self.page_row.hide()
        self.stage.setCurrentIndex(0)
        self.preview_label.clear_image(tr("Kein Bild geladen"))
        self.info_label.setText("")
        self.input_label.setText(tr("Keine Dateien ausgewählt"))
        self.set_kind(self.input_label, 'muted')
        self.output_label.setText(tr("Automatisch generiert"))
        self.set_kind(self.output_label, 'muted')
        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_label.hide()
        self.open_folder_button.hide()
        self.set_status(tr("Liste geleert"), 'muted')

    def remove_index(self, index):
        """Entfernt eine einzelne Datei aus der Warteschlange"""
        if not (0 <= index < len(self.input_paths)):
            return
        removed = self.input_paths.pop(index)
        self.thumbnails.pop(removed, None)

        if not self.input_paths:
            self.clear_files()
            return

        if self.selected_index is not None:
            if index < self.selected_index:
                self.selected_index -= 1
            elif index == self.selected_index:
                self.selected_index = min(index, len(self.input_paths) - 1)
        self.refresh_file_list()
        self.load_selected()

    def _thumbnail_for(self, path):
        """Mini-Vorschau für die Dateiliste (nur Bilder, gecacht)"""
        if path in self.thumbnails:
            return self.thumbnails[path]
        if core.is_pdf(path) or len(self.input_paths) > MAX_THUMBNAILS:
            return None
        try:
            dpr = self.devicePixelRatioF()
            img = Image.open(path)
            img.thumbnail((int(22 * dpr), int(22 * dpr)),
                          Image.Resampling.BILINEAR)
            thumb = QPixmap.fromImage(pil_to_qimage(img))
            thumb.setDevicePixelRatio(dpr)
        except Exception:
            thumb = None
        self.thumbnails[path] = thumb
        return thumb

    def _file_row_widget(self, index, path):
        """Baut eine Zeile der Dateiliste: Thumbnail/Chip, Name, Entfernen"""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 2, 4, 2)
        layout.setSpacing(8)

        if core.is_pdf(path):
            chip = QLabel("PDF")
            chip.setObjectName("chip")
            chip.setFont(self.font_small)
            layout.addWidget(chip)
        else:
            thumb_label = QLabel()
            thumb_label.setFixedSize(22, 22)
            thumb = self._thumbnail_for(path)
            if thumb:
                thumb_label.setPixmap(thumb)
                thumb_label.setScaledContents(False)
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(thumb_label)

        name_label = QLabel(path.name)
        layout.addWidget(name_label, 1)

        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("toolBtn")
        remove_btn.setFixedWidth(28)
        remove_btn.clicked.connect(lambda: self.remove_index(index))
        layout.addWidget(remove_btn)
        return row

    def refresh_file_list(self):
        """Baut die Warteschlangen-Liste in der Sidebar neu auf"""
        self.file_list.blockSignals(True)
        self.file_list.clear()

        for i, path in enumerate(self.input_paths):
            item = QListWidgetItem()
            widget = self._file_row_widget(i, path)
            item.setSizeHint(QSize(widget.sizeHint().width(),
                                   max(28, widget.sizeHint().height())))
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)
        if self.selected_index is not None:
            self.file_list.setCurrentRow(self.selected_index)
        self.file_list.blockSignals(False)

    def on_row_changed(self, row):
        if row < 0 or row == self.selected_index:
            return
        self.selected_index = row
        self.load_selected()

    @property
    def selected_path(self):
        if self.selected_index is None or not self.input_paths:
            return None
        return self.input_paths[self.selected_index]

    def load_selected(self):
        """Lädt die ausgewählte Datei für Vorschau und Infos"""
        path = self.selected_path
        if path is None:
            return
        try:
            if core.is_pdf(path):
                self.pdf_page_count = core.pdf_page_count(path)
                self.page_entry.setText("1")
                self.page_count_label.setText(
                    tr("von {n}").format(n=self.pdf_page_count))
                self.page_row.show()
                self.image = core.load_image(path, 1)
            else:
                self.pdf_page_count = 0
                self.page_row.hide()
                self.image = core.load_image(path)

            self.refresh_display()
            self.stage.setCurrentIndex(1)

            if len(self.input_paths) == 1:
                short_name = path.name
                if len(short_name) > 45:
                    short_name = short_name[:42] + "..."
                self.input_label.setText(f"✓ {short_name}")
            else:
                self.input_label.setText(
                    tr("✓ {n} Dateien in der Warteschlange")
                    .format(n=len(self.input_paths)))
            self.set_kind(self.input_label, 'success')

            self.convert_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.update_output_path()
            self.set_status(tr("✓ Datei erfolgreich geladen"), 'success')

        except Exception as e:
            self.set_status(tr("✗ Fehler beim Laden: {error}").format(error=e),
                            'error')

    def refresh_display(self):
        """Aktualisiert Bildinformationen, Vorschau und Auflösungsfelder"""
        path = self.selected_path
        if self.pdf_page_count:
            format_text = tr("PDF · Seite {page} von {count}").format(
                page=self.page_entry.text(), count=self.pdf_page_count)
        else:
            format_text = self.image.format or Image.open(path).format
            if core.is_animated(self.image):
                format_text += tr(" · animiert ({n} Frames)").format(
                    n=self.image.n_frames)

        exif_count = len(core.read_exif(self.image))
        exif_text = (tr("{n} Einträge").format(n=exif_count)
                     if exif_count else tr("keine"))

        info = tr("Datei:      {name}").format(name=path.name) + "\n"
        info += tr("Größe:      {size:.2f} MB").format(
            size=path.stat().st_size / (1024 * 1024)) + "\n"
        info += tr("Auflösung:  {w} × {h} Pixel").format(
            w=self.image.size[0], h=self.image.size[1]) + "\n"
        info += tr("Format:     {format}").format(format=format_text) + "\n"
        info += tr("EXIF:       {exif}").format(exif=exif_text)
        self.info_label.setText(info)

        # Vorschau
        preview_img = self.image.copy() if not core.is_animated(self.image) \
            else self.image.convert('RGB')
        preview_img.thumbnail((1400, 1000), Image.Resampling.LANCZOS)
        self.preview_label.set_image(preview_img)

        # Auflösungsfelder vorbefüllen; die Werte gelten als "unverändert",
        # bis der User sie anfasst (wichtig für Batch-Konvertierung)
        self.width_entry.setText(str(self.image.size[0]))
        self.height_entry.setText(str(self.image.size[1]))
        self.prefilled_size = (self.width_entry.text(), self.height_entry.text())

    # ---------- PDF-Seitennavigation ----------

    def step_page(self, delta):
        try:
            page = int(self.page_entry.text()) + delta
        except ValueError:
            page = 1
        self.page_entry.setText(str(page))
        self.on_page_change()

    def on_page_change(self):
        """Rendert die gewählte PDF-Seite neu (mit Bereichsprüfung)"""
        if not self.pdf_page_count:
            return
        try:
            page = int(self.page_entry.text())
        except ValueError:
            page = 1
        page = max(1, min(page, self.pdf_page_count))
        if self.page_entry.text() != str(page):
            self.page_entry.setText(str(page))
        try:
            self.image = core.load_image(self.selected_path, page)
            self.refresh_display()
            self.update_output_path()
            self.set_status(tr("✓ Seite {page} geladen").format(page=page),
                            'success')
        except Exception as e:
            self.set_status(tr("✗ Fehler beim Laden der Seite: {error}")
                            .format(error=e), 'error')

    # ---------- Einstellungen ----------

    def on_format_change(self, choice=None):
        output_format = SUPPORTED_FORMATS[self.format_menu.currentText()]

        if output_format in core.QUALITY_SETTINGS:
            settings = core.QUALITY_SETTINGS[output_format]
            self.quality_slider.blockSignals(True)
            self.quality_slider.setRange(settings['min'], settings['max'])
            self.quality_slider.setValue(settings['default'])
            self.quality_slider.blockSignals(False)
            self.quality_slider.setEnabled(True)
            self.quality_label.setText(tr(settings['name']))
            self.on_quality_change()
        else:
            self.quality_slider.setEnabled(False)
            self.quality_label.setText(
                tr("Qualität (für dieses Format nicht verfügbar)"))
            self.quality_value_label.setText("--")

        # Zielgröße nur für JPEG/WebP
        if output_format in core.TARGET_SIZE_FORMATS:
            self.target_check.setEnabled(True)
            self.target_entry.setEnabled(True)
        else:
            self.target_check.setChecked(False)
            self.target_check.setEnabled(False)
            self.target_entry.setEnabled(False)

        # Zusammenfassen nur bei Zielformat PDF
        if output_format == 'PDF':
            self.merge_check.show()
        else:
            self.merge_check.setChecked(False)
            self.merge_check.hide()

        self.on_target_toggle()
        self.update_output_path()

    def on_quality_change(self, value=None):
        self.quality_value_label.setText(str(self.quality_slider.value()))

    def on_target_toggle(self):
        """Bei aktiver Zielgröße übernimmt die Qualitätssuche den Slider"""
        output_format = SUPPORTED_FORMATS[self.format_menu.currentText()]
        if self.target_check.isChecked() and \
                output_format in core.TARGET_SIZE_FORMATS:
            self.quality_slider.setEnabled(False)
            self.quality_value_label.setText(tr("auto"))
        elif output_format in core.QUALITY_SETTINGS:
            self.quality_slider.setEnabled(True)
            self.on_quality_change()

    def parse_resolution(self):
        """Liest die Zielauflösung; unveränderte oder leere Felder bedeuten
        'Originalgröße beibehalten' (None, None)"""
        width_text = self.width_entry.text().strip()
        height_text = self.height_entry.text().strip()
        if (width_text, height_text) == self.prefilled_size:
            return None, None
        if not width_text and not height_text:
            return None, None
        try:
            width = int(width_text) if width_text else None
            height = int(height_text) if height_text else None
        except ValueError:
            self.set_status(tr("Ungültige Auflösung — Originalgröße wird verwendet"),
                            'warning')
            return None, None
        return width, height

    def parse_target_kb(self):
        if not self.target_check.isChecked():
            return None
        try:
            target = int(self.target_entry.text())
            if target < 1:
                raise ValueError
            return target
        except ValueError:
            self.set_status(tr("Ungültige Zielgröße — bitte KB als Zahl angeben"),
                            'warning')
            return None

    def build_watermark(self):
        """Wasserzeichen-Einstellungen als Dict (oder None)"""
        if not self.watermark_check.isChecked():
            return None
        text = self.watermark_text_entry.text().strip()
        if not text:
            self.set_status(tr("Wasserzeichen aktiviert, aber kein Text angegeben"),
                            'warning')
            return None
        try:
            opacity = max(0, min(100, int(self.watermark_opacity_entry.text())))
        except ValueError:
            opacity = 50
        return {
            'text': text,
            'position': self.watermark_pos_labels.get(
                self.watermark_pos_menu.currentText(), 'unten-rechts'),
            'opacity': opacity,
        }

    @staticmethod
    def resolution_for(img, width, height, keep_aspect):
        """Berechnet die Zielauflösung für ein konkretes Bild.

        Fehlende Dimensionen werden seitenverhältnistreu ergänzt; bei aktivem
        'Seitenverhältnis beibehalten' richtet sich die Breite nach der Höhe.
        """
        if width is None and height is None:
            return None, None
        ratio = img.size[0] / img.size[1]
        if width is None:
            return round(height * ratio), height
        if height is None:
            return width, round(width / ratio)
        if keep_aspect:
            return round(height * ratio), height
        return width, height

    # ---------- EXIF-Editor ----------

    def open_exif_editor(self):
        if self.image is None:
            self.set_status(tr("Bitte zuerst eine Datei laden"), 'warning')
            return

        editor = QDialog(self)
        editor.setWindowTitle(tr("EXIF-Metadaten"))
        editor.resize(560, 640)
        layout = QVBoxLayout(editor)
        layout.setContentsMargins(PAD, PAD, PAD, PAD)
        layout.setSpacing(10)

        fields_title = QLabel(tr("Bearbeitbare Felder").upper())
        fields_title.setObjectName("sectionTitle")
        fields_title.setFont(self.font_section)
        layout.addWidget(fields_title)

        current_exif = self.image.getexif()
        entries = {}
        originals = {}
        for name, (tag, label) in core.EXIF_EDITABLE_TAGS.items():
            field_row = QHBoxLayout()
            field_row.setSpacing(10)
            field_label = QLabel(tr(label))
            field_label.setMinimumWidth(190)
            field_row.addWidget(field_label)
            entry = QLineEdit()
            original = str(current_exif.get(tag, '')).strip()
            # Bereits vorgemerkte Änderungen haben Vorrang vor den Dateiwerten
            entry.setText(self.exif_overrides.get(name, original))
            originals[name] = original
            field_row.addWidget(entry, 1)
            layout.addLayout(field_row)
            entries[name] = entry

        viewer_title = QLabel(tr("Alle Metadaten der ausgewählten Datei").upper())
        viewer_title.setObjectName("sectionTitle")
        viewer_title.setFont(self.font_section)
        layout.addSpacing(4)
        layout.addWidget(viewer_title)

        viewer = QPlainTextEdit()
        viewer.setObjectName("exifViewer")
        viewer.setFont(self.font_mono)
        viewer.setReadOnly(True)
        all_tags = core.read_exif(self.image)
        if all_tags:
            width = max(len(name) for name, _ in all_tags)
            viewer.setPlainText("\n".join(
                f"{name:<{width}}  {value}" for name, value in all_tags))
        else:
            viewer.setPlainText(tr("Keine EXIF-Daten vorhanden."))
        layout.addWidget(viewer, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        layout.addLayout(button_row)

        def apply():
            self.exif_overrides = {
                name: entry.text().strip()
                for name, entry in entries.items()
                if entry.text().strip() != originals[name]
            }
            self.update_exif_hint()
            editor.accept()
            if self.exif_overrides:
                self.set_status(
                    tr("✓ {n} EXIF-Feld(er) werden beim Konvertieren angepasst")
                    .format(n=len(self.exif_overrides)), 'success')
            else:
                self.set_status(tr("EXIF-Änderungen zurückgesetzt"), 'muted')

        cancel_btn = QPushButton(tr("Abbrechen"))
        cancel_btn.clicked.connect(editor.reject)
        button_row.addWidget(cancel_btn)
        apply_btn = QPushButton(tr("Übernehmen"))
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(apply)
        button_row.addWidget(apply_btn)

        editor.exec()

    def update_exif_hint(self):
        if self.exif_overrides:
            fields = ', '.join(tr(core.EXIF_EDITABLE_TAGS[n][1]).split(' (')[0]
                               for n in self.exif_overrides)
            self.exif_hint_label.setText(
                tr("Wird angepasst: {fields}").format(fields=fields))
            self.exif_hint_label.show()
        else:
            self.exif_hint_label.hide()

    # ---------- Ausgabe ----------

    def build_jobs(self):
        """Erstellt die Auftragsliste: (Pfad, Seite-oder-None).

        Die Seitenauswahl gilt für die aktuell ausgewählte PDF; weitere PDFs in
        der Warteschlange werden mit Seite 1 exportiert — außer 'Alle Seiten'
        ist aktiv, dann werden alle Seiten jeder PDF exportiert.
        """
        jobs = []
        for path in self.input_paths:
            if not core.is_pdf(path):
                jobs.append((path, None))
            elif self.all_pages_check.isChecked():
                jobs.extend((path, p)
                            for p in range(1, core.pdf_page_count(path) + 1))
            elif path == self.selected_path:
                jobs.append((path, int(self.page_entry.text())))
            else:
                jobs.append((path, 1))
        return jobs

    def update_output_path(self):
        if not self.input_paths:
            return
        ext = EXT_MAP.get(self.format_menu.currentText(), '.jpg')
        first = self.input_paths[0]

        if self.merge_check.isChecked() and \
                SUPPORTED_FORMATS[self.format_menu.currentText()] == 'PDF':
            name = (self.output_file.name if self.output_file
                    else f"{first.stem}_gesamt.pdf")
            self.output_label.setText(name)
        elif len(self.input_paths) == 1 and not (self.pdf_page_count
                                                 and self.all_pages_check.isChecked()):
            if self.output_file:
                name = self.output_file.name
            else:
                page = int(self.page_entry.text()) if self.pdf_page_count else None
                name = core.output_stem(first, page) + ext
            self.output_label.setText(name)
        else:
            target = self.output_dir.name if self.output_dir else tr("je Eingabeordner")
            self.output_label.setText(
                tr("Mehrere Dateien → {target}").format(target=target))
        self.set_kind(self.output_label, 'accent')

    def select_output(self):
        if not self.input_paths:
            self.set_status(tr("Bitte zuerst Dateien auswählen"), 'warning')
            return

        merge = self.merge_check.isChecked() and \
            SUPPORTED_FORMATS[self.format_menu.currentText()] == 'PDF'
        single = len(self.input_paths) == 1 and not (self.pdf_page_count
                                                     and self.all_pages_check.isChecked())

        if merge or single:
            ext = '.pdf' if merge else EXT_MAP.get(self.format_menu.currentText(), '.jpg')
            fmt_filter = f"{self.format_menu.currentText()} (*{ext});;" + \
                tr("Alle Dateien") + " (*)"
            filename, _ = QFileDialog.getSaveFileName(
                self, tr("Ausgabedatei speichern"), '', fmt_filter)
            if filename:
                self.output_file = Path(filename)
        else:
            dirname = QFileDialog.getExistingDirectory(
                self, tr("Ausgabeordner wählen"))
            if dirname:
                self.output_dir = Path(dirname)

        self.update_output_path()

    # ---------- Größenschätzung ----------

    def estimate_size(self):
        if self.image is None:
            self.set_status(tr("Bitte zuerst eine Datei laden"), 'warning')
            return

        try:
            output_format = SUPPORTED_FORMATS[self.format_menu.currentText()]
            exif_mode = 'strip' if self.exif_strip_check.isChecked() else 'keep'
            watermark = self.build_watermark()
            width, height = self.parse_resolution()
            width, height = self.resolution_for(self.image, width, height,
                                                self.aspect_check.isChecked())

            target_kb = self.parse_target_kb()
            if target_kb and output_format in core.TARGET_SIZE_FORMATS:
                quality, estimated = core.quality_for_target(
                    self.image, output_format, target_kb, width, height,
                    exif_mode, self.exif_overrides, watermark)
                self.estimate_label.setText(
                    tr("Geschätzt: {size:.2f} MB (Qualität {q})")
                    .format(size=estimated, q=quality))
                self.set_kind(self.estimate_label, 'accent')
                self.set_status(tr("Zielgröße {kb} KB → Qualität {q}")
                                .format(kb=target_kb, q=quality), 'success')
                return

            quality = (int(self.quality_slider.value())
                       if output_format in core.QUALITY_SETTINGS else None)
            estimated = core.estimate_size(self.image, output_format, quality,
                                           width, height, exif_mode,
                                           self.exif_overrides, watermark)
            original = self.selected_path.stat().st_size / (1024 * 1024)
            self.estimate_label.setText(
                tr("Geschätzt: {size:.2f} MB (Original: {orig:.2f} MB)")
                .format(size=estimated, orig=original))
            self.set_kind(self.estimate_label, 'accent')
            if original > 0:
                compression = (1 - estimated / original) * 100
                if compression > 0:
                    self.set_status(tr("Schätzung: -{value:.1f}% kleiner")
                                    .format(value=compression), 'success')
                else:
                    self.set_status(tr("Schätzung: +{value:.1f}% größer")
                                    .format(value=abs(compression)), 'warning')
        except Exception as e:
            self.estimate_label.setText(tr("Konnte Größe nicht schätzen"))
            self.set_kind(self.estimate_label, 'muted')
            self.set_status(tr("✗ Fehler bei Größenberechnung: {error}")
                            .format(error=e), 'error')

    # ---------- Konvertierung ----------

    def convert(self):
        if not self.input_paths:
            self.set_status(tr("Bitte zuerst Dateien auswählen"), 'warning')
            return

        # Alle Parameter im GUI-Thread einsammeln -- der Worker-Thread
        # darf keine Qt-Widgets anfassen
        output_format = SUPPORTED_FORMATS[self.format_menu.currentText()]
        extension = EXT_MAP[self.format_menu.currentText()].lstrip('.')

        try:
            jobs = self.build_jobs()
        except Exception as e:
            self.set_status(f"✗ {e}", 'error')
            return

        settings = {
            'format': output_format,
            'extension': extension,
            'quality': (int(self.quality_slider.value())
                        if output_format in core.QUALITY_SETTINGS else None),
            'target_kb': self.parse_target_kb(),
            'resolution': self.parse_resolution(),
            'keep_aspect': self.aspect_check.isChecked(),
            'exif_mode': 'strip' if self.exif_strip_check.isChecked() else 'keep',
            'exif_overrides': dict(self.exif_overrides),
            'watermark': self.build_watermark(),
            'overwrite': self.overwrite_check.isChecked(),
            'merge': (self.merge_check.isChecked() and output_format == 'PDF'
                      and len(jobs) > 0),
            'all_pages': self.all_pages_check.isChecked(),
            'output_file': self.output_file if len(jobs) == 1 or self.merge_check.isChecked()
                           else None,
            'output_dir': self.output_dir,
        }

        self.convert_button.setEnabled(False)
        self.result_label.hide()
        self.open_folder_button.hide()
        self.set_status(tr("Konvertiere..."), 'accent')
        self.progress_bar.setValue(0)

        thread = threading.Thread(target=self._convert_thread, args=(jobs, settings))
        thread.daemon = True
        thread.start()

    def _output_for_job(self, path, page, settings):
        if settings['output_file']:
            # Explizit gewählte Zieldatei: der Speichern-Dialog hat das
            # Überschreiben bereits bestätigt
            return settings['output_file']
        stem = core.output_stem(path, page, settings['all_pages'])
        directory = settings['output_dir'] or path.parent
        out = directory / f"{stem}.{settings['extension']}"
        if not settings['overwrite']:
            out = core.unique_path(out)
        return out

    def _convert_thread(self, jobs, settings):
        results = []
        total = len(jobs)

        try:
            if settings['merge']:
                images = [core.load_image(path, page or 1) for path, page in jobs]
                if settings['watermark']:
                    images = [core.apply_watermark(img, **settings['watermark'])
                              for img in images]
                out = settings['output_file'] or \
                    (settings['output_dir'] or jobs[0][0].parent) / \
                    f"{jobs[0][0].stem}_gesamt.pdf"
                if not settings['output_file'] and not settings['overwrite']:
                    out = core.unique_path(out)
                core.images_to_pdf(images, out)
                size_mb = out.stat().st_size / (1024 * 1024)
                results.append((tr("{n} Seite(n) → {name} ({size:.2f} MB)")
                                .format(n=total, name=out.name, size=size_mb),
                                True, out))
                self._signals.done.emit(results)
                return

            for i, (path, page) in enumerate(jobs):
                label = path.name if page is None \
                    else f"{path.name} ({tr('S.')} {page})"
                out = self._output_for_job(path, page, settings)
                try:
                    img = core.load_image(path, page or 1)
                    width, height = self.resolution_for(
                        img, *settings['resolution'], settings['keep_aspect'])

                    quality = settings['quality']
                    if settings['target_kb'] and \
                            settings['format'] in core.TARGET_SIZE_FORMATS:
                        quality, _ = core.quality_for_target(
                            img, settings['format'], settings['target_kb'],
                            width, height, settings['exif_mode'],
                            settings['exif_overrides'], settings['watermark'])

                    note = ''
                    if core.is_animated(img) and \
                            settings['format'] not in core.ANIMATED_FORMATS:
                        note = tr(" (Animation ging verloren)")

                    core.convert(img, out, settings['format'], quality,
                                 width, height, settings['exif_mode'],
                                 settings['exif_overrides'], settings['watermark'])
                    size_mb = out.stat().st_size / (1024 * 1024)
                    results.append((f"{label} → {out.name} ({size_mb:.2f} MB){note}",
                                    True, out))
                except Exception as e:
                    results.append((f"{label}: {e}", False, None))

                self._signals.progress.emit((i + 1) / total)

            self._signals.done.emit(results)

        except Exception as e:
            results.append((str(e), False, None))
            self._signals.done.emit(results)

    def _on_convert_done(self, results):
        """Zeigt das Ergebnis inline an (im GUI-Thread)"""
        self.convert_button.setEnabled(True)
        succeeded = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]

        self.progress_bar.setValue(100 if not failed else 0)

        lines = []
        if len(results) == 1:
            lines.append(("✓ " if results[0][1] else "✗ ") + results[0][0])
        else:
            lines.append(tr("✓ {ok} von {total} konvertiert")
                         .format(ok=len(succeeded), total=len(results)))
            lines.extend(f"✗ {text}" for text, ok, _ in failed[:3])
            if len(failed) > 3:
                lines.append(tr("… und {n} weitere Fehler")
                             .format(n=len(failed) - 3))

        self.result_label.setText("\n".join(lines))
        self.set_kind(self.result_label, 'success' if not failed else 'error')
        self.result_label.show()

        if succeeded:
            self.last_output_dir = succeeded[0][2].parent
            self.open_folder_button.show()

        if failed:
            self.set_status(tr("✗ {n} Konvertierung(en) fehlgeschlagen")
                            .format(n=len(failed)), 'error')
        else:
            self.set_status(tr("✓ Konvertierung abgeschlossen"), 'success')

    def open_output_folder(self):
        if self.last_output_dir:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.last_output_dir)))


def main():
    # Manueller HiDPI-Override (Qt skaliert unter Wayland sonst automatisch)
    override = os.environ.get("PICCONVERTER_SCALE")
    if override and "QT_SCALE_FACTOR" not in os.environ:
        os.environ["QT_SCALE_FACTOR"] = override

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("PicConverter")
    app.setDesktopFileName("picconverter")
    window = PicConverterGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
