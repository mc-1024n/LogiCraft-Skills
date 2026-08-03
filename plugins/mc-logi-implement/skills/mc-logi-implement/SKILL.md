---
name: mc-logi-implement
description: mc-logi-implement-kit 이 만든 로컬 구현 키트(./docs/design/{slug}-{DOMAIN-ID}/)를 단일 진실원으로 삼아, 도메인 구현을 스펙→플랜→TDD구현→반영→logicraft 추적까지 phase 게이트로 완주하는 오케스트레이터 스킬. 사용자가 "D005 구현해줘", "키트대로 구현하자", "구현 계획 세우고 구현까지", "DOMAIN-003 구현 시작", "/mc-logi-implement" 등 logicraft 도메인의 실제 코드 구현을 요청할 때 실행. 키트가 없으면 mc-logi-implement-kit 을 먼저 호출하고, 키트가 stale 이면 재동기화부터 한다. 도메인 규칙(보존 정책·제약·빌드 순서)은 스킬에 없고 전부 키트에서 읽는다. phase 인자로 중단 지점부터 재개 가능 ("플랜부터", "구현만", "추적만"). ★ 이 스킬은 **백엔드·도메인 기능 위주 구현**(API·ERD/DB·domain_event·service·NFR)이며, **프론트엔드 화면(screen_spec) 구현은 `mc-logi-screen-implement` 가 담당**한다. 범위에 화면이 포함돼 있어도 화면을 직접 구현하지 않고, Phase 0 에서 사용자에게 화면은 screen-implement 로 진행하라고 안내한 뒤 기본 제외한다(중복 구현 방지). ★ 구현 코드 주 seam 에 `@design <ITEM-ID>` traceability 태그를 심어 코드↔설계 양방향 추적을 확보하고(원칙 7, IMPREC 짝), 설계 변경 시 `grep @design` 로 영향 코드를 기계적으로 발견한다.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.0"
  domain: logicraft-orchestration
  triggers: 키트 구현, 도메인 구현, 구현해줘, 키트대로 구현, 구현 계획, 구현 시작, D001 구현, DOMAIN-XXX 구현, 스펙 플랜 구현, 구현 추적, implement
  role: orchestrator
  scope: logicraft-domain-implementation
  output-format: feature 브랜치 코드 + 스펙·플랜 문서 + IMPREC 구현 추적 + 키트 현황 갱신
  related-skills: mc-logi-implement-kit, mc-logi-screen-implement, mc-logi-update, mc-logi-implement-review, mc-logi-domain-review
---

# mc-logi-implement — 키트 기반 구현 오케스트레이터

logicraft 도메인의 로컬 구현 키트를 읽고, **스펙 → 플랜 → TDD 구현 → 반영 → logicraft 추적**을
phase 게이트로 완주한다. 이 스킬은 **절차만** 안다 — 무엇을 보존하고, 어떤 순서로 쌓고, 어떤 제약을
지킬지는 전부 키트가 말한다.

## 핵심 원칙

1. **키트가 단일 진실원** — 도메인 규칙·제약·빌드 순서·보존 정책을 이 스킬에 하드코딩하지 않는다.
   `kit-contract.md` 의 매핑대로 키트 파일에서 읽어 각 phase 에 주입한다. 키트에 없는 도메인 지식을
   임의로 지어내지 않는다 (모르면 사용자에게).
2. **mc-logi-implement-kit 선행 종속** — 키트가 없으면 그 스킬을 먼저 실행하고, 키트가 오래됐으면
   SYNC 재실행을 먼저 한다. 키트의 version-master 가 CHANGED 를 보고하면 변경분 검토 없이
   구현을 진행하지 않는다.
3. **phase 게이트** — 스펙 승인 / 플랜 승인 / 머지 방식, 세 지점에서 사용자 확인을 받는다.
   그 사이는 자율 진행 (subagent-driven 연속 실행).
