"""Appens namn och adresser, som rapporterna anger när de hänvisar till Vitki."""

APP_NAME = "Vitki"
APP_URL = "https://vitkirunor.se"
REPO_URL = "https://github.com/Precatio/runes"


def software_reference(version: str = "2.0") -> str:
    """Referensen till programvaran i rapporternas litteraturlistor."""
    return f"Vitki, version {version}. Programvara. {APP_URL} (källkod: {REPO_URL})"
