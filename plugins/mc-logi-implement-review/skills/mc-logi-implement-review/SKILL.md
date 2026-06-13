---
name: mc-logi-implement-review
description: 현재 구현된 코드가 로컬 구현 키트(docs/design/{slug}-{DOMAIN-ID}/)와 정합하는지 6차원(api/schema/policy/coverage/acceptance/role) 병렬 점검하는 read-only 스킬. 사용자가 "구현이 키트랑 맞는지 확인", "코드 정합 점검", "D004 구현 검토", "키트 대비 코드 표류 찾아줘", "구현 정합성 감사", "/mc-logi-implement-review" 를 요청하면 logi-implement-auditor 에이전트 6건을 병렬 실행해 키트(설계)·코드(실제)·IMPREC(주장) 3방향 삼각 대조로 불일치를 검출. 5종 분류(code_drift/design_stale/coverage_gap/extra_code/imprec_mismatch) 후 코드수정/설계갱신 2버킷으로 핸드오프. ITEM·코드 수정 안 함 — 검출만. 후속 수정은 mc-logi-implement(코드)/mc-logi-update(설계) 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.0.1"
  domain: logicraft-orchestration
  triggers: 구현 정합, 코드 정합 점검, 키트 대비 코드, 구현 검토, 코드 표류, 구현 정합성 감사, conformance review, 키트 정합, D004 구현 검토, implement review
  role: orchestrator-readonly
  scope: code-kit-conformance
  output-format: 정합 리포트 (Markdown 표 + YAML 원본)
  related-skills: mc-logi-implement, mc-logi-implement-kit, mc-logi-update, mc-logi-domain-review
---

SKILL_BODY_PLACEHOLDER
