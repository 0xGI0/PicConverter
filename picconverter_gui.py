#!/usr/bin/env python3
"""
PicConverter GUI - Modernes Bildkonvertierungs-Tool (CustomTkinter)
"""

import os
import sys
import tempfile
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox

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

# Drag & Drop ist optional -- ohne tkinterdnd2 läuft die GUI trotzdem
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


# Unterstützte Formate
SUPPORTED_FORMATS = {
    'JPEG (.jpg, .jpeg)': 'JPEG',
    'PNG (.png)': 'PNG',
    'BMP (.bmp)': 'BMP',
    'TIFF (.tiff, .tif)': 'TIFF',
    'GIF (.gif)': 'GIF',
    'WebP (.webp)': 'WebP',
    'ICO (.ico)': 'ICO'
}

# Dateiendung je Formatname
EXT_MAP = {
    'JPEG (.jpg, .jpeg)': '.jpg',
    'PNG (.png)': '.png',
    'BMP (.bmp)': '.bmp',
    'TIFF (.tiff, .tif)': '.tiff',
    'GIF (.gif)': '.gif',
    'WebP (.webp)': '.webp',
    'ICO (.ico)': '.ico'
}

# Akzeptierte Eingabedateien (Dialog und Drag & Drop)
SUPPORTED_INPUT_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp', '.ico'
}

