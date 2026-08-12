# mc-logi-implement-kit

Logicraft 특정 프로젝트의 **특정 도메인을 로컬에서 바이브코딩으로 그대로 구현 가능**하도록, 구현 핵심 ITEM 을 **결정적 다운로더로 무열화 다운로드** + 버전 추적하는 **read-only** 스킬. logicraft ITEM 은 절대 수정하지 않는다.

## 무엇을 하나

- `D002 구현 키트 만들어줘` 한마디로 → 그 도메인의 구현에 필요한 ITEM(DFEAT/API/ERD/SEQ/SCREEN/UC/EVT/AC/ROLE/CONST + ADR/NFR/GUIDE 제약)을 `./docs/design/{slug}-{DOMAIN-ID}/` 트리로 일괄 다운로드.
- 각 ITEM = **서버 결정적 스켈레톤 `.md`**(원본 필드를 한 글자도 안 바꾸고 verbatim 재포맷 — 의역 0) + **원본 raw `.json`** 둘 다 보존.
- **`IMPLEMENTATION.md`** 진입점 자동 생성: 빌드 순서(제약→데이터→이벤트→API→로직→인가→화면→검증) + 의존 그래프 + 구현 현황.

## 동작 방식 — 결정적 다운로더 (LLM 0)

- **옛 방식(LLM 요약 fetcher)을 폐기**하고, LogiCraft 서버의 **배치 export 엔드포인트(API-152 `GET /projects/:id/kit-export`)**를 호출하는 순수 노드 다운로더(`bin/download-kit.mjs`)로 대체(ADR-026).
- 서버가 **원본 JSON + verbatim 스켈레톤 + content_hash + 그래프 links** 를 반환 → 다운로더가 델타(version 비교)로 변경분만 받아 디스크에 기록.
- **무열화**: content-hash 로 소스↔로컬 일치를 기계 검증. 옛 LLM 요약의 내용 손실(30~40%) 문제를 없앤다.
- **초 단위**: 도메인 수백 ITEM 도 초 단위(옛 LLM 병렬 요약은 분 단위). LLM 토큰 0.
- 인증: MCP 와 동일한 `lc_` api-key(`LOGICRAFT_API_KEY`).

## 버전 추적 (재동기화)

- 다운로더가 `.kit-manifest.json`(id→version/hash) + `version-master.md`(신선도·changelog·ITEM 표)를 생성.
- 재실행 시 **NEW / CHANGED / UNCHANGED / RETIRED** 자동 분류. UNCHANGED 는 페치·재렌더 skip(토큰·시간 절약), RETIRED 는 `_retired/` 이동(물리 삭제 금지). frontmatter 에 version/status/prev_version/content_hash/links.

## 견고성 (폴백·자가재생성)

- 다운로더 스크립트가 없으면 → **사용자에게 물어보고** 배포-안전 소스 캐리어(`download-kit-src.md`)에서 재생성(설치본 첫 실행).
- 서버에 엔드포인트가 없으면(구버전 서버) → 옛 fetcher 방식으로 폴백. 네트워크/인증 오류는 사용자에게 보고.

## read-only 보장

조회 도구만 사용(get_item/list_items/get_neighbors/get_related/get_implementation_coverage/list_unimplemented 등). 쓰기 도구(create/update/register/propose) 절대 호출 안 함. logicraft 변경은 `mc-logi-update` 별도.

## 구성

- `SKILL.md` — 워크플로·가용성 게이트·폴백 정책
- `bin/download-kit.mjs` — 결정적 다운로더(순수 node, 의존성 0)
- `download-kit-src.md` — 배포-안전 소스 캐리어(다운로더 자가재생성용)
- `core-item-set.md` — Tier 1~3 고정 세트 + 빌드 순서 + 의존 그래프 규칙
- `version-tracking.md` — version-master 포맷 + 차이 감지 알고리즘
- `summary-templates.md` — 타입별 요약 포맷(참고·폴백용)
- `checklist.md` — 폴백 fetcher 하드룰(read-only·정확성)

## 함께 쓰기

`mc-logi-domain-review`(갭 검출) → `mc-logi-update`(수정·cascade) → **`mc-logi-implement-kit`(무열화 키트 다운로드)** → `mc-logi-implement`(바이브코딩).
