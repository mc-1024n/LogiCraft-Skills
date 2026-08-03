# Coverage & Drift Dimension

키트 ITEM **전수** ↔ 코드 심볼 매핑 + IMPREC(구현 주장) 대조. 키트(설계 진실원)·코드(실제)·IMPREC(주장) **3방향 삼각 대조의 중심 차원**이다.

- **① 키트 → 코드 (미구현)**: 키트 active ITEM 이 코드에 실현됐는가 (3중 추적)
- **② 코드 → 키트 (표류·여분)**: 코드 클래스가 어떤 키트 ITEM 에도 추적되는가
- **③ IMPREC ↔ 코드 (주장 검증)**: 구현됐다는 IMPREC 주장이 실제 코드·버전과 일치하는가

> 룰 ID 접두사는 이 차원만 `COV-NNN` (다른 차원의 `<DIM>-CONF-NNN` 과 달리 `CONF` 접미 없음). checklist.md §6 출력 스키마 참조.

## STEP 0 — 입력 보강 (전수 카탈로그 + IMPREC 적재)

판정 전 두 진실원을 적재한다:

1. **키트 전 ITEM 카탈로그 (타입 무관)**: `item_catalog` 로 키트 도메인의 active ITEM 전체(`api_endpoint`·`erd`·`adr`·`acceptance`·`permission_role`·`domain_feature`·`use_case` 등 타입 무관)를 수집한다. 이 차원은 특정 타입에 한정하지 않고 **키트 전수**를 대상으로 한다.
2. **`imprec_data`**: 메인이 주입한 `get_implementation_coverage` 결과(IMPREC 레코드 = ITEM별 status·version·commit·구현 심볼 노트).

### degraded 게이트
- `degraded == true` (logicraft 미가용 → `imprec_data` 부재) 면 **IMPREC 의존 룰 COV-003 / COV-004 / COV-005 를 전부 SKIP** 한다.
- 이 경우 **COV-001 / COV-002 만 수행** + 출력 YAML 에 `degraded: true` 명시 + `notes_for_main.unable_to_verify` 에 "logicraft 미가용 — IMPREC 대조(COV-003/004/005) 생략, 키트↔코드 단방향만 수행" 기재.
- checklist.md §8 자가검증 7: `degraded: true` 면 `imprec_mismatch` finding 0건이어야 한다 (COV-003/004/005 가 imprec_mismatch 생성원이므로 SKIP 시 자동 충족).

## 검토 룰

각 룰: **조건 → severity → `finding_type` / `bucket` → 검출**. confidence 등급·반증 우선·3중 추적 방법은 **checklist.md §4·§5 인용** (이 차원에서 재정의하지 않음).

### ① 키트 → 코드 / ② 코드 → 키트 (degraded 무관 — 항상 수행)

#### COV-001: 미구현 ITEM
- **조건**: 키트 active ITEM 에 대응하는 코드 심볼/파일이 없음 (키트는 구현을 요구하나 코드에 실현 부재)
- **severity**: P1
- **finding_type**: `coverage_gap` → **bucket**: `code_fix`
- **검출**: checklist.md §4 의 **3중 추적**(① IMPLEMENTATION.md 의존맵 ② IMPREC 커밋/심볼 ③ 계약 문자열 grep)이 **모두 실패** — 어떤 경로로도 ITEM↔코드 매핑을 찾지 못함. 단정 전 checklist.md §5 반증 우선: "다른 클래스·다른 계층에 다르게 구현됐을 가능성" 을 먼저 배제. 배제 못 하면 `needs_human: true` + P2 강등.
- **gap 예시**: "API-336 (외부 학습데이터 조회) 키트 active 인데 컨트롤러/서비스 심볼·계약 path grep·IMPREC 매핑 3중 추적 모두 실패 — 미구현"

#### COV-002: 키트 외 코드 (역방향 표류)
- **조건**: 컨트롤러/엔티티/서비스 클래스가 **어떤 키트 ITEM 에도** 추적되지 않음 (코드에만 존재)
- **severity**: P1 (불확실 시 P2 강등)
- **finding_type**: `extra_code` → **bucket**: `design_update`
- **검출**: 코드 측 클래스 인벤토리(serena 심볼 + Grep) 각각을 키트 전수 카탈로그에 역추적. 매핑 0건이면 후보. **반드시 명명 차이를 먼저 배제** (checklist.md §5) — 키트 ITEM 명과 클래스명이 표기만 다른(예 `ArtifactRegistrar` ↔ `artifact_registrar` ITEM) 경우는 finding 아님. 배제 못 하면 `needs_human: true` + **P2**. 의도된 보존 코드(1차 보존 클래스 등 키트 보존 정책 명시)는 finding 아님.
- **gap 예시**: "`PortalDispatcherStub` 클래스가 키트 전수 카탈로그 어디에도 추적 안 됨 — 명명 차이 배제 후에도 대응 ITEM 부재 (설계 갱신 또는 의도 확인 필요)"

### ③ IMPREC ↔ 코드 (degraded == true 시 SKIP)

