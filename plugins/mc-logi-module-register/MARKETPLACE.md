# mc-logi-module-register

구현된 코드 클래스를 logicraft `code_module` 그래프에 빠짐없이 등록·정합시키는 오케스트레이터 스킬.

## 무엇을 해결하나
도메인 구현이 진행되면 코드(컨트롤러·서비스·워커·엔티티·리포·config)는 쌓이는데 logicraft `code_module` 은 자주 뒤처진다. 그 결과:
- **미등록** — 구현했는데 그래프에 없는 클래스
- **도메인 미연결** — `register_module` 이 `domain_id` 파라미터를 안 받아, 등록됐지만 `list_items(domain_id)` 필터에 안 잡히는 유령 모듈
- **死모듈** — 폐기 설계 잔재로 logicraft 에만 남고 코드엔 없는 모듈
- **draft 정체** — 구현 완료인데 status 가 draft 인 모듈

이 스킬은 이 4가지를 도메인 단위로 한 번에 정합한다.

## 워크플로 (8 Phase)
1. 도메인·프로젝트·코드 루트 식별
2. logicraft 현재 code_module 카탈로그 조회 (연결됨/미연결/retired 분류)
3. `Explore` 에이전트로 코드 클래스 전수 스캔 (Glob+Grep, read-only)
4. 갭 3버킷(미등록/미연결/死모듈) 산출 + **등록 범위 사용자 확정**(AskUserQuestion)
5. `register_module` 신규 등록 (ADR·CONST·SCREEN·MOD 링크 연결)
6. ★ `update_item(domain_id)` 로 **도메인 backfill + approved** (register_module 의 domain 미지원 보정)
7. 부수정리 — 미연결 backfill·死모듈 deprecated·draft→approved 승격
8. 검증 + 메모리 저장

## 핵심 가치
**검출(코드 스캔·갭 분석)은 자동, 실제 등록(쓰기)은 범위를 사용자와 확정한 뒤** 수행해 안전하다. 등록이 끝나면 그래프에서 "어느 클래스가 어느 API/DFEAT/CONST 를 구현하는지" 탐색 가능해져, 다음 세션·다른 작업자가 코드 실태를 바로 파악한다.

## 같은 계열과의 경계
- `mc-logi-implement-review` — 코드↔키트(docs) **본문 표류** 검출 (이 스킬은 code_module **ITEM 등록 자체**를 정합)
- `mc-logi-update` — 설계 ITEM(ADR/ERD/API) 수정
- `mc-logi-implement-kit` — 키트 다운로드

code_module 은 키트 Tier 범위 밖이라 본 스킬은 **logicraft 등록만** 한다 (docs/·git 무변경).

## 트리거
"코드모듈 등록해줘", "D002 코드모듈 정합", "구현한 클래스 logicraft 에 등록", "MOD 등록 누락 찾아줘", `/mc-logi-module-register <도메인>`