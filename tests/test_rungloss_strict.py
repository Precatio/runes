"""The strict Swedish draft (src/rungloss.swedish(strict=True), used by Forskningsluckor's list): a word whose English
gloss has no Swedish equivalent stays in its Old Norse form, and a name stays as read."""
from src import rungloss as rg


class _Gloss:
    """A stand-in for rg.Glossary with fixed best glosses."""
    names = {"osunns"}

    def __init__(self, best):
        self._best = best
        self.t = {}

    def best(self, w):
        return self._best.get(w.lstrip("§"))

    translate = rg.Glossary.translate


def test_strict_keeps_untranslatable_words_and_names():
    en = _Gloss({"æftiR": "in memory of", "hiortstaðum": "people", "osunns": "runasteinn", "faður": "father"})
    words = ["æftiR", "faður", "§osunns", "hiortstaðum"]
    loose = rg.swedish(words, en, reorder=False)
    strict = rg.swedish(words, en, reorder=False, strict=True)
    assert "people" in loose.lower()          # the default lets the English gloss through (unchanged behaviour)
    assert strict == "efter fader Osunns hiortstaðum"
