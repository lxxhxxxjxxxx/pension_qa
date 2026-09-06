# MCP 진단 플레이북 — 증상 → 분류 → 원인 (22강 자산)

> 새벽에 MCP가 터지면 로그부터 파지 말고 이 파일부터 연다. 넓은 그물 → 좁히기.
> ① `claude mcp list`(3초 분류) → ② `/mcp`(서버별 승인·인증·도구) → ③ `claude --debug "api,mcp"` + stdio 직접 실행(서버 속).

## 상태표 (`claude mcp list`, Claude Code 2.1.260 실측)

| 상태 | 의미 | 1차 조치 |
|---|---|---|
| `✔ Connected` | 연결 정상 — **단, 스코프 불일치는 여기 안 뜬다** | `/mcp` 도구 목록을 읽기 전용 계약과 대조 |
| `⏸ Pending approval` | 승인 대기(clone ≠ 자동 실행) | `/mcp`에서 승인. 잘못 거부했으면 `claude mcp reset-project-choices` |
| `! Needs authentication` | 401/403 — **재시도 금지**(사람이 토큰을 고칠 실패) | 토큰·환경변수 교체 확인 |
| `! tools fetch failed` | 서버는 붙었는데 도구 목록 실패 | `--debug` + stdio 직접 실행 |
| `✘ Failed to connect` | 호스트에 못 닿음 / startup 타임아웃 | URL·프로세스·네트워크. 메시지 꼬리가 원인(`ENOTFOUND …` = DNS, `connection timed out after Nms` = 느린 startup, `MCP_TIMEOUT`) |

## 실패를 가르는 신호 (20강 에러 분류)

- `✘ Failed to connect` **≠** `404`(없는 리소스). **404는 서버가 살아서 대답까지 한 것** — 연결·네트워크를 뒤지면 밤을 샌다. 진짜 원인은 이름·경로·미배포 문서.
- **401/404는 재시도 대상이 아니다.** 백 번 불러도 같은 결과 — 비용만 쌓인다(20강 폭주).
- **스코프 불일치는 상태표에 안 뜬다.** `✔ Connected` 인데 도구가 늘어 있다 → `/mcp` 도구 목록으로만 발견, 차단은 `mcp__.*` 훅(`guard-mcp.sh`).

## stdio 직접 실행 (원인 찾기 치트키)

```bash
python3 -m pension_qa_docs.server   # Claude 를 거치지 않고 서버가 혼자 뱉는 에러를 날것으로
```
경로·토큰 환경변수·의존성 문제를 MCP 계층 없이 서버 자체만 본다.
