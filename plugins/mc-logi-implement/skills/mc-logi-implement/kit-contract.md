# kit-contract.md — 키트 ↔ phase 데이터 계약

이 스킬이 도메인 지식을 얻는 **유일한** 출처는 mc-logi-implement-kit 산출물이다.
키트 구조(implement-kit 의 산출 규약)와 각 파일에서 무엇을 읽어 어느 phase 에 주입하는지를 정의한다.
키트 포맷이 바뀌면 이 파일만 갱신하면 된다.

## 키트 구조 (입력 계약)

```
docs/design/{slug}-{DOMAIN-ID}/
├── IMPLEMENTATION.md        ← 바이브코딩 진입점 (빌드 순서·의존 그래프·제약·현황·⚠️불일치)
├── version-master.md        ← 버전 마스터 (last sync, ITEM 표, changelog: NEW/CHANGED/RETIRED)
├── _domain.md               ← 도메인 경계 (책임/책임 제외/설계 원칙/ubiquitous language/brownfield)
├── {type}/{ID}.md           ← ITEM 구현지향 요약 (frontmatter: version/stale/status/links)
├── {type}/_raw/{ID}.json    ← logicraft 원본 (요약이 모호하면 원본 확인)
└── _retired/                ← 폐기 ITEM (구현 금지 — 코드 제거 검토 대상)
```

## Phase 0 적재 목록 (메인 컨텍스트로 읽음)

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| IMPLEMENTATION.md | 전체 — 구현 대상 영역 표 / 빌드 순서 / 의존 그래프 / 구속 제약 표 / 구현 현황 / "주의 — 데이터 불일치(⚠️)" 섹션 | 모든 phase 의 골격 |
| _domain.md | 책임·책임 제외(보존/위임 경계) / 핵심 설계 원칙 / brownfield 정책 / 외부 의존 | 스펙의 불변 규칙 (인용 출처) |
| version-master.md | 헤더(last sync·세션) + 직전 changelog 의 CHANGED/RETIRED | 신선도 게이트 / 재반영 범위 |

## Phase 별 추가 참조 (필요 시 해당 파일만)

| phase | 키트 출처 | 용도 |
|---|---|---|
| 1 스펙 | `adr/*.md` 의 "구현 영향" / `nfr/*.md` 의 강제사항 | 스펙 불변 규칙·예산 (ID 인용) |
| 1 스펙 | `code_module/*.md` (기구현 모듈) | 레포 실코드와 매칭 → 재사용·위임 지점 확정 |
| 1 스펙 | frontmatter `stale`·본문 spec-pending 표기 | 사용자 결정 질문 후보 |
| 2 플랜 | `erd/*.md`(DDL·컬럼) `migration_plan/*.md`(forward/rollback 원문·검증 절차) | 데이터 계층 태스크 — **원문 집행 기준** |
| 2 플랜 | `api_endpoint/*.md`(계약 표) `domain_feature/*.md`(비즈니스 규칙) `diagram_sequence/*.md`(호출 순서) | 태스크별 구현 명세 + 참조 경로 |
| 2 플랜 | `permission_role/*.md`(권한·data scope) `constant/*.md`(실값) | 인가·설정 태스크 |
| 3 구현 | 태스크별 ITEM 요약 경로 (플랜에 명시된 것) | 구현자/스펙리뷰어 프롬프트에 전달 |
| 3 구현 | `acceptance/*.md` `use_case/*.md` (Given/When/Then) | 테스트 직역 + AC 통합 검증 |
| 4 반영 | `migration_plan/*.md` 의 pre/post 검증 절차 | DB 적용 절차 |
| 5 추적 | version-master ITEM 표 (구현한 ITEM ID 목록) | IMPREC 대상 식별 |

## 해석 규칙

1. **⚠️ 표기 우선순위**: 키트 요약이 ⚠️ 로 명시한 불일치(예: "forward_ddl 원문이 집행 기준",
   "인덱스 컬럼명 정정 필요")는 그 지시를 그대로 따른다. 키트가 답을 안 줬으면 사용자에게.
2. **deprecated/retired ITEM**: `_retired/` 와 frontmatter status, version-master 의 표기를 따라
   **구현하지 않는다**. 다운로드됐지만 "logicraft상 deprecated" 배너가 있는 ITEM 도 동일
   (테스트화·코드화 제외).
3. **요약 vs 원본**: 요약(.md)으로 부족하면 `_raw/{ID}.json` 을 연다 — 단 거대한 JSON 은
   서브에이전트/Bash 파싱으로 (메인 컨텍스트 오염 방지).
4. **키트 ≠ 코드 현실**: 키트는 설계의 스냅샷이다. 레포의 실코드·실DB 와 다르면 그것은 오류가
   아니라 **발견**이다 — 실측으로 확정하고, 결정을 스펙 "구현 중 확정" 단락과 IMPREC 노트에
   기록하며, mc-logi-update 권고 목록에 올린다 (설계를 현실에 맞출지 코드를 설계에 맞출지는
   사용자/키트 정책의 몫).
5. **스킬에 도메인 지식 금지**: 이 계약 파일을 포함해 스킬 어디에도 특정 프로젝트의 규칙
   (보존 정책·롤코드·DBMS 등)을 적지 않는다. 그런 내용이 필요해지면 키트(또는 logicraft 설계)에
   넣을 일이지 스킬에 넣을 일이 아니다.
