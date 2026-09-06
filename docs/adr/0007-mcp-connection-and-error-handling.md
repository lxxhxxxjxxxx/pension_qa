# ADR 0007 — MCP 직접 연결 · 에러 처리 · 결정적 게이트

- 날짜: 2026-09-06 (22강)
- 상태: 채택

## 맥락
18강(설계)·20강(신뢰성)을 실제 연결 위에서 돈다. 외부는 항상 실패한다(20강) — 연결은 `claude mcp add` 한 줄이고, 어려운 건 그 다음(실패·진단·처리)이다.

## 결정
1. **읽기 전용을 코드로 강제.** `pension_qa_docs/server.py`는 `list_docs`·`read_doc`만 노출한다. 쓰기 도구는 `--with-write` 실습 스위치로만 등장(스코프 불일치 재현). 읽기 전용을 플래그·약속이 아니라 '쓰기 도구의 부재'로 지킨다(18강).
2. **에러 처리는 20강 5요소.** `app/mcp_client.py`가 타임아웃·분류 재시도(5xx·타임아웃만, 401/404 제외)·상한(=비용 캡)·폴백(캐시 stale → 없으면 보수적 실패=fail-closed)·로그를 담는다. `llm.py`(20강)와 같은 패턴을 MCP 호출에 적용.
3. **상한은 설정·훅으로 강제(모델 선의 X).** `settings.json` env `MCP_TIMEOUT`(연결/startup) · `MCP_TOOL_TIMEOUT`(도구 호출) — 20강에서 이미 고정. PreToolUse `mcp__.*` 훅에 `guard-external.sh`(정책 검사, 20강) + `guard-mcp.sh`(쓰기성 도구 exit 2 차단, 22강)를 함께 건다.
4. **진단은 자산으로.** `TROUBLESHOOTING.md`(증상→분류→원인, 상태표×1차조치).

## 근거 (2026-09-06 실측, Claude Code 2.1.260 · mcp 2.1.1)
- 서버 handshake: `initialize` → serverInfo, `tools/list` → `list_docs`·`read_doc`(기본) / +`write_doc`(--with-write).
- `claude mcp add … -- python3 -m pension_qa_docs.server` → `claude mcp list` = `✔ Connected`. 틀린 URL = `✘ Failed to connect — ENOTFOUND`. `--slow`(5초) → env 3000ms에 걸려 `✘ Failed to connect — connection timed out after 3000ms`.
- 스코프 불일치(`--with-write`): `claude mcp list` = `✔ Connected`(정상!), `claude mcp get`은 도구 목록을 안 보여준다 → `/mcp`로만 발견.
- **결정적 게이트 실증(20강 미룬 지점):** `.mcp.json` 서버를 `claude -p`가 승인 없이 로드하고, 모델이 `mcp__pension_qa-docs__write_doc` 을 호출하자 PreToolUse `guard-mcp.sh`가 exit 2로 **실제 차단**(`is_error=True`). 읽기 도구(`list_docs`)는 통과.

## 결과
- 강의 중 라이브로 만드는 산출물이 이 브랜치에 실물로 있다: `pension_qa_docs/server.py`·`TROUBLESHOOTING.md`·`.mcp.json`·`app/mcp_client.py`·`guard-mcp.sh` + 테스트.
- pytest: mcp 설치 시 서버 테스트 포함, 미설치면 `importorskip`으로 skip.
