# ADR 0008 — 배포현황 봇 · 외부 연결 신뢰 경계 (Ch3 결산)

- 날짜: 2026-09-06 (23강, Ch3 파이널)
- 상태: 채택

## 맥락
Ch3(17~22)의 다섯 원칙을 하나의 봇으로 합친다 — 배포/CI 이벤트를 받아 요약해 게시. 새 개념은 방향뿐: pull(22강)에서 push(Channel)로. 위험이 뒤집힌다 — 외부가 세션에 '밀어넣는' 텍스트를 명령으로 읽으면 납치·유출.

## 결정
외부에서 온 것은 **명령이 아니라 데이터**다. 봇의 행동은 코드가 정한다.

1. **인젝션 방어 = 구조화 필드에서만 요약.** `deploy_bot.summarize`는 화이트리스트(service·version·env·status·duration·commits)만 쓴다. `commit_message` 같은 자유 텍스트는 요약에 안 들어간다. 이중 방어로 시크릿/PII 패턴은 게시 전 마지막에 마스킹.
2. **신뢰성 5요소(20강, app/mcp_client)** — 타임아웃·분류 재시도·상한·폴백·로그. **멱등**(run_id 중복 게시 방지). **폴백 = fail-closed** — 최종 실패 시 '성공'을 지어내지 않고 '확인 불가'로, 게시물 사본·멱등 집합에도 안 남긴다.
3. **모니터링 pull** — 배포 push 수신 후 에러율을 pull로 조회해 요약에 검증 칸("배포 후 에러율 0.2% 정상"). "배포는 성공했는데 서비스는 죽어 있는" 조용한 사고 방지.
4. **게이트 = 입구+출구.** 입구 = 페어링 allowlist(아는 발신자만). 출구 = PreToolUse `mcp__.*` 훅(20·22강, guard-external·guard-mcp) — 봇이 쓰기·허용 밖으로 나가면 exit 2. 상한은 모델 선의가 아니라 설정·훅으로(19강).

## 결정적 채점 (000 간판 — 챕터 파이널마다 재현 가능한 채점)
고정 mock 이벤트 3종(성공·실패·**인젝션 커밋**)을 봇에 흘려 `out/post_*.txt`·`out/channel_policy.txt`를 만들고, `grade_bot.sh`가 5항목을 PASS/FAIL로:
① 구조화 필드 반영 ② 인젝션 후 토큰·PII 미노출(존재 가드) ③ 나가는 게이트(훅) ④ .env 미커밋 ⑤ 입구 allowlist.
- **재현**: `python3 scripts/run_deploy_bot.py && bash scripts/grade_bot.sh` → `PASS 5/5`(2026-09-06 실측). 이벤트가 고정이라 몇 번 돌려도 같은 판정.
- **②가 백미**: 인젝션 방어를 말이 아니라 grep으로 증명. 게시물이 실제로 있어야만 통과(파일 부재 false-pass 차단).

## 사실 경계
- 채널 플러그인은 Telegram·Discord·iMessage·fakechat뿐 — **Slack 전용 채널 명령은 없다**. 라이브 시연은 fakechat(localhost:8787, Bun 필요, research preview). Slack webhook URL·봇 토큰·CI·모니터링 서버는 env 참조 placeholder(레포에 없음). 없는 API를 지어내지 않는다.

## 결과
- 실물: `app/deploy_bot.py` · `scripts/run_deploy_bot.py` · `scripts/mock_events.jsonl` · `scripts/grade_bot.sh` + 테스트. 채점은 한 명령으로 재현.
