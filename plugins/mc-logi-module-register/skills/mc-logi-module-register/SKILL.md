---
name: mc-logi-module-register
description: 구현된 실제 코드(컨트롤러·서비스·워커·엔티티·리포·config)를 logicraft code_module ITEM 으로 등록·정합시키는 오케스트레이터 스킬. 코드는 구현됐는데 logicraft code_module 에 안 잡히거나(미등록), 과거 등록됐지만 도메인 미연결(도구 업데이트 전 레거시 잔재)이거나, 코드에 없는 死모듈이 남아있는 상태를 도메인 단위로 해소한다. 사용자가 "코드모듈 등록해줘", "D002 코드모듈 정합", "구현한 클래스 logicraft 에 등록", "code_module 등록 검토", "코드↔logicraft 모듈 정합", "MOD 등록 누락 찾아줘", "/mc-logi-module-register <도메인>" 등을 요청하면 트리거. 코드 자산을 그래프에 인지시켜 다음 세션이 어느 클래스가 어느 API/DFEAT/CONST 를 구현하는지 탐색 가능하게 만든다. 검출(코드 스캔·갭 분석)은 자동이고, 등록은 갭을 보고한 뒤 코드 자산 전체를 기본 등록한다(매번 범위를 되묻지 않음 — 호출에서 명시적으로 한정한 경우만 좁힘). mc-logi-implement-review(코드↔키트 표류 검출)와 다름 — 이건 코드↔logicraft code_module ITEM 의 등록 자체를 정합.
metadata:
  version: 0.3.0
---

# mc-logi-module-register — 코드 ↔ logicraft code_module 등록 정합

구현된 실제 코드 클래스를 logicraft `code_module` ITEM 으로 빠짐없이 등록하고, 도메인 연결·상태(approved)·링크(ADR/CONST/SCREEN/MOD)를 정합시킨다. **검출은 자동(read-only 코드 스캔 + 갭 분석), 등록은 갭 보고 후 코드 자산 전체를 기본 등록**(범위를 매번 되묻지 않음 — 호출에서 명시적으로 한정한 경우만 좁힘).

## When to Use
- 도메인 구현이 한참 진행됐는데 logicraft code_module 이 코드 실태를 못 따라온 경우
- (레거시) 도구 업데이트 전 register_module 로 등록돼 도메인 미연결인 모듈을 `list_items(domain_id)` 에 잡히게 backfill
- 코드에 없는데 logicraft 에 남은 死모듈(폐기 설계 잔재) 정리
- 구현 완료 모듈을 draft→approved 로 일괄 확정

## When NOT to Use
- 코드 ↔ 키트(docs/design) 본문 표류 검출 → **mc-logi-implement-review**
- 설계 ITEM(ADR/ERD/API) 수정 → **mc-logi-update**
- 키트 다운로드 → **mc-logi-implement-kit**
- code_module 은 키트 Tier 범위 밖이라 본 스킬은 **logicraft 등록만** 한다 (docs/ 갱신·git 커밋 없음)

## ★ register_module 단일 패스 등록 (도구 업데이트 반영)
register_module 이 아래 파라미터를 지원하므로 **등록 한 번으로 도메인·상태·DFEAT/API 링크까지 완결**된다 (구 update_item 2-pass 제거):
- **`implements_domains: [{domain_id, responsibility, primary}]`** — 등록과 동시에 belongs_to_domain 엣지 생성 → `list_items(type=code_module, domain_id)` 필터에 **즉시** 잡힌다. (구 "등록 직후 update_item(domain_id) backfill" 불필요)
- **`status: "approved"`** — 구현 완료분은 바로 approved 등록 (구 draft→update_item 승격 불필요). 미지정 시 draft.
- **`realizes_domain_features: ['DFEAT-N']`** — 코드↔domain_feature 정식 그래프 링크 (구 description 텍스트 명시 대체)
- **`implements_apis: ['API-N']`** — 코드↔api_endpoint 정식 그래프 링크 (구 description 텍스트 명시 대체)
- 그 외: `realizes_features`(FEAT)·`realizes_screens`(SCREEN)·`consumes_constants`(CONST)·`based_on_adr`(ADR)·`depends_on_modules`(MOD)·`title`·`session_summary`.