4. **추적 역동기화 의무** — 구현이 끝나면 logicraft `create_implementation_record` 로 IMPREC 를
   남기고 키트의 구현 현황을 갱신한다. 키트(read-only 산출물)와 달리 이 스킬은 logicraft 에
   **구현 기록 쓰기만** 한다 (설계 ITEM data 수정은 안 함 — 그건 mc-logi-update).
5. **superpowers 재사용** — 스펙은 `superpowers:brainstorming`, 플랜은 `superpowers:writing-plans`,
   구현은 `superpowers:subagent-driven-development` 를 그대로 쓴다. 이 스킬은 그 사이에
   "키트 컨텍스트 주입"과 "logicraft 왕복"을 접착한다.
6. **★ 백엔드·도메인 기능 위주 — 화면 구현은 분리** — 이 스킬은 **백엔드/도메인 로직**
   (api_endpoint·erd→DB·domain_event·service·nfr·infra 등) 구현을 담당한다. **프론트엔드 화면
   (screen_spec) 구현은 `mc-logi-screen-implement`** 가 담당한다(전용 화면 키트 `docs/screen-design/` 기반,
   DS 토큰·ui_component·와이어프레임·디자인 시안 소비). implement-kit 번들에 screen_spec 이 포함돼 있어도
   **이 스킬은 화면을 직접 구현하지 않는다.** Phase 0 에서 범위에 화면이 있으면 사용자에게
   "화면은 mc-logi-screen-implement 로 진행" 이라고 **안내하고 기본 제외**한다. **자동 중복 방지 장치는
   없으므로**(두 경로가 같은 screen_spec 을 각자 구현할 수 있음) 범위 분담을 명시적으로 처리한다.
   권장 순서: 화면은 screen-implement(목업·컴포넌트·라우팅) → 이 스킬이 백엔드(API/DB/이벤트) → 연동.
7. **★ 코드↔설계 traceability 태그 (in-code — 원칙 4 IMPREC 의 역방향 짝)** — 구현하는 코드 seam 에
   그것이 실현하는 키트 ITEM ID 를 코드 안에 심어 **코드→설계** 방향을 남긴다. IMPREC(logicraft, 설계→코드)와
   짝을 이뤄 양방향 traceability 를 **구현 순간에 부산물로** 확보한다. 사후 별도 작업이 아니다.
   - **형식(기본)**: Javadoc 태그 `@design API-259, ADR-080, AC-045` — ITEM ID 콤마 구분.
     정규식 `(ADR|API|SVC|IAPI|LIB|DP|CONST|DFEAT|UC|AC|SEQ|ERD|INT|MOD|NFR|EVT|ROLE|PMAN|SETT)-\d+` 로 전 소스 추출 가능해야 한다
     (경계 계약 4종 API/SVC/IAPI/LIB + 파이프라인 DP + 데스크톱 PMAN/SETT 포함 — prefix 는 서버 `ID_PREFIX` 가 진실원,
     새 타입 추가 시 이 정규식도 함께 갱신).
   - **대상 = 주 seam 만**: 컨트롤러 메서드 → 실현 API, 서비스 클래스/메서드 → DFEAT/UC, 엔티티/필드 →
     ERD/CONST. 헬퍼·getter/setter·DTO 잡필드는 태그하지 않는다(잡음 방지). 한 요소에 그 요소가
     **직접 실현하는** ITEM 만.
   - **강제 검증 옵션**: 팀이 원하면 `@DesignRef({"API-259"})` 어노테이션(`@Retention(SOURCE)`,
     런타임/WAR 무영향)으로 승격 + annotation processor 로 dangling ID 빌드 검증. 기본은 Javadoc 태그.
   - **★ 어노테이션 형식 채택 시 타입 부트스트랩 (없으면 생성)**: `@DesignRef` 를 쓰기로 하면 코드에 달기
     **전에** 레포에 타입 존재를 확인하고(`grep -rl '@interface DesignRef' src`), **없으면 1회 생성**한다 —
     타입 없이 어노테이션만 달면 컴파일 실패하므로 필수 선행. canonical 정의(레포 패키지 규칙에 맞춰 배치,
     예 `.../common/annotation/DesignRef.java`):
     ```java
     @Retention(RetentionPolicy.SOURCE)          // 컴파일 후 폐기 = WAR·런타임 무영향
     @Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
     public @interface DesignRef { String[] value(); }
     ```
     부트스트랩 자체가 부담되거나 사용자가 원치 않으면 **기본 Javadoc 태그로 진행**(파일 생성 없이).
   - **목적**: ① 설계 변경 시 `grep @design <ITEM-ID>` 로 영향 코드를 **기계적으로 전량 발견**(Phase 0
     신선도 게이트) ② Phase 5 에서 IMPREC 와 대조해 편측 링크/미추적 검출.
   - ⚠️ **런타임·빌드 무영향**(주석 또는 SOURCE 리텐션). strict doclint 경고가 걸리면 라인주석
     `// [design: API-259, ADR-080]` 대안 허용(추출 정규식 동일). 이 스킬은 **신규/수정 코드에만** 태그하고,
     레거시 백필은 강제하지 않는다(점진적).

