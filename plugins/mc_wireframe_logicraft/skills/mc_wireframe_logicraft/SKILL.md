---
name: mc_wireframe_logicraft
description: "Logicraft 의 SCREEN 화면정의서를 Figma 에 흑백 로우피델리티 와이어프레임으로 자동 렌더링하는 스킬. SCREEN-NNN ID 를 받으면 sections/components/role/layout/triggers_api 메타를 그대로 시각화하고, 결과 Figma 노드를 SCREEN.external_designs[] 에 자동 등록. PRD + IA 차트 텍스트로도 일반 와이어프레임 생성 가능. 사용자가 'SCREEN 와이어프레임', 'Logicraft 화면 그려줘', '화면정의서 시각화', '와이어프레임 만들어줘', 'figma 와이어프레임' 을 말하거나 SCREEN-NNN 같은 Logicraft ID 를 언급하며 시각화·다이어그램·Figma 출력을 요청할 때 반드시 이 스킬을 사용. 기획서·화면 설계·UI 와이어프레임·로우피델리티 디자인이 필요한 모든 경우에 트리거. 'wireframe 그려줘' 같은 짧은 요청에서도 적극 트리거."
user_invocable: true
---

# mc_wireframe_logicraft 스킬

Logicraft 의 SCREEN 화면정의서를 Figma 에 흑백 로우피델리티 와이어프레임으로 자동 렌더링한다. 보조 모드로 PRD + IA 차트 기반 일반 와이어프레임도 지원한다.

## 🚀 스킬 시작 시 안내 (필수)

스킬 실행 즉시 사용자에게 모드 선택을 안내한다:

```
📐 Wireframe Logicraft 스킬을 시작합니다.

본 스킬은 두 가지 모드를 지원합니다:

  [모드 A] Logicraft SCREEN 기반 (주 모드)
    - 입력: project_id + SCREEN-NNN ID (또는 ID 배열)
    - 자동: SCREEN data 의 sections/components/role/layout 을 Figma 에 그대로 시각화
    - 결과: Figma 노드 생성 + SCREEN.external_designs[] 자동 등록 (--register on, 기본)

  [모드 B] PRD + IA 차트 기반 (일반)
    - 입력: 기획서(PRD) + IA(Information Architecture) 차트
    - 자동: 헤더/히어로/카드/CTA/푸터 등 일반 패턴 적용
    - 결과: Figma 노드 생성

✅ 결과물은 흑백(그레이스케일) 로우피델리티 와이어프레임입니다.
✅ 완성형 디자인이 아닌 구조 중심 와이어프레임입니다.

어느 모드로 진행할까요? (예: "SCREEN-001 그려줘" 또는 "PRD 첨부합니다")
```

## 모드 분기 로직

사용자 메시지에서 다음 신호를 감지해 모드를 결정한다:

| 신호 | 모드 |
|------|------|
| SCREEN-NNN ID 언급 | **모드 A** |
| project_id (UUID) 언급 | **모드 A** |
| Logicraft / 화면정의서 / SCREEN 언급 | **모드 A** |
| PRD / 기획서 / IA 차트 언급 | **모드 B** |
| 모호한 경우 | 사용자에게 명시적으로 묻기 |

신호가 명확하면 사용자에게 재확인하지 말고 바로 진행한다.

---

## 모드 A — Logicraft SCREEN 기반 (주 모드)

### 한 눈에 보는 흐름

1. 입력 수집 → `project_id` (없으면 사용자에게 요청) + `SCREEN-NNN` ID(들)
2. 각 SCREEN 에 대해 `mcp__logicraft__get_item` 호출 → data 파싱
3. Figma 캔버스 레이아웃 계획 (다중 SCREEN 시 1440px + 200px 간격으로 가로 배치)
4. 각 SCREEN 별로 Figma 프레임 생성 → role 기반 자동 배치 → components 렌더링
5. 메타 캡션 추가 (UC realizes / consumes APIs / route)
6. `get_screenshot` 으로 결과 검증
7. **`--register` ON (기본)**: Figma URL/node_id 를 `SCREEN.external_designs[]` 에 자동 추가

자세한 단계는 `references/logicraft_mode.md` 참조.

### 핵심 매핑 한 줄 요약

- **section.role** → 프레임 내 위치 (header=상단, filter=좌측 좁게, main=중앙, side=우측 패널, modal=별도, footer=하단)
- **section.layout** → 내부 배치 (form=세로 스택, list=Table, dashboard=2~3열 Grid, tabs=Tabs, ...)
- **components[].type** → Figma 노드 (Button/Input/Table/Tabs/Dialog/Stat/Alert/...). `Custom` 은 회색 박스 + custom_name 라벨
- **components[].triggers_api** → 컴포넌트 우측에 회색 캡션 "→ API-NNN"

