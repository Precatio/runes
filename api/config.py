"""Gemensam konfiguration för API:t."""
import os

# Gemini-modeller. Googles "-latest"-alias följer med när enskilda versioner avvecklas
# (1.5 och 2.5 är redan avstängda för nya nycklar). Lås en exakt version via miljövariabel vid behov.
GEMINI_PRO_MODEL = os.environ.get("GEMINI_PRO_MODEL", "gemini-pro-latest")
GEMINI_FLASH_MODEL = os.environ.get("GEMINI_FLASH_MODEL", "gemini-flash-latest")

# Claude-modeller (standard). Den kraftfullaste för analys och text, en snabbare för enkla uppgifter.
CLAUDE_PRO_MODEL = os.environ.get("CLAUDE_PRO_MODEL", "claude-opus-5-5")
CLAUDE_FAST_MODEL = os.environ.get("CLAUDE_FAST_MODEL", "claude-haiku-4-5-20251001")

APP_NAME = "Vitki"
APP_VERSION = "2.0.0"
# Version av mätmetoden. Höjs när beräkningen ändras så att gamla och nya mätningar kan skiljas åt.
# groove-2: V-vinkeln mäts som öppningsvinkel mellan väggarna (rättad 2026-10-04; groove-1 gav 180° - V).
# groove-3: väggarna anpassas mellan 20 och 80 % av djupet, bredden mäts mellan väggarnas linjer vid
#           spårkanten och snittet begränsas till ett fönster runt mätpunkten (2026-10-04).
# groove-4: profilen räknas om till jämnt punktavstånd och alla fönster anges i mm (2026-10-06).
# groove-5: automatiska analysen mäter bara spår som känns igen som runor, och fyller bara små hål i
#           spårmasken (slingband som stängs av stavar räknades förut som en enda bred yta) (2026-10-10).
METHOD_VERSION = "groove-5"
