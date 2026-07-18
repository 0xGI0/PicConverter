"""Testkonfiguration: Sprache auf Deutsch pinnen, damit die Assertions
auf deutsche Meldungen auch in englischsprachigen CI-Umgebungen halten."""

import os

os.environ.setdefault('PICCONVERTER_LANG', 'de')
