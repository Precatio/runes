# Manuella utvecklingsskript

Lösa skript för felsökning mot externa tjänster (Gemini, K-samsök) och benchmark.
De är inte automatiska tester – de riktiga testerna ligger i `tests/` och körs med `pytest`.

Kör från projektroten så att `api` och `src` kan importeras:

```bash
.venv/bin/python -m scripts.list_all_models
```

Skript som anropar Gemini läser nyckeln från miljövariabeln `GEMINI_API_KEY`.