→ **신규 등록 = register_module 단일 호출**로 도메인·상태·전 링크 완결. `update_item` 2-pass 는 **레거시(도구 업데이트 전 등록분)·기존 모듈 정리(死모듈 deprecated·draft 승격·도메인 backfill)** 에만 사용한다.

★ 잔존 주의:
- 링크 ID 오타 시 응답 `unresolved > 0` → 확인·수정.
- 도메인 연결은 `implements_domains` 로 한다(register_module 엔 `domain_id` 단독 파라미터 없음). `update_item` 의 `domain_id` 는 레거시 backfill 전용.

## 작업 정책 (logicraft 쓰기 정책 준수)
- 코드 스캔·logicraft 조회(list/get/find)는 **자동 OK**.
- ★ **등록 범위 기본 = 코드 자산 전체** (컨트롤러·서비스·워커·엔티티·리포·config·util 전부). **매번 범위를 묻지 않는다** — 갭을 보고한 뒤 바로 전체 등록한다. 코드 자산을 그래프에 빠짐없이 인지시키는 게 이 스킬의 목적이라, 부분 등록은 추적 구멍을 남긴다. **예외: 사용자가 호출에서 범위를 명시적으로 한정한 경우**(예 "컨트롤러·서비스만 등록", "TUS 모듈만")에만 그 범위로 좁힌다.
- 부수정리(domain 미연결 backfill · draft→approved 승격)는 **기본 수행**. 死모듈 deprecated 는 코드 부재를 Grep 으로 **확인한 뒤** 기본 수행(보고에 명시).
- 각 모듈 메타(file_path·역할·API/DFEAT 매핑·ADR·CONST)는 **코드 근거**로 채운다(파일 실재·실제 구현 기준). logicraft 에 없는 값을 상상해 채우지 말 것 — 모르면 비우고 보고에 명시.
- 등록 전 갭 표를 **보고**(투명성)하되, 범위 확정용 질문으로 멈추지 않는다. 실제 등록 내역·결과는 Phase 8 에서 표로 보고한다.

---

## 워크플로 (7 Phase)

### Phase 1 — 진입 + 도메인·프로젝트 식별
1. 사용자 입력에서 도메인 ID(`D002`/`DOMAIN-002`) 파싱. 없으면 `list_items(type=domain)` 로 매핑하거나 `AskUserQuestion`.
2. project_id 식별: `~/.claude/projects/*/memory/MEMORY.md` 또는 키트 frontmatter(`docs/design/{slug}-{ID}/_domain.md`)에서. 없으면 `list_projects` 제시.
3. 코드 루트 식별: cwd 가 코드 레포(또는 submodule 묶음 워크스페이스)인지 확인. 각 배포 모듈(submodule) 경로 파악.

### Phase 2 — logicraft 현재 code_module 카탈로그 (read)
```
list_items(type=code_module, domain_id=DOMAIN-XXX)   # 도메인 연결된 것 (active + retired)
list_items(type=code_module, limit=300)              # 전체 — domain 미연결인데 이 도메인 소속인 것 식별 (title/file_path/change_summary 로 판별)
list_orphan_code_modules(project_id)                 # realizes 링크 없는 고아 모듈
```
- **현재 등록 집합** 정리: {도메인 연결됨} / {등록됐으나 domain 미연결(backfill 대상)} / {retired}.
- changelog·MEMORY 에 "register됨" 언급된 MOD 가 domain_id 필터에 안 잡히면 → domain 미연결 후보.

