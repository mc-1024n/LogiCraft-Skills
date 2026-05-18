# mc-logi-implement-kit

Logicraft 특정 프로젝트의 **특정 도메인을 로컬에서 바이브코딩으로 그대로 구현 가능**하도록, 구현 핵심 ITEM 을 다운로드 + 구현지향 요약 + 버전 추적하는 **read-only** 스킬. logicraft ITEM 은 절대 수정하지 않는다.

## 무엇을 하나

- `D002 구현 키트 만들어줘` 한마디로 → 그 도메인의 구현에 필요한 ITEM(DFEAT/API/ERD/SEQ/SCREEN/UC/EVT/AC/ROLE/CONST + ADR/NFR/GUIDE/MOD 제약)을 `./docs/design/{slug}-{DOMAIN-ID}/` 트리로 일괄 다운로드.
- 각 ITEM = **구현지향 요약 `.md`**(코드로 바로 직역 가능: ERD→DDL, API→시그니처, SEQ→호출순서, AC→테스트) + **원본 raw `.json`** 둘 다 보존.
- **`IMPLEMENTATION.md`** 진입점 자동 생성: 빌드 순서(제약→데이터→이벤트→API→로직→인가→화면→검증) + 의존 그래프 + 구현 현황(이미 구현/미구현/시작점).

## 버전 추적 (재동기화)

- 각 ITEM 헤더에 logicraft `current_version`(정수) 박음 + `version-master.md` 마스터 표.
- 재실행 시 정수 비교로 **NEW / CHANGED / UNCHANGED / RETIRED** 자동 분류. CHANGED 는 `v11 → v12` 배너 + change_summary 삽입으로 "코드 재반영 필요" 강조. RETIRED 는 `_retired/` 이동(물리 삭제 금지). UNCHANGED 는 다운로드 skip(토큰 절약).
- Changelog append-only — git 과 함께 변경 히스토리 추적.

## 동작 방식

- `logi-implement-fetcher` 에이전트를 ITEM 타입별 **병렬**(상한 8) 실행 — 거대 ITEM 은 Bash python 파싱으로 메인 컨텍스트 보호.
- Tier 1(구현 본체) / Tier 2(제약·기존구현) / Tier 3(조건부: 외부연동·AI거버넌스·class diagram 등) **결정적 규칙**으로 대상 고정 — 매 실행 동일.

## read-only 보장

조회 도구만 사용(get_item/list_items/get_neighbors/get_related/get_implementation_coverage/list_unimplemented 등). 쓰기 도구(create/update/register/propose) 절대 호출 안 함. logicraft 변경은 `mc-logi-update` 별도.

## 구성

- `SKILL.md` — 워크플로(Phase 1~6)·진입·병렬정책
- `core-item-set.md` — Tier 1~3 고정 세트 + 빌드 순서 + 의존 그래프 규칙
- `version-tracking.md` — version-master 포맷 + 차이 감지 알고리즘
- `summary-templates.md` — 타입별 구현지향 요약 포맷(코드 직역 기준)
- `checklist.md` — fetcher 하드룰(read-only·정확성·빈요약 금지)

## 함께 쓰기

`mc-logi-domain-review`(갭 검출) → `mc-logi-update`(수정·cascade) → **`mc-logi-implement-kit`(구현 키트 다운로드)** → 바이브코딩.