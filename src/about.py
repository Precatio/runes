"""Appens namn och adresser, som rapporterna anger när de hänvisar till Vitki."""

APP_NAME = "Vitki"
APP_URL = "https://vitkirunor.se"
REPO_URL = "https://github.com/Precatio/runes"


# Zenodo: one DOI per release and one for all versions (RELEASING.md step 8)
CONCEPT_DOI = "10.5281/zenodo.24004431"
VERSION_DOIS = {"3.1.0": "10.5281/zenodo.24004432"}


def software_reference(version: str = "2.0") -> str:
    """Referensen till programvaran i rapporternas litteraturlistor, med versionens DOI när den finns, annars den för alla
    versioner."""
    doi = VERSION_DOIS.get(version)
    ref = f"https://doi.org/{doi}" if doi else f"alla versioner: https://doi.org/{CONCEPT_DOI}"
    return f"Vitki, version {version}. Programvara. {ref}. {APP_URL} (källkod: {REPO_URL})"
