"""Gemensam konfiguration för API:t."""
import os

# Gemini-modeller. Googles "-latest"-alias följer med när enskilda versioner avvecklas
# (1.5 och 2.5 är redan avstängda för nya nycklar). Lås en exakt version via miljövariabel vid behov.
GEMINI_PRO_MODEL = os.environ.get("GEMINI_PRO_MODEL", "gemini-pro-latest")
GEMINI_FLASH_MODEL = os.environ.get("GEMINI_FLASH_MODEL", "gemini-flash-latest")

APP_NAME = "Runforskning (Aagaard Research)"
APP_VERSION = "2.0.0"
# Version av mätmetoden. Höjs när beräkningen ändras så att gamla och nya mätningar kan skiljas åt.
# groove-2: V-vinkeln mäts som öppningsvinkel mellan väggarna (rättad 2026-10-04; groove-1 gav 180° - V).
# groove-3: väggarna anpassas mellan 20 och 80 % av djupet, bredden mäts mellan väggarnas linjer vid
#           spårkanten och snittet begränsas till ett fönster runt mätpunkten (2026-10-04).
METHOD_VERSION = "groove-3"
