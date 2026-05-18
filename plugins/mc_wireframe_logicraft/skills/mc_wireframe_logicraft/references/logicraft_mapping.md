# Logicraft SCREEN → Figma 컴포넌트 매핑표

`section.role`, `section.layout`, `component.type` 별 Figma 노드 변환 규칙. 모드 A 의뜟 핵심 참조 문서.

## 목차
- [section.role 매핑](#sectionrole-매핑)
- [section.layout 매핑](#sectionlayout-매핑)
- [components[].type 매핑 (43종 enum)](#components-type-매핑-43종-enum)
- [공통 메타 필드 처리](#공통-메타-필드-처리)
- [예시 — 컴포넌트별 시각화](#예시--컴포넌트별-시각화)

---

## section.role 매핑

각 섹션은 화면 내 위치·너비를 결정한다.

| role | 위치 | 너비 (1440 desktop) | 배경 |
|------|------|---------------------|------|
| `header` | 최상단 | FILL (1440) | `#FFFFFF` + 하단 1px `#D1D1D1` |
| `navigation` | header 아래 | FILL (1440) | `#FFFFFF` + 하단 1px `#D1D1D1` |
| `hero` | main 영역 최상단 | FILL (main 영역) | `#F5F5F5` 또는 `#FFFFFF` |
| `filter` | main 좌측 또는 main 위쪽 | 240~280 (좌측 시) / FILL (위쪽 시) | `#FFFFFF` + 테두리 |
| `main` | 중앙 본문 | 남은 너비 (예: 720~1240) | `#FFFFFF` |
| `side` | main 우측 | 300~360 | `#FFFFFF` + 좌측 1px `#D1D1D1` |
| `modal` | 별도 프레임 (메인 옆 200px 간격) | 480 또는 640 | `#FFFFFF` + shadow |
| `footer` | 최하단 | FILL (1440) | `#1A1A1A` (다크) 또는 `#F5F5F5` |

기본값: 명시 안 된 섹션은 `main` 으로 처리.

### 역할별 배치 알고리즘

```
1. role='header' 인 섹션 → 프레임 최상단에 추가
2. role='navigation' → header 바로 아래
3. role='hero' → 다음 단계의 main 영역 최상단
4. middle row 구성:
   - role='filter' (좌측 or 위쪽) + role='main' + role='side'
   - 셋이 다 있으면 HORIZONTAL: filter(280) + main(FILL) + side(360)
   - filter 없으면 main(FILL) + side
   - side 없으면 filter(280) + main(FILL)
   - filter·side 둘 다 없으면 main 만
5. role='footer' → 최하단
6. role='modal' → 메인 프레임 외부, 우측 200px 간격에 별도 프레임
```

---

## section.layout 매핑

섹션 내부 components[] 의 배치 방식.

| layout | Auto Layout 설정 | 사용 패턴 |
|--------|------------------|----------|
| `form` | VERTICAL, itemSpacing=16 | 라벨+입력 페어 반복, 마지막에 버튼 |
| `list` | VERTICAL, itemSpacing=0 | Table 컴포넌트 또는 List 항목 반복 |
| `detail` | VERTICAL, itemSpacing=24 | Heading + KeyValue + 본문 + 부가 |
| `dashboard` | HORIZONTAL Grid, itemSpacing=24 (또는 wrap) | Stat 카드 2~4개 가로 배치, Chart 큰 영역 |
| `grid` | HORIZONTAL Grid (3~4열), itemSpacing=16 | Card 반복 |
| `tabs` | VERTICAL — Tabs 상단 + 콘텐츠 하단 | 첫 컴포넌트가 Tabs, 나머지가 본문 |
| `stack` (default) | VERTICAL, itemSpacing=16 | 일반 적층 |

기본값: 명시 안 된 섹션은 `stack` 으로 처리.

---

## components[].type 매핑 (43종 enum)

각 type 별 Figma 노드 표현. type 외 메타(`label`, `placeholder`, `variant`, `state`, `options`, `columns`, `triggers_api`, `binds_to`, `note`)도 함께 활용.

### Display

| type | 시각 표현 |
|------|----------|
| `Text` | 일반 텍스트, Regular 14~16px `#333333` |
| `Heading` | Bold 20~32px `#1A1A1A` (label 길이로 size 조정) |
| `Image` | 회색 박스 (`#CCCCCC`) + "IMG" 라벨, 비율 16:9 또는 1:1 |
| `Avatar` | 원형 (`#CCCCCC`), 32x32 또는 40x40, 가운데 이니셜 텍스트 |
| `Badge` | 라운드 필 (border-radius 12), `#E5E5E5` 배경 + Regular 12px `#333333`. variant=primary 면 `#1A1A1A` 배경 + `#FFFFFF` 텍스트 |
| `Icon` | 정사각형 (`#999999`), 24x24 |
| `Divider` | 1px line, `#D1D1D1`, FILL 가로 |

### Inputs

| type | 시각 표현 |
|------|----------|
| `Input` | 라벨(label) + 박스(테두리 1px `#999999`, 배경 `#FFFFFF`, 높이 40, 좌측 패딩 12). placeholder 가 있으면 박스 안에 `#999999` 텍스트 |
| `Textarea` | Input 과 같지만 높이 96 + 우측 하단 리사이즈 핸들 표시 |
| `Select` | Input + 우측에 ▼ 아이콘 회색. options[] 가 있으면 박스 아래 펼침 회색 박스에 첫 옵션 표시 |
| `RadioGroup` | options[] 마다 ○ + 라벨, VERTICAL itemSpacing=8. 첫 옵션은 ● (선택 표시) |
| `Checkbox` | □ + 라벨, 28px × label 너비 |
| `Switch` | label + 우측에 36x20 토글 (회색 트랙 + 흰 노브, 기본 OFF) |
| `DatePicker` | Input + 우측 📅 대신 회색 사각형 아이콘 |
| `FileUpload` | 점선 테두리 박스 (`#D1D1D1`, dashed), 중앙에 "파일 끌어다 놓기 또는 클릭" 텍스트, 높이 96 |

### Actions

| type | 시각 표현 |
|------|----------|
| `Button` | 높이 40, 좌우 패딩 16. variant 에 따라: primary=`#1A1A1A` 배경 + `#FFFFFF` 텍스트 / secondary=`#FFFFFF` + `#999999` 테두리 / destructive=`#FFFFFF` + `#1A1A1A` 두꺼운 테두리 + `#1A1A1A` 텍스트 / outline=secondary 동일 / ghost=배경 없음 + `#666666` 텍스트. state=disabled 면 50% opacity |
| `Link` | underline + `#333333` |
| `IconButton` | 32x32 정사각형 + 회색 아이콘 |
| `Menu` | 회색 박스에 옵션 리스트 (●, label) |

### Containers

| type | 시각 표현 |
|------|----------|
| `Card` | 박스, 1px `#D1D1D1` 테두리, 16~24 패딩, `#FFFFFF` 배경, 8px border-radius |
| `Tabs` | options[] 가로 배치. 활성 탭은 하단 2px `#1A1A1A` 보더, 비활성은 `#666666` 텍스트 |
| `Accordion` | 항목 헤더 + ▶ / ▼ 아이콘. 첫 항목은 펼친 상태로 |
| `Stack` | VERTICAL Auto Layout 컨테이너 (자체 내부 children 렌더) |
| `Grid` | HORIZONTAL Auto Layout, 균등 분배 (자체 내부 children 렌더) |

### Data Display

| type | 시각 표현 |
|------|----------|
| `Table` | columns[] 가 헤더 행 (Bold 14px `#1A1A1A`, `#F5F5F5` 배경, 12 패딩). 더미 데이터 행 3개 (`#FFFFFF`, 12 패딩, 셀별 텍스트는 "—" 또는 짧은 더미) |
| `List` | 각 항목 박스 (1px 하단 `#D1D1D1`), 12 패딩. 5개 정도 더미 |
| `KeyValue` | label : value 페어 반복, label=`#666666` 12px / value=`#1A1A1A` 14px, 8px 간격 |
| `Chart` | 회색 박스 (`#F5F5F5`), 가운데 "CHART" 라벨 + note 가 있으면 (line/bar/pie) 추가, 비율 16:9 |
| `Stat` | 큰 숫자 Bold 32px `#1A1A1A` (예: "1,234") + 라벨 Regular 12px `#666666` |
| `Timeline` | 좌측 1px 세로선 + 점들 (●), 각 점 우측에 시각·내용 |
| `Tree` | 들여쓰기 + ▶ 아이콘, 3~4 노드 더미 |

### Feedback

| type | 시각 표현 |
|------|----------|
| `Alert` | 박스, 좌측 4px 보더, `#F5F5F5` 배경. variant: default=회색 / destructive=두꺼운 보더 (`#1A1A1A`) / primary=`#1A1A1A` 보더 |
| `Toast` | 다크 박스 (`#1A1A1A`) + `#FFFFFF` 텍스트, 우측 하단 위치, 작은 닫기 X |
| `Dialog` | modal 섹션의 본체. 480~640 너비, `#FFFFFF` 배경, 24 패딩, 8px border-radius, 그림자 효과 (회색 사각형 위에 약간 오프셋으로) |
| `Drawer` | 사이드 슬라이딩 패널 — modal 처럼 별도 프레임. 320~400 너비, 화면 전체 높이 |
| `Progress` | 1px 트랙 (`#E5E5E5`) + 진행 막대 (`#1A1A1A`), 60% 정도로 더미 |
| `Skeleton` | 회색 박스 (`#E5E5E5`), 다양한 크기 라인 모사 |
| `Tooltip` | 작은 다크 박스 + 흰 텍스트 + 화살표 (1cm 정도 길이의 작은 도형) |

### Navigation

| type | 시각 표현 |
|------|----------|
| `Breadcrumb` | "홈 > 카테고리 > 현재" 형식, `#666666` 14px, > 구분자 |
| `Pagination` | "< 1 2 3 ... N >" 가로 배치, 활성 페이지는 다크 박스 |
| `Stepper` | 단계 ●—○—○—○ 가로 배치, 라벨 아래 (활성 ●는 채움, 비활성 ○는 outline) |

### Custom

| type | 시각 표현 |
|------|----------|
| `Custom` | 회색 박스 (`#F5F5F5`), 1px dashed 테두리 (`#999999`). 가운데 다음 텍스트 표시: 첫 줄 = label (Bold 14px `#333333`), 둘째 줄 = `[Custom: ${custom_name}]` (Regular 11px `#999999`), note 있으면 셋째 줄 = note (Regular 11px `#666666`). 박스 비율은 가용 너비 × 80~120px 높이 |

---

## 공통 메타 필드 처리

### `triggers_api`
컴포넌트 우측에 8px 간격으로 작은 회색 캡션:

```
[Button: 조치 실행]  → API-005
```

캡션 스타일: Poppins Regular 11px, color `#999999`. 전체를 HORIZONTAL Auto Layout 으로 묶어 한 줄 유지.

길이 제약:
- 라벨이 너무 길면 (>30자) 캡션을 컴포넌트 아래 줄로 이동
- 모바일 레이아웃 (375 width) 일 때는 항상 아래 줄

### `binds_to`
`note` 가 없으면 컴포넌트 아래에 작은 캡션 "← {binds_to}" (Regular 10px `#999999`) 추가. note 가 있으면 binds_to 는 생략 (note 우선).

### `note`
컴포넌트 아래 행에 캡션 (Regular 11px `#666666`). 줄바꿈 허용.

### `state`
- `default`: 표준
- `disabled`: 50% opacity
- `loading`: 컴포넌트 위에 회색 반투명 오버레이 + 가운데 "···" 텍스트
- `error`: 1px `#1A1A1A` 두꺼운 테두리 + 아래 작은 "오류 안내" 캡션 더미
- `readonly`: `#F5F5F5` 배경
- `hidden`: 점선 outline 만 표시 (실제 렌더는 minimal — 박스 + label "(hidden)")

### `variant`
[Actions](#actions) 의 Button 항목 참조. Alert/Badge 도 variant 에 따라 강조도 조정.

---

## 예시 — 컴포넌트별 시각화

### Input (라벨 + 입력)
```
┌────────────────────────────────────┐
│ 사용자 ID                          │  ← label (Medium 14px)
│ ┌──────────────────────────────┐   │
│ │ 아이디를 입력하세요           │   │  ← box + placeholder
│ └──────────────────────────────┘   │
└────────────────────────────────────┘
```

### Select with options
```
┌────────────────────────────────────┐
│ 카테고리                           │
│ ┌──────────────────────────┐ ▼    │
│ │ account                  │      │  ← 첫 옵션 표시
│ └──────────────────────────┘      │
└────────────────────────────────────┘
```

### RadioGroup
```
조치 유형
● restart
○ config_change
○ emergency_stop
```

### Table with columns
```
┌──────────┬──────────┬──────────┬──────────┐
│ ID       │ 지자체   │ 상태     │ 조치     │  ← 헤더 (Bold, #F5F5F5 배경)
├──────────┼──────────┼──────────┼──────────┤
│ —        │ —        │ —        │ —        │  ← 더미 행 1
├──────────┼──────────┼──────────┼──────────┤
│ —        │ —        │ —        │ —        │  ← 더미 행 2
├──────────┼──────────┼──────────┼──────────┤
│ —        │ —        │ —        │ —        │  ← 더미 행 3
└──────────┴──────────┴──────────┴──────────┘
```

### Button + triggers_api
```
[ 조치 실행 ]  → API-005
   ↑              ↑
   다크 필         회색 캡션 11px
```

### Custom
```
┌──────────────────────────────────────┐  ← 점선 테두리
│       지도 픽커                      │  ← label Bold 14px
│       [Custom: MapPicker]            │  ← Regular 11px gray
│       클릭으로 lat/lng 지정          │  ← note Regular 11px
└──────────────────────────────────────┘
```

### Stat
```
1,234
조회 건수
 ↑
Regular 12px gray
```

### Tabs
```
┌──────────┬──────────┬──────────┐
│ FAQ 관리 │ 서비스 요청 │ 통계   │
└══════════┴──────────┴──────────┘
   ↑활성     비활성
   2px 보더  텍스트만
```

### Dialog (modal section)
```
       (메인 프레임 옆 200px 간격)
       ┌──────────────────────────┐
       │  활성화 확인              │  ← 헤더 Bold 18px
       │  ─────────────────────    │
       │  이 룰셋을 활성화하면      │
       │  현재 활성 룰셋이 자동    │  ← 본문 Regular 14px
       │  으로 폐기됩니다.         │
       │                           │
       │     [취소]   [확인]       │  ← 버튼 우측 정렬
       └──────────────────────────┘
       (그림자: 약간 오프셋)
```
