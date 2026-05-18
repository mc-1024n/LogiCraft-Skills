# mc_wireframe_logicraft — SCREEN → Figma 와이어프레임

Logicraft 의 **SCREEN 화면정의서를 Figma 흑백 로우피델리티 와이어프레임으로 자동 렌더링**하는 스킬입니다. 결과 Figma 노드를 `SCREEN.external_designs[]`에 자동 등록해 설계와 시안을 연결합니다.

## 두 가지 모드

| 모드 | 입력 | 동작 |
|---|---|---|
| **A. Logicraft SCREEN (주 모드)** | `project_id` + `SCREEN-NNN`(들) | SCREEN data 의 sections/components/role/layout 을 그대로 Figma 시각화 + `external_designs[]` 자동 등록 |
| **B. PRD + IA 차트 (일반)** | 기획서(PRD) + IA 차트 | 헤더/히어로/카드/CTA/푸터 등 일반 패턴 적용 |

SCREEN-NNN·project_id·"화면정의서" 언급 시 자동으로 모드 A.

## 핵심 매핑 (모드 A)

- `section.role` → 프레임 내 위치 (header=상단 / filter=좌측 / main=중앙 / side=우측 / modal=별도 / footer=하단)
- `section.layout` → 내부 배치 (form=세로 스택 / list=Table / dashboard=Grid / tabs=Tabs …)
- `components[].type` → Figma 노드 (Button/Input/Table/Tabs/Dialog/Stat/Alert …, `Custom`=회색 박스+라벨)
- `components[].triggers_api` → 컴포넌트 옆 "→ API-NNN" 캡션

## 효과 / 받는 것

- 화면정의서를 **사람이 그릴 필요 없이** 구조 충실한 와이어프레임으로 즉시 시각화
- **설계↔시안 추적성** — Figma URL/node_id 가 SCREEN.external_designs[] 에 자동 기록(`--register` 기본 ON, `--no-register` 로 끄기)
- 다중 SCREEN 가로 배치 + 메타 캡션(UC realizes / consumes APIs / route) + 스크린샷 검증

## 와이어프레임 규칙 (전 모드 적용)

- **그레이스케일만** — 브랜드/Primary 컬러 금지, 강조는 굵기·크기로
- 폰트 Pretendard/Poppins(→ Noto Sans KR fallback), Auto Layout + Hug(절대좌표 금지)
- 이모지·그라디언트·글로우 배제, Desktop 1440px 기본

## 사용 예

```
"SCREEN-001 그려줘"            → 모드 A, Figma 렌더 + external_designs 등록
"SCREEN-001~005 와이어프레임"  → 다중 가로 배치
"PRD 첨부합니다 + IA 차트"     → 모드 B 일반 패턴
```

## 한계

- 흑백 로우피델리티만 (컬러 시안은 다른 스킬)
- 학습 패턴 외 특수 화면(어드민·복잡 폼)은 단순화될 수 있음
- Figma API 노드 수 제한 → 매우 큰 화면은 섹션 분할
- `Custom` 컴포넌트는 이름+박스로만 표현(실 동작 불가)

> 미검증 마켓플레이스 항목 — 설치 전 SKILL.md 원문도 함께 확인하세요.