#### COV-003: IMPREC 거짓 주장
- **조건**: IMPREC 레코드의 `status == implemented` 인데 실제 코드가 부재 (구현됐다는 주장이 거짓)
- **severity**: P0
- **finding_type**: `imprec_mismatch` → **bucket**: `imprec_fix`
- **검출**: `imprec_data` 의 `implemented` 상태 ITEM 각각을 코드에 추적(3중 추적). **추적 실패** = 주장과 실제 불일치. 가장 위험한 거짓양성-반대 케이스(추적 휴리스틱 실패를 거짓주장으로 오판)이므로 checklist.md §5 에 따라 코드 부재를 grep·심볼로 **직접 확인**한 경우만 P0 단정. 직접 확인 못 하면 `needs_human: true` + P1 강등.
- **gap 예시**: "IMPREC: API-337 status=implemented (commit a85ffcc) 주장이나 해당 핸들러 심볼·계약 path grep 모두 부재 — IMPREC 거짓 주장"

#### COV-004: 버전 stale
- **조건**: 키트 ITEM 의 current_version 이 IMPREC 가 기록한 구현 시점 version 보다 **높음** (`kit_version > imprec_version`) → 코드가 **옛 계약**을 구현했을 가능성
- **severity**: P1
- **finding_type**: `imprec_mismatch` → **bucket**: `imprec_fix`
- **검출**: 키트 `version-master.md` 의 ITEM 버전 ↔ `imprec_data` 노트에 기록된 구현 시점 버전 대조. 키트 버전이 더 높으면 그 사이 계약 변경분이 코드에 미반영됐을 가능성. 단 버전 차이만으로 코드 표류를 단정하지 말 것 — 실제 계약 변경분이 무엇인지 확인 불가하면 `needs_human: true` 로 표기하고 api/schema 차원과 교차(`cross_dimension_hint`).
- **gap 예시**: "ERD-010 version-master v28 인데 IMPREC 구현 노트 v26 기록 — 코드가 v26 계약 구현 가능성, schema 차원 교차 확인 필요"

#### COV-005: 부분 구현 미표기
- **조건**: 코드가 stub/부분 구현(예 `PortalDispatcher` Stub·항상-허용 가드·미완 분기)인데 IMPREC `status == implemented` 로 완전 구현 주장
- **severity**: P1
- **finding_type**: `imprec_mismatch` → **bucket**: `imprec_fix`
- **검출**: COV-003 추적은 성공(코드 존재)했으나 코드 본문이 stub/TODO/부분임을 심볼 본문·`TODO`/`Stub` grep 으로 확인 + IMPREC=implemented 대조. 정직한 상태 표기(`in_progress`)로의 정정을 권고. (D004 PortalDispatcher Stub·AccessGuard TODO 실증 패턴.)
- **gap 예시**: "`PortalDispatcher` 본문이 Stub(송신 프로토콜 3종 TBD)인데 관련 IMPREC=implemented — 정직 in_progress 표기 권고"

## degraded 모드 요약

| 모드 | 수행 룰 | SKIP 룰 | 보고 |
|---|---|---|---|
| 정상 (logicraft 가용) | COV-001 ~ COV-005 전부 | 없음 | `degraded: false` |
| degraded (logicraft 불가) | COV-001 / COV-002 만 | COV-003 / COV-004 / COV-005 | `degraded: true` + `unable_to_verify` 명시, `imprec_mismatch` 0건 |

## 룰 ID ↔ finding_type ↔ bucket 매핑 (고정)

| 룰 ID | 조건 | severity | finding_type | bucket | degraded 시 |
|---|---|---|---|---|---|
| `COV-001` | 미구현 ITEM | P1 | `coverage_gap` | `code_fix` | 수행 |
| `COV-002` | 키트 외 코드 | P1(불확실 P2) | `extra_code` | `design_update` | 수행 |
| `COV-003` | IMPREC 거짓 주장 | P0 | `imprec_mismatch` | `imprec_fix` | SKIP |
| `COV-004` | 버전 stale | P1 | `imprec_mismatch` | `imprec_fix` | SKIP |
| `COV-005` | 부분 구현 미표기 | P1 | `imprec_mismatch` | `imprec_fix` | SKIP |

## Evidence·confidence·반증 (checklist.md 인용)

- **evidence 강제** (checklist.md §3): 모든 finding 은 `kit_item`(ITEM ID 또는 `"->코드에만 존재"`) + `code_ref`(`relative/path.java:line` 또는 코드 부재 시 `"<부재>"`) 동반. 추적 실패 finding 은 보고 금지(폐기).
- **confidence** (checklist.md §4): 3중 추적 중 2+ 일치 = `high`, 1개 = `medium`, 코드 측 직접 확인 못 함 = `low`. `low` 는 P2 강등 + `needs_human: true` 권장.
- **반증 우선** (checklist.md §5): `coverage_gap`(COV-001)·`extra_code`(COV-002) 단정 전 "다르게 구현됐을 가능성"(명명 차이·다른 계층) 먼저 배제. 못 하면 단정 금지 → `needs_human: true` + P2. 의도된 보존 상태(키트 보존 정책 명시)는 gap 아님.
- **cross-dimension**: 버전 stale(COV-004)·미구현(COV-001) 의 구체 계약 차이는 api/schema 차원 소관 — gap 직접 보고 대신 `notes_for_main.cross_dimension_hint` 로 전달.
