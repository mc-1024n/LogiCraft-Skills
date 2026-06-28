---
name: mc-logi-screen-design
description: mc-logi-screen-kit 이 만든 로컬 화면 키트(./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/)를 입력으로, 와이어프레임 골격을 보존한 고충실도 화면을 Claude 가 직접 작성해 screens/SCREEN-NNN/design/ 에 떨구는 화면 디자인 오케스트레이터 스킬. 사용자가 "SCREEN-027 디자인해줘", "화면 디자인해줘", "고충실도 목업 만들어줘", "D001 화면 디자인", "/mc-logi-screen-design" 등 화면 비주얼 디자인을 요청할 때 실행. 키트가 없으면 mc-logi-screen-kit 을 먼저 호출하고, 키트가 stale 이면 SYNC 재실행을 먼저 한다. 결과는 mc-logi-screen-implement 가 와이어프레임보다 우선 소비한다. 단순 흑백→컬러 치환이 아니라 와이어프레임에 없는 디자인 결정(상태별·데이터밀도·시각위계·컴포넌트 디테일)을 DS 토큰 안에서 입힌다(규격 내 AI slop 회피). 외부 디자인 도구 없이 Claude 가 직접 작성하고, 확정 디자인은 screen_design(SD) ITEM 에 upload_design_render(css 분리)로 역등록한다(와이어프레임과 비교 뷰 짝지음, 렌더 URL=프리뷰).
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.1"
  domain: logicraft-orchestration
  triggers: 화면 디자인, 화면 디자인해줘, screen design, 고충실도 목업, 고충실도 디자인, SCREEN-NNN 디자인, D001 화면 디자인, 화면 비주얼 디자인, 디자인 목업 만들어줘
  role: orchestrator
  scope: logicraft-screen-visual-design
  output-format: docs/screen-design/{slug}-{DOMAIN-ID}/screens/SCREEN-NNN/design/ (design-{surface}.html + design.css + design-{surface}.png + design-notes.md) + SCREENS.md design 인덱스 갱신 + logicraft screen_design(SD) upload_design_render(render_id=와이어프레임 동일, css 분리) + (선택) 새 컴포넌트 ui_component 보강 권고·동의 시 register_ui_components
  related-skills: mc-logi-screen-kit, mc-logi-screen-implement, mc-logi-update
---

[본문 생략 표시 금지 — 아래 실제 본문 계속]