### Phase 3 — 코드 클래스 전수 스캔 (Explore agent, read-only)
`Explore` 에이전트(또는 general-purpose)로 각 배포 모듈의 **2차/신규 구현 클래스**를 전수. 파일을 다 읽지 말고 Glob+Grep 로 클래스명·경로·어노테이션(@RestController/@Service/@Scheduled/@Entity/@Repository)·주요 @RequestMapping 만 빠르게 수집.
- 분류: 컨트롤러 / 서비스 / 워커·스케줄러 / 엔티티 / 리포 / config·util. 1차 보존 vs 2차 신규 구분.
- 각 클래스: 상대 file_path(배포모듈 prefix 포함) + export 명 + 역할 1줄 + 관련 API/DFEAT.
- 출력은 모듈별·종류별 구조화 목록. (프롬프트 골격은 `references/code-scan-agent.md` 참조)

### Phase 4 — 갭 분석 + 등록 계획 (★ 범위 묻지 않음)
코드 ↔ logicraft 대조로 3 버킷 산출:
1. **미등록** — 코드에 있는데 logicraft code_module 에 없음 (신규 register 대상)
2. **domain 미연결** — 등록됐으나 belongs_to_domain 없음 (backfill 대상)
3. **死모듈** — logicraft 에 있는데 코드에 없음 (deprecated 후보)
+ **draft 다수** — 구현 완료인데 status=draft (approved 승격 후보)
+ **정식 링크 미비** — 도구 업데이트 전 등록분에 `implements_apis`/`realizes_domain_features` 가 비어 있음(API/DFEAT 를 description 텍스트로만 명시). 정식 그래프 엣지로 backfill 대상. get_item 으로 샘플 1건 확인해 공백이면 전수 보강.

**기본 동작 — 범위 확정 질문 없이 전체 등록.** 갭 표를 사용자에게 **보고**(어떤 클래스를 등록/backfill/deprecated/승격하는지 투명하게)한 뒤, `AskUserQuestion` 없이 **바로 Phase 5~6 으로 진행**한다. 등록 대상 = 코드 자산 전체(컨트롤러·서비스·워커·엔티티·리포·config·util).

범위를 묻는 것은 다음 경우뿐:
- 사용자가 호출에서 범위를 명시적으로 한정했고("컨트롤러·서비스만") 그 해석이 모호할 때 → 1회 확인.
- 갭이 비정상적으로 큼(예 100+ 미등록)이라 일괄 등록 전 한 번 규모를 알릴 필요가 있을 때 → 규모만 보고하고 진행 여부 확인.

그 외에는 **묻지 말고 전체 등록**한다. 부수정리(domain backfill · draft→approved 승격 · 死모듈 deprecated[코드 부재 Grep 확인 후])도 기본 포함.

### Phase 5 — 신규 등록 (register_module, ★ 단일 패스 — 도메인·상태·링크 완결)
확정 범위의 미등록 클래스를 `register_module` 로 등록. 한 메시지에 병렬(8~11개씩 배치). 각 호출:
- `kind`: 컨트롤러·서비스·워커 → `service` / 엔티티·리포 → `schema` / config·util·예외 → `util` (기존 도메인 등록 패턴과 일치시킴 — 컨트롤러도 service 로 등록돼 있으면 따른다)
- `file_path`: 레포 루트 기준 상대(배포모듈 prefix 포함, 예 `klid_system_was_clip_egov/src/.../ApiVideoReviewList.java`)
- `name`/`title`/`description`(역할+멱등/주의 — API/DFEAT 는 아래 정식 링크로)
- ★ **단일 패스 링크 (등록과 동시에 완결)**:
  - `implements_domains=[{domain_id:"DOMAIN-XXX", responsibility:"<역할 1줄>", primary:true}]` → belongs_to_domain 자동
  - `status="approved"` (구현 완료분)
  - `realizes_domain_features`(DFEAT)·`implements_apis`(API)·`realizes_features`(FEAT)·`realizes_screens`(SCREEN)·`consumes_constants`(CONST)·`based_on_adr`(ADR)·`depends_on_modules`(MOD) 가능한 채움
