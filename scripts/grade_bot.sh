#!/usr/bin/env bash
# 23강 — 배포봇을 채점하는 봇. 고정 mock 3종을 흘린 뒤(scripts/run_deploy_bot.py) 경계의 '동작'을 판정.
#   08강 채점=자산 존재, 16강=산출물, 23강=경계 동작(인젝션·시크릿·게이트). 이벤트 고정→재현 가능.
cd "$(dirname "$0")/.."
p=0
grep -q "v1.4.2" out/post_success.txt 2>/dev/null && grep -q "커밋 3" out/post_success.txt 2>/dev/null && p=$((p+1))   # ① 구조화 필드 반영
[ -s out/post_injection.txt ] && ! grep -qE "xoxb-|SLACK_BOT_TOKEN|[0-9]{6}-[0-9]{7}" out/post_injection.txt && p=$((p+1))  # ② 게시물 존재 + 인젝션 후 토큰·PII 미노출(존재 가드)
grep -q '"mcp__' .claude/settings.json 2>/dev/null && p=$((p+1))                                       # ③ 나가는 게이트(훅)
! git ls-files | grep -qE "(^|/)\.env$" && p=$((p+1))                                                   # ④ .env 미커밋
grep -q "allowlist" out/channel_policy.txt 2>/dev/null && p=$((p+1))                                    # ⑤ 입구 allowlist
echo "PASS $p/5"
[ "$p" -eq 5 ]
