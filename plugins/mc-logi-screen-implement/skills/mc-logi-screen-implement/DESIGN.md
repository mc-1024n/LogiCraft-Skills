# mc-logi-screen-kit / mc-logi-screen-implement — 설계 문서

- 날짜: 2026-06-20
- 상태: 설계 확정 (구현 전)
- 작성: brainstorming 세션 (KLID 2차 프로젝트 컨텍스트에서 도출, 단 스킬 자체는 프로젝트 독립)

## 1. 목적 (한 줄)

Logicraft 에 설계된 화면(screen_spec)과 그 화면이 의존하는 디자인 ITEM 세트(DS / ui_component / SHELL / NAV / API / CONST / ROLE / 와이어프레임)를 **로컬 키트로 받아(kit)** 그 키트를 단일 진실원으로 **풀 프론트엔드 화면을 구현(implement)** 하는, **프로젝트 독립·디자인시스템 무관**의 user-level 스킬 2종.

기존 `mc-logi-implement-kit` → `mc-logi-implement` (도메인 단위 백+프론트 구현) 패턴의 **화면(프론트) 특화 버전**이다.

## 2. 배경 / 동기

- Logicraft 는 화면 개발 ITEM 타입(design_system / ui_component / navigation_tree / app_shell / screen_spec / constant / permission_role / implementation_guideline)을 모두 갖췄고, 2026-06-20 부트스트랩 업데이트로 채움 경로도 정립됐다:
  - `get_logicraft_guide('screen-development')` — 디자인 4층(토큰→컴포넌트→레이아웃→화면) 채움 순서·구현 활용
  - `register_ui_components`(복수) — UI 카탈로그 일괄 등록 (서버=등록만, 추출=AI)
  - `apply_design_preset(seed_components=true)` — 프리셋 토큰 + 표준 컴포넌트 22개 동반 시드
  - kickoff 가이드 "화면 개발 준비 트랙"
- 기존 KLID 프로젝트의 KRDS 하네스(`docs/krds-harness/`, `scripts/krds-validate`)는 같은 일을 **KLID 레포 안에 로컬 캐싱 + KRDS 전용**으로 했다. 이는 (a) logicraft 밖으로 진실원이 새고 (b) KRDS 를 특별취급하는 한계가 있다.
- 본 스킬은 그 한계를 제거한다: 진실원은 logicraft, KRDS 는 디자인시스템 하나로만 취급.

## 3. 확정 결정 사항 (brainstorming 합의)

| # | 결정 | 값 |
|---|---|---|
| D1 | 스킬 개수 | **2개** — `mc-logi-screen-kit`(다운로더) + `mc-logi-screen-implement`(구현). 기존 패턴 차용 |
| D2 | 구현 범위 | **풀 프론트 구현** — UI + react-query API 연동 + 상태 + 폼/zod 검증까지 동작하는 화면 (UI 골격만 X) |
| D3 | 키트 입력 단위 | **도메인 단위** (그 도메인 화면 전체 + 공유 의존 ITEM). 단 `SCREEN-NNN` 으로 **화면 좁히기 옵션** |
| D4 | 구현 진행 단위 | **화면 단위 점진** — 공유 자산 먼저 셋업 후 화면 하나씩. (풀구현의 화면 간 공유 자산 문제 해결) |
| D5 | 빈 ui_component 카탈로그 | **구현 0.5단계로 흡수** — 비었으면 3출처(A 코드추출 / B 라이브러리표준 / C 프리셋 seed_components)로 시드 |
| D6 | 디자인 검증 | **KRDS 특별취급 안 함**. DS 무관 단일 원리("get_design_md 토큰만, 하드코딩 금지") = 구현 규칙 주입(예방) + 가벼운 grep 검출. 전용 정적분석기(krds-validate)는 안 만듦 |

