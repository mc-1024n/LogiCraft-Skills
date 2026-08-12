# mc-logi-screen-kit

Logicraft 특정 프로젝트의 **화면(screen_spec)과 그 화면이 의존하는 디자인 ITEM 세트**를, 프론트엔드 화면 구현이 바로 가능하도록 **결정적 다운로더로 무열화 다운로드** + **화면 중심 레이아웃으로 정리** + 버전 추적하는 **read-only** 스킬. logicraft ITEM 은 절대 수정하지 않는다.

`mc-logi-implement-kit`(도메인 단위 백+프론트)의 **화면(프론트) 특화 버전**이다. 산출 키트는 `mc-logi-screen-implement` 가 그대로 소비한다.

## 무엇을 하나

- `SCREEN-011 화면 키트 만들어줘` / `D002 화면 다운로드` 한마디로 → 그 화면(들)과 의존 ITEM(design_system · ui_component · app_shell · navigation_tree · api_endpoint · constant · permission_role · implementation_guideline + 화면별 use_case · acceptance · 와이어프레임 · 고충실 디자인 렌더)을 `./docs/screen-design/{slug}-{DOMAIN-ID}/` **화면 중심 트리**로 일괄 다운로드.
- 각 ITEM = **서버 결정적 스켈레톤 `.md`**(원본 필드를 한 글자도 안 바꾸고 verbatim 재포맷 — 의역 0) + **원본 raw `.json`** 둘 다 보존.
- **`SCREENS.md`** 진입점 + `_shared/`(공유 자산) + `screens/SCREEN-NNN/`(화면별 스펙·와이어프레임·UC·AC·디자인) 자동 생성.

## 동작 방식 — 결정적 2-스크립트 (LLM 0)

옛 방식(타입별 LLM 요약 fetcher, 30~40% 열화)을 **폐기**하고 결정적 2-스크립트로 대체(ADR-026):

1. **`bin/download-kit.mjs`** — LogiCraft 배치 export 엔드포인트(API-152 `GET /projects/:id/kit-export`)를 호출해 **원본 JSON + verbatim 스켈레톤 + content_hash + 그래프 links + 렌더 정적파일**(와이어프레임·디자인, css self-contain)을 받아 평평한 스테이징에 기록. 델타(version/hash)로 변경분만.
2. **`bin/arrange-screen-kit.mjs`** — 네트워크 0·순수 로컬. 스테이징을 **화면 중심 레이아웃**(`screens/SCREEN-NNN/…` + `_shared/…`)으로 재배치하고 `SCREENS.md`·`version-master.md`·`ui-catalog.md`·`shell-nav.md`·`design-system.md` 를 결정적 합성. 본문은 verbatim 이동 → **열화 원천 차단**.

- **무열화**: content-hash 로 소스↔로컬 일치를 기계 검증. 본문은 요약/변형 0(서버 스켈레톤 그대로 이동).
- **초 단위**: 수십 화면 + 렌더도 초 단위(옛 LLM 병렬 요약은 분 단위). LLM 토큰 0.
- **오프라인 렌더**: 와이어프레임 공통 css·디자인 css 를 함께 받아 상대경로로 치환 → 로컬에서 바로 열림.
- 인증: MCP 와 동일한 `lc_` api-key(`LOGICRAFT_API_KEY`).

## 화면↔UC/AC 정확 귀속

화면에 직접 연결된 UC(`references`/`realizes`)는 물론, **화면→UC→(covered_by)→AC** 로 이어진 **depth-2 AC** 까지 찾아 해당 화면 폴더 아래(`uc/`·`ac/`)에 중첩. AC 가 다른 도메인에 있어도 id 로 정확히 수집.

## 버전 추적 (재동기화)

- 다운로더가 `.kit-manifest.json`(id→version/hash) + run-report 를, arranger 가 `version-master.md`(신선도·changelog·ITEM 표)를 생성.
- 재실행 시 **NEW / CHANGED / UNCHANGED / RETIRED** 자동 분류. UNCHANGED 는 재다운로드 skip, RETIRED 는 `_retired/` 이동(물리 삭제 금지). frontmatter 에 version/status/prev_version/content_hash/links.

## 견고성 (폴백·자가재생성)

- 스크립트가 없으면 → **사용자에게 물어보고** 배포-안전 소스 캐리어(`download-kit-src.md`·`arrange-screen-kit-src.md`)에서 재생성(설치본 첫 실행).
- 서버에 엔드포인트가 없으면(구버전 서버) → 옛 fetcher 방식으로 폴백. 네트워크/인증 오류는 사용자에게 보고.

## read-only 보장

logicraft **조회 도구만** 사용. 쓰기 도구(create_item / update_item / register_* / mark_implementation 등) 절대 호출 금지. 로컬 파일 시스템만 변경. logicraft 변경은 `mc-logi-update` 별도 사용.

## 다음 단계

산출된 `SCREENS.md` 부터 **`mc-logi-screen-implement`** 로 빌드 순서대로 화면 구현. 재동기화는 이 스킬 재실행 시 변경분만 갱신.
