> 📚 **강의 스냅샷 — 13강을 마친 상태입니다.**  
> 시작점 `ch2-12-done` → **지금 여기 `ch2-13-done`** → 다음 강 시작점 `ch2-14-start`

## 13강 · [실습] 코드리뷰 → 수정까지 완료하는 Skill 만들기

번들 `/code-review`는 **잘 찾는다**. 문제는 12건 중 뭐가 머지 블로커인지 정해주지 않는다는 것. 판정하는 스킬을 직접 만든다.

**배우는 것**

- 심각도 정의 + 제외 규칙 → 리포트가 Nit 0건으로 줄어든다
- `` !`grep` ``·`` !`pytest` ``를 본문에 박아 **결정적 게이트 실행 결과**를 근거로 쓴다
- 수정 라우팅: 기계가 판정한 형식 위반만 자동 수정, 판단이 필요한 건 사람 큐로
- 동명 프로젝트 스킬이 번들 스킬을 덮어쓴다

**이 브랜치에 들어온 것**

- `.claude/skills/code-review/SKILL.md`
- `.claude/skills/code-review/checklist.md`
- `.claude/settings.json` allow에 동적 주입 명령 3종(`git diff`·`grep`·`python -m pytest`)

> 리뷰 대상 나쁜 PR 3종(가드레일 우회 캐시 · 범위 확대 · bare except)은 **`ch2-13-pr`** 브랜치에 있다.
> `git checkout ch2-13-pr && git diff HEAD~1` — 비교 기준은 반드시 `HEAD~1`.

**확인해 보기**

```bash
grep -rEn "except\s*:" app/ || echo "OK: bare except 없음"
python -m pytest -q        # 31 passed
```

전체 강별 브랜치 지도는 [`main` 브랜치 README](../../tree/main#강의별-브랜치-지도)에 있습니다.
<!-- /강의안내 -->

# pension_qa — 연금 안내 Q&A 에이전트

사용자의 연금(연금저축·IRP·연금소득세) 질문에 **사내 연금 가이드 문서를 검색(RAG)** 해서 근거와 함께 답하는 작은 LLM 프로덕트.

> ⚠️ 클린룸 예제입니다. 모든 문서·코드는 강의용으로 새로 작성한 **가상** 데이터이며 실제 사내 시스템과 무관합니다.

## 동작

```
질문 → [입력 가드레일] → 문서 검색 → LLM 답변 → [출력 가드레일] → 답변+근거
```

## 실행

```bash
pip install -r requirements.txt
python -m app.main "연금저축 세액공제 한도가 얼마인가요?"
```

`ANTHROPIC_API_KEY`가 없으면 LLM 호출은 stub 응답으로 대체됩니다(검색·가드레일은 그대로 동작).

## 구조

- `app/retriever.py` — 문서 검색(단순 키워드 스코어)
- `app/guardrails.py` — 입력(PII·범위)·출력(유출) 가드레일
- `app/llm.py` — LLM 클라이언트(Anthropic, 없으면 stub)
- `app/agent.py` — 오케스트레이션
- `app/pension_calc.py` — 연금 계산 유틸(Decimal 전용 — 아직 답변 파이프라인 미연결)
- `data/` — 가상 연금 가이드
- `tests/` — 샘플 테스트

## TODO (알려진 거친 부분)

- 가드레일이 stub 수준(정규식 몇 개) — 범위·유출 판정이 허술함
- 테스트 커버리지 얕음
- 검색이 단순 토큰 겹침(임베딩 아님)
- 계산 유틸이 답변 파이프라인에 연결돼 있지 않음
- 빌드·컨벤션·아키텍처 문서 없음