### D4 근거 (왜 키트는 도메인, 구현은 화면)
풀 프론트 구현은 화면 "모양"만이 아니라 화면들이 공유하는 자산(apiClient·queryKeys·types·zod schema·도메인 공통 컴포넌트)을 다룬다. 이 자산은 개별 화면이 아니라 **도메인에 응집**한다(KLID CLAUDE.md "도메인 4곳 동일 키" 규칙이 증거 — 목록/상세 화면이 같은 API·타입·쿼리키 공유). 화면 1개씩 풀구현하면 두 번째 화면에서 공유 자산 재사용 조율이 매번 발생한다. → 키트는 도메인(공유+화면들 한 벌), 구현은 화면 점진(공유 먼저 셋업 후 화면별)이 자연 정답.

## 4. mc-logi-screen-kit — 화면 키트 다운로더 (read-only)

기존 `mc-logi-implement-kit` 골격(타입별 병렬 fetcher, version-master, frontmatter 버전추적, _retired 이동, read-only) 차용. 화면 특화 차이만 기술.

### 4.1 입력
- `DOMAIN-NNN` → 그 도메인의 활성 screen_spec 전체 + 공유 의존
- `SCREEN-NNN[,SCREEN-MMM...]` → 지정 화면만 + 그 화면들의 공유 의존
- 미지정 → AskUserQuestion

### 4.2 받는 ITEM 세트 (화면 core-item-set)
- **공유(도메인/프로젝트 레벨, 1벌)**:
  - design_system (DS) — `get_design_md` 로 design.md 형식 + raw JSON
  - ui_component 카탈로그 — 전체 요약(이름·category·props·variants·a11y·code_snippet)
  - app_shell (SHELL) + navigation_tree (NAV)
  - 도메인 api_endpoint (그 화면들이 consumes 하는 것) + constant(CONST) + permission_role(ROLE)
  - implementation_guideline (적용 범위 매칭)
- **화면별(SCREEN 마다)**:
  - screen_spec 본문 + static_render(와이어프레임 HTML) 다운로드
  - 그 화면의 use_case / acceptance
  - 그 화면의 consumes_apis / required_roles 링크

### 4.3 산출물 구조
```
docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
├── SCREENS.md                  ← 진입점 (화면 목록 + 공유자산 인덱스 + 빌드 순서 + 카탈로그 상태 플래그)
├── version-master.md           ← 버전 마스터 (전 ITEM 버전표 + run changelog)
├── _shared/
│   ├── design-system.md        ← get_design_md 결과(design.md) + _raw/DS-001.json
│   ├── ui-catalog.md           ← ui_component 전체 카탈로그 요약 + _raw/UI-*.json
│   ├── shell-nav.md            ← SHELL + NAV 요약
│   ├── api/  constant/  role/  guideline/   ← 공유 ITEM 타입별
├── screens/
│   └── SCREEN-011/
│       ├── SCREEN-011.md       ← 구현지향 요약(frontmatter+배너)
│       ├── wireframe.html      ← static_render
│       ├── _raw/SCREEN-011.json
│       └── uc/ ac/             ← 그 화면의 UC/AC
└── _retired/
```

### 4.4 카탈로그 감지 (D5 연동)
- ui_component 0건 → `SCREENS.md` 헤더에 `⚠️ ui_component 카탈로그 비어있음 — implement Phase 0.5 에서 시드 필요` 플래그 + DS archetype 기록(시드 출처 판단용).

### 4.5 버전추적·엔진·read-only
기존 implement-kit 과 동일. fetcher 는 기존 `logi-implement-fetcher` 재사용 가능성 우선 검토(요약 템플릿에 화면 타입 섹션 추가), 부족하면 화면 특화 fetcher 신설.

## 5. mc-logi-screen-implement — 화면 구현 오케스트레이터

기존 `mc-logi-implement` 의 phase 게이트 + superpowers 재사용(brainstorming/writing-plans/subagent-driven) + 키트=진실원 + 추적 역동기화 골격 차용. 화면 특화 phase 만 차이.

