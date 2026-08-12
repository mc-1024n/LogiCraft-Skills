# phase-gates.md — phase 별 산출물·게이트·재개 규약

## 산출물·게이트 표

| Phase | 산출물 (재개 판정 기준) | 게이트 | 게이트에서 묻는 것 |
|---|---|---|---|
| 0 키트 게이트 | `docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/SCREENS.md` 존재 + `version-master.md` 신선 | (자동) | CHANGED/RETIRED 다수 시에만 영향 확인 |
| 0.5 카탈로그 시드 | `SCREENS.md` `⚠️ ui_component 카탈로그 비어있음` 플래그 해소 — register_ui_components 또는 apply_design_preset 완료 | **게이트 0.5** | 시드 dry 제시 → 사용자 승인 (logicraft 쓰기 발생 지점) |
| 1 공유 자산 셋업 | `feature/{slug}` 브랜치 — apiClient 3파일 세트·queryKeys·types·zod schema + 라우팅/셸 결선 커밋 | (자동) | 레포 컨벤션 미확인 구조·정책 차이 발견 시에만 |
| 2 스펙 | `docs/superpowers/specs/YYYY-MM-DD-{slug}-screen-design.md` (커밋) | **게이트 1** | 스펙 검토·승인 (수정 요청 루프) |
| 3 플랜 | `docs/superpowers/plans/YYYY-MM-DD-{slug}-screen.md` (커밋) | **게이트 2** | 플랜 승인 + 실행 방식 (서브에이전트 권장/인라인) |
| 4 화면별 구현 | `feature/{slug}` 브랜치 — 화면별 커밋 + 최종 전체 리뷰 통과 + raw hex grep 클린 | (자동) | BLOCKED/정책 차이·카탈로그 외 컴포넌트 발견 시에만 |
| 5 반영·추적 | lint+build 그린 → 머지 → IMPREC N건 + 역링크 + SCREENS.md 현황 갱신 커밋 | **게이트 3** | 머지 방식 (main 머지/브랜치 유지/PR) |

---

## 게이트 상세

### 게이트 0.5 — 카탈로그 시드 승인 (logicraft 쓰기 발생)

**트리거**: Phase 0 종료 시 `SCREENS.md`에 `⚠️ ui_component 카탈로그 비어있음` 플래그 확인.
populated 상태면 Phase 0.5 skip (게이트 없이 Phase 1 진입).

**logicraft 쓰기 경계**: Phase 0.5 와 Phase 5 에서만 logicraft 쓰기(register_ui_components /
apply_design_preset / create_implementation_record / register_module / link_ui_component_to_module)
가 발생한다. 그 외 Phase(0·1·2·3·4)는 logicraft read(get_*, find_*, list_*) 또는 레포 코드 작업만.

**dry 제시 절차 (승인 전 절대 쓰기 금지)**:
1. 출처 판단: `_shared/design-system.md` + 레포 코드 Explore 결과를 토대로 A/B/C 중 해당 출처 특정.
   - A) 레포에 컴포넌트 코드 있음 → AI 가 파일 읽어 추출 → `register_ui_components`
   - B) 라이브러리 정함(shadcn 등) → 표준 지식으로 `register_ui_components`
   - C) 코드/라이브러리 없음 → `_shared/design-system.md` DS archetype 확인 → `apply_design_preset(seed_components=true)`
2. 등록 대상 목록 dry 제시: "출처 X로 다음 N건을 logicraft에 등록합니다 — [컴포넌트 이름·category·근거 목록]"
3. **사용자 승인 대기** (logicraft 정책: 사용자 확정 데이터만, AI 임의 추정 금지).
4. 승인 후 실행 → 결과 보고.

**게이트 0.5 게이트 질문 예시**:
```
[게이트 0.5] 카탈로그 시드 계획 확인

출처: A) 레포 코드 추출 (또는 B/C)
등록 예정 컴포넌트 (N건):
  - Button (primary/secondary/ghost 변형, category: action)
  - Modal (confirm/info, category: overlay)
  - ... (전체 목록)
근거: src/components/base/ 에서 추출 / 라이브러리 X 표준 / DS archetype Y

logicraft register_ui_components 를 실행합니다. 승인하시겠습니까?
수정이 필요하면 목록·출처를 알려주세요.
```

