#!/usr/bin/env python3
"""
PicConverter GUI - Modernes Bild- & PDF-Konvertierungs-Tool (CustomTkinter)
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog

try:
    import customtkinter as ctk
except ImportError:
    print("Fehler: customtkinter konnte nicht importiert werden.", file=sys.stderr)
    print("\nBitte installieren Sie die Abhängigkeiten:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

from PIL import Image
try:
    from PIL import ImageTk  # noqa: F401 -- wird von CTkImage benötigt
except ImportError:
    print("Fehler: ImageTk konnte nicht importiert werden.", file=sys.stderr)
    print("\nBitte installieren Sie das python3-pillow-tk Paket:", file=sys.stderr)
    print("  sudo dnf install python3-pillow-tk", file=sys.stderr)
    print("\nOder mit pip:", file=sys.stderr)
    print("  pip install Pillow[tk]", file=sys.stderr)
    sys.exit(1)

import picconverter_core as core

# Drag & Drop ist optional -- ohne tkinterdnd2 läuft die GUI trotzdem
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


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

# Akzeptierte Eingabedateien (Dialog und Drag & Drop)
SUPPORTED_INPUT_EXTENSIONS = {f'.{ext}' for ext in core.FORMAT_BY_EXT}

# Farbpaare (hell, dunkel) -- CustomTkinter wählt je nach Appearance-Mode
COLORS = {
    'accent': ('#1f538d', '#6ea8dc'),
    'success': ('#1a7a3c', '#a6e3a1'),
    'error': ('#b3261e', '#f38ba8'),
    'warning': ('#8a5a00', '#f9e2af'),
    'muted': ('gray35', 'gray65'),
    'panel': ('gray88', 'gray17'),
    'border': ('gray70', 'gray35'),
}

PAD = 16  # Einheitlicher Abstand zwischen Sektionen


if DND_AVAILABLE:
    class _DnDWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        """CTk-Hauptfenster mit tkdnd-Unterstützung"""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)


def create_window():
    """Erstellt das Hauptfenster; fällt ohne funktionierendes tkdnd auf CTk zurück"""
    global DND_AVAILABLE
    if DND_AVAILABLE:
        try:
            return _DnDWindow()
        except Exception:
            DND_AVAILABLE = False
    return ctk.CTk()


class PicConverterGUI:
    def __init__(self, root, ui_scale=1.0):
        self.root = root
        self.root.title("PicConverter - Bild- & PDF-Konverter")

        # Wunschgröße 1100x900 (in Skalierungseinheiten), aber nie größer
        # als der Bildschirm -- wichtig bei HiDPI-Skalierung auf kleinen Displays
        width = min(1100, int(self.root.winfo_screenwidth() * 0.92 / ui_scale))
        height = min(900, int(self.root.winfo_screenheight() * 0.90 / ui_scale))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(960, width), min(700, height))

        self.input_paths = []          # Warteschlange aller geladenen Dateien
        self.selected_index = None     # Index der Datei, die Vorschau/Infos zeigt
        self.image = None              # geladenes Bild der ausgewählten Datei
        self.preview_image = None
        self.pdf_page_count = 0        # 0 = ausgewählte Datei ist keine PDF
        self.prefilled_size = ('', '') # zuletzt vorbefüllte Auflösungswerte
        self.exif_overrides = {}       # EXIF-Änderungen aus dem Editor
        self.output_file = None        # gewählte Zieldatei (nur Einzelkonvertierung)
        self.output_dir = None         # gewählter Zielordner
        self.last_output_dir = None    # für den "Ordner öffnen"-Button

        self.setup_fonts()
        self.setup_ui()
        if DND_AVAILABLE:
            self.setup_dnd()

    def setup_fonts(self):
        try:
            mono_family = tkfont.nametofont("TkFixedFont").actual("family")
        except Exception:
            mono_family = "Courier"
        self.font_title = ctk.CTkFont(size=26, weight="bold")
        self.font_subtitle = ctk.CTkFont(size=13)
        self.font_section = ctk.CTkFont(size=14, weight="bold")
        self.font_bold = ctk.CTkFont(size=13, weight="bold")
        self.font_mono = ctk.CTkFont(family=mono_family, size=12)

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # ---------- Header ----------
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(PAD, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🖼️ PicConverter", font=self.font_title,
                     anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Moderner Bild- & PDF-Konverter", font=self.font_subtitle,
                     text_color=COLORS['muted'], anchor="w").grid(row=1, column=0, sticky="w")

        self.appearance_switch = ctk.CTkSegmentedButton(
            header, values=["System", "Dunkel", "Hell"],
            command=self.on_appearance_change)
        self.appearance_switch.set("System")
        self.appearance_switch.grid(row=0, column=1, rowspan=2, sticky="e")

        # ---------- Inhalt: zwei Spalten ----------
        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(8, 8))
        content.grid_columnconfigure(0, weight=1, uniform="col")
        content.grid_columnconfigure(1, weight=1, uniform="col")
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD // 2))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(PAD // 2, 0))
        right.grid_columnconfigure(0, weight=1)

        # ---------- Eingabedateien ----------
        input_card, input_content = self.create_card(left, "📁 Eingabedateien")
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, PAD))

        self.drop_zone = ctk.CTkFrame(input_content, corner_radius=8, border_width=2,
                                      border_color=COLORS['border'],
                                      fg_color=COLORS['panel'])
        self.drop_zone.grid(row=0, column=0, sticky="ew")
        self.drop_zone.grid_columnconfigure(0, weight=1)

        drop_text = ("Bilder oder PDFs hierher ziehen\noder klicken zum Auswählen"
                     if DND_AVAILABLE else "Klicken, um Bilder oder PDFs auszuwählen")
        self.drop_label = ctk.CTkLabel(self.drop_zone, text=drop_text,
                                       text_color=COLORS['muted'], justify="center")
        self.drop_label.grid(row=0, column=0, padx=PAD, pady=16)
        for widget in (self.drop_zone, self.drop_label):
            widget.bind("<Button-1>", lambda e: self.select_files())
            widget.configure(cursor="hand2")

        file_row = ctk.CTkFrame(input_content, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        file_row.grid_columnconfigure(0, weight=1)

        self.input_label = ctk.CTkLabel(file_row, text="Keine Dateien ausgewählt",
                                        anchor="w", text_color=COLORS['muted'])
        self.input_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(file_row, text="Dateien auswählen", width=140,
                      command=self.select_files).grid(row=0, column=1, padx=(PAD, 0))
        ctk.CTkButton(file_row, text="Leeren", width=70,
                      fg_color="transparent", border_width=1,
                      border_color=COLORS['border'], hover_color=COLORS['panel'],
                      text_color=("gray10", "gray90"),
                      command=self.clear_files).grid(row=0, column=2, padx=(8, 0))

        # Dateiliste -- wird erst ab zwei Dateien eingeblendet
        self.file_list = ctk.CTkScrollableFrame(input_content, height=96,
                                                fg_color=COLORS['panel'],
                                                corner_radius=8)
        try:
            # Workaround: die interne Scrollbar erzwingt sonst ~200px Mindesthöhe
            self.file_list._scrollbar.configure(height=0)
        except AttributeError:
            pass
        self.file_list.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.file_list.grid_columnconfigure(0, weight=1)
        self.file_list.grid_remove()

        # PDF-Seitennavigation -- wird nur bei geladener PDF eingeblendet
        self.page_row = ctk.CTkFrame(input_content, fg_color="transparent")
        self.page_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.page_row.grid_remove()

        ctk.CTkLabel(self.page_row, text="PDF-Seite").grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(self.page_row, text="◀", width=32,
                      command=lambda: self.step_page(-1)).grid(row=0, column=1)
        self.page_var = tk.StringVar(value="1")
        self.page_entry = ctk.CTkEntry(self.page_row, textvariable=self.page_var,
                                       width=56, justify="center")
        self.page_entry.grid(row=0, column=2, padx=6)
        self.page_entry.bind("<Return>", lambda e: self.on_page_change())
        self.page_entry.bind("<FocusOut>", lambda e: self.on_page_change())
        ctk.CTkButton(self.page_row, text="▶", width=32,
                      command=lambda: self.step_page(1)).grid(row=0, column=3)
        self.page_count_label = ctk.CTkLabel(self.page_row, text="von 1",
                                             text_color=COLORS['muted'])
        self.page_count_label.grid(row=0, column=4, padx=(8, 0))

        self.all_pages_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.page_row, text="Alle Seiten exportieren",
                        variable=self.all_pages_var).grid(row=0, column=5, padx=(PAD, 0))

        # ---------- Vorschau ----------
        preview_card, preview_content = self.create_card(left, "👁️ Vorschau")
        preview_card.grid(row=1, column=0, sticky="nsew", pady=(0, PAD))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_content.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(preview_content, text="Kein Bild geladen",
                                          text_color=COLORS['muted'], corner_radius=8,
                                          fg_color=COLORS['panel'], height=240)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        # ---------- Bildinformationen ----------
        info_card, info_content = self.create_card(left, "ℹ️ Bildinformationen")
        info_card.grid(row=2, column=0, sticky="ew")

        self.info_text = ctk.CTkTextbox(info_content, height=110, corner_radius=8,
                                        font=self.font_mono, fg_color=COLORS['panel'],
                                        activate_scrollbars=False)
        self.info_text.grid(row=0, column=0, sticky="ew")
        self.info_text.configure(state="disabled")

        # ---------- Konvertierungseinstellungen ----------
        settings_card, settings = self.create_card(right, "⚙️ Konvertierungseinstellungen")
        settings_card.grid(row=0, column=0, sticky="ew", pady=(0, PAD))
        settings.grid_columnconfigure(0, weight=1)

        # Format
        ctk.CTkLabel(settings, text="Ausgabeformat", anchor="w").grid(
            row=0, column=0, sticky="w")
        self.format_var = tk.StringVar(value=list(SUPPORTED_FORMATS.keys())[0])
        self.format_menu = ctk.CTkOptionMenu(settings, variable=self.format_var,
                                             values=list(SUPPORTED_FORMATS.keys()),
                                             width=230, command=self.on_format_change)
        self.format_menu.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))

        # PDF zusammenfassen -- nur bei Zielformat PDF sichtbar
        self.merge_var = tk.BooleanVar(value=False)
        self.merge_check = ctk.CTkCheckBox(
            settings, text="Alle Eingaben in eine PDF zusammenfassen",
            variable=self.merge_var, command=self.update_output_path)
        self.merge_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self.merge_check.grid_remove()

        # Qualität
        self.quality_label = ctk.CTkLabel(settings, text="Qualität", anchor="w")
        self.quality_label.grid(row=3, column=0, sticky="w")

        self.quality_value_label = ctk.CTkLabel(settings, text="85", font=self.font_bold,
                                                text_color=COLORS['accent'])
        self.quality_value_label.grid(row=3, column=1, sticky="e")

        self.quality_var = tk.IntVar(value=85)
        self.quality_slider = ctk.CTkSlider(settings, from_=1, to=100, number_of_steps=99,
                                            variable=self.quality_var,
                                            command=self.on_quality_change)
        self.quality_slider.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 8))

        # Zielgröße statt Qualität (nur JPEG/WebP)
        target_row = ctk.CTkFrame(settings, fg_color="transparent")
        target_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.use_target_var = tk.BooleanVar(value=False)
        self.target_check = ctk.CTkCheckBox(target_row, text="Zielgröße:",
                                            variable=self.use_target_var,
                                            command=self.on_target_toggle)
        self.target_check.grid(row=0, column=0)
        self.target_var = tk.StringVar(value="500")
        self.target_entry = ctk.CTkEntry(target_row, textvariable=self.target_var,
                                         width=80, justify="center")
        self.target_entry.grid(row=0, column=1, padx=(8, 6))
        ctk.CTkLabel(target_row, text="KB (Qualität wird automatisch gesucht)",
                     text_color=COLORS['muted']).grid(row=0, column=2)

        # Auflösung
        ctk.CTkLabel(settings, text="Auflösung", anchor="w").grid(
            row=6, column=0, sticky="w")

        resolution_row = ctk.CTkFrame(settings, fg_color="transparent")
        resolution_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 6))

        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()

        ctk.CTkLabel(resolution_row, text="Breite").grid(row=0, column=0, padx=(0, 6))
        ctk.CTkEntry(resolution_row, textvariable=self.width_var,
                     width=90, justify="center").grid(row=0, column=1)
        ctk.CTkLabel(resolution_row, text="×").grid(row=0, column=2, padx=8)
        ctk.CTkLabel(resolution_row, text="Höhe").grid(row=0, column=3, padx=(0, 6))
        ctk.CTkEntry(resolution_row, textvariable=self.height_var,
                     width=90, justify="center").grid(row=0, column=4)
        ctk.CTkLabel(resolution_row, text="px").grid(row=0, column=5, padx=(8, 0))

        self.aspect_ratio_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings, text="Seitenverhältnis beibehalten",
                        variable=self.aspect_ratio_var).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(6, 12))

        # Größenschätzung
        estimate_row = ctk.CTkFrame(settings, fg_color="transparent")
        estimate_row.grid(row=9, column=0, columnspan=2, sticky="ew")
        estimate_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(estimate_row, text="Größe schätzen", width=140,
                      fg_color="transparent", border_width=1,
                      border_color=COLORS['border'],
                      hover_color=COLORS['panel'],
                      text_color=("gray10", "gray90"),
                      command=self.estimate_size).grid(row=0, column=0)

        self.estimate_label = ctk.CTkLabel(estimate_row,
                                           text="Geschätzte Ausgabegröße: -- MB",
                                           anchor="w", justify="left",
                                           text_color=COLORS['warning'])
        self.estimate_label.grid(row=0, column=1, sticky="w", padx=(12, 0))

        # ---------- EXIF-Metadaten ----------
        exif_card, exif_content = self.create_card(right, "🏷️ EXIF-Metadaten")
        exif_card.grid(row=1, column=0, sticky="ew", pady=(0, PAD))

        exif_row = ctk.CTkFrame(exif_content, fg_color="transparent")
        exif_row.grid(row=0, column=0, sticky="ew")
        exif_row.grid_columnconfigure(1, weight=1)

        self.exif_strip_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(exif_row, text="Metadaten entfernen",
                        variable=self.exif_strip_var).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(exif_row, text="Anzeigen / Bearbeiten", width=170,
                      fg_color="transparent", border_width=1,
                      border_color=COLORS['border'], hover_color=COLORS['panel'],
                      text_color=("gray10", "gray90"),
                      command=self.open_exif_editor).grid(row=0, column=2, sticky="e")

        self.exif_hint_label = ctk.CTkLabel(exif_content, text="", anchor="w",
                                            text_color=COLORS['accent'])
        self.exif_hint_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.exif_hint_label.grid_remove()

        # ---------- Ausgabe ----------
        output_card, output_content = self.create_card(right, "💾 Ausgabe")
        output_card.grid(row=2, column=0, sticky="ew", pady=(0, PAD))

        output_row = ctk.CTkFrame(output_content, fg_color="transparent")
        output_row.grid(row=0, column=0, sticky="ew")
        output_row.grid_columnconfigure(0, weight=1)

        self.output_label = ctk.CTkLabel(output_row, text="Automatisch generiert",
                                         anchor="w", text_color=COLORS['muted'])
        self.output_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(output_row, text="Speicherort wählen", width=160,
                      command=self.select_output).grid(row=0, column=1, padx=(PAD, 0))

        # ---------- Konvertieren + Fortschritt ----------
        action_card, action_content = self.create_card(right, "🚀 Konvertierung")
        action_card.grid(row=3, column=0, sticky="ew")
        action_content.grid_columnconfigure(0, weight=1)

        self.convert_button = ctk.CTkButton(action_content, text="Konvertieren starten",
                                            height=46, font=self.font_bold,
                                            fg_color="#2fa572", hover_color="#106a43",
                                            state="disabled",
                                            command=self.convert)
        self.convert_button.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(action_content, height=10)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        self.result_label = ctk.CTkLabel(action_content, text="", anchor="w",
                                         justify="left", wraplength=420)
        self.result_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.result_label.grid_remove()

        self.open_folder_button = ctk.CTkButton(
            action_content, text="📂 Ordner öffnen", width=140,
            fg_color="transparent", border_width=1,
            border_color=COLORS['border'], hover_color=COLORS['panel'],
            text_color=("gray10", "gray90"),
            command=self.open_output_folder)
        self.open_folder_button.grid(row=2, column=1, sticky="e", pady=(10, 0))
        self.open_folder_button.grid_remove()

        # ---------- Statusleiste ----------
        status_bar = ctk.CTkFrame(self.root, corner_radius=0)
        status_bar.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(status_bar, text="Bereit", anchor="w",
                                         text_color=COLORS['accent'])
        self.status_label.pack(fill="both", expand=True, padx=PAD, pady=6)

        if not DND_AVAILABLE:
            self.set_status("Bereit — Tipp: 'pip install tkinterdnd2' aktiviert Drag & Drop",
                            'muted')
        elif not core.PDF_AVAILABLE:
            self.set_status("Bereit — Tipp: 'pip install pymupdf' aktiviert PDF-Eingabe",
                            'muted')

        # Initiale Format-Einstellung
        self.on_format_change()

    def create_card(self, parent, title):
        """Erstellt eine Card mit Titelzeile; gibt (Card, Content-Frame) zurück"""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=title, font=self.font_section, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=PAD, pady=(12, 6))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(0, 14))
        content.grid_columnconfigure(0, weight=1)

        return card, content

    def set_status(self, message, kind='accent'):
        """Zeigt eine Statusmeldung farbcodiert in der Statusleiste an"""
        self.status_label.configure(text=message, text_color=COLORS[kind])

    def on_appearance_change(self, choice):
        modes = {"System": "system", "Dunkel": "dark", "Hell": "light"}
        ctk.set_appearance_mode(modes.get(choice, "system"))

    # ---------- Drag & Drop ----------

    def setup_dnd(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        self.root.dnd_bind('<<DropEnter>>', lambda e: self.drop_zone.configure(
            border_color=COLORS['accent']))
        self.root.dnd_bind('<<DropLeave>>', lambda e: self.drop_zone.configure(
            border_color=COLORS['border']))

    def on_drop(self, event):
        self.drop_zone.configure(border_color=COLORS['border'])
        try:
            paths = self.root.tk.splitlist(event.data)
        except tk.TclError:
            paths = [event.data]
        self.add_files([Path(p) for p in paths])

    # ---------- Dateiauswahl und Laden ----------

    def select_files(self):
        filetypes = [
            ("Alle unterstützten Dateien",
             "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif *.webp *.ico *.pdf"),
            ("Alle Bilder", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif *.webp *.ico"),
            ("PDF", "*.pdf"),
            ("Alle Dateien", "*.*")
        ]
        filenames = filedialog.askopenfilenames(
            title="Bilder oder PDFs auswählen", filetypes=filetypes)
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
                self.set_status("✗ Keine unterstützten Dateien dabei", 'error')
            return

        # Gewählter Speicherort bezieht sich auf die alte Auswahl
        self.output_file = None

        if self.selected_index is None:
            self.selected_index = 0
        self.refresh_file_list()
        self.load_selected()

        if skipped:
            self.set_status(f"✓ {added} Datei(en) geladen — {skipped} nicht unterstützte "
                            f"übersprungen", 'warning')

    def clear_files(self):
        self.input_paths = []
        self.selected_index = None
        self.image = None
        self.pdf_page_count = 0
        self.output_file = None
        self.output_dir = None
        self.refresh_file_list()
        self.page_row.grid_remove()
        self.preview_label.configure(image=None, text="Kein Bild geladen")
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.configure(state="disabled")
        self.input_label.configure(text="Keine Dateien ausgewählt",
                                   text_color=COLORS['muted'])
        self.output_label.configure(text="Automatisch generiert",
                                    text_color=COLORS['muted'])
        self.convert_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.result_label.grid_remove()
        self.open_folder_button.grid_remove()
        self.set_status("Liste geleert", 'muted')

    def refresh_file_list(self):
        """Baut die Dateiliste neu auf (sichtbar ab zwei Dateien)"""
        for widget in self.file_list.winfo_children():
            widget.destroy()

        if len(self.input_paths) < 2:
            self.file_list.grid_remove()
            return

        self.file_list.grid()
        for i, path in enumerate(self.input_paths):
            selected = (i == self.selected_index)
            btn = ctk.CTkButton(
                self.file_list, text=path.name, anchor="w", height=26,
                fg_color=COLORS['accent'] if selected else "transparent",
                text_color=("white", "gray10") if selected else ("gray10", "gray90"),
                hover_color=COLORS['border'],
                command=lambda i=i: self.select_index(i))
            btn.grid(row=i, column=0, sticky="ew", pady=1)

    def select_index(self, index):
        self.selected_index = index
        self.refresh_file_list()
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
                self.page_var.set("1")
                self.page_count_label.configure(text=f"von {self.pdf_page_count}")
                self.page_row.grid()
                self.image = core.load_image(path, 1)
            else:
                self.pdf_page_count = 0
                self.page_row.grid_remove()
                self.image = core.load_image(path)

            self.refresh_display()

            if len(self.input_paths) == 1:
                short_name = path.name
                if len(short_name) > 45:
                    short_name = short_name[:42] + "..."
                self.input_label.configure(text=f"✓ {short_name}",
                                           text_color=COLORS['success'])
            else:
                self.input_label.configure(
                    text=f"✓ {len(self.input_paths)} Dateien in der Warteschlange",
                    text_color=COLORS['success'])

            self.convert_button.configure(state="normal")
            self.progress_bar.set(0)
            self.update_output_path()
            self.set_status("✓ Datei erfolgreich geladen", 'success')

        except Exception as e:
            self.set_status(f"✗ Fehler beim Laden: {e}", 'error')

    def refresh_display(self):
        """Aktualisiert Bildinformationen, Vorschau und Auflösungsfelder"""
        path = self.selected_path
        if self.pdf_page_count:
            format_text = f"PDF · Seite {self.page_var.get()} von {self.pdf_page_count}"
        else:
            format_text = self.image.format or Image.open(path).format

        exif_count = len(core.read_exif(self.image))

        info = f"Datei:      {path.name}\n"
        info += f"Größe:      {path.stat().st_size / (1024*1024):.2f} MB\n"
        info += f"Auflösung:  {self.image.size[0]} × {self.image.size[1]} Pixel\n"
        info += f"Format:     {format_text}\n"
        info += f"EXIF:       {exif_count} Einträge" if exif_count else "EXIF:       keine"

        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", info)
        self.info_text.configure(state="disabled")

        # Vorschau
        preview_img = self.image.copy()
        preview_img.thumbnail((460, 300), Image.Resampling.LANCZOS)
        self.preview_image = ctk.CTkImage(light_image=preview_img,
                                          dark_image=preview_img,
                                          size=preview_img.size)
        self.preview_label.configure(image=self.preview_image, text="")

        # Auflösungsfelder vorbefüllen; die Werte gelten als "unverändert",
        # bis der User sie anfasst (wichtig für Batch-Konvertierung)
        self.width_var.set(str(self.image.size[0]))
        self.height_var.set(str(self.image.size[1]))
        self.prefilled_size = (self.width_var.get(), self.height_var.get())

    # ---------- PDF-Seitennavigation ----------

    def step_page(self, delta):
        try:
            page = int(self.page_var.get()) + delta
        except ValueError:
            page = 1
        self.page_var.set(str(page))
        self.on_page_change()

    def on_page_change(self, event=None):
        """Rendert die gewählte PDF-Seite neu (mit Bereichsprüfung)"""
        if not self.pdf_page_count:
            return
        try:
            page = int(self.page_var.get())
        except ValueError:
            page = 1
        page = max(1, min(page, self.pdf_page_count))
        self.page_var.set(str(page))
        try:
            self.image = core.load_image(self.selected_path, page)
            self.refresh_display()
            self.update_output_path()
            self.set_status(f"✓ Seite {page} geladen", 'success')
        except Exception as e:
            self.set_status(f"✗ Fehler beim Laden der Seite: {e}", 'error')

    # ---------- Einstellungen ----------

    def on_format_change(self, choice=None):
        output_format = SUPPORTED_FORMATS[self.format_var.get()]

        if output_format in core.QUALITY_SETTINGS:
            settings = core.QUALITY_SETTINGS[output_format]
            self.quality_slider.configure(from_=settings['min'], to=settings['max'],
                                          number_of_steps=settings['max'] - settings['min'],
                                          state="normal")
            self.quality_var.set(settings['default'])
            self.quality_label.configure(text=settings['name'])
            self.on_quality_change()
        else:
            self.quality_slider.configure(state="disabled")
            self.quality_label.configure(text="Qualität (für dieses Format nicht verfügbar)")
            self.quality_value_label.configure(text="--")

        # Zielgröße nur für JPEG/WebP
        if output_format in core.TARGET_SIZE_FORMATS:
            self.target_check.configure(state="normal")
            self.target_entry.configure(state="normal")
        else:
            self.use_target_var.set(False)
            self.target_check.configure(state="disabled")
            self.target_entry.configure(state="disabled")

        # Zusammenfassen nur bei Zielformat PDF
        if output_format == 'PDF':
            self.merge_check.grid()
        else:
            self.merge_var.set(False)
            self.merge_check.grid_remove()

        self.on_target_toggle()
        self.update_output_path()

    def on_quality_change(self, value=None):
        self.quality_value_label.configure(text=str(int(self.quality_var.get())))

    def on_target_toggle(self):
        """Bei aktiver Zielgröße übernimmt die Qualitätssuche den Slider"""
        output_format = SUPPORTED_FORMATS[self.format_var.get()]
        if self.use_target_var.get() and output_format in core.TARGET_SIZE_FORMATS:
            self.quality_slider.configure(state="disabled")
            self.quality_value_label.configure(text="auto")
        elif output_format in core.QUALITY_SETTINGS:
            self.quality_slider.configure(state="normal")
            self.on_quality_change()

    def parse_resolution(self):
        """Liest die Zielauflösung; unveränderte oder leere Felder bedeuten
        'Originalgröße beibehalten' (None, None)"""
        width_text = self.width_var.get().strip()
        height_text = self.height_var.get().strip()
        if (width_text, height_text) == self.prefilled_size:
            return None, None
        if not width_text and not height_text:
            return None, None
        try:
            width = int(width_text) if width_text else None
            height = int(height_text) if height_text else None
        except ValueError:
            self.set_status("Ungültige Auflösung — Originalgröße wird verwendet", 'warning')
            return None, None
        return width, height

    def parse_target_kb(self):
        if not self.use_target_var.get():
            return None
        try:
            target = int(self.target_var.get())
            if target < 1:
                raise ValueError
            return target
        except ValueError:
            self.set_status("Ungültige Zielgröße — bitte KB als Zahl angeben", 'warning')
            return None

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
            self.set_status("Bitte zuerst eine Datei laden", 'warning')
            return

        editor = ctk.CTkToplevel(self.root)
        editor.title("EXIF-Metadaten")
        editor.geometry("560x640")
        editor.transient(self.root)
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(editor, text="Bearbeitbare Felder", font=self.font_section,
                     anchor="w").grid(row=0, column=0, sticky="ew",
                                      padx=PAD, pady=(PAD, 6))

        fields_frame = ctk.CTkFrame(editor, fg_color="transparent")
        fields_frame.grid(row=1, column=0, sticky="ew", padx=PAD)
        fields_frame.grid_columnconfigure(1, weight=1)

        current_exif = self.image.getexif()
        entries = {}
        originals = {}
        for row, (name, (tag, label)) in enumerate(core.EXIF_EDITABLE_TAGS.items()):
            ctk.CTkLabel(fields_frame, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", pady=3, padx=(0, 10))
            var = tk.StringVar()
            original = str(current_exif.get(tag, '')).strip()
            # Bereits vorgemerkte Änderungen haben Vorrang vor den Dateiwerten
            var.set(self.exif_overrides.get(name, original))
            originals[name] = original
            ctk.CTkEntry(fields_frame, textvariable=var).grid(
                row=row, column=1, sticky="ew", pady=3)
            entries[name] = var

        ctk.CTkLabel(editor, text="Alle Metadaten der ausgewählten Datei",
                     font=self.font_section, anchor="w").grid(
            row=2, column=0, sticky="sew", padx=PAD, pady=(12, 6))

        viewer = ctk.CTkTextbox(editor, font=self.font_mono,
                                fg_color=COLORS['panel'], corner_radius=8)
        viewer.grid(row=3, column=0, sticky="nsew", padx=PAD)
        editor.grid_rowconfigure(3, weight=1)

        all_tags = core.read_exif(self.image)
        if all_tags:
            width = max(len(name) for name, _ in all_tags)
            viewer.insert("1.0", "\n".join(
                f"{name:<{width}}  {value}" for name, value in all_tags))
        else:
            viewer.insert("1.0", "Keine EXIF-Daten vorhanden.")
        viewer.configure(state="disabled")

        button_row = ctk.CTkFrame(editor, fg_color="transparent")
        button_row.grid(row=4, column=0, sticky="ew", padx=PAD, pady=PAD)
        button_row.grid_columnconfigure(0, weight=1)

        def apply():
            self.exif_overrides = {
                name: var.get().strip()
                for name, var in entries.items()
                if var.get().strip() != originals[name]
            }
            self.update_exif_hint()
            editor.destroy()
            if self.exif_overrides:
                self.set_status(f"✓ {len(self.exif_overrides)} EXIF-Feld(er) werden "
                                f"beim Konvertieren angepasst", 'success')
            else:
                self.set_status("EXIF-Änderungen zurückgesetzt", 'muted')

        ctk.CTkButton(button_row, text="Abbrechen", width=110,
                      fg_color="transparent", border_width=1,
                      border_color=COLORS['border'], hover_color=COLORS['panel'],
                      text_color=("gray10", "gray90"),
                      command=editor.destroy).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(button_row, text="Übernehmen", width=110,
                      command=apply).grid(row=0, column=2)

    def update_exif_hint(self):
        if self.exif_overrides:
            fields = ', '.join(core.EXIF_EDITABLE_TAGS[n][1].split(' (')[0]
                               for n in self.exif_overrides)
            self.exif_hint_label.configure(text=f"✎ Wird angepasst: {fields}")
            self.exif_hint_label.grid()
        else:
            self.exif_hint_label.grid_remove()

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
            elif self.all_pages_var.get():
                jobs.extend((path, p)
                            for p in range(1, core.pdf_page_count(path) + 1))
            elif path == self.selected_path:
                jobs.append((path, int(self.page_var.get())))
            else:
                jobs.append((path, 1))
        return jobs

    def update_output_path(self):
        if not self.input_paths:
            return
        ext = EXT_MAP.get(self.format_var.get(), '.jpg')
        first = self.input_paths[0]

        if self.merge_var.get() and SUPPORTED_FORMATS[self.format_var.get()] == 'PDF':
            name = (self.output_file.name if self.output_file
                    else f"{first.stem}_gesamt.pdf")
            self.output_label.configure(text=name, text_color=COLORS['accent'])
        elif len(self.input_paths) == 1 and not (self.pdf_page_count
                                                 and self.all_pages_var.get()):
            if self.output_file:
                name = self.output_file.name
            else:
                page = int(self.page_var.get()) if self.pdf_page_count else None
                name = core.output_stem(first, page) + ext
            self.output_label.configure(text=name, text_color=COLORS['accent'])
        else:
            target = self.output_dir if self.output_dir else Path("je Eingabeordner")
            self.output_label.configure(text=f"Mehrere Dateien → {target.name}",
                                        text_color=COLORS['accent'])

    def select_output(self):
        if not self.input_paths:
            self.set_status("Bitte zuerst Dateien auswählen", 'warning')
            return

        merge = self.merge_var.get() and \
            SUPPORTED_FORMATS[self.format_var.get()] == 'PDF'
        single = len(self.input_paths) == 1 and not (self.pdf_page_count
                                                     and self.all_pages_var.get())

        if merge or single:
            ext = '.pdf' if merge else EXT_MAP.get(self.format_var.get(), '.jpg')
            filename = filedialog.asksaveasfilename(
                title="Ausgabedatei speichern", defaultextension=ext,
                filetypes=[(self.format_var.get(), f"*{ext}"), ("Alle Dateien", "*.*")])
            if filename:
                self.output_file = Path(filename)
        else:
            dirname = filedialog.askdirectory(title="Ausgabeordner wählen")
            if dirname:
                self.output_dir = Path(dirname)

        self.update_output_path()

    # ---------- Größenschätzung ----------

    def estimate_size(self):
        if self.image is None:
            self.set_status("Bitte zuerst eine Datei laden", 'warning')
            return

        try:
            output_format = SUPPORTED_FORMATS[self.format_var.get()]
            exif_mode = 'strip' if self.exif_strip_var.get() else 'keep'
            width, height = self.parse_resolution()
            width, height = self.resolution_for(self.image, width, height,
                                                self.aspect_ratio_var.get())

            target_kb = self.parse_target_kb()
            if target_kb and output_format in core.TARGET_SIZE_FORMATS:
                quality, estimated = core.quality_for_target(
                    self.image, output_format, target_kb, width, height,
                    exif_mode, self.exif_overrides)
                self.estimate_label.configure(
                    text=f"Geschätzt: {estimated:.2f} MB (Qualität {quality})")
                self.set_status(f"📉 Zielgröße {target_kb} KB → Qualität {quality}",
                                'success')
                return

            quality = (int(self.quality_var.get())
                       if output_format in core.QUALITY_SETTINGS else None)
            estimated = core.estimate_size(self.image, output_format, quality,
                                           width, height, exif_mode,
                                           self.exif_overrides)
            original = self.selected_path.stat().st_size / (1024 * 1024)
            self.estimate_label.configure(
                text=f"Geschätzt: {estimated:.2f} MB (Original: {original:.2f} MB)")
            if original > 0:
                compression = (1 - estimated / original) * 100
                if compression > 0:
                    self.set_status(f"📉 Schätzung: -{compression:.1f}% kleiner", 'success')
                else:
                    self.set_status(f"📈 Schätzung: +{abs(compression):.1f}% größer",
                                    'warning')
        except Exception as e:
            self.estimate_label.configure(text="Konnte Größe nicht schätzen")
            self.set_status(f"✗ Fehler bei Größenberechnung: {e}", 'error')

    # ---------- Konvertierung ----------

    def convert(self):
        if not self.input_paths:
            self.set_status("Bitte zuerst Dateien auswählen", 'warning')
            return

        # Alle Parameter im GUI-Thread einsammeln -- der Worker-Thread
        # darf keine Tkinter-Variablen anfassen
        output_format = SUPPORTED_FORMATS[self.format_var.get()]
        extension = EXT_MAP[self.format_var.get()].lstrip('.')

        try:
            jobs = self.build_jobs()
        except Exception as e:
            self.set_status(f"✗ {e}", 'error')
            return

        settings = {
            'format': output_format,
            'extension': extension,
            'quality': (int(self.quality_var.get())
                        if output_format in core.QUALITY_SETTINGS else None),
            'target_kb': self.parse_target_kb(),
            'resolution': self.parse_resolution(),
            'keep_aspect': self.aspect_ratio_var.get(),
            'exif_mode': 'strip' if self.exif_strip_var.get() else 'keep',
            'exif_overrides': dict(self.exif_overrides),
            'merge': (self.merge_var.get() and output_format == 'PDF'
                      and len(jobs) > 0),
            'all_pages': self.all_pages_var.get(),
            'output_file': self.output_file if len(jobs) == 1 or self.merge_var.get()
                           else None,
            'output_dir': self.output_dir,
        }

        self.convert_button.configure(state="disabled")
        self.result_label.grid_remove()
        self.open_folder_button.grid_remove()
        self.set_status("⏳ Konvertiere...", 'accent')
        self.progress_bar.set(0)

        thread = threading.Thread(target=self._convert_thread, args=(jobs, settings))
        thread.daemon = True
        thread.start()

    def _output_for_job(self, path, page, settings):
        if settings['output_file']:
            return settings['output_file']
        stem = core.output_stem(path, page, settings['all_pages'])
        directory = settings['output_dir'] or path.parent
        return directory / f"{stem}.{settings['extension']}"

    def _convert_thread(self, jobs, settings):
        results = []
        total = len(jobs)

        try:
            if settings['merge']:
                images = [core.load_image(path, page or 1) for path, page in jobs]
                out = settings['output_file'] or \
                    (settings['output_dir'] or jobs[0][0].parent) / \
                    f"{jobs[0][0].stem}_gesamt.pdf"
                core.images_to_pdf(images, out)
                size_mb = out.stat().st_size / (1024 * 1024)
                results.append((f"{total} Seite(n) → {out.name} ({size_mb:.2f} MB)",
                                True, out))
                self.root.after(0, lambda: self._on_convert_done(results))
                return

            for i, (path, page) in enumerate(jobs):
                label = path.name if page is None else f"{path.name} (S. {page})"
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
                            settings['exif_overrides'])

                    core.convert(img, out, settings['format'], quality,
                                 width, height, settings['exif_mode'],
                                 settings['exif_overrides'])
                    size_mb = out.stat().st_size / (1024 * 1024)
                    results.append((f"{label} → {out.name} ({size_mb:.2f} MB)",
                                    True, out))
                except Exception as e:
                    results.append((f"{label}: {e}", False, None))

                progress = (i + 1) / total
                self.root.after(0, lambda p=progress: self.progress_bar.set(p))

            self.root.after(0, lambda: self._on_convert_done(results))

        except Exception as e:
            results.append((str(e), False, None))
            self.root.after(0, lambda: self._on_convert_done(results))

    def _on_convert_done(self, results):
        """Zeigt das Ergebnis inline an (im GUI-Thread)"""
        self.convert_button.configure(state="normal")
        succeeded = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]

        self.progress_bar.set(1.0 if not failed else 0)

        lines = []
        if len(results) == 1:
            lines.append(("✓ " if results[0][1] else "✗ ") + results[0][0])
        else:
            lines.append(f"✓ {len(succeeded)} von {len(results)} konvertiert")
            lines.extend(f"✗ {text}" for text, ok, _ in failed[:3])
            if len(failed) > 3:
                lines.append(f"… und {len(failed) - 3} weitere Fehler")

        self.result_label.configure(
            text="\n".join(lines),
            text_color=COLORS['success'] if not failed else COLORS['error'])
        self.result_label.grid()

        if succeeded:
            self.last_output_dir = succeeded[0][2].parent
            self.open_folder_button.grid()

        if failed:
            self.set_status(f"✗ {len(failed)} Konvertierung(en) fehlgeschlagen", 'error')
        else:
            self.set_status("✓ Konvertierung abgeschlossen", 'success')

    def open_output_folder(self):
        if self.last_output_dir:
            subprocess.Popen(['xdg-open', str(self.last_output_dir)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def detect_ui_scale():
    """Ermittelt den HiDPI-Skalierungsfaktor.

    CustomTkinter erkennt Display-Skalierung nur auf Windows/macOS selbst;
    unter Linux (X11/XWayland) wird sie hier aus der Server-DPI abgeleitet.
    Muss VOR dem Erstellen des Hauptfensters aufgerufen werden, damit alle
    Widgets von Anfang an korrekt skaliert gezeichnet werden.
    Manueller Override über die Umgebungsvariable PICCONVERTER_SCALE.
    """
    override = os.environ.get("PICCONVERTER_SCALE")
    if override:
        try:
            return max(0.5, min(3.0, float(override)))
        except ValueError:
            print(f"Warnung: Ungültiger Wert PICCONVERTER_SCALE={override!r} "
                  f"wird ignoriert", file=sys.stderr)
    if not sys.platform.startswith("linux"):
        return None
    try:
        probe = tk.Tk()
        probe.withdraw()
        scale = probe.winfo_fpixels('1i') / 96.0
        probe.destroy()
    except tk.TclError:
        return None
    if scale > 1.05:
        return min(scale, 3.0)
    return None


def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    scale = detect_ui_scale()
    if scale:
        ctk.set_widget_scaling(scale)
        ctk.set_window_scaling(scale)
    root = create_window()
    app = PicConverterGUI(root, ui_scale=scale or 1.0)
    root.mainloop()


if __name__ == '__main__':
    main()
