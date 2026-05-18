# mc-logi-figma-wireframe

Logicraft 의 **SCREEN 화면정의서**를 Figma 에 **흑백 로우피델리티 와이어프레임**으로 자동 렌더링하는 스킬. 코드 한 줄 없이 설계 ITEM 을 시각화한다.

## 무엇을 하나

- **모드 A — Logicraft SCREEN 기반 (주 모드)**: `project_id` + `SCREEN-NNN` 만 주면 SCREEN.data 의 `sections / components / role / layout / triggers_api` 메타를 그대로 Figma 프레임으로 렌더. 다중 SCREEN·도메인 단위(`DOMAIN-001 SCREEN 다 그려줘`) 일괄 배치 지원. 결과 Figma node 를 `SCREEN.external_designs[]` 에 자동 역등록(`--register` 기본 ON).
- **모드 B — PRD + IA 차트 기반 (일반)**: 기획서 + 정보구조 차트만으로 헤더/히어로/카드/CTA/푸터 등 일반 패턴 와이어프레임 생성.

## 어떤 효과

- 설계(Logicraft)와 시각(Figma)을 한 번에 동기화 — 이해관계자가 클릭 가능한 와이어프레임으로 바로 리뷰.
- `section.role` → 프레임 위치, `section.layout` → 내부 배치, `components[].type`(43종 enum) → Figma 노드, `triggers_api` → "→ API-NNN" 캡션까지 1:1 매핑.
- 결과물은 **그레이스케일 구조 중심** — 컬러·브랜드·AI 느낌(이모지/그라디언트/글로우) 배제. Pretendard/Poppins(폴백 Noto Sans KR), Auto Layout 강제(절대좌표 금지).

## 사용 예

```
SCREEN-001 와이어프레임 그려줘 (project_id <uuid>)
DOMAIN-001 SCREEN 들 와이어프레임 그려줘
PRD 첨부합니다 + IA 차트 (모드 B)
```

## 요구 사항

- **Logicraft MCP**: `get_item` / `update_item`(external_designs 등록 시)
- **Figma MCP**: `use_figma` / `get_metadata` / `get_screenshot` (Figma 데스크톱 앱 플러그인 연결 필요)

## 구성

- `SKILL.md` — 진입·모드 분기·공통 규칙
- `references/logicraft_mode.md` — 모드 A 단계별(수집→렌더→등록)
- `references/logicraft_mapping.md` — role/layout/component 43종 매핑표
- `references/prd_mode.md` — 모드 B 워크플로
- `references/grayscale_rules.md` — 컬러·폰트·오토레이아웃 규칙(필수)
- `references/figma_helpers.md` — use_figma JS 헬퍼·분할 호출 전략

## 한계

흑백 로우피델리티 전용(컬러 시안 불가). 특수 어드민·복잡 폼은 단순화. Figma API 노드 수 제한으로 큰 화면은 섹션 분할. `Custom` 컴포넌트는 박스+라벨로만 표현.