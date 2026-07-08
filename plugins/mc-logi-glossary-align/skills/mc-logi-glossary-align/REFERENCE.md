# REFERENCE — mc-logi-glossary-align 함정·노하우 상세

Session 95 (D001 ERD-005) 실측 기반. 각 항목은 발견 컨텍스트 + 회피/대응 패턴.

---

## 1. 등록 순서 위반 함정

**증상**: 용어 등록 시 word_id unresolved 에러.
**원인**: 단어 미등록 상태에서 `program_glossary_create(word_ids=[...])` 호출.
**대응**: Phase 3 절차 강제 — 도메인 → 단어 → 용어. `suggest_term_from_words` 의 unresolved 0 검증 통과 후만 용어 등록.

## 2. E_CONFLICT 핸들링 (단어)

자주 겹치는 사전 단어 (program 사전에 이미 있음):
- 카테고리 (195)
- IP (287)
- 초 (384) — ⚠️ is_format_word=false 상태일 수 있음
- 주기 (224)
- 플랫폼 (347)
- 범위 (379)
- 승인 (182)

**대응**: 무조건 program_word_create 호출 전에 `program_word_search(word_ko=X, word_en_abbr=Y)` 로 사전 점검. 있으면 id 재사용.

## 3. is_format_word 보정 패턴

"초"(SEC), "건수"(NOCS), "율"(USGRT) 같은 형식단어가 일반단어로 등록되어 있을 수 있음.

```
program_word_update(
  word_id=384,
  is_format_word=true,
  default_domain_classification="수"  # 한글 분류명
)
```

`default_domain_classification` 은 **한글 분류명**(수/명/연월일시분초/율/여부/코드/내용 등). 영문 코드 ❌.

## 4. KLID-BM 표준용어정의서 충돌 (Q6)

이미 KLID-BM 사업 표준에 박힌 용어 4건 패턴 (D001 사례):
- 전송속도 (880, TRSM_SPD)
- 정렬순서 (896, SORT_SEQ)
- 요청일시 (796, **DMND_DT**) ← 우리 계획 RQST_DT
- 완료일시 (793, **CMPT_DT**) ← 우리 계획 CMPL_DT

**Q6 질문 필수**: 영문 약어 차이 시 (1) KLID-BM 표준 → ERD 영문 rename, (2) ERD 유지 + 의미 매핑만 중 사용자 결정.

## 5. ERD update_item patch ops 패턴

```yaml
data_mode: patch
patch_ops:
  - op: set
    path: tables[name=relay_servers].columns[name=created_at].field
    value:
      name: crt_dt
      type: TIMESTAMP
      logical_column_name: 생성일시
      ...
```

**함정**:
- `data_mode: merge` 는 top-level replace, omit 시 default 리셋 → patch ops 권장
- selector path 는 단일 객체까지 끝남 (`...columns[name=Y]` 까지가 아니라 `.field` 까지)
- responses[키] 인덱싱 미지원 → 전체 set 으로 우회
- `[-]` add 별칭은 array 만 (object key 추가는 set)

## 6. base_version 추적 (2-Round Split)

영문 rename 작업은 2 round 로 atomic:
- Round 1: logical_column_name patch (예: 73 ops)
- Round 2: 영문 컬럼 rename + name + type 동시 patch (예: 12 ops)

각 round 후 `get_item` 으로 current_version 확인 후 다음 round base_version 입력.

## 7. analyze_impact 한계

`analyze_impact(target_erd_id, depth=3)` 는 **graph-link 만** 감지.

감지 가능: ERD ↔ MIG, ERD ↔ RISK, ERD ↔ INFRA, ERD ↔ LEGACY, ERD ↔ DOMAIN.

**감지 못함** (semantic cascade — grep 필수):
- DFEAT.persists_in_tables 본문 인용
- API payload schema / example / responses 인용
- SCREEN binding (sections·components)
- SEQ messages 본문
- AC scenario 본문
- CDIAG attributes
- RUNBOOK / RISK 본문

→ logi-update-specialist 위임으로 처리.

## 8. specialist 위임 패턴

```
Agent(
  subagent_type=logi-update-specialist,
  prompt=self-contained:
    - target_id, item_type
    - edit_intent ("영문 rename cascade")
    - rename 매핑 표 전체 (12건 그대로)
    - AI 추정 금지 명시 ("본문 grep 후 실제 인용만 patch")
    - YAML 결과 + cascade_candidates 보고
)
```

**동시 ≤3건 안정**. 4~5건 동시 시 소켓 끊김 1~2건 (재실행 필요).

