"""Studie 4, förutsättning 0c: led F:s blindprov (utdata/sparlasare/led_f.py, 2026-10-17) på stenarna utanför
Södermanland. Hela ord på 2–6 runor döljs och fylls utan spår, med skannerns spår och med omflyttade spår (kontroll).
Spårens särdrag kommer ur src/trace_reader (data/cache/traces) i stället för led E:s egna cachefiler; samma format.
    PYTHONPATH=. .venv/bin/python utdata/forskningsplan/s4_blindprov.py "M 1" "Hs 21" ..."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "sparlasare"))
from src import trace_reader as tr  # noqa: E402
import led_e, led_f  # noqa: E402
led_e.load_features = led_f.led_e.load_features = lambda s: tr.features(s) or tr.compute_features(s)
led_f.HERE = os.path.dirname(os.path.abspath(__file__))
led_f.main(*sys.argv[1:])
