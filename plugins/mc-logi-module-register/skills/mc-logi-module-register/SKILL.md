---
name: mc-logi-module-register
description: 구현된 실제 코드(컨트롤러·서비스·워커·엔티티·리포·config)를 logicraft code_module ITEM 으로 등록·정합시키는 오케스트레이터 스킬. 코드는 구현됐는데 logicraft code_module 에 안 잡히거나(미등록), 등록은 됐지만 도메인 미연결(register_module 의 domain 미지원 잔재)이거나, 코드에 없는 死모듈이 남아있는 상태를 도메인 단위로 해소한다. 사용자가 "코드모듈 등록해줘", "D002 코드모듈 정합", "구현한 클래스 logicraft 에 등록", "code_module 등록 검토", "코드↔logicraft 모듈 정합", "MOD 등록 누락 찾아줘", "/mc-logi-module-register <도메인>" 등을 요청하면 트리거. 코드 자산을 그래프에 인지시켜 다음 세션이 어느 클래스가 어느 API/DFEAT/CONST 를 구현하는지 탐색 가능하게 만든다. 검출(코드 스캔·갭 분석)은 자동, 실제 등록은 범위를 사용자와 확정한 뒤 수행. mc-logi-implement-review(코드↔키트 표류 검출)와 다름 — 이건 코드↔logicraft code_module ITEM 의 등록 자체를 정합.
metadata:
  version: 0.1.0
---

# mc-logi-module-register — 코드 ↔ logicraft code_module 등록 정합

구현된 실제 코드 클래스를 logicraft `code_module` ITEM 으로 빠짐없이 등록하고, 도메인 연결·상태(approved)·링크(ADR/CONST/SCREEN/MOD)를 정합시킨다. **검출은 자동(read-only 코드 스캔 + 갭 분석), 등록(쓰기)은 범위를 사용자와 확정한 뒤 수행.**

## When to Use
- 도메인 구현이 한참 진행됐는데 logicraft code_module 이 코드 실태를 못 따라온 경우
- register_module 로 등록은 했지만 도메인 미연결로 `list_items(domain_id)` 필터에 안 잡히는 모듈 정리
- 코드에 없는데 logicraft 에 남은 死모듈(폐기 설계 잔재) 정리
- 구현 완료 모듈을 draft→approved 로 일괄 확정

## When NOT to Use
- 코드 ↔ 키트(docs/design) 본문 표류 검출 → **mc-logi-implement-review**
- 설계 ITEM(ADR/ERD/API) 수정 → **mc-logi-update**
- 키트 다운로드 → **mc-logi-implement-kit**
- code_module 은 키트 Tier 범위 밖이라 본 스킬은 **logicraft 등록만** 한다 (docs/ 갱신·git 커밋 없음)

## ★ 핵심 함정 (이 스킬이 존재하는 이유)
- **register_module 은 `domain_id`/`implements_domains` 파라미터가 없다.** 신규 등록 시 도메인 연결이 안 되므로, 등록 직후 반드시 `update_item(id, domain_id="DOMAIN-XXX")` 로 backfill 해야 `list_items(type=code_module, domain_id)` 필터에 잡힌다. 이걸 빼먹으면 등록은 됐는데 도메인에서 보이지 않는 유령 모듈이 된다.
- **register_module 의 `realizes_*` 는 FEAT/SCREEN 만 받는다** (`realizes_features`/`realizes_screens`). API_endpoint·domain_feature 는 realizes 링크 대상이 아니다 → API/DFEAT 매핑은 `description` 본문에 ID 로 명시하고, 화면이 있으면 `realizes_screens`, 상수는 `consumes_constants`, 결정근거는 `based_on_adr`, 의존 모듈은 `depends_on_modules` 로 연결한다.
- **신규는 register 후 status=draft.** 구현 완료분이면 `update_item(status="approved")` 로 승격 (domain backfill 과 한 번에 처리 가능).

## 작업 정책 (logicraft 쓰기 정책 준수)
- 코드 스캔·logicraft 조회(list/get/find)는 **자동 OK**.
- **등록·수정(register_module/update_item)은 범위를 사용자와 확정한 뒤** 수행. AI 임의 추정으로 박지 말 것.
- 각 모듈 메타(file_path·역할·API/DFEAT 매핑·ADR·CONST)는 **코드 근거**로 채운다(파일 실재·실제 구현 기준). logicraft 에 없는 값을 상상해 채우지 말 것 — 모르면 비우고 보고에 명시.
- 死모듈 deprecated·draft→approved 같은 상태 변경도 사용자 승인 후.

