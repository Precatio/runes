import os
import re

from src import blog_labels

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _ts_pairs(block: str) -> list[tuple[str, str]]:
    return re.findall(r'\["([^"]+)", "([^"]+)"\]', block)


def test_label_lists_agree_between_python_and_typescript():
    ts = open(os.path.join(ROOT, "web", "src", "lib", "labels.ts"), encoding="utf-8").read()
    types = ts.split("export const TYPES")[1].split("];")[0]
    subjects = ts.split("export const SUBJECTS")[1].split("];")[0]
    assert _ts_pairs(types) == blog_labels.TYPES
    assert _ts_pairs(subjects) == blog_labels.SUBJECTS
    assert int(re.search(r"MAX_LABELS = (\d+)", ts).group(1)) == blog_labels.MAX_LABELS


def test_check_rejects_unknown_two_types_and_too_many():
    assert blog_labels.check(["Forskning", "Ristare"]) is None
    assert "Okänd" in blog_labels.check(["Forskning", "Runor"])
    assert "en typ" in blog_labels.check(["Forskning", "Metod"])
    assert "Högst" in blog_labels.check(["Forskning"] + blog_labels.SUBJECT_NAMES[:6])
    assert blog_labels.ordered(["Norden", "Forskning", "Ristare"]) == ["Forskning", "Ristare", "Norden"]