---

### 게이트 1 — 스펙 승인

**트리거**: Phase 2 스펙 문서(`docs/superpowers/specs/YYYY-MM-DD-{slug}-screen-design.md`) 작성 완료.

**게이트 1 질문**:
스펙 문서 경로·요지 한 단락 + "이대로 플랜 작성을 진행할까요? 수정할 부분이 있으면 알려주세요."
수정 요청 시 스펙 재작성 → 다시 승인 루프. 승인 후 Phase 3 진입.

---

### 게이트 2 — 플랜 승인 + 실행 방식

**트리거**: Phase 3 플랜 문서(`docs/superpowers/plans/YYYY-MM-DD-{slug}-screen.md`) 작성 완료.

**게이트 2 질문**:
플랜 문서 경로·태스크 목록 요약 + 다음 두 가지를 동시에 확인:
1. "이 플랜으로 구현을 진행할까요? 수정할 부분이 있으면 알려주세요."
2. "구현 실행 방식: (권장) 서브에이전트 병렬 실행 / 인라인 순차 실행 중 어떤 방식으로 진행할까요?"
승인 + 방식 선택 후 Phase 4 진입.

---

### 게이트 3 — 머지 방식

**트리거**: Phase 4 구현 완료 + lint + build 그린 확인.

**게이트 3 질문**:
결과 요약(구현 화면 수·커밋 수·그린 확인) + "다음 중 어떤 방식으로 반영할까요?
  A) main 직머지  B) 브랜치 유지 (PR 나중에)  C) PR 생성"
선택 후 Phase 5 진입.

---

## 재개 (phase 인자)

사용자가 재개 지점을 말하면 ("공유자산부터", "구현만", "추적만", "Phase N부터"):

1. 해당 phase 의 **선행 산출물 존재**를 아래 표로 검증 — 누락 시 선행 phase 부터 재진행 요청.

| 재개 요청 | 필요한 선행 산출물 | 확인 위치 |
|---|---|---|
| "공유자산부터" (Phase 1 재개) | `SCREENS.md` + `version-master.md` 존재 | `docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/` |
| "구현만" (Phase 4 재개) | 스펙 문서 + 플랜 문서 + Phase 1 브랜치 커밋 | `docs/superpowers/specs/` + `plans/` + git log |
| "추적만" (Phase 5 재개) | lint+build 그린 상태 + 머지 완료 | git status + 브랜치 상태 |
| "Phase N부터" | N-1 phase 산출물 (위 표 기준) | 위에 준함 |

2. 선행 산출물이 있으면 읽어 컨텍스트 복원:
   - 스펙 문서: 결정 사항·화면별 컴포넌트 매핑.
   - 플랜 문서: 태스크 체크박스(`- [ ]`/`- [x]`) + git log 로 완료/잔여 태스크 식별 → 다음 태스크부터.
   - `SCREENS.md`: 화면별 구현 현황 표.

3. **Phase 0 (키트 게이트)는 재개 시에도 생략하지 않는다** — 키트 신선도가 모든 phase 의 전제.
   `version-master.md` last sync 를 확인해 stale 이면 screen-kit 재실행 제안 후 계속.

---

## 게이트 운영 원칙

- 게이트는 **사용자 결정이 필요한 지점**이다 — 승인 요청을 진행 보고와 분리해 명확히 묻는다.
  게이트 사이에서는 "계속할까요?" 류 중간 확인을 하지 않는다.
- 게이트 밖 추가 질문이 허용되는 경우:
  - 구현 중 발견된 **정책 차이** (키트 ⚠️ 에 답이 없고 레포 동작을 바꾸는 결정)
  - `_shared/ui-catalog.md` 에 없는 컴포넌트가 필요한 경우 (카탈로그 추정 금지 → 사용자 확인 후 register_ui_components 권고)
  - 파괴적 작업, 범위 변경
