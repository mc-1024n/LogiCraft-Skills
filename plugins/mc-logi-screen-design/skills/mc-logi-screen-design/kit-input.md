# kit-input.md — 키트 → 디자인 작성 입력 계약

이 스킬이 도메인 지식을 얻는 **유일한** 출처는 mc-logi-screen-kit 산출물이다.
어느 키트 파일에서 무엇을 읽어 `design-prompt.md` 의 어느 슬롯에 주입하는지를 정의한다.
키트 포맷이 바뀌면 이 파일만 갱신한다.

## 키트 구조 (입력 계약)

```
docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
├── SCREENS.md                  ← 진입점 (화면 목록 + surface 집합 + 공유자산 인덱스 + 변경 알림)
├── version-master.md           ← 버전 마스터 (last sync · 화면 집합)
├── _shared/
│   ├── design-system.md        ← 디자인 토큰 (color/typography/spacing/radius + Do·Don't)
│   ├── ui-catalog.md           ← ui_component 카탈로그 인덱스 (UI-NNN 이름·variants)
│   └── ...                     ← api/constant/role 등 (디자인 단계에서는 미사용)
└── screens/
    └── SCREEN-NNN/
        ├── SCREEN-NNN.md       ← screen_spec 골격 (sections·components·consumes_apis·layout)
        ├── wireframe-*.html    ← surface 별 와이어프레임 (없으면 _no-wireframe.md)
        └── wireframe.css       ← 와이어프레임 CSS
```

- 키트 루트: `docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/`.
- 디자인 단계는 **시각 구성에 필요한 파일만** 읽는다(api/constant/role/uc/ac 는 implement 의 몫 — 디자인엔 미사용).

---

## Phase 0 — 키트 게이트 적재 목록

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `SCREENS.md` | 화면 목록 표 / 화면별 surface 집합 / 도메인 슬러그 / 변경 알림(CHANGED/RETIRED) / last sync | 디자인 대상 화면·surface 결정. RETIRED 제외 |
| `version-master.md` | 헤더(last sync·화면 집합) | 신선도 판단(stale → screen-kit SYNC 권고) |

**게이트 결정**: `SCREENS.md` 없음 → screen-kit 선행. last sync 오래됨/사용자 SYNC 요청 → SYNC 권고.
CHANGED/RETIRED 있으면 영향 정리 후 진행.

---

## Phase 1 — 디자인 입력 합성 (프롬프트 슬롯 주입)

`design-prompt.md` 의 슬롯과 1:1 매핑. **슬롯 이름은 design-prompt.md 와 정확히 일치해야 한다.**

| 슬롯 | 키트 파일 | 읽는 것 | 비고 |
|---|---|---|---|
| `{{DS_TOKENS}}` | `_shared/design-system.md` | color base hex·scale / typography step(size·weight·line-height·**font-family**·@font-face 소스) / spacing / radius / Do·Don't 규칙 전량 | DS 강제 컨텍스트(키트 design-system.md 의 **그** DS — KRDS든 무엇이든; 특정 DS 가정 안 함). "이 토큰만 사용, 임의 hex/px 금지" 와 함께 주입. **파일 없음·토큰 공백이면 SKILL Phase 1-0 DS 부재 게이트로 중단**(임의 추정 금지) |
| `{{SCREEN_STRUCTURE}}` | `screens/SCREEN-NNN/SCREEN-NNN.md` | sections[] / components[] / layout / consumes_apis(맥락용) / brownfield 보존 메모 / 라우트·구현 요지 | 골격. 이 구조는 유지하고 디자인만 입힘 |
| `{{WIREFRAME_REF}}` | `screens/SCREEN-NNN/wireframe-*.html` (+ `wireframe.css`) | surface 목록(main/detail/modal 등) + 각 surface 의 영역 배치 | 없으면 `_no-wireframe.md` 확인 → SCREEN-NNN.md sections[] 만으로 골격 추론 |
| `{{COMPONENT_CATALOG}}` | `_shared/ui-catalog.md` | 카탈로그 인덱스(UI-NNN id·이름·category·variants) | 매핑 대상. 카탈로그 외 컴포넌트 추정 금지 |
| `{{SCREEN_ID}}` | `SCREENS.md` / 대상 식별 | SCREEN-NNN id | 프롬프트·project 이름·파일 경로 |
| `{{SURFACE}}` | `{{WIREFRAME_REF}}` 의 wireframe 파일명 | surface 키(main/detail/register/...) | surface 별 생성 단위 |

**surface 결정**: `{{WIREFRAME_REF}}` 의 wireframe 파일 1개 = surface 1개. 파일별로 디자인 화면을
작성한다(예: `wireframe-main.html` → `{{SURFACE}}`=main → `design-main.html`).

---

## 해석 규칙

1. **키트가 진실원** — 골격·토큰·컴포넌트는 키트에서 읽는다. 스킬·이 파일에 특정 프로젝트 값
   (토큰명·컴포넌트 id 등)을 적지 않는다.
2. **⚠️ 표기 우선** — 키트 파일이 ⚠️ 로 명시한 불일치는 그 지시대로. 키트가 답을 안 줬으면 사용자에게 묻는다.
3. **토큰 추측 금지** — `design-system.md` 에 없는 색·간격을 임의 hex/px 로 만들지 않는다. 개별 토큰 1~2개
   결손이면 프롬프트에 "해당 토큰 미정 — 임의 색 금지" 로 전달하고 진행. **DS 전체가 없거나 토큰이 통째로
   비면(부분 결손 아님) → 프롬프트로 흘리지 말고 SKILL Phase 1-0 DS 부재 게이트로 중단.**
4. **카탈로그 외 컴포넌트 추정 금지** — `ui-catalog.md` 에 없는 컴포넌트를 새로 발명하지 않는다. 필요하면
   사용자에게 알리고 screen-kit/register_ui_components 보강 권고.
5. **셸 제외** — 헤더·사이드바·푸터는 app_shell 소관. 디자인 대상은 화면 본문만.
6. **RETIRED 제외** — `_retired/` 또는 SCREENS.md RETIRED 표기 화면은 디자인 대상에서 뺀다.
