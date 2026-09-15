# ADR 0013 — 하네스를 플러그인으로 묶어 팀 표준으로 배포한다

- 상태: 채택 (28강)
- 맥락: 0001~0012 로 쌓은 하네스(스킬·리뷰어·훅·output-style·MCP)는 전부 이 레포의 `.claude/` 에 있고,
  clone 하면 같이 온다. 그래서 **이 레포 안에서는** 이미 공유된다. 그러나 ① 팀의 다른 프로덕트 레포엔 없다
  (복사하면 그날부터 드리프트) ② 레포 안에서는 PR 한 번으로 꺼진다(0009 의 `ConfigChange` 감사 훅은 잡을 뿐
  막지 못한다) ③ 버전이 없어 누가 어느 규칙을 쓰는지 모른다 ④ `settings.local.json`·`~/.claude` 는 오지 않는다.

## 결정 1 — 이 레포가 곧 마켓플레이스다

`.claude-plugin/marketplace.json`(`pension_qa-team`)이 `plugins/ai-product-harness/` 를 가리킨다.
별도 레포를 두지 않는다 — 하네스와 그것을 만든 코드가 같은 역사를 가져야 "왜 이 훅이 있나"(0009 지식 증발)가 남는다.
팀원은 `/plugin marketplace add lxxhxxxjxxxx/pension_qa` → `/plugin install ai-product-harness@pension_qa-team`.

## 결정 2 — 플러그인은 손으로 복사하지 않고 `.claude/` 에서 빌드한다

`scripts/build_plugin.py` 가 `.claude/` → `plugins/ai-product-harness/` 를 결정적으로 만들고,
`tests/test_plugin_sync.py` 가 "지금 다시 만들면 커밋본과 같은가"를 묻는다. `.claude/` 원본은 **유지**한다 —
이 레포 안의 표준 동작·`harness_check.sh`·훅 테스트가 거기 서 있다. 원본 삭제(공식 문서의 전환 절차)는
다른 레포·strict 조직에서 플러그인만 쓸 때의 일이다.

- 옮기며 바뀌는 것: 훅 경로 `"$CLAUDE_PROJECT_DIR"/.claude/hooks/` → `"${CLAUDE_PLUGIN_ROOT}"/hooks/`.
  MCP 서버 모듈·문서는 `servers/` 로 같이 싣고 `PYTHONPATH` 로 가리킨다.
- 옮기지 못하는 것: `permissions`·`env`(플러그인 `settings.json` 은 `agent`·`subagentStatusLine` 만) ·
  CLAUDE.md · rules · memory. 이건 레포 몫 — 팀 표준화는 **플러그인(실행 하네스) + 레포(컨텍스트·권한)** 두 축이다.
- 같은 레포에서 `.claude/` 와 플러그인이 둘 다 켜지면 훅이 2중 등록된다(Stop 게이트 2회). 이 레포에선 플러그인을
  설치하지 않는다 — 다른 레포에서 설치한다.

## 결정 3 — 버전은 명시하고, 올리기 전에 먼저 굴린다

`version` 을 박아 두면 push 해도 bump 전엔 아무도 새 버전을 받지 못한다("already at the latest version").
반대로 생략하면 commit SHA 가 버전이라 매 커밋이 전파된다(카나리 불가). 우리는 명시한다 —
`claude plugin validate` + 한두 명 환경에서 `--plugin-dir` 로 먼저 굴린 뒤 bump. 잘못된 훅 하나가 전 팀을 동시에
막는 것이 배포의 blast radius(0006).

## 결과

- 강제는 마지막 수단. 순서: 자발 설치 → 버전 정합 → PII·규제가 걸린 조직만 managed `enabledPlugins`
  (`{"ai-product-harness@pension_qa-team": true}` 객체) · `strictPluginOnlyCustomization` · `disableSideloadFlags`.
  strict 를 켜면 이 레포의 `.claude/` 도 꺼진다 — 플러그인이 완성된 뒤에만 켤 수 있다.
- 뚫리는 날은 온다. 그날엔 `.claude/` 에 규칙을 추가 → `build_plugin.py` → version bump. 바닥은 그렇게 올라간다(0004·0010).