- `session_summary`: 등록 맥락 한 줄
- 응답의 `unresolved == 0` 확인(링크 ID 오타 검출). **★ 신규는 여기서 도메인·상태·전 링크 완결 — 별도 update_item backfill 불필요.**

### Phase 6 — 부수정리 (update_item — ★ 레거시·기존 모듈만)
신규 등록분은 Phase 5 에서 완결됐으므로 **대상 아님**. 도구 업데이트 전 등록분·기존 모듈만 정리:
- **레거시 domain 미연결 backfill**: (구 register_module 로 등록돼 도메인 미연결인 모듈) `update_item(id, domain_id="DOMAIN-XXX", status="approved", base_version=<조회값>, change_summary)`.
- **死모듈 deprecated**: 코드 부재 Grep **확인 후** `update_item(status="deprecated", change_summary=폐기근거)`.
- **draft→approved 승격**: 기존 구현완료 MOD `update_item(status="approved")`.
- **★ 정식 API/DFEAT 링크 backfill** (도구 업데이트 전 등록분): `implements_apis`/`realizes_domain_features` 가 공백인 모듈에 `update_item(data_mode="merge", data={implements_apis:["API-N"...], realizes_domain_features:["DFEAT-N"...]})` 로 정식 그래프 엣지 추가. description 텍스트 매핑을 정식 링크로 승격하는 것 — merge 라 기존 based_on_adr/realizes_screens/consumes_constants 보존. **컨트롤러·서비스는 implements_apis+realizes_domain_features / 워커·로더는 realizes_domain_features 만(API 직접 구현 없음) / 엔티티·리포·config·util·인증공통은 제외**(API/DFEAT 직접 구현 아님). API/DFEAT 매핑은 각 모듈 description 에서 추출.
- ★ `base_version` 은 각 ITEM 의 현재 `current_version` 과 정확히 일치(낙관적 동시성). list_items/get_item 으로 확인.
- 한 메시지에 병렬 배치. **신규 등록만 있고 레거시/死모듈/draft/링크미비 가 없으면 이 Phase 는 skip.**

### Phase 7 — 검증 + 메모리
1. `list_items(type=code_module, domain_id=DOMAIN-XXX)` 재조회 → active/retired 카운트·전부 approved·stale 확인.
2. 결과 표 보고: 작업 전→후 카운트, 신규 N·backfill N·deprecated N·승격 N, unresolved/warnings 0 확인.
3. **메모리 저장 문의**(mc-logi-update 정책): `~/.claude/projects/<project>/memory/` 에 등록 이력 + MEMORY.md 인덱스 1줄. ★ register_module 단일 패스(implements_domains·status·realizes_domain_features·implements_apis) — 신규는 1회 등록으로 도메인·상태·링크 완결, update_item 은 레거시 backfill 전용임을 메모에 남김.
4. code_module 은 키트 범위 밖 → **git 변경·docs 갱신 없음** 을 명시.

---

## hard rules
공통 품질·안전 룰은 `references/checklist.md` 참조 (등록 전후 검증 루프, AI 추정 금지, base_version 정합, unresolved 0 확인 등).

## 진입 멘트
"mc-logi-module-register 시작합니다.

대상: `<DOMAIN-ID> <도메인명>` / 프로젝트: `<project>`
모드: 코드↔logicraft code_module 등록 정합 (검출 자동 · 갭 보고 후 바로 등록)
범위: **코드 자산 전체 등록** (기본 — 따로 한정 안 하면 컨트롤러·서비스·워커·엔티티·리포·config 전부) · logicraft 등록만(docs/·git 무변경)

현재 등록 카탈로그 조회 + 코드 전수 스캔 후 갭을 보고하고, 전체 등록으로 진행합니다 (범위 한정은 호출 시 명시한 경우만)."
