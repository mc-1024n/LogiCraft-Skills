---
name: mc-logi-screen-implement
description: mc-logi-screen-kit 이 만든 로컬 화면 키트(./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/)를 단일 진실원으로 삼아, 프론트엔드 화면 구현을 공유자산 셋업→스펙→플랜→화면별 구현→반영·추적까지 phase 게이트로 완주하는 오케스트레이터 스킬. 사용자가 "SCREEN-011 구현해줘", "화면 구현해줘", "키트대로 화면 구현", "D002 화면 구현 시작", "/mc-logi-screen-implement" 등 화면 프론트엔드 구현을 요청할 때 실행. 키트가 없으면 mc-logi-screen-kit 을 먼저 호출하고, 키트가 stale 이면 SYNC 재실행을 먼저 한다. 도메인 규칙·디자인 토큰·컴포넌트 카탈로그·빌드 순서는 이 스킬에 하드코딩하지 않고 전부 키트에서 읽는다. phase 인자로 중단 지점부터 재개 가능 ("공유자산부터", "구현만", "추적만").
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.1.0"
  domain: logicraft-orchestration
  role: orchestrator
---

# mc-logi-screen-implement

> ★ 이 버전(v1.1.0)의 전체 본문은 발행 직후 보완 커밋으로 갱신된다 — repo 최신 HEAD 를 볼 것.
