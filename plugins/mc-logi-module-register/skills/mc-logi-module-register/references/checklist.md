# checklist.md — mc-logi-module-register hard rules

## 범위 (★ 매번 묻지 않음)
- [ ] 등록 범위 기본 = **코드 자산 전체**(컨트롤러·서비스·워커·엔티티·리포·config·util). 갭 보고 후 AskUserQuestion 없이 바로 전체 등록. 사용자가 호출에서 명시적으로 범위를 한정한 경우(또는 갭이 100+ 로 비정상적으로 큰 경우)에만 1회 확인.

## 등록 전 (필수)
- [ ] `get_item_schema("code_module")` 로 필드·링크 타입·enum 확인(처음/가물거리면). 특히 register_module 의 파라미터엔 `domain_id` 가 **없음**을 재확인.
- [ ] 코드 스캔 결과의 file_path 가 **실재**하는지(Glob/Explore 근거). 추정 경로 금지.
- [ ] 기존 도메인 등록 패턴(kind 매핑·title 포맷)을 먼저 보고 **일관**되게. 예: 컨트롤러가 기존에 `service` kind 로 등록돼 있으면 신규도 service.
- [ ] kind 매핑 기본: 컨트롤러/서비스/워커 → `service` · 엔티티/리포 → `schema` · config/util/예외 → `util`.

## 등록 메타 품질 (빈 모듈 금지)
- [ ] `description` 은 역할 1~2줄 + **API/DFEAT ID** + 멱등/주의(있으면). "사용자가 X 할 수 있다" 일반론 금지 — 구현 사실만.
- [ ] `based_on_adr`·`consumes_constants`·`realizes_screens`·`depends_on_modules` 를 가능한 채움(코드 근거). 모르면 비우고 보고에 "X 미연결 — 추후 확인" 명시.
- [ ] API_endpoint·domain_feature 는 realizes 대상 **아님** → description 본문 ID 로만. realizes_screens 는 화면 있을 때만.
- [ ] 한글 메타에 `\uXXXX` escape 금지(UTF-8 그대로).

## 등록 직후 (★ 가장 흔한 누락)
- [ ] register_module 응답 `unresolved == 0` 확인(>0 이면 링크 ID 오타 → 수정). created/updated 수 확인.
- [ ] **신규 등록 MOD 는 반드시 `update_item(domain_id="DOMAIN-XXX")` 로 도메인 연결** — 안 하면 `list_items(domain_id)` 에서 안 보임. status 도 구현완료면 approved 로.

## update_item (backfill·승격·deprecated)
- [ ] `base_version` = 대상 ITEM 의 현재 `current_version` 과 정확히 일치(낙관적 동시성). list_items/get_item 으로 확인 후 호출.
- [ ] 응답 `warnings[]` 확인 — 있으면 사용자에게 노출.
- [ ] 死모듈 deprecated 는 코드 부재를 **확인**(Grep)한 뒤. 추정으로 폐기 금지.

## 검증 루프 (등록 후)
- [ ] `list_items(type=code_module, domain_id=DOMAIN-XXX)` 재조회 → 기대 카운트·전부 approved·stale 점검.
- [ ] 死모듈이 retired_items 로 빠졌는지 확인.

## 금지 안티패턴
- ❌ register_module 후 domain backfill 누락 (유령 모듈)
- ❌ realizes_features 에 API/DFEAT ID 박기 (FEAT/SCREEN 만 허용)
- ❌ base_version 추측 (낙관적 동시성 충돌)
- ❌ logicraft 에 없는 ADR/CONST/SCREEN ID 상상해서 링크 (unresolved 발생)
- ❌ 코드 부재 확인 없이 死모듈 deprecated
- ❌ docs/ 갱신·git 커밋 (code_module 은 키트 범위 밖 — logicraft 등록만)
