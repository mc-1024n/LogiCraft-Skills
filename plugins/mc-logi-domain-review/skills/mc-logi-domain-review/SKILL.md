---
name: mc-logi-domain-review
description: Logicraft 도메인을 10 차원(coverage/links/schema/stale/policy/acceptance/requirement/content/diagram/test_scenario) 병렬 감사해 갭을 검출하는 read-only 스킬. 사용자가 도메인 검토를 요청하면(예 "D002 검토해줘", "DOMAIN-001 갭 찾아줘", "도메인 정합 확인") logi-domain-auditor 에이전트 10건을 병렬 실행해 갭 리포트를 우선순위(P0/P1/P2)별로 생성. ITEM 수정 안 함 — 검출만. 후속 수정은 사용자가 mc-logi-update 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.4.0"
  domain: logicraft-orchestration
  role: orchestrator-readonly
---

# mc-logi-domain-review

> ★ 이 버전(v1.4.0)의 전체 본문은 발행 직후 보완 커밋으로 갱신된다 — repo 최신 HEAD 를 볼 것.