전체 매핑표는 `references/logicraft_mapping.md` 참조.

### --register 플래그 (기본 ON)

기본적으로 Figma 출력 후 `mcp__logicraft__update_item` 을 호출해 SCREEN.data.external_designs[] 에 다음 항목을 추가한다:

```json
{
  "source": "figma",
  "url": "<Figma file URL with node ID>",
  "label": "Auto-generated wireframe (wireframe_logicraft)",
  "node_id": "<Figma node ID>",
  "preview_image_url": "<screenshot URL if available>",
  "synced_at": "<ISO timestamp>"
}
```

사용자가 `--no-register` 또는 "등록은 하지 마" 등으로 명시하면 스킵.

---

## 모드 B — PRD + IA 차트 기반 (일반)

기획서(PRD, 기능 명세, 화면 설명)와 IA 차트(사이트맵·화면 흐름·계층 구조)를 받아 일반 패턴 와이어프레임을 그린다.

자료가 둘 다 제공되지 않으면 진행 불가 → 재요청.

자세한 단계는 `references/prd_mode.md` 참조.

---

## 공통 — 흑백 와이어프레임 컬러·폰트·레이아웃 규칙 (필수)

**모든 모드에 무조건 적용**:

- **컬러**: 그레이스케일만. Primary·브랜드 컬러 일체 금지. 강조는 굵기·크기로만.
- **폰트**: Pretendard(한국어) / Poppins(영어). 둘 다 불가 시 Noto Sans KR fallback.
- **행간**: 24px 이상 텍스트 = 140%, 20px 이하 = 180%.
- **레이아웃**: Auto Layout + Hug Contents. 절대 좌표(x, y) 사용 금지.
- **이미지**: 회색 박스 + "IMG" 라벨 또는 대각선.
- **AI 느낌 배제**: 이모지·그라디언트·글로우 금지. 챗봇 말풍선 지양.
- **Desktop 기본**: 1440px width, 좌우 100px 패딩, 섹션 간 80~100px 간격.

전체 색상표·폰트 스케일·오토레이아웃 코드 패턴은 `references/grayscale_rules.md` 참조.

---

## Figma MCP 사용

Figma MCP 도구는 다음 패턴으로 사용:

- `get_metadata` / `get_screenshot` — 작업 전후 상태 파악·검증
- `use_figma` — 실제 노드 생성 (JavaScript Plugin API 코드 실행)

복잡한 페이지는 `use_figma` 를 여러 번 분할 호출 (한 번 호출당 노드 수 제한 있음). 분할 시 `figma.currentPage.findOne(n => n.name === "프레임명")` 으로 부모 프레임 재참조.

자주 쓰는 헬퍼 함수(`createText`, `createAutoFrame`, `createImagePlaceholder` 등)와 use_figma 호출 템플릿은 `references/figma_helpers.md` 참조.

---

## 결과 검증·공유

1. `get_screenshot` 으로 생성된 프레임 확인
2. 사용자에게 Figma 파일 URL + 캡처 이미지 공유
3. 모드 A: SCREEN.external_designs[] 등록 결과도 보고

---

## 한계 (사용자에게 미리 안내)

- 흑백 로우피델리티만. 컬러 시안 필요 시 다른 스킬 사용.
- 학습된 패턴 외 특수 화면(어드민·복잡 폼)은 단순화될 수 있음.
- Figma API 노드 수 제한으로 매우 큰 화면은 섹션 분할 필요.
- `Custom` 컴포넌트는 이름과 박스로만 표현 (실제 위젯 동작은 표현 불가).

---

## 참조 파일 (progressive disclosure)

| 파일 | 언제 읽는가 |
|------|-------------|
| `references/grayscale_rules.md` | 모든 모드 — 첫 use_figma 호출 직전 색상·폰트·오토레이아웃 규칙 확인 |
| `references/logicraft_mode.md` | 모드 A — SCREEN fetch → 그리기 → 등록 단계별 상세 |
| `references/logicraft_mapping.md` | 모드 A — section/component 마다 Figma 노드 변환 결정 시 |
| `references/prd_mode.md` | 모드 B — PRD/IA 차트 받은 후 |
| `references/figma_helpers.md` | use_figma JavaScript 코드 작성 시 — 헬퍼 함수·호출 템플릿 |
