# 모드 A — Logicraft SCREEN 기반 와이어프레임 워크플로우

Logicraft 의 SCREEN 화면정의서를 Figma 에 자동 렌더링하는 단계별 가이드.

## 목차
- [전제 조건](#전제-조건)
- [입력 수집](#1-입력-수집)
- [SCREEN 데이터 가져오기](#2-screen-데이터-가져오기)
- [캔버스 레이아웃 계획](#3-캔버스-레이아웃-계획)
- [SCREEN 별 프레임 생성](#4-screen-별-프레임-생성)
- [메타 캡션 추가](#5-메타-캡션-추가)
- [결과 검증](#6-결과-검증)
- [SCREEN.external_designs 자동 등록 (--register)](#7-screenexternal_designs-자동-등록---register)
- [에러 처리](#에러-처리)

---

## 전제 조건

다음 MCP 도구가 사용 가능해야 한다:
- `mcp__logicraft__get_item` — SCREEN data 조회
- `mcp__logicraft__update_item` — external_designs 등록 (--register on 시)
- Figma MCP 도구 (`use_figma`, `get_metadata`, `get_screenshot`)

도구 부재 시 사용자에게 명시적으로 보고하고 중단.

---

## 1. 입력 수집

사용자에게서 다음 정보를 수집:

| 항목 | 필수 | 설명 |
|------|------|------|
| `project_id` | 예 | Logicraft project UUID. 사용자 메시지에 없으면 명시적으로 요청 |
| `SCREEN-NNN` ID | 예 | 단일 또는 배열. 예: "SCREEN-001" / "SCREEN-001~005" / "SCREEN-001, 003, 007" |
| `--register` / `--no-register` | 아니요 | 기본 ON. 사용자가 "등록은 하지 마"라고 하면 OFF |
| Figma 파일 컨텍스트 | 아니요 | 새 파일 / 기존 파일에 추가. 사용자가 명시 안 하면 새 캔버스 영역 사용 |

다중 SCREEN 입력 처리:
- "SCREEN-001~005" → 5개 (001, 002, 003, 004, 005)
- "SCREEN-001, 003, 007" → 3개 (지정만)
- 도메인 단위: "DOMAIN-001 SCREEN 다 그려줘" → list_items 호출 후 해당 도메인 SCREEN 추출

---

## 2. SCREEN 데이터 가져오기

각 SCREEN 마다 호출:

```
mcp__logicraft__get_item(project_id=<uuid>, id="SCREEN-NNN")
```

응답 `item.data` 에서 다음 필드 활용:

| 필드 | 용도 |
|------|------|
| `title` | Figma 프레임 이름·헤더 캡션 |
| `route` | 헤더 우측에 작은 캡션 |
| `purpose` | 프레임 상단 요약 텍스트 |
| `device` | 너비 결정 (desktop=1440, mobile=375, tablet=768, responsive=1440) |
| `sections[]` | 섹션별 렌더링 — 핵심 |
| `realizes_use_cases[]` | 메타 캡션 "Realizes: UC-001, UC-002" |
| `consumes_apis[]` | 메타 캡션 "Consumes: API-004, API-005, ..." |
| `required_roles[]` | 메타 캡션 "Roles: ROLE-001, ..." |
| `external_designs[]` | 기존 Figma 링크 확인 (중복 등록 방지) |

데이터 누락 처리:
- `sections[]` 가 비어있으면 → "이 SCREEN 은 sections 가 정의되지 않아 와이어프레임 생성 불가" 보고하고 사용자에게 sections 작성 권장
- `components[]` 안의 옛 단순 문자열 항목도 호환 처리: `{ type: 'Custom', label: <문자열>, custom_name: <문자열> }` 로 변환

---

## 3. 캔버스 레이아웃 계획

다중 SCREEN 입력 시:
- 가로 배치 (좌→우)
- 각 SCREEN 너비 + 200px 간격 (예: desktop 1440 + 200 = 1640px 단위)
- y 좌표는 캔버스 상단 (0 또는 기존 노드 아래)

단일 SCREEN: 캔버스 빈 영역에 그냥 생성.

`get_metadata` 호출로 기존 노드 위치 파악 → 겹치지 않는 영역 선택.

---

## 4. SCREEN 별 프레임 생성

### 4-1. 루트 프레임

```javascript
const screenFrame = figma.createFrame();
screenFrame.name = `[SCREEN-NNN] ${title}`;
screenFrame.layoutMode = "VERTICAL";
screenFrame.primaryAxisSizingMode = "AUTO";
screenFrame.counterAxisSizingMode = "FIXED";
screenFrame.resize(1440, 100);  // device 에 따라 너비 조정
screenFrame.primaryAxisSizingMode = "AUTO";  // resize 후 재설정 필수
screenFrame.fills = [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }];  // 페이지 배경
screenFrame.itemSpacing = 0;  // 섹션 간격은 섹션이 자체 마진으로
```

### 4-2. 메타 헤더 (프레임 최상단)

화면 정보를 한눈에 보여주는 작은 영역:

```
┌─────────────────────────────────────────────────────────────┐
│ SCREEN-NNN · {title}                            {route}     │
│ Realizes: UC-001, UC-002 · Consumes: API-004, API-005, ...  │
└─────────────────────────────────────────────────────────────┘
```

배경 `#FFFFFF`, 본문 `#666666`, 24px 패딩, 하단 `#D1D1D1` 보더.

### 4-3. role 기반 섹션 배치

`sections[]` 를 role 별로 그룹화하고 다음 순서로 렌더:

```
1. role='header'    → 1440 width × 64~80px height, 최상단
2. role='navigation' → header 아래 또는 좌측 사이드 (Tabs 면 가로 탭바)
3. role='hero'      → main 영역 상단
4. main + side 영역 (수평 분할):
   - role='filter'   → main 좌측 또는 main 위쪽 좁은 패널 (240~280px wide)
   - role='main'     → 주 본문 (남은 너비)
   - role='side'     → main 오른쪽 패널 (300~360px wide)
5. role='footer'    → 1440 width, 최하단
6. role='modal'     → 별도 프레임으로 (메인 프레임 옆 200px 간격)
```

수평 분할이 있는 경우 중간 행을 HORIZONTAL Auto Layout 으로 묶음.

### 4-4. 섹션 내부 렌더링

각 섹션은 자체 프레임:

```javascript
const sectionFrame = createAutoFrame(parentRow, name, "VERTICAL", 16, 24, [{type:'SOLID', color:{r:1,g:1,b:1}}]);
sectionFrame.layoutSizingHorizontal = "FILL"; // 또는 FIXED with 너비
```

섹션 헤더 (이름·설명):
- name → SemiBold 18px `#1A1A1A`
- description → Regular 14px `#666666`

그 아래 components[] 를 순회하며 렌더 (다음 섹션 참조).

### 4-5. 컴포넌트 렌더링

`section.components[]` 의 각 항목은 ComponentSpec 객체. type 별 렌더링은 `references/logicraft_mapping.md` 참조.

`section.layout` 에 따라 컴포넌트 컨테이너 스타일 조정:

| layout | 컨테이너 |
|--------|----------|
| `form` | VERTICAL stack, itemSpacing 16, 라벨+입력 페어 |
| `list` | VERTICAL stack, itemSpacing 0, Table 컴포넌트 그대로 |
| `detail` | VERTICAL stack, itemSpacing 24, Heading + KeyValue + 본문 |
| `dashboard` | HORIZONTAL Grid (2~3열), itemSpacing 24 |
| `grid` | HORIZONTAL Grid (3~4열), itemSpacing 16 |
| `tabs` | VERTICAL — 상단 Tabs + 하위 콘텐츠 |
| `stack` (default) | VERTICAL, itemSpacing 16 |

---

## 5. 메타 캡션 추가

각 컴포넌트가 `triggers_api` 를 가지면 컴포넌트 우측에 작은 회색 캡션:

```
[Button: 조치 실행]  → API-005
```

폰트: Poppins Regular 11px, color `#999999`.

API 캡션은 컴포넌트와 같은 줄에 8px 간격으로 붙여 HORIZONTAL Auto Layout.

---

## 6. 결과 검증

생성 완료 후:

1. `get_screenshot` 으로 결과 캡처 (screenFrame 의 nodeId 지정)
2. 사용자에게 다음 정보 보고:
   - Figma 파일 URL + node deep-link
   - 캡처 이미지 (가능하면 인라인 표시)
   - 생성된 SCREEN 개수
   - Mode A 일 경우 등록한 external_designs 항목

검증 체크리스트:
- [ ] 그레이스케일만 사용 (RGB 채널 동일값)
- [ ] 폰트가 Pretendard/Poppins/Noto Sans KR
- [ ] 절대 좌표 없음 (모든 프레임 Auto Layout)
- [ ] sections 모두 렌더링됨 (누락 없음)
- [ ] triggers_api 캡션 모두 표기됨

---

## 7. SCREEN.external_designs 자동 등록 (--register)

기본 ON. `--no-register` 또는 사용자가 "등록은 하지 마"라고 명시할 때만 스킵.

### 등록 데이터

```javascript
const newEntry = {
  source: "figma",
  url: `<Figma file URL>?node-id=<encoded_node_id>`,
  label: `Auto-generated wireframe (mc_wireframe_logicraft)`,
  node_id: "<Figma node ID e.g. '12:34'>",
  preview_image_url: "<screenshot URL if available>",
  synced_at: new Date().toISOString()
};
```

### update_item 호출

```
1. mcp__logicraft__get_item(project_id, "SCREEN-NNN") 로 현재 data + base_version 가져오기
2. data.external_designs 배열에 newEntry 추가 (기존 항목 보존)
3. mcp__logicraft__update_item(
     project_id,
     id="SCREEN-NNN",
     base_version=<현재 version>,
     change_summary=`v<N>: external_designs 자동 등록 (mc_wireframe_logicraft, Figma node <id>)`,
     data=<수정된 전체 data>
   )
```

base_version 충돌(다른 작업이 동시 수정)이면 → get_item 재호출 후 재시도 1회. 두 번째도 실패 시 사용자에게 보고.

### 중복 방지

기존 external_designs 에 동일 `node_id` 가 있으면 새로 추가하지 않고 `synced_at` 만 갱신.

---

## 에러 처리

### Figma MCP 부재
"Figma MCP 도구를 사용할 수 없습니다. Figma 데스크톱 앱에서 Plugin → Claude MCP 연결을 먼저 확인해 주세요." 보고 후 중단.

### SCREEN 데이터 누락
- `sections=[]` → "SCREEN-NNN 은 sections 가 비어있어 그릴 콘텐츠가 없습니다. 먼저 sections 정의가 필요합니다."
- `components` 안에 옛 문자열만 있음 → 자동 변환 (Custom 으로) + 사용자에게 "옛 형식 컴포넌트 N개를 Custom 박스로 처리했습니다. 마이그레이션을 권장합니다." 안내

### use_figma 노드 수 초과
한 호출에 너무 많은 노드 → 섹션 단위로 분할 호출 (`references/figma_helpers.md` 참조).

### update_item base_version 충돌
1회 재시도. 두 번째도 실패 시 사용자에게 "external_designs 등록에 실패했습니다 (동시 수정 충돌). Figma 결과는 정상 생성되었습니다. 수동 등록이 필요합니다." 보고.

---

## 사용 예시

### 단일 SCREEN
```
사용자: SCREEN-001 와이어프레임 그려줘 (project_id 95f00d2e-30e8-4426-bc37-9bd85aa969e9)
스킬:
  1. get_item(SCREEN-001) → data 파싱
  2. Figma 캔버스에 1440x?? 프레임 생성
  3. 메타 헤더 + sections 렌더
  4. get_screenshot 캡처
  5. update_item 으로 external_designs 등록
  6. URL + 이미지 + 등록 결과 보고
```

### 도메인 단위 다중 SCREEN
```
사용자: DOMAIN-001 SCREEN 들 와이어프레임 그려줘
스킬:
  1. list_items(type=screen_spec, domain_id=DOMAIN-001) → SCREEN-001/002/003/004/005
  2. 각각 get_item → 5개 data 수집
  3. Figma 캔버스에 1640px 간격으로 가로 5개 배치
  4. 각 프레임 렌더 + 캡처
  5. 5개 모두 external_designs 등록
  6. 통합 보고 (URL 5개 또는 페이지 URL 1개)
```
