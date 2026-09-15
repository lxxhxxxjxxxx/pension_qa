# ai-product-harness — pension_qa 팀 하네스 플러그인 (28강)

`.claude/` 에 Ch1~Ch4 동안 쌓은 하네스를 **한 덩어리로** 묶은 것. 손으로 복사하지 않는다 —
`python3 scripts/build_plugin.py` 가 `.claude/` 에서 다시 만들고, `--check`(테스트)가 드리프트를 잡는다.

- `skills/` 코드리뷰 스킬 · `agents/` 리뷰어 4역할 + 렌즈 3 · `output-styles/` 리뷰 포맷 · `commands/` `/adr`
- `hooks/hooks.json` + `hooks/*.sh` — 게이트·상한·부채 백로그·감사 훅. 경로는 `${CLAUDE_PLUGIN_ROOT}`
- `.mcp.json` + `servers/` — 근거문서 MCP 서버를 플러그인과 함께 나른다(`PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/servers`)
- 여기 **없는** 것: CLAUDE.md · rules · memory(레포 컨텍스트) · `permissions`·`env`(플러그인 settings.json 은 agent·subagentStatusLine 만)

설치: `/plugin marketplace add lxxhxxxjxxxx/pension_qa` → `/plugin install ai-product-harness@pension_qa-team`.
버전을 올리기 전엔 `claude plugin validate plugins/ai-product-harness` + 한두 명 환경에서 `--plugin-dir` 로 먼저 굴린다.
