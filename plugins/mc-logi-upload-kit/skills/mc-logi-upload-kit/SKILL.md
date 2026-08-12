---
name: mc-logi-upload-kit
description: 로컬에 작업해둔 파일(HTML 데모·아티팩트·디자인 렌더·markdown 첨부)을 LogiCraft 에 REST 로 직접 업로드하는 스킬. 본문이 AI 컨텍스트를 거치지 않아 5MB 데모도 토큰 0 으로 등록된다. 사용자가 "이 파일 데모로 올려줘", "demo.html 업로드", "이 HTML 아티팩트 등록", "디자인 렌더 파일 올려줘", "/mc-logi-upload-kit" 등 로컬 파일을 LogiCraft 산출물로 등록하려 할 때 실행. download-kit(키트 다운로더)의 역방향 업로더.
metadata:
  version: 1.2.0
---

# mc-logi-upload-kit — LogiCraft 파일 업로더

로컬 파일을 LogiCraft 의 파일 업로드 REST 엔드포인트(API-159~163, ADR-029/CO-007)로 **직접 전송**한다.
`create_app_demo(html="...")` 처럼 본문을 문자열 인자로 넘기면 AI 가 파일을 Read→재출력하는 왕복이 생겨
큰 파일(5MB)은 토큰 폭발로 등록 불가다. 이 스킬은 결정적 스크립트(`bin/upload-artifact.mjs`)가
파일을 직접 읽어 REST 로 보내므로 **본문이 AI 컨텍스트를 안 거친다(토큰 0)**.

`mc-logi-implement-kit`(download-kit.mjs, 다운로드)의 **대칭**이다.

## When to Use
- 로컬에 작업해둔 HTML/markdown 파일을 LogiCraft 산출물로 등록 (예: "이 demo.html 데모로 올려줘")
- 큰 데모/아티팩트 HTML(수백 KB~5MB)을 MCP 문자열 채널 없이 등록
- implement/screen-implement/dispatch 가 로컬 렌더 산출물을 등록하는 스텝

## When NOT to Use
- 작은 본문(수 KB): 기존 MCP 도구(create_app_demo 등)도 무방
- ITEM 설계 자체 수정(mc-logi-update)
- 키트 다운로드(mc-logi-implement-kit)
- **스킬을 마켓플레이스에 발행** → **`mc-logi-publish-skill`** (별도 스킬. 대상이 파일이 아니라
  스킬 폴더 전체이고, 발행 시맨틱·dry-run 강제가 달라 분리돼 있다)

## 대상 타입

| --type | 대상 | 엔드포인트 | 필수 인자 |
|---|---|---|---|
| `app_demo` | 앱 데모 후보(+v1) | POST …/demos/upload | --title |
| `app_demo_version` | 앱 데모 버전 추가 | POST …/demos/:parent/versions/upload | --parent(demoId) |
| `project_artifact` | 프로젝트 아티팩트 | POST …/artifacts/upload | --title |
| `attachment` | 아티팩트 md 첨부 | POST …/artifacts/:parent/attachments/upload | --parent(artifactId) --title |
| `design_render` | 디자인 렌더(html+css) | POST …/items/:parent/design-render/upload | --parent(SD-ID) |

## 사전 준비 (환경)
- `LOGICRAFT_API_KEY` — MCP 와 **동일한 lc_ 키**(`.mcp.json` 의 AUTH_TOKEN 에서 `lc_...` 부분). api-key 경로는
  서버 guard 가 write 스코프를 강제(read-only 키는 403, ADR-029/CO-007).
- `LOGICRAFT_API_BASE` — 대상 서버(개발 `http://localhost:14000/api`, 상용 `https://logicraft.cudo.co.kr:10000/api`).
  ★ 등록 대상 프로젝트가 있는 서버로 맞출 것(다운로더와 동일 규칙).

## 워크플로

### Phase 1 — 대상 확정
사용자 요청에서 **파일 경로 · 타입 · project_id · (버전/첨부/렌더면) parent** 를 파악. 불명확하면 되묻는다.
- 파일 있는지 확인(Glob/Read 로 존재만, 본문 통독 불필요 — 본문은 스크립트가 읽는다).
- project_id 는 `list_projects`(MCP) 또는 사용자 확인. server base 는 그 프로젝트가 있는 서버.

### Phase 2 — 업로드 실행
스크립트 위치는 설치 무관하게 `Glob("**/mc-logi-upload-kit/bin/upload-artifact.mjs")` 로 탐색 후:
```bash
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<서버 base> \
  node <upload-artifact.mjs> --type <타입> --project <uuid> --file <경로> [--parent <id>] [--title "..."] [--change-note "..."] [--css <경로>] [--surface main] [--description "..."] [--tags "a,b"] [--category-id <uuid>]
```
- 종료코드: **0** 성공 · **1** 인자 오류 · **2** HTTP/인증 오류(키·스코프·네트워크·base) · **3** 파일 오류.
- 성공 시 `✅ <타입> 업로드 완료` + 생성된 id/version JSON 출력.

### Phase 3 — 결과 보고
생성된 id·version 을 사용자에게 보고. 데모면 `/app/projects/<id>/demo` 갤러리에서 확인 가능함을 안내.
실패(비-0)면 종료코드·stderr 를 그대로 노출하고 원인(키 미설정·스코프·잘못된 parent·base 불일치)을 짚는다.

## 보안 메모
- 업로드된 본문도 **서버가 기존 sanitize + 봉인(ADR-025) 파이프라인을 그대로 경유** — 스크립트는 전송만.
- 데모/아티팩트 쓰기는 이 REST(api-key/세션) + MCP 만. 익명 업로드 불가(guard fail-closed).
- markdown 첨부는 sandbox/CSP 가 아니라 앱 DOM prose 렌더(rehype-raw 금지, XSS 원천차단, ADR-025 원칙 9).

## 설계 근거
ADR-029(파일 업로드 채널) · DFEAT-060 · API-159~163 · CO-007. download-kit(ADR-026)의 대칭.

> 스킬 발행 기능은 v1.1.0 에 잠시 들어왔다가 **CO-035 에서 `mc-logi-publish-skill` 로 분리**됐다.
> 대상(단일 파일 vs 스킬 폴더)·시맨틱(upsert/replace/삭제/semver)·리스크(공개 레포 커밋)가 달라
> 한 스킬의 `description` 에 묶으면 둘 다 호출 트리거가 약해지기 때문이다.
