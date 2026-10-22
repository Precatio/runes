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


def detached(args, cwd=None, log_path=None) -> int:
    """Starts `args` (in `cwd`) through posix_spawn in a session of its own, so that it outlives the calling process
    (subprocess cannot: start_new_session takes it to the copying path). Output is appended to `log_path`, input is
    empty. Returns the process id; a thread collects the process when it ends, so that no zombie is left behind."""
    import threading
    args = command(args, cwd)
    fd = os.open(log_path or os.devnull, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        pid = os.posix_spawn(args[0], args, dict(os.environ),
                             file_actions=[(os.POSIX_SPAWN_OPEN, 0, os.devnull, os.O_RDONLY, 0),
                                           (os.POSIX_SPAWN_DUP2, fd, 1), (os.POSIX_SPAWN_DUP2, fd, 2)],
                             setsid=True)
    finally:
        os.close(fd)  # the child has its own copies

    def reap():
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
    threading.Thread(target=reap, daemon=True).start()
    return pid