## Phase 개요

```
Phase 0  키트 게이트     키트 존재/신선도 확인 → 없으면 implement-kit 호출, stale 이면 SYNC
Phase 1  스펙           키트 컨텍스트 + 레포 탐색 → brainstorming → 스펙 문서 → [게이트: 승인]
Phase 2  플랜           writing-plans (키트 빌드 순서 = 태스크 순서 기본값) → [게이트: 승인]
Phase 3  구현           feature 브랜치 + subagent-driven (태스크별 스펙리뷰→품질리뷰) + 최종 전체 리뷰
Phase 4  반영           전체 테스트·빌드 → (지시 시) DB 적용 → [게이트: 머지 방식] → 머지
Phase 5  추적           IMPREC 기록 + 키트 현황 갱신 + mc-logi-update 권고 목록 + 메모리 문의
```

재개: 사용자가 phase 를 지정하면 (예: "플랜부터", "Phase 3 부터", "추적만") 해당 phase 의
선행 산출물(스펙/플랜 문서) 존재를 확인하고 그 지점부터 진행한다. 선행 산출물이 없으면
어느 phase 부터 시작할지 보고 후 확인.

---

## Phase 0 — 키트 게이트 (선행 종속)

1. **대상 식별**: 도메인 ID(D005/DOMAIN-005)·프로젝트를 인자/대화/메모리에서 확정.
   불명확하면 질문.
2. **키트 탐색**: `docs/design/*-{DOMAIN-ID}/IMPLEMENTATION.md` 존재 확인.
   - **없음** → `Skill(mc-logi-implement-kit)` 를 먼저 실행해 키트 생성 (사용자에게 선행 실행을
     알리고 진행). 생성 후 본 스킬 계속.
   - **있음** → `version-master.md` 의 last sync 시각 확인. logicraft 접근이 가능하고
     ① 마지막 sync 가 오래됐거나 ② 사용자가 "최신으로" 류 요청을 했으면 implement-kit 을
     SYNC 모드로 재실행 권고 (간단 확인 후 실행). SYNC 결과 **CHANGED/RETIRED 가 있으면
     그 목록을 사용자에게 보여주고 구현 범위에 미치는 영향을 정리한 뒤** 진행.
     - **영향 코드 발견(원칙 7 태그 활용)**: CHANGED 된 ITEM 마다 `grep -rl '@design.*<ITEM-ID>' src`
       (라인주석 형식 포함) 로 **재반영 대상 코드를 기계적으로 전량 수집** → 영향 정리에 첨부.
       태그가 아직 없는 레거시 영역은 키트 `code_module`(MOD-*)/IMPREC 로 보완 추정(불완전함을 명시).
3. **키트 컨텍스트 적재**: `kit-contract.md` 의 "Phase 0 적재 목록"을 읽는다 —
   IMPLEMENTATION.md 전체, _domain.md, version-master 헤더. 여기서 얻는 것:
   구현 대상 영역 표 / 빌드 순서 / 의존 그래프 / 구속 제약 / 보존·경계 정책 / 키트 ⚠️ 불일치 목록 /
   구현 현황(이미 구현된 영역 — 재구현 방지).