- 사용자가 게이트에서 방향을 바꾸면 해당 phase 산출물을 수정 커밋하고 이후 phase 산출물은 무효 처리(재생성).

---

## 보고 포맷

### Phase 0 키트 게이트 보고

```
## Phase 0 키트 게이트 완료

키트 루트: docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
화면 집합: SCREEN-NNN, SCREEN-MMM, ... (N건)
last sync: YYYY-MM-DD / 신선도: OK (또는 ⚠️ stale — screen-kit 재실행 권고)

CHANGED: (해당 ITEM ID 목록 또는 없음)
RETIRED: (해당 ITEM·화면 목록 또는 없음) → 구현 대상 제외

ui_component 카탈로그: populated N건 (또는 ⚠️ 비어있음 — Phase 0.5 시드 필요)

→ 다음: (카탈로그 비어있으면 Phase 0.5 게이트 / 이미 populated 이면 Phase 1 공유 자산 셋업)
```

### Phase 전환 보고 (각 phase 종료 시)

한 단락 요약 + 다음 게이트 질문. 포맷:

```
## Phase N 완료 — {phase 이름}

산출물: {경로 또는 내용 한 줄}
주요 결정: {스펙/플랜/구현 중 확정된 사항}

→ [게이트 N] {게이트 질문}
```

### Phase 4 화면별 구현 현황 표 (진행 중·완료 시 갱신)

| 화면 | 상태 | 사용한 ui_component | IMPREC 기록 | 운영 전 확인 잔여 |
|---|---|---|---|---|
| SCREEN-NNN | 완료 / 진행중 / 대기 | UI-001·UI-003·UI-007 | IMPREC-NNN (created) | 없음 / [수동 절차 N건] |
| SCREEN-MMM | 완료 | UI-002·UI-005 | IMPREC-MMM (created) | API 계약 확인 필요 |

- 상태 값: `대기` / `진행중` / `완료` / `제외(RETIRED)`
- IMPREC 기록: Phase 5 전에는 `(미생성)`, Phase 5 후에는 `IMPREC-NNN (created)`
- 운영 전 확인 잔여: 키트 ⚠️ spec-pending 항목·수동 절차·미결 계약 변경

### 최종 보고 (Phase 5 완료)

```markdown
# {DOMAIN-ID} {도메인명} 화면 구현 완료

## 결과
- 브랜치/머지: {feature/{slug} → 방식} / 빌드: lint+build 그린 / 커밋: N건
- 구현 화면: N건 완료 (SCREEN-NNN, SCREEN-MMM, ...) / 제외(RETIRED): N건

## 화면별 구현 현황
(위 현황 표 최종본)

## logicraft 추적
- IMPREC: N건 생성 (implemented: N / in_progress: N)
- 역링크: link_ui_component_to_module N건 (UI-NNN ↔ MOD 경로)
- 커버리지: get_implementation_coverage 기준 code N건

## 구현 중 확정 사항 (→ mc-logi-update 권고)
- (설계 ↔ 현실 차이와 채택한 결정, 키트/스펙 근거)
- (없으면 "없음")

## 운영 전 확인
- (키트 ⚠️ spec-pending·수동 절차·미결 계약 변경 잔여 목록)
- (없으면 "없음")
```

---

## 이 스킬이 하지 않는 것

- logicraft 설계 ITEM 의 data 수정 (→ mc-logi-update)
- 키트 생성·동기화 자체 (→ mc-logi-screen-kit 호출로 위임)
- Phase 0.5 외 phase 에서의 logicraft 쓰기 (0·1·2·3·4 는 read 또는 레포 코드 작업만)
- 도메인 갭 검출 (→ mc-logi-domain-review)
- 키트 없이 "기억"으로 구현 — 키트가 없고 만들 수도 없으면 중단
- `_shared/ui-catalog.md` 에 없는 ui_component ID 를 임의로 사용 (카탈로그 외 추정 금지)
