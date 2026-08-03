---
name: mc-logi-screen-kit
description: Logicraft 특정 프로젝트의 특정 화면(screen_spec)과 그 화면이 의존하는 디자인 ITEM 세트(design_system / ui_component / app_shell / navigation_tree / api_endpoint / constant / permission_role / implementation_guideline + 화면별 use_case / acceptance / wireframe / 디자인 렌더)를 ./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/ 화면 중심 구조로 다운로드 + 버전 추적하는 화면 특화 키트 다운로더. 사용자가 "SCREEN-011 화면 키트 만들어줘", "D002 화면 다운로드", "화면 키트 준비해줘", "logicraft 화면 로컬로 내려받아줘", "화면 키트 동기화해줘" 등을 요청할 때 실행. 결정적 다운로더(bin/download-kit.mjs, 배치 export API-152)로 서버 verbatim 스켈레톤 + 원본 JSON + 렌더 정적파일을 받고, arranger(bin/arrange-screen-kit.mjs)가 화면 중심 레이아웃 + 인덱스로 정리 — LLM 0·초 단위·content-hash 무열화(ADR-026, 옛 logi-implement-fetcher LLM 요약 폐기). ITEM 수정 안 함 — read-only 다운로드.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.2.0"
  domain: logicraft-orchestration
  triggers: 화면 키트, screen kit, 화면 다운로드, 화면 구현 준비, 화면 키트 동기화, SCREEN-NNN 키트, SCREEN-NNN 다운로드, 화면 로컬 다운, 화면 구현 준비해줘, logicraft 화면 로컬로 내려받아, screen-design 동기화, D001 화면 키트, D002 화면 다운로드
  role: orchestrator-readonly
  scope: logicraft-screen-implementation-prep
  output-format: docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/ 트리 (SCREENS.md + version-master.md + _shared/ + screens/)
  related-skills: mc-logi-screen-implement, mc-logi-implement-kit, mc-logi-update, mc-logi-domain-review
---

# mc-logi-screen-kit — Logicraft Screen Kit Downloader

> ★ 이 버전(v1.2.0)의 전체 본문은 발행 직후 보완 커밋으로 갱신된다 — 이 파일이 이 문구를 포함하면 보완 커밋 이전 상태이므로 repo 최신 HEAD 를 볼 것.
