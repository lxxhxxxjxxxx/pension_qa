"""25강 — surgical 상한 게이트가 결정적으로 동작하는지. git diff --numstat 파싱을 검증."""

import subprocess
from pathlib import Path

HOOK = (
    Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "guard-diff-size.sh"
)


def _run(env_over, cwd):
    import os

    env = {**os.environ, **env_over}
    return subprocess.run(
        ["bash", str(HOOK)], cwd=cwd, capture_output=True, text=True, env=env
    )


def test_within_limit_passes(tmp_path):
    # 작은 변경(파일 1·라인 1)은 통과
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("1\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("1\n2\n")  # +1 라인
    r = _run({"CLAUDE_PROJECT_DIR": str(tmp_path)}, tmp_path)
    assert r.returncode == 0


def test_over_line_limit_blocks(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text(
        "\n".join(str(i) for i in range(50)) + "\n"
    )  # +49 라인
    r = _run({"CLAUDE_PROJECT_DIR": str(tmp_path), "GUARD_MAX_LINES": "10"}, tmp_path)
    assert r.returncode == 2
    assert "surgical 상한 초과" in r.stderr


def test_over_file_limit_blocks(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    for i in range(3):
        (tmp_path / f"f{i}.txt").write_text("a\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    for i in range(3):
        (tmp_path / f"f{i}.txt").write_text("a\nb\n")  # 3 파일 변경
    r = _run({"CLAUDE_PROJECT_DIR": str(tmp_path), "GUARD_MAX_FILES": "2"}, tmp_path)
    assert r.returncode == 2