specialist 결과 분류:
- patch 적용 (실제 인용 있음)
- ack-only (인용 없음, 책임영역 분리)
- 부분 실패 (소켓 끊김 등, 재실행)

ack 비율 ~50% 정상.

## 9. ERD-001 deprecated STALE warning

`get_item` 결과에 ERD_MAPPING_STALE_COLUMN / STALE_TABLE_REF warning 나옴.

**원인**: ERD-001(논리 페어)이 Session 93 에서 deprecated. graph 부작용.

**대응**: benign, 무시. ERD-005 (물리+논리 통합본) 만 작업 대상.

## 10. SCREEN cascade 특성

SCREEN 은 한글 라벨 + API 식별자 위주 → 영문 컬럼명 직접 노출 적음.

- 한글 라벨만 인용 → ack
- 단 1건 컬럼 헤더 (`downloaded_at (PULL)` 같은) → patch + static_render 재업로드 필요

→ static_render 재업로드는 본 라운드와 분리 (잔여 sweep).

## 11. API payload schema vs ERD column 분리

API request/response 필드명은 별 네임스페이스 (API 계약).

- 대부분 API: DB 컬럼 rename ≠ API 필드 rename (자동 변환 없음)
- 일부 API (예: API-235): schema 필드를 ERD 컬럼명 그대로 사용 → 정합 필요 (큰 patch)
- 응답 필드가 컬럼 직접 노출 안 함 (예: `last_metric_received_at` 같은 별 명칭) → 정합 불요

specialist 가 본문 grep 으로 판단.

## 12. MIG forward_ddl 동반 수정

영문 rename Round 2 시 동반 갱신:
- MIG-{ERD}.forward_ddl (실제 DDL ALTER 문장)
- MIG-{ERD}.brownfield.diff_summary (변경 요약)

MIG in-place ADD 시점에 표준 약어로 정의 → 1차 보존 원칙 저촉 0 (D001 사례).

## 13. 도메인별 책임 영역 분리

DFEAT 별로 책임 테이블이 다름:
- DFEAT-045 = event_types/event_type_mappings 책임
- DFEAT-001 = relay_servers 책임

→ 무차별 cascade 회피. specialist prompt 에 책임 영역 명시 (rename 매핑 표 에 테이블별 묶음).

## 14. 9 md 산출물 표준 템플릿

| 파일 | 필수 섹션 |
|---|---|
| README.md | 작업 개요 / 5단계 절차 / 도구 매트릭스 / 디폴트 결정 (Q1=A·Q2=유지·Q4=일괄·Q5=권장) / 진행 상태 |
| 01_현황요약.md | 컬럼 총수·A/B/C 분류 통계·gov compliance 전후·통합 coverage 전후·핵심 발견 |
| 02_A_영문표준약어_정합.md | A 그룹 rename 매핑 표 (테이블·컬럼·현재 → 변경 후·gov_term_id) |
| 03_B_사업용어_정합.md | B 그룹 logical 정합 표 (테이블·컬럼·logical·기존 term_id) |
| 04_C_신규등록_계획.md | C 그룹 서브카테고리별 (보안/운영/영상/이벤트/액션/도구/메타) |
| 05_신규단어_목록.md | 단어 신설 후보 (W## 가배정·en_abbr·도메인 분류·is_format_word) |
| 06_결정필요.md | Q3 동의어 / Q6 KLID-BM 충돌 항목 + 사용자 답 기록 |
| 07_등록단어_ID매핑.md | Phase 3 후 채움 (실제 word_id·기존 활용 vs 신규) |
| 08_등록용어_ID매핑.md | Phase 3 후 채움 (실제 term_id·기존 활용 vs 신규) |

## 15. 종료 후 메모리 저장 패턴

```
~/.claude/projects/{project-slug}/memory/
  session_NN_{domain}_glossary_alignment_{YYYYMMDD}.md
```

내용:
- 사용자 요청 흐름 (Phase 별)
- 통계 (단어 N·용어 M·ERD vX→vY·patch R건)
- 결정 사항 (Q3/Q6 사용자 답)
- 노하우 발견 (새로 추가된 함정)
- 잔여 작업

MEMORY.md 인덱스 1줄 추가 (≤200자):

```markdown
- ★★★★★ [Session NN D{NNN} ERD-XXX 용어사전 정합 — 단어 N·용어 M·... (YYYY-MM-DD)](session_NN_d{NNN}_glossary_alignment_{YYYYMMDD}.md) — ...
```