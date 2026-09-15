#!/usr/bin/env python3
"""29강 — 텔레메트리를 화면(console exporter)으로 돌린다.

24강이 `.claude/settings.json` `env` 에 OTel(otlp → localhost:4317)을 박아 뒀다. 그 값은 **셸 env 를 이긴다** —
터미널에서 `export OTEL_METRICS_EXPORTER=console` 을 쳐도 아무것도 안 뜬다(collector 가 없으면 조용히 어디로도
안 간다). 이기는 건 `.claude/settings.local.json`(local > project). 이 스크립트가 그 파일의 env 만 켜고 끈다.

  python3 scripts/otel_console.py on     # settings.local.json 에 console exporter env 추가
  python3 scripts/otel_console.py off    # 그 키만 제거(다른 local 설정은 보존)

켠 뒤: claude -p "/code-review HEAD~1" 2>&1 | tee docs/otel/console.log   (docs/otel/ 은 gitignore — 계정 식별자가 찍힌다)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".claude" / "settings.local.json"
KEYS = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "console",
    "OTEL_LOGS_EXPORTER": "console",
    "OTEL_METRIC_EXPORT_INTERVAL": "1000",
    "OTEL_LOGS_EXPORT_INTERVAL": "1000",
    "OTEL_LOG_TOOL_DETAILS": "1",  # 없으면 사용자 정의 스킬·에이전트 이름이 "custom" 으로 가려진다
    "OTEL_EXPORTER_OTLP_ENDPOINT": "",  # project settings 의 4317 을 비워 둔다
}


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else ""
    data = json.loads(LOCAL.read_text(encoding="utf-8")) if LOCAL.exists() else {}
    env = dict(data.get("env", {}))
    if mode == "on":
        env.update(KEYS)
        data["env"] = env
        LOCAL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✔ {LOCAL.relative_to(ROOT)} — console exporter 켬. 다음 세션부터 텔레메트리가 표준출력에 찍힌다.")
        print('  claude -p "/code-review HEAD~1" 2>&1 | tee docs/otel/console.log')
        return 0
    if mode == "off":
        for k in KEYS:
            env.pop(k, None)
        if env:
            data["env"] = env
        else:
            data.pop("env", None)
        if data:
            LOCAL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif LOCAL.exists():
            LOCAL.unlink()
        print("✔ console exporter 끔 — project settings 의 otlp 로 돌아간다.")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