4. **이미 구현된 영역 감지**: 키트 구현 현황과 logicraft `get_implementation_coverage(scope=domain)` 로
   기구현 ITEM 을 식별 — 이번 범위에서 제외하거나 "재구현/수정" 인지 사용자에게 확인.
5. **★ 화면(screen_spec) 범위 분리 안내 (중복 구현 방지 — 런타임 필수 안내)**: 키트/도메인 범위에
   `screen_spec` 이 포함돼 있으면, 사용자에게 다음을 **명시적으로 안내**한다:
   > "이 스킬은 **백엔드·도메인 위주**입니다. **화면(SCREEN-NNN) 구현은 `mc-logi-screen-implement`**
   > (화면 키트 `docs/screen-design/`) 가 담당하니, 화면은 이번 구현 범위에서 **제외**합니다.
   > (화면을 여기서 함께 구현하길 원하시면 말씀해 주세요.)"
   - 기본 동작: screen_spec 을 이번 구현 범위에서 **제외**(빌드 순서·플랜 태스크에 화면 빌드 미포함).
     남은 백엔드/도메인 ITEM(경계 계약 4종 api_endpoint·service_interface·module_api·library_api ·
     erd·domain_event·data_pipeline·service·nfr·permission_manifest·settings_schema 등)만 대상으로 진행.
   - 사용자가 "화면도 여기서" 라고 **명시**한 경우에만 화면을 포함(그땐 screen-implement 와 중복되지
     않도록 어느 경로가 소유하는지 확정).
   - 화면이 screen-implement 로 이미 구현됐으면(IMPREC/coverage 로 확인) 그 사실을 보고에 반영.

## Phase 1 — 스펙 (brainstorming 위임 + 키트 주입)

`superpowers:brainstorming` 을 호출하되, 다음을 키트에서 가져와 출발점으로 쓴다:

- **탐색 컨텍스트**: 레포 구조·컨벤션은 Explore 에이전트로 실측한다 (빌드 도구/계층/응답 래퍼/
  테스트 인프라 유무). 키트의 "보존 영역·기존 모듈(code_module 요약)"과 실코드를 매칭해
  **위임 지점**(재사용할 기존 클래스)을 확인한다 — 키트는 설계를 말하고, 코드의 현재 모습은
  레포가 말한다. 둘이 다르면 그 자체가 스펙에 기록할 발견이다.
- **질문 후보**: 키트가 미확정으로 표기한 것들이 곧 사용자 결정 사항이다 — 예: spec-pending
  외부 연동(stub 로 갈지/제외할지), 마이그레이션 적용 방식, 테스트 수준, 구현 범위(영역 전체 vs 단계).
  키트가 이미 답을 가진 것(빌드 순서, 제약)은 묻지 않는다.
- **스펙 작성 규칙**: 모든 요구·제약·불변 규칙에 **키트 ITEM ID 와 파일 경로를 인용**한다
  (예: "1차 보존 — `_domain.md` 책임 제외 / ADR-014 구현 영향"). 스킬이 아니라 키트가 근거다.
  키트 ⚠️ 불일치는 키트가 명시한 우선순위(예: "forward_ddl 이 집행 기준")를 그대로 스펙에 옮긴다.
- 스펙 저장: `docs/superpowers/specs/YYYY-MM-DD-{slug}-design.md` + 커밋.

**[게이트 1]** 사용자 스펙 승인 후 Phase 2.

## Phase 2 — 플랜 (writing-plans 위임)

`superpowers:writing-plans` 를 호출하되:

- **태스크 순서 = 키트 빌드 순서** (IMPLEMENTATION.md §빌드 순서)를 기본값으로. 테스트 인프라가
  레포에 없으면 Task 0 으로 신설을 추가.
- **각 태스크에 키트 참조를 명시**: 그 태스크가 구현하는 ITEM 의 요약 파일 경로
  (예: `docs/design/.../api_endpoint/API-047.md`)와 검증 근거 AC 경로를 Files 섹션 옆에 적는다.
  구현 서브에이전트가 키트 원문을 직접 읽을 수 있어야 한다.