# Qualitäts-/Kompressionseinstellungen je Format
QUALITY_SETTINGS = {
    'JPEG': {'min': 1, 'max': 100, 'default': 85, 'name': 'Qualität'},
    'PNG': {'min': 0, 'max': 9, 'default': 6, 'name': 'Kompression'},
    'WebP': {'min': 0, 'max': 100, 'default': 80, 'name': 'Qualität'},
    'TIFF': {'min': 0, 'max': 9, 'default': 6, 'name': 'Kompression'},
}

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
        self.root.title("PicConverter - Moderner Bildkonverter")

        # Wunschgröße 1100x780 (in Skalierungseinheiten), aber nie größer
        # als der Bildschirm -- wichtig bei HiDPI-Skalierung auf kleinen Displays
        width = min(1100, int(self.root.winfo_screenwidth() * 0.92 / ui_scale))
        height = min(780, int(self.root.winfo_screenheight() * 0.90 / ui_scale))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(960, width), min(700, height))

        self.input_path = None
        self.image = None
        self.preview_image = None
        self.output_path = None

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
        ctk.CTkLabel(header, text="Moderner Bildkonverter", font=self.font_subtitle,
                     text_color=COLORS['muted'], anchor="w").grid(row=1, column=0, sticky="w")

        self.appearance_switch = ctk.CTkSegmentedButton(
            header, values=["Dunkel", "Hell"], command=self.on_appearance_change)
        self.appearance_switch.set("Dunkel")
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

        # ---------- Eingabedatei ----------
        input_card, input_content = self.create_card(left, "📁 Eingabedatei")
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, PAD))

        self.drop_zone = ctk.CTkFrame(input_content, corner_radius=8, border_width=2,
                                      border_color=COLORS['border'],
                                      fg_color=COLORS['panel'])
        self.drop_zone.grid(row=0, column=0, sticky="ew")
        self.drop_zone.grid_columnconfigure(0, weight=1)

        drop_text = ("Bild hierher ziehen\noder klicken zum Auswählen"
                     if DND_AVAILABLE else "Klicken, um eine Bilddatei auszuwählen")
        self.drop_label = ctk.CTkLabel(self.drop_zone, text=drop_text,
                                       text_color=COLORS['muted'], justify="center")
        self.drop_label.grid(row=0, column=0, padx=PAD, pady=20)
        for widget in (self.drop_zone, self.drop_label):
            widget.bind("<Button-1>", lambda e: self.select_file())
            widget.configure(cursor="hand2")

        file_row = ctk.CTkFrame(input_content, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        file_row.grid_columnconfigure(0, weight=1)

        self.input_label = ctk.CTkLabel(file_row, text="Keine Datei ausgewählt",
                                        anchor="w", text_color=COLORS['muted'])
        self.input_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(file_row, text="Datei auswählen", width=150,
                      command=self.select_file).grid(row=0, column=1, padx=(PAD, 0))

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

        self.info_text = ctk.CTkTextbox(info_content, height=100, corner_radius=8,
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
        self.format_menu.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, PAD))

        # Qualität
        self.quality_label = ctk.CTkLabel(settings, text="Qualität", anchor="w")
        self.quality_label.grid(row=2, column=0, sticky="w")

        self.quality_value_label = ctk.CTkLabel(settings, text="85", font=self.font_bold,
                                                text_color=COLORS['accent'])
        self.quality_value_label.grid(row=2, column=1, sticky="e")

        self.quality_var = tk.IntVar(value=85)
        self.quality_slider = ctk.CTkSlider(settings, from_=1, to=100, number_of_steps=99,
                                            variable=self.quality_var,
                                            command=self.on_quality_change)
        self.quality_slider.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, PAD))

        # Auflösung
        ctk.CTkLabel(settings, text="Auflösung", anchor="w").grid(
            row=4, column=0, sticky="w")

        resolution_row = ctk.CTkFrame(settings, fg_color="transparent")
        resolution_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 6))

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
            row=6, column=0, columnspan=2, sticky="w", pady=(6, PAD))

        # Größenschätzung
        estimate_row = ctk.CTkFrame(settings, fg_color="transparent")
        estimate_row.grid(row=7, column=0, columnspan=2, sticky="ew")
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

        # ---------- Ausgabedatei ----------
        output_card, output_content = self.create_card(right, "💾 Ausgabedatei")
        output_card.grid(row=1, column=0, sticky="ew", pady=(0, PAD))

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
        action_card.grid(row=2, column=0, sticky="ew")

        self.convert_button = ctk.CTkButton(action_content, text="Konvertieren starten",
                                            height=46, font=self.font_bold,
                                            fg_color="#2fa572", hover_color="#106a43",
                                            state="disabled",
                                            command=self.convert_image)
        self.convert_button.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(action_content, height=10)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        # ---------- Statusleiste ----------
        status_bar = ctk.CTkFrame(self.root, corner_radius=0)
        status_bar.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(status_bar, text="Bereit", anchor="w",
                                         text_color=COLORS['accent'])
        self.status_label.pack(fill="both", expand=True, padx=PAD, pady=6)

        if not DND_AVAILABLE:
            self.set_status("Bereit — Tipp: 'pip install tkinterdnd2' aktiviert Drag & Drop",
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
        ctk.set_appearance_mode("dark" if choice == "Dunkel" else "light")

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

        if not paths:
            return

        path = Path(paths[0])
        if not path.is_file():
            self.set_status("✗ Das abgelegte Element ist keine Datei", 'error')
            return
        if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
            self.set_status(f"✗ Nicht unterstütztes Format: {path.suffix or path.name}",
                            'error')
            return
        if len(paths) > 1:
            self.set_status("Mehrere Dateien abgelegt — nur die erste wird geladen",
                            'warning')

        self.input_path = path
        self.load_image()

    # ---------- Dateiauswahl und Laden ----------

    def select_file(self):
        """Wählt eine Datei aus via Dialog"""
        filetypes = [
            ("Alle Bilder", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif *.webp *.ico"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("TIFF", "*.tiff *.tif"),
            ("GIF", "*.gif"),
            ("WebP", "*.webp"),
            ("ICO", "*.ico"),
            ("Alle Dateien", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=filetypes
        )

        if filename:
            self.input_path = Path(filename)
            self.load_image()

    def load_image(self):
        try:
            self.image = Image.open(self.input_path)

            # Bildinformationen
            info = f"Datei:      {self.input_path.name}\n"
            info += f"Größe:      {os.path.getsize(self.input_path) / (1024*1024):.2f} MB\n"
            info += f"Auflösung:  {self.image.size[0]} × {self.image.size[1]} Pixel\n"
            info += f"Format:     {self.image.format}"

            self.info_text.configure(state="normal")
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", info)
            self.info_text.configure(state="disabled")

            # Vorschau
            preview_img = self.image.copy()
            preview_img.thumbnail((460, 320), Image.Resampling.LANCZOS)
            self.preview_image = ctk.CTkImage(light_image=preview_img,
                                              dark_image=preview_img,
                                              size=preview_img.size)
            self.preview_label.configure(image=self.preview_image, text="")

            # Eingabelabel
            short_name = self.input_path.name
            if len(short_name) > 50:
                short_name = short_name[:47] + "..."
            self.input_label.configure(text=f"✓ {short_name}",
                                       text_color=COLORS['success'])

            # Standardauflösung
            self.width_var.set(str(self.image.size[0]))
            self.height_var.set(str(self.image.size[1]))

            # Button aktivieren
            self.convert_button.configure(state="normal")
            self.progress_bar.set(0)

            # Ausgabedatei
            self.update_output_path()

            self.set_status("✓ Bild erfolgreich geladen", 'success')

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Bildes:\n{e}")
            self.set_status(f"✗ Fehler beim Laden: {e}", 'error')

    # ---------- Einstellungen ----------

    def on_format_change(self, choice=None):
        format_name = self.format_var.get()
        output_format = SUPPORTED_FORMATS[format_name]

        if output_format in QUALITY_SETTINGS:
            settings = QUALITY_SETTINGS[output_format]
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

        self.update_output_path()

    def on_quality_change(self, value=None):
        self.quality_value_label.configure(text=str(int(self.quality_var.get())))

    def parse_resolution(self):
        """Liest Breite/Höhe aus den Eingabefeldern; ungültige Werte werden gemeldet"""
        width = None
        height = None
        try:
            if self.width_var.get():
                width = int(self.width_var.get())
            if self.height_var.get():
                height = int(self.height_var.get())
        except ValueError:
            self.set_status("Ungültige Auflösung — Originalgröße wird verwendet", 'warning')
        return width, height

    # ---------- Ausgabedatei ----------

    def update_output_path(self):
        if self.input_path:
            ext = EXT_MAP.get(self.format_var.get(), '.jpg')
            output_name = self.input_path.stem + ext
            self.output_label.configure(text=output_name,
                                        text_color=COLORS['accent'])
            self.output_path = self.input_path.parent / output_name

    def select_output(self):
        if not self.input_path:
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst eine Eingabedatei aus.")
            self.set_status("Bitte zuerst eine Eingabedatei auswählen", 'warning')
            return

        format_name = self.format_var.get()
        ext = EXT_MAP.get(format_name, '.jpg')

        filename = filedialog.asksaveasfilename(
            title="Ausgabedatei speichern",
            defaultextension=ext,
            filetypes=[(format_name, f"*{ext}"), ("Alle Dateien", "*.*")]
        )

        if filename:
            self.output_path = Path(filename)
            self.output_label.configure(text=self.output_path.name,
                                        text_color=COLORS['accent'])

    # ---------- Größenschätzung ----------

    def estimate_size(self):
        if not self.image:
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst eine Eingabedatei aus.")
            self.set_status("Bitte zuerst eine Eingabedatei auswählen", 'warning')
            return

        try:
            format_name = self.format_var.get()
            output_format = SUPPORTED_FORMATS[format_name]

            quality = int(self.quality_var.get()) if output_format in QUALITY_SETTINGS else None
            width, height = self.parse_resolution()

            estimated_size = self.calculate_estimated_size(self.image, output_format,
                                                           quality, width, height)

            if estimated_size is not None:
                original_size = os.path.getsize(self.input_path) / (1024 * 1024)
                self.estimate_label.configure(
                    text=f"Geschätzt: {estimated_size:.2f} MB "
                         f"(Original: {original_size:.2f} MB)"
                )
                if original_size > 0:
                    compression = (1 - estimated_size / original_size) * 100
                    if compression > 0:
                        self.set_status(f"📉 Schätzung: -{compression:.1f}% kleiner", 'success')
                    else:
                        self.set_status(f"📈 Schätzung: +{abs(compression):.1f}% größer", 'warning')
            else:
                self.estimate_label.configure(text="Konnte Größe nicht schätzen")
                self.set_status("✗ Fehler bei Größenberechnung", 'error')

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Größenberechnung:\n{e}")
            self.set_status(f"✗ Fehler bei Größenberechnung: {e}", 'error')

    def calculate_estimated_size(self, image, output_format, quality, width=None, height=None):
        try:
            temp_img = image.copy()

            if width and height:
                temp_img = temp_img.resize((width, height), Image.Resampling.LANCZOS)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format.lower()}') as tmp:
                temp_path = tmp.name

            save_kwargs = {}
            if output_format == 'JPEG':
                save_kwargs['quality'] = quality if quality else 85
                save_kwargs['optimize'] = True
            elif output_format == 'PNG':
                if quality is not None:
                    save_kwargs['compress_level'] = 9 - quality
            elif output_format == 'WebP':
                save_kwargs['quality'] = quality if quality else 80
            elif output_format == 'TIFF':
                save_kwargs['compression'] = 'tiff_lzw'

            temp_img.save(temp_path, format=output_format, **save_kwargs)

            size_mb = os.path.getsize(temp_path) / (1024 * 1024)

            os.unlink(temp_path)

            return size_mb
        except Exception:
            return None

    # ---------- Konvertierung ----------

    def convert_image(self):
        if not self.image:
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst eine Eingabedatei aus.")
            self.set_status("Bitte zuerst eine Eingabedatei auswählen", 'warning')
            return

        # Alle Parameter im GUI-Thread einsammeln -- der Worker-Thread
        # darf keine Tkinter-Variablen anfassen
        format_name = self.format_var.get()
        output_format = SUPPORTED_FORMATS[format_name]

        quality = None
        if output_format in QUALITY_SETTINGS:
            quality = int(self.quality_var.get())

        width, height = self.parse_resolution()

        if self.aspect_ratio_var.get() and width and height and self.image:
            original_ratio = self.image.size[0] / self.image.size[1]
            if width / height != original_ratio:
                width = int(height * original_ratio)

        self.convert_button.configure(state="disabled")
        self.set_status("⏳ Konvertiere...", 'accent')
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        thread = threading.Thread(target=self._convert_thread,
                                  args=(output_format, quality, width, height))
        thread.daemon = True
        thread.start()

    def _convert_thread(self, output_format, quality, width, height):
        try:
            success, error = self.perform_conversion(
                self.input_path, self.output_path, output_format,
                quality, width, height
            )

            if success:
                final_size = os.path.getsize(self.output_path) / (1024 * 1024)
                message = (f"✓ Konvertierung erfolgreich!\n\n"
                           f"📁 Ausgabedatei: {self.output_path.name}\n"
                           f"💾 Größe: {final_size:.2f} MB")
                self.root.after(0, lambda: self._on_convert_done(True, message))
            else:
                self.root.after(0, lambda err=error: self._on_convert_done(False, err))

        except Exception as e:
            self.root.after(0, lambda err=str(e): self._on_convert_done(False, err))

    def _on_convert_done(self, success, detail):
        """Beendet die Fortschrittsanzeige und meldet das Ergebnis (im GUI-Thread)"""
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0 if success else 0)
        self.convert_button.configure(state="normal")

        if success:
            self.set_status("✓ Konvertierung abgeschlossen", 'success')
            messagebox.showinfo("Erfolg", detail)
        else:
            self.set_status(f"✗ Fehler bei Konvertierung: {detail}", 'error')
            messagebox.showerror("Fehler", f"Fehler bei der Konvertierung:\n{detail}")

    def perform_conversion(self, input_path, output_path, output_format,
                           quality=None, width=None, height=None):
        try:
            img = Image.open(input_path)

            if output_format in ['JPEG', 'BMP'] and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode not in ('RGB', 'RGBA', 'L', 'P'):
                img = img.convert('RGB')

            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            save_kwargs = {}
            if output_format == 'JPEG':
                save_kwargs['quality'] = quality if quality else 85
                save_kwargs['optimize'] = True
            elif output_format == 'PNG':
                if quality is not None:
                    save_kwargs['compress_level'] = 9 - quality
            elif output_format == 'WebP':
                save_kwargs['quality'] = quality if quality else 80
            elif output_format == 'TIFF':
                save_kwargs['compression'] = 'tiff_lzw'

            img.save(output_path, format=output_format, **save_kwargs)
            return True, None
        except Exception as e:
            return False, str(e)


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
    ctk.set_appearance_mode("dark")
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
