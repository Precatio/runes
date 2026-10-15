"""Starta andra program (git, Rscript) från analysmotorn utan att kopiera hela dess process.

subprocess startar normalt ett program genom att först kopiera den anropande processen (fork). I den långkörande
analysmotorn, med många trådar (Firestore/gRPC, numpy), kan kopian på macOS krascha innan programmet hinner starta:
git och R dog då med signal 11 (2026-10-14 och 2026-10-15), medan samma kommandon fungerade från terminalen.
Med posix_spawn startas programmet direkt utan kopia. Python använder posix_spawn bara om programmet anges med full
sökväg, close_fds=False och ingen arbetskatalog anges; en arbetskatalog sätts därför av /bin/sh, som byter katalog
och sedan ersätter sig själv med programmet (exec). Python skapar filbeskrivare som inte ärvs (PEP 446), så
close_fds=False lämnar inget öppet åt barnprocessen utöver dess egna in- och utdata."""
import os
import shutil
import subprocess


def command(args, cwd=None):
    """The argument list that starts `args` (in `cwd`) through posix_spawn."""
    exe = args[0] if os.path.dirname(args[0]) else (shutil.which(args[0]) or args[0])
    args = [exe, *args[1:]]
    if cwd and os.path.abspath(cwd) != os.getcwd():
        return ["/bin/sh", "-c", 'cd "$0" && exec "$@"', cwd, *args]
    return args


def run(args, cwd=None, **kw):
    """subprocess.run without copying the calling process."""
    kw.setdefault("close_fds", False)
    return subprocess.run(command(args, cwd), **kw)
