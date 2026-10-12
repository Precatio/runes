#!/usr/bin/env bash
# The analysis engine in development, reloading only when the code changes (api/ and src/). Watching the whole project –
# data/cache, web/node_modules and web/.next, which Next writes to all the time – keeps the reloader busy at full CPU and
# restarts the server in the middle of a corpus job in R.
cd "$(dirname "$0")/.." || exit 1
exec .venv/bin/uvicorn api.main:app --reload --port "${PORT:-8000}" --reload-dir api --reload-dir src
