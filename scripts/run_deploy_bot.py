#!/usr/bin/env python3
"""고정 mock 이벤트 3종을 배포봇에 흘려 채점 입력(out/)을 만든다 (23강 §5 리허설).

grade_bot.sh 가 읽는 out/post_*.txt · out/channel_policy.txt 를 '봇이 실제로 생성'한다 —
naive 재실행으로도 PASS 5/5가 재현되게. 이벤트가 고정이라 몇 번 돌려도 같은 결과.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import deploy_bot


def _fake_post(summary):  # 게시(reply/webhook)는 데모라 표준출력으로 갈음
    print("[게시]", summary)
    return "ok"


def _fake_monitor(service):  # 모니터링 pull(에러율) — 데모 고정값
    return "0.2% 정상"


def main():
    out = Path("out")
    out.mkdir(exist_ok=True)
    (out / "channel_policy.txt").write_text(
        "policy=allowlist\n", encoding="utf-8"
    )  # §1 입구 정책(⑤)
    seen = set()
    events = Path(__file__).parent / "mock_events.jsonl"
    for line in events.read_text(encoding="utf-8").splitlines():
        if line.strip():
            deploy_bot.post_status(
                _fake_post, json.loads(line), monitor=_fake_monitor, seen=seen
            )
    print("생성:", ", ".join(sorted(p.name for p in out.glob("*.txt"))))


if __name__ == "__main__":
    main()
