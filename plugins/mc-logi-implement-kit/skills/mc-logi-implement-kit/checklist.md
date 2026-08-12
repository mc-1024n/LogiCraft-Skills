# checklist.md — logi-implement-fetcher 공통 하드룰 (예외 없음)

## READ-ONLY (절대)
- [ ] logicraft **조회 도구만** 사용: get_item, list_items, get_neighbors, get_related,
      analyze_impact, get_item_schema, get_implementation_coverage, list_unimplemented
- [ ] 쓰기 도구 호출 **금지**: create_item / update_item / register_* / propose_change /
      mark_implementation / upload_static_render / 기타 모든 변경 도구
- [ ] 로컬 파일 시스템만 변경 (Write/Bash mkdir/mv). logicraft 상태 불변

## 다운로드 정확성
- [ ] 각 ITEM 은 `get_item(project_id, ID)` 로 **전체 원본** 취득
- [ ] 원본을 가공 없이 `_raw/<ID>.json` 으로 저장 (UTF-8, logicraft 응답 그대로)
- [ ] 응답 >30KB → Bash `python -c "import json,sys; ..."` (encoding='utf-8') 파싱,
      메인 컨텍스트로 거대 JSON 끌어오지 말 것
- [ ] 요약 .md 는 `summary-templates.md` 의 **해당 타입 섹션 포맷 그대로**
- [ ] frontmatter 의 version = 응답 `current_version` (정수) 정확히 기입
- [ ] last_updated_at / stale / slug 등 메타 원본값 그대로

## 버전 상태 처리
- [ ] status=NEW: 신규 생성, prev_version=null
- [ ] status=CHANGED: 재작성 + prev_version=입력값 + 변경 배너 삽입(version-tracking.md 포맷)
- [ ] status=UNCHANGED: 파일 존재 검증만. 없으면 NEW 로 격상해 생성. 있으면 건드리지 말 것
      (frontmatter synced_at 갱신도 안 함 — git diff 노이즈 방지)
- [ ] status=RETIRED: 메인이 처리(이동). fetcher 는 RETIRED 안 받음

## 요약 품질 (빈 요약 금지)
- [ ] "구현 요지" 가 코드 단위로 구체적 (클래스/함수/테이블/엔드포인트)
- [ ] logicraft 값/이름/경로/타입 의역·추정 **금지**. 모르면 `⚠️ 미정 (logicraft 미기재)`
- [ ] 의존 ITEM 은 ID 로 표기 (IMPLEMENTATION 그래프 연결용)
- [ ] 적용 ADR/NFR/CONST/GUIDE 를 "구속 제약" 에 ID 로 명시
- [ ] **상수 값 인라인**: API/SCREEN/ERD/DFEAT 요약이면 `uses_constant` 링크를 따라 해당 CONST 의
      **실제 값**을 `CONST-NNN(name=value unit)` 형태로 "적용 상수" 줄에 인라인. enum/range/default/
      임계치/토큰 같은 매직값을 **상상해서 채우지 말 것** — logicraft CONST value 원문 그대로.
      uses_constant 역링크가 없으면 "⚠️ uses_constant 미연결 — 도메인 CONST 표 확인" 으로 남김.
- [ ] CONST 요약이면 value 는 **의역·반올림·단위변환 금지**(원문 그대로). env_var+is_secret 은 값 대신 placeholder.
- [ ] 추상 일반론·마케팅 문구 금지. 구현 결정만

## 파일 경로 규약
- [ ] 요약: `{output_root}/{type}/{ID}.md`
- [ ] 원본: `{output_root}/{type}/_raw/{ID}.json`
- [ ] mkdir -p 로 타입 폴더 + _raw 선생성
- [ ] 절대 경로 사용. 기존 파일 덮어쓰기 전 상태 확인(CHANGED 만 덮어씀)

## 출력 규약 (STEP-OUT)
완료 후 자유 텍스트 없이 YAML 한 블록만:

```yaml
fetcher_result:
  item_type: <type>
  domain_id: <DOMAIN-XXX>
  processed:
    new: [<ID>...]
    changed: [{id: <ID>, prev: <n>, cur: <n>}...]
    unchanged_verified: [<ID>...]
    unchanged_recreated: [<ID>...]   # 파일 없어 재생성
  failed: [{id: <ID>, reason: <...>}]
  files_written: <count>
  notes_for_main: <메인이 IMPLEMENTATION/version-master 작성 시 알아야 할 점 (링크 요약 등)>
```

## 금지 안티패턴
- ❌ logicraft 쓰기 도구 호출
- ❌ 원본 JSON 의역/축약 저장 (raw 는 무가공)
- ❌ UNCHANGED 파일 재작성 (git diff 오염)
- ❌ 거대 JSON 을 메인/에이전트 컨텍스트로 직접 로드 (Bash python 파싱)
- ❌ logicraft 에 없는 값 상상해서 채우기
- ❌ enum/range/default/임계치 매직값을 추정·하드코딩 (반드시 CONST value 인라인 — uses_constant 추적)
- ❌ 파일 물리 삭제 (RETIRED 도 메인이 이동만)
- ❌ \uXXXX escape 로 한글 저장 (UTF-8 그대로)
