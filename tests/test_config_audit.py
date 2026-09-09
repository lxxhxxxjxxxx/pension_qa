"""24강 — ConfigChange 감사 훅이 설정 변경 source를 append-only 로그로 남기는지 검증.

ConfigChange 발화 자체는 세션 이벤트(라이브)라 재현이 어렵지만, 훅 스크립트는 stdin JSON을 받아
로그를 남기는 순수한 동작이라 결정적으로 테스트할 수 있다(모델 무관).
"""

import json
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "audit-config-change.sh"


def _run(payload: str, log: Path):
    return subprocess.run(
        ["bash", str(SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        env={**os.environ, "CONFIG_AUDIT_LOG": str(log)},
    )


def test_logs_config_source(tmp_path):
    log = tmp_path / "audit.log"
    r = _run(json.dumps({"hook_event_name": "ConfigChange", "source": "project_settings"}), log)
    assert r.returncode == 0
    line = log.read_text(encoding="utf-8").strip()
    assert "ConfigChange" in line and "source=project_settings" in line


def test_appends_not_overwrites(tmp_path):
    # 감사 로그는 append-only — 두 번째 변경이 첫 줄을 덮지 않는다.
    log = tmp_path / "audit.log"
    _run(json.dumps({"source": "user_settings"}), log)
    _run(json.dumps({"source": "local_settings"}), log)
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert "source=user_settings" in lines[0] and "source=local_settings" in lines[1]


def test_malformed_payload_does_not_crash(tmp_path):
    # 깨진 stdin이 와도 훅은 통과(감사 유실은 있어도 세션은 안 막는다)하고 unknown으로 남긴다.
    log = tmp_path / "audit.log"
    r = _run("not-json{{{", log)
    assert r.returncode == 0
    assert "source=unknown" in log.read_text(encoding="utf-8")