---

## 워크플로 (8 Phase)

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

### Phase 4 — 갭 분석 + 범위 확정 (AskUserQuestion)
코드 ↔ logicraft 대조로 3 버킷 산출:
1. **미등록** — 코드에 있는데 logicraft code_module 에 없음 (신규 register 대상)
2. **domain 미연결** — 등록됐으나 belongs_to_domain 없음 (backfill 대상)
3. **死모듈** — logicraft 에 있는데 코드에 없음 (deprecated 후보)
+ **draft 다수** — 구현 완료인데 status=draft (approved 승격 후보)

갭 표를 사용자에게 제시하고 `AskUserQuestion` 으로 **등록 범위** 확정:
- 컨트롤러+서비스+워커 (로직 단위 — 추적가치 높음, 기본 권장)
- + 엔티티·리포·config (데이터/인프라 계층 포함)
- 전부 (유틸·예외까지)

부수정리(domain backfill·死모듈 deprecated·draft→approved)도 함께 할지 multiSelect 로 확인.

### Phase 5 — 신규 등록 (register_module)
확정 범위의 미등록 클래스를 `register_module` 로 등록. 한 메시지에 병렬(8~11개씩 배치). 각 호출:
- `kind`: 컨트롤러·서비스·워커 → `service` / 엔티티·리포 → `schema` / config·util·예외 → `util` (기존 도메인 등록 패턴과 일치시킴 — 컨트롤러도 service 로 등록돼 있으면 따른다)
- `file_path`: 레포 루트 기준 상대(배포모듈 prefix 포함, 예 `klid_system_was_clip_egov/src/.../ApiVideoReviewList.java`)
- `name`/`title`/`description`(역할+API/DFEAT ID+멱등/주의)
- `based_on_adr`·`consumes_constants`·`realizes_screens`·`depends_on_modules` 가능한 채움
- `session_summary`: 등록 맥락 한 줄
- 응답의 `unresolved` 가 0 인지 확인(링크 ID 오타 검출). 반환 MOD ID 수집(다음 Phase update 용).

### Phase 6 — 도메인 연결 + approved (update_item)
★ register_module 이 domain 미지원이므로 **필수**. 신규 등록 MOD 전부 `update_item`:
- `domain_id="DOMAIN-XXX"` + `status="approved"` + `base_version=1` + `change_summary`
- 한 메시지에 병렬 배치.

### Phase 7 — 부수정리 (사용자 승인분만)
- **domain 미연결 backfill**: 해당 MOD `update_item(domain_id=..., status=approved)`. base_version 은 Phase 2 조회값.
- **死모듈 deprecated**: `update_item(status="deprecated", change_summary=폐기근거)`.
- **draft→approved 승격**: 기존 구현완료 MOD `update_item(status="approved")`. base_version 정확히(조회값).
- ★ base_version 은 각 ITEM 의 현재 current_version 과 일치해야 함(낙관적 동시성). list_items/get_item 으로 확인.

### Phase 8 — 검증 + 메모리
1. `list_items(type=code_module, domain_id=DOMAIN-XXX)` 재조회 → active/retired 카운트·전부 approved·stale 확인.
2. 결과 표 보고: 작업 전→후 카운트, 신규 N·backfill N·deprecated N·승격 N, unresolved/warnings 0 확인.
3. **메모리 저장 문의**(mc-logi-update 정책): `~/.claude/projects/<project>/memory/` 에 등록 이력 + MEMORY.md 인덱스 1줄. ★ register_module domain 미지원 함정을 메모에 남겨 다음 세션이 반복 안 하게.
4. code_module 은 키트 범위 밖 → **git 변경·docs 갱신 없음** 을 명시.

---

## hard rules
공통 품질·안전 룰은 `references/checklist.md` 참조 (등록 전후 검증 루프, AI 추정 금지, base_version 정합, unresolved 0 확인 등).

## 진입 멘트
"mc-logi-module-register 시작합니다.

대상: `<DOMAIN-ID> <도메인명>` / 프로젝트: `<project>`
모드: 코드↔logicraft code_module 등록 정합 (검출 자동 · 등록은 범위 확정 후)
범위: logicraft 등록만 (docs/·git 무변경)

현재 등록 카탈로그 조회 + 코드 전수 스캔 후 갭을 제시하고, 등록 범위를 확정해 진행합니다."