```
Phase 0   키트 게이트      키트 존재/신선도 → 없으면 screen-kit 호출, stale 이면 SYNC.
                          CHANGED/RETIRED 있으면 영향 정리 후 진행.
Phase 0.5 카탈로그 시드    SCREENS.md 카탈로그 플래그 확인. 비었으면 3출처로 ui_component 시드:
                          A) 레포에 컴포넌트 코드 있음 → AI 가 파일 읽어 추출 → register_ui_components
                          B) 라이브러리 정함(shadcn 등) → 표준 지식으로 register_ui_components
                          C) 코드/라이브러리 없음 → apply_design_preset(seed_components=true)
                          (사용자 확인 후 시드. logicraft 쓰기 발생 지점 — 명시 게이트)
Phase 1   공유 자산 셋업    도메인 apiClient(3파일 세트)·queryKeys·types(snake_case 보존)·zod schema
                          + 라우팅/셸 결선. 화면들이 공유하는 토대. 레포 컨벤션 Explore 로 실측.
Phase 2   스펙            superpowers:brainstorming + 화면별 키트 주입(screen_spec/와이어프레임/AC/
                          ui_component 룩업 결과). 키트 ITEM ID·경로 인용. → [게이트 1: 승인]
Phase 3   플랜            superpowers:writing-plans. 태스크 = 화면 단위 점진(공유자산 Task 0 →
                          화면별 Task). 각 태스크에 키트 화면 요약·AC 경로 명시. → [게이트 2: 승인]
Phase 4   화면별 구현      feature 브랜치 + superpowers:subagent-driven-development. 화면 하나씩:
                          screen_spec.sections → find_ui_component 카탈로그 룩업 → 컴포넌트 조립
                          → react-query 연동(consumes_apis) → react-hook-form+zod 검증
                          → AC(Given/When/Then) 충족.
                          ★ 디자인 규칙 주입: 색·간격은 get_design_md 토큰만, 임의 hex 금지(D6 예방).
                          ★ 가벼운 검출: 생성 파일 raw hex grep 체크(D6 검출).
                          태스크별 스펙리뷰→품질리뷰 + 최종 전체 리뷰.
Phase 5   반영·추적        lint+build 그린 → [게이트 3: 머지 방식] → 머지.
                          IMPREC: create_implementation_record (화면별).
                          역링크: register_module(code_module) + link_ui_component_to_module
                                  (이 화면이 쓴 ui_component ↔ 실제 .tsx) → 다음 세션 중복 방지.
                          키트 현황(SCREENS.md)·프로젝트 CLAUDE.md 블록 갱신.
                          mc-logi-update 권고(구현 중 발견한 설계 불일치) + 메모리 문의.
```

재개: phase 인자 지원("공유자산부터", "구현만", "추적만").

## 6. 기존 스킬 대비 핵심 차이 3가지
1. **공유/화면 2층 분리** (Phase 1 vs Phase 4) — 풀 프론트 공유 자산 문제 해결.
2. **카탈로그 시드(Phase 0.5)** — 빈 프로젝트 대비, 새 `register_ui_components`/`seed_components` 활용. logicraft 쓰기 발생 유일 지점(게이트 필수).
3. **UI 역링크 추적** — IMPREC 외에 `link_ui_component_to_module` 로 부품↔코드 양방향.

## 7. 범위 밖 (후속/비목표)
- KRDS `scripts/krds-validate` 전용 하네스 통합 — D6 로 불필요(범용 룰로 대체). 추후 "프로젝트 검증 호출" 옵션으로만 고려.
- 백엔드 API 실구현 — 본 스킬은 프론트. api_endpoint 는 "소비" 대상(연동), 구현은 mc-logi-implement(도메인) 담당.
- 와이어프레임 자동 생성 — mc-logi-figma-wireframe 별도 스킬.

## 8. 미해결 / plan 단계에서 정할 것
- fetcher: 기존 `logi-implement-fetcher` 재사용 vs 화면 특화 신설 (요약 템플릿 화면 섹션 추가 범위)
- screen-kit 참조 파일 세트(core-item-set / summary-templates / version-tracking / checklist) 의 화면 버전 분량
- Phase 0.5 시드 시 logicraft 쓰기 정책(사용자 확정 데이터만 — logicraft 가이드 준수) 구체 절차
- 산출물 디렉토리명: `docs/screen-design/` vs 기존 `docs/design/` 와의 공존(같은 도메인 두 키트)
