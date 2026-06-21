# mc-logi-implement-review

현재 구현된 코드가 로컬 구현 키트(설계 진실원)와 정합하는지 6차원 병렬 감사하는 read-only 스킬. 키트(설계)·코드(실제)·IMPREC(구현 주장) 3방향 삼각 대조로 표류를 검출하며, 코드·설계 아무것도 수정하지 않는다.

## 무엇을 하나
- **6차원 병렬 auditor**(`logi-implement-auditor`): api / schema / policy / coverage / acceptance / role 동시 감사.
- **3방향 판정**: 키트 ↔ 코드 ↔ IMPREC 삼각 대조(logicraft 불가 시 2방향 자동 축소).
- **5종 분류**: code_drift / design_stale / coverage_gap / extra_code / imprec_mismatch.
- **2버킷 핸드오프**: 코드 수정(mc-logi-implement) / 설계 갱신(mc-logi-update) / 추적 정정으로 분리해 입력 포맷까지 변환.

## 어떤 효과
- 구현이 설계 계약(API envelope·ERD 제약·ADR 정책·권한 가드 등)을 지키는지 한 번에 점검.
- 모든 finding에 **evidence + confidence 필수** — 거짓양성 방어, 불확실 시 반증 우선.
- P0/P1/P2 우선순위 + 키트 ID·`file:line` 근거가 달린 정합 리포트.

## 사용 예
- "D004 구현이 키트랑 맞는지 확인"
- "키트 대비 코드 표류 찾아줘"
- "지금 브랜치 구현분이 키트 지키는지 점검" (git diff 범위 한정)

## 요구 사항
- **에이전트**: logi-implement-auditor (플러그인 설치 시 자동 동봉·scoped 등록; 미발견 시 general-purpose fallback)
- **코드 분석**: serena(심볼)·Grep·Read
- **LogiCraft MCP**: `get_implementation_coverage` 등(IMPREC; 불가 시 2방향 degrade)
- **선행**: mc-logi-implement-kit으로 생성된 로컬 키트(`docs/design/{slug}-{DOMAIN-ID}/`)

## 구성
- `SKILL.md` — 판정 모델·6차원·Phase 흐름·에이전트 호출
- `checklist.md` — evidence/confidence 규약 + read-only 보장 + 출력 YAML 스키마
- `dimensions/{api,schema,policy,coverage,acceptance,role}.md` — 차원별 점검 룰 6종

## 한계
- **read-only** — 코드·logicraft·키트 아무것도 수정 안 함(검출만). 수정은 후속 스킬.
- 키트 선행 필수(없으면 중단, stale면 경고 후 진행).
- 정합 매핑은 휴리스틱 — confidence low/needs_human은 P2로 분류.