- DDL·계약 등 "원문 보존" 산출물은 키트의 해당 파일에서 **원문 그대로** 가져오도록 지시한다
  (의역 금지 — 키트가 명시한 집행 기준 따름).
- 플랜 저장: `docs/superpowers/plans/YYYY-MM-DD-{slug}.md` + 커밋.

**[게이트 2]** 플랜 승인 + 실행 방식(서브에이전트/인라인) 선택 후 Phase 3.

## Phase 3 — 구현 (subagent-driven 위임 + 키트 전달)

`superpowers:subagent-driven-development` 로 실행하되:

- main 직접 작업 금지 — `feature/{slug}` 브랜치 생성.
- **구현자 프롬프트에 포함할 것**: 플랜의 해당 태스크 전문 + 그 태스크의 키트 ITEM 요약 경로 +
  스펙의 관련 불변 규칙(키트 인용 포함). 구현자가 "왜"를 키트에서 확인할 수 있게 한다.
- **★ traceability 태그 지시 (원칙 7)**: 구현자에게 각 태스크가 실현하는 키트 ITEM ID 를 코드
  **주 seam** 에 `@design <ITEM-IDs>` (Javadoc, 콤마 구분) 로 심도록 지시한다. 태스크의 키트 참조
  (플랜 Files 옆 ITEM 경로)가 곧 태그할 ID 다 — 컨트롤러 메서드=API, 서비스=DFEAT/UC, 엔티티/필드=ERD/CONST.
  헬퍼·getter 은 제외. (팀이 `@DesignRef` 어노테이션을 채택했으면 그 형식으로 — 이때 **원칙 7 의 타입
  부트스트랩**: 코드에 달기 전 `@interface DesignRef` 존재 확인, 없으면 canonical 정의로 1회 생성.)
- **리뷰어 프롬프트에 포함할 것**: 스펙 리뷰어에게는 키트 계약(API .md 의 계약 표, AC 의
  Given/When/Then)을 대조 기준으로 제공 + **`@design` 태그 누락/오참조(실현 ITEM 과 불일치) 점검**을
  체크 항목에 포함. 품질 리뷰어는 통상대로.
- **키트 ↔ 실코드 불일치 발견 시** (구현 중 가장 흔한 사건):
  1. 키트에 ⚠️ 우선순위가 있으면 따른다.
  2. 없으면 — 실측(코드/DB)이 이긴다는 보장이 없으므로 **중단하고 컨트롤러(메인)가 판단**:
     레포의 기존 동작을 깨는 변경인지로 가르고, 사용자 결정이 필요한 정책 차이면 게이트 밖이라도 묻는다.
  3. 어느 쪽이든 결정 사항을 **스펙 문서에 "구현 중 확정" 단락으로 추가 커밋**하고,
     Phase 5 의 mc-logi-update 권고 목록에 적재한다 (logicraft 설계가 현실과 달랐다는 발견이므로).
- 모든 태스크 후 **최종 전체 리뷰** 1회 (브랜치 분기점 대비 전체 diff — 스펙 커버리지·보존 영역
  무결성·통합 정합·잔여 표식). Critical/Important 는 수정 후 종료.

## Phase 4 — 반영

1. 클린 전체 테스트 + 빌드 (`clean test` + 패키징) 그린 확인.
2. **DB/인프라 적용은 사용자가 지시·접속정보를 제공한 경우만** — 적용 전 검증(pre), 적용,
   사후 검증(post — 키트 마이그레이션 ITEM 의 검증 절차 따름). 적용 중 실패하면 원인을 실측으로
   진단하고(예: charset/collation), 수정은 산출물에 반영해 커밋.
3. **[게이트 3]** 머지 방식 확인 (main 머지 / 브랜치 유지 / PR) 후 실행.
   운영 전 확인 필요 사항(키트가 spec-pending·수동 적용으로 표기한 것)을 머지 보고에 명시.

