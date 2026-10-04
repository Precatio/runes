"""Normalisering av runsignum för uppslag."""
import re
import unicodedata


def fold_signum(signum: str) -> str:
    """Nyckel för uppslag: utan diakritiska tecken, mellanslag och skiftläge ("Sö 113" -> "so113")."""
    s = unicodedata.normalize("NFKD", signum)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[\s_]+", "", s).lower()
