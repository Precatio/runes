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
