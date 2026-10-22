"""Program startas utan att analysmotorns process kopieras (src/spawn.py)."""
import os
import subprocess

from src import spawn


def test_programs_are_started_by_posix_spawn():
    # Python takes the posix_spawn path only for a full path, no working directory and close_fds=False
    args = spawn.command(["git", "--version"])
    assert os.path.isabs(args[0])
    assert subprocess._USE_POSIX_SPAWN


def test_a_working_directory_is_set_by_the_shell(tmp_path):
    args = spawn.command(["pwd"], cwd=str(tmp_path))
    assert args[:2] == ["/bin/sh", "-c"]
    out = spawn.run(["pwd"], cwd=str(tmp_path), capture_output=True, text=True)
    assert os.path.realpath(out.stdout.strip()) == os.path.realpath(str(tmp_path))


def test_git_runs_in_the_repository():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = spawn.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
    assert out.returncode == 0 and os.path.realpath(out.stdout.strip()) == os.path.realpath(root)


def test_a_detached_program_runs_in_its_own_session(tmp_path):
    import time
    log = tmp_path / "job.log"
    pid = spawn.detached(["/bin/sh", "-c", 'pwd; ps -o pgid= -p $$'], cwd=str(tmp_path), log_path=str(log))
    for _ in range(100):
        if log.exists() and len(log.read_text().split()) >= 2:
            break
        time.sleep(0.05)
    out = log.read_text().split()
    assert os.path.realpath(out[0]) == os.path.realpath(str(tmp_path))
    assert int(out[1]) == pid != os.getpgid(0)  # a process group (and session) of its own