## Phase 5 — 추적 역동기화

1. **IMPREC 기록**: 구현된 design ITEM 별로 `create_implementation_record`
   (status=implemented/in_progress, progress, 커밋 해시, 구현 노트 — 잔여 작업과 "구현 중 확정"
   사항 포함). 부분 구현(stub·명세 대기)은 정직하게 in_progress + 잔여 명시.
   record 생성이 design ITEM 의 implementation 필드를 자동 동기화한다.
   - **★ 코드태그 ↔ IMPREC 양방향 정합 (원칙 7)**: `grep -rn '@design' src`(라인주석 포함) 로 심은
     태그를 수집해 IMPREC 기록과 대조 — ① IMPREC 엔 있는데 코드 태그 없음(편측 링크) ② 코드가 참조한
     ID 가 키트/logicraft 에 없음(dangling) 을 보고에 명시. 이번 구현 범위의 주 seam 이 전부 태그됐는지 확인.
2. **키트 현황 갱신**: IMPLEMENTATION.md 구현 현황 표 + "구현 완료 기록" 단락 (브랜치/커밋/
   운영 전 확인 사항) — 커밋. **프로젝트 CLAUDE.md 의 `mc-logi-kit` 블록**도 갱신
   (해당 도메인 행의 구현 현황 1줄 + `⚠️ 변경 N건 재반영 필요` 표식 해제 + 운영 전 확인 잔여 —
   implement-kit 의 `claude-md-block.md` 규약 따름).
3. **mc-logi-update 권고**: Phase 3 에서 적재한 "구현 중 확정/설계 불일치" 목록을 사용자에게
   제시 — logicraft 설계 ITEM 반영은 mc-logi-update 로 별도 진행 (이 스킬이 직접 설계를
   수정하지 않는다).
4. `get_implementation_coverage(scope=domain)` 로 도메인 커버리지 보고.
5. 메모리 저장 문의 (구현 중 확정된 프로젝트 사실 — 키트/레포가 기록 못 하는 것만).

## 에러·중단 처리

| 상황 | 대응 |
|---|---|
| 키트 없음 + logicraft 도 불가 | 중단 — 키트가 진실원이므로 키트 없이 구현하지 않음 |
| version-master CHANGED 다수 | 변경 요약 제시 → 사용자 확인 후 진행 (코드 재반영 범위에 포함) |
| logicraft 서버 일시 불가 (Phase 5) | 재시도 (생성 여부를 ID 조회로 확인해 중복 record 방지) → 계속 불가면 기록할 내용을 보고에 남기고 사용자에게 재실행 안내 |
| 구현 중 키트 자체 모순 발견 | 키트 ⚠️ 우선순위 → 없으면 사용자 → 결정을 스펙+IMPREC 노트에 기록 |
| 서브에이전트 BLOCKED | subagent-driven 스킬의 에스컬레이션 절차 따름 |

## 참조 파일

- `kit-contract.md` — **키트 ↔ phase 데이터 계약** (어느 키트 파일에서 무엇을 읽어 어느 phase 에
  주입하는지). Phase 0 진입 시 반드시 읽을 것.
- `phase-gates.md` — phase 별 산출물·게이트·재개 조건 상세 + 보고 포맷.

## 진입 멘트

"mc-logi-implement 시작합니다.

대상: `<DOMAIN-ID> <도메인명>` / 프로젝트: `<project>`
키트: `<경로>` (last sync `<시각>`, 모드 `<신선/SYNC 필요/없음→implement-kit 선행>`)
재개 지점: `<Phase 0~5>`
범위: **백엔드·도메인 위주** (API·DB·이벤트·서비스). 화면(screen_spec)은 `mc-logi-screen-implement` 담당 — 범위에 화면이 있으면 안내 후 기본 제외합니다.
traceability: 구현 코드 주 seam 에 `@design <ITEM-ID>` 태그를 심어 코드↔설계를 잇습니다(원칙 7, IMPREC 양방향 짝).

키트 게이트부터 진행합니다."
