# mc-logi-implement-review — Code ↔ Kit Conformance Auditor

현재 구현된 코드가 로컬 구현 키트(`docs/design/{slug}-{DOMAIN-ID}/`, 설계 진실원)와 정합하는지 **6차원 병렬 감사**해 불일치를 검출하는 **read-only** 스킬. 코드·logicraft·키트 아무것도 수정하지 않으며, 후속 수정은 코드=`mc-logi-implement` / 설계=`mc-logi-update` 로 핸드오프한다.

## 위치 — 키트 패밀리의 빈 칸
`mc-logi-implement-kit`(키트 다운로드) → `mc-logi-implement`(구현) → **`mc-logi-implement-review`(코드↔키트 정합 점검)**. `mc-logi-domain-review`(설계↔설계)·`mc-code-reviewer`(코드↔best-practice)가 비워둔 **코드 ↔ 키트** 정합 칸을 채운다.

## 판정 — 3방향 삼각 대조
키트(설계 진실원)·코드(실제)·logicraft IMPREC(구현 주장) 셋을 대조해 불일치를 5종으로 분류:
- `code_drift`(코드가 키트 위반) → 코드 수정
- `coverage_gap`(키트 ITEM 미구현) → 코드 수정
- `design_stale`(코드가 키트보다 앞섬) → 설계 갱신
- `extra_code`(키트에 없는 코드) → 설계 갱신
- `imprec_mismatch`(IMPREC 거짓 주장) → 추적 정정

logicraft 불가 시 2방향(키트↔코드)으로 자동 degrade.

## 6차원 병렬 auditor (`logi-implement-auditor`)
- **api** — 컨트롤러 path/method/요청·응답/envelope(ADR-072) ↔ API ITEM 계약
- **schema** — 엔티티+Flyway 마이그레이션 ↔ ERD 테이블/컬럼/제약/인덱스
- **policy** — 코드 패턴 ↔ ADR 결정(구현 함정)
- **coverage** — 키트 ITEM↔코드 심볼 매핑 + 역방향 표류 + IMPREC 대조
- **acceptance** — JUnit 테스트 ↔ AC Given/When/Then
- **role** — 권한 가드 ↔ ROLE required_roles

## 거짓양성 방어
정합 매핑은 본질적으로 휴리스틱이라, 모든 finding 에 evidence(키트 ID + `file:line`) + confidence(3중 추적 2+ 일치=high)를 필수화하고, 불확실하면 반증 우선으로 `needs_human`+P2 강등한다.

## 호출 예
"D004 구현이 키트랑 맞는지 확인" / "키트 대비 코드 표류 찾아줘" / "구현 정합성 감사" / "/mc-logi-implement-review". 기본 도메인 전체 스캔, 인자로 특정 ITEM·브랜치 diff 타겟 지정 가능.

## 산출
경고 배너(키트 stale/degrade) + 커버리지 요약 + P0/P1/P2 finding 표 + [코드 수정 버킷]/[설계 갱신 버킷]/[추적 정정] 분리 리포트.