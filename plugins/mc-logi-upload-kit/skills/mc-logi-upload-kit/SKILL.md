---
name: mc-logi-upload-kit
description: 로컬 파일을 LogiCraft 에 REST 로 직접 올리는 업로더 스킬. 두 트랙 — ⑴ 산출물 업로드(HTML 데모·아티팩트·디자인 렌더·markdown 첨부) ⑵ 스킬 발행(로컬 스킬 폴더를 마켓플레이스에 publish). 본문이 AI 컨텍스트를 거치지 않아 5MB 데모도 토큰 0 이고, 스킬은 잘림·줄번호 오염·재타이핑 오타 없이 바이트 그대로 올라간다. 사용자가 "이 파일 데모로 올려줘", "demo.html 업로드", "이 HTML 아티팩트 등록", "디자인 렌더 파일 올려줘", "이 스킬 올려줘", "스킬 마켓에 발행", "스킬 업데이트해서 올려줘", "/mc-logi-upload-kit" 등 로컬 파일·스킬을 LogiCraft 에 등록하려 할 때 실행. download-kit(키트 다운로더)의 역방향 업로더.
metadata:
  version: 1.1.0
---

# mc-logi-upload-kit — LogiCraft 파일 업로더 · 스킬 발행기

로컬 파일을 LogiCraft 의 REST 엔드포인트로 **직접 전송**한다.
`create_app_demo(html="...")`·`publish_skill(files=[...])` 처럼 본문을 문자열 인자로 넘기면
AI 가 파일을 Read→재출력하는 왕복이 생겨 ⑴ 큰 파일은 토큰 폭발·출력 한도로 잘리고
⑵ 재타이핑 과정에서 오타가 섞인다(실측: 마켓 발행본에 `컬럼`→`컴럼`, `과잉`→`과익`).
이 스킬은 결정적 스크립트가 파일을 직접 읽어 보내므로 **본문이 AI 컨텍스트를 안 거친다.**

`mc-logi-implement-kit`(download-kit.mjs, 다운로드)의 **대칭**이다.

## 두 트랙

| 트랙 | 대상 | 스크립트 | 절 |
|---|---|---|---|
| **A · 산출물 업로드** | 앱 데모 · 아티팩트 · 첨부 · 디자인 렌더 | `bin/upload-artifact.mjs` | [트랙 A](#트랙-a--산출물-업로드) |
| **B · 스킬 발행** | 로컬 스킬 폴더 → 마켓플레이스 | `bin/publish-skill.mjs` | [트랙 B](#트랙-b--스킬-발행-publish-skillmjs) |

두 스크립트는 `LOGICRAFT_API_KEY` · `LOGICRAFT_API_BASE` · 종료코드 규약을 **공유**하지만
인자 체계가 완전히 달라 파일이 나뉘어 있다. 섞어 쓰지 말 것.

## When to Use
- 로컬에 작업해둔 HTML/markdown 파일을 LogiCraft 산출물로 등록 (예: "이 demo.html 데모로 올려줘")
- 큰 데모/아티팩트 HTML(수백 KB~5MB)을 MCP 문자열 채널 없이 등록
- implement/screen-implement/dispatch 가 로컬 렌더 산출물을 등록하는 스텝
- **로컬 스킬을 마켓플레이스에 발행·갱신** (예: "이 스킬 올려줘") — 특히 파일이 여러 개거나 큰 스킬

## When NOT to Use
- 작은 본문(수 KB): 기존 MCP 도구(create_app_demo 등)도 무방
- ITEM 설계 자체 수정(mc-logi-update)
- 키트 다운로드(mc-logi-implement-kit)
- 스킬 **삭제**(`delete_skill` MCP) — 이 스킬은 발행만 한다

---

# 트랙 A — 산출물 업로드

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

---

# 트랙 B — 스킬 발행 (`publish-skill.mjs`)

로컬 스킬 폴더(`~/.claude/skills/<name>/`)를 LogiCraft 마켓플레이스에 발행한다.
`POST {BASE}/skills/:name/publish` 직송이며, MCP `publish_skill` 과 **같은 서버 코어**를 거치므로
결과(커밋 형식·plugin.json 구조)가 동일하다.

## ★★ MCP `publish_skill` 대신 이걸 쓰는 이유
MCP 도구는 AI 가 모든 파일 본문을 **한 tool call 에 실어야** 한다. 그래서:
- 파일이 많거나 크면 **모델 출력 한도에서 잘린다** → 잘린 채 발행돼 나머지 파일이 소멸했다(과거 사고)
- `Read` 도구로 읽으면 줄번호 prefix(`   123→`)가 섞인다
- AI 가 본문을 다시 타이핑하면서 **오타가 들어간다** (실측 손상: `컬럼→컴럼`·`과잉→과익`·`뜰→뜸`)

이 스크립트는 파일을 직접 읽어 multipart 로 보낸다 — 위 세 가지가 **원천적으로 불가능**하다.
**스킬 발행은 기본적으로 이 트랙을 쓴다.** MCP 도구는 파일 1~2개짜리 소형 스킬에만.

## ★ 발행 전 반드시 — dry-run 게이트 (건너뛰기 금지)

발행은 **공개 레포에 커밋을 남기는 되돌리기 번거로운 행위**다. 순서를 지킨다:

1. `--dry-run` 으로 실행 → 서버가 검증만 하고 **커밋·push 하지 않는다**
2. 출력의 `written / kept / deleted / plugin` 을 **사용자에게 그대로 보여준다**
3. 사용자가 승인하면 `--dry-run` 을 빼고 재실행

> dry_run 을 통과하면 실발행도 통과한다(그 사이 원격이 안 바뀌는 한).
> 단 하나의 예외 — 대소문자·유니코드 별칭으로 파일이 파일시스템에서 합쳐지는 경우는
> 실제로 써 봐야 알 수 있어 실발행에서 `E_SKILL_WRITE_INVARIANT` 로 거부될 수 있다(그때도 커밋 없음).

## 사용법

```bash
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<서버 base> \
  node <publish-skill.mjs> <스킬디렉터리> --category <카테고리> [옵션]
```
스크립트 위치는 설치 무관하게 `Glob("**/mc-logi-upload-kit/bin/publish-skill.mjs")` 로 탐색.

| 인자 | 설명 |
|---|---|
| `<스킬디렉터리>` | 필수. 발행할 폴더 (예: `~/.claude/skills/mc-logi-update`) |
| `--category` | 필수. `design` \| `feature_impl` \| `screen_impl` \| `operations` \| `review` \| `other` |
| `--name` | 스킬명. 기본 = 디렉터리명 (SKILL.md frontmatter `name` 과 같아야 함) |
| `--mode` | `upsert`(기본, 넘긴 파일만 갱신·나머지 보존) \| `replace`(전체 교체) |
| `--allow-delete` | `replace` 에서 파일 소멸 허용(소멸 가드 해제) |
| `--delete <경로>` | upsert 에서 지울 **스킬** 파일. 반복 지정 가능 |
| `--delete-plugin <경로>` | 지울 **플러그인 레벨** 파일. 반복 지정 가능 |
| `--changelog` / `--summary` | 커밋 메시지 요약 / 카드 한 줄 요약 |
| `--listing <파일>` | 카드 상세(MARKETPLACE.md). **생략하면 기존 상세 보존** |
| `--dry-run` | 예행연습 — 원격 무변경 |
| `--list-only` | 전송 없이 보낼 목록만 출력 (네트워크·키 불필요) |
| `--api-key` / `--api-base` | 기본값 = 환경변수. `--api-base` 는 **`/api` 를 포함**한다 |

## ★ 플러그인 레벨 파일 — `_plugin/` 규칙

Claude Code 플러그인은 **서브에이전트를 `plugins/<name>/agents/` 에서 로드**한다.
`skills/<name>/agents/` 에 두면 설치해도 에이전트로 잡히지 않는다(죽은 파일).

스킬 폴더 안의 **`_plugin/` 아래 파일**이 그 자리로 간다:

```
~/.claude/skills/mc-logi-update/
  SKILL.md                          → plugins/mc-logi-update/skills/mc-logi-update/SKILL.md
  cascade-patterns.md               → plugins/mc-logi-update/skills/mc-logi-update/cascade-patterns.md
  _plugin/agents/specialist.md      → plugins/mc-logi-update/agents/specialist.md   ★
```

- `_plugin/` 이 없으면 `plugin_files` 파트를 **보내지 않으며**, 서버는 기존 플러그인 레벨 파일을 **보존**한다.
- `_plugin/` 안에 `.claude-plugin/` · `MARKETPLACE.md` · `skills/` 는 **금지**(서버가 `E_SKILL_BADPLUGINPATH`).
- ⚠️ **동봉 에이전트는 사본이다.** 진실원은 유저레벨 `~/.claude/agents/<agent>.md` 이고
  `_plugin/agents/` 는 배포용 복사본이다. **원본을 고치면 `_plugin/` 사본도 같이 갱신**해야
  설치자에게 최신이 간다. 원본을 `_plugin/` 으로 **옮기지 말 것** — 현재 세션의 에이전트가 원본에서 로드된다.
- 제외 대상: `.git` · `node_modules` · `.DS_Store` (`_plugin/` 안에서도 동일).

## 버전 규칙 (놓치기 쉬움)

기존 스킬은 **`SKILL.md` 의 `metadata.version` 이 semver 로 증가**해야 발행된다. 안 올리면 서버가 거부한다.
- 오타·문구 수정만 → patch
- 내용 추가·절차 변경·동봉 에이전트 추가 → minor
- ⚠️ **나눠 올리면 호출마다 버전을 올려야 한다.** 이 트랙은 한 번에 전부 보내므로 그럴 일이 없다 —
  그게 upsert 청크 우회보다 이 채널이 나은 또 하나의 이유다.

## 워크플로

### Phase 1 — 대상 확정
발행할 스킬 폴더·카테고리·서버 base 확정. `SKILL.md` frontmatter 의 `name` 이 폴더명과 같은지 확인.
로컬이 마켓보다 최신인지 확인이 필요하면 발행 전에 대조한다(아래 참조).

### Phase 2 — 버전 범프
`metadata.version` 을 위 규칙대로 올린다. **이걸 빼먹으면 Phase 4 에서 거부된다.**

### Phase 3 — dry-run  🚦게이트
`--dry-run` 실행 → `written/kept/deleted/plugin` 을 사용자에게 제시 → **승인 대기**.
`deleted` 에 의도하지 않은 경로가 있으면 **중단하고 사용자에게 확인**한다.

### Phase 4 — 실발행
`--dry-run` 을 빼고 재실행. 성공 시 `✅ <name>@<version> — commit <sha>` 와 설치 명령이 출력된다.

### Phase 5 — 결과 보고·검증
커밋 sha·`written/deleted` 를 보고. 필요하면 원격 트리를 대조한다:
```bash
gh api "repos/<owner>/<repo>/git/trees/main?recursive=1" --jq '.tree[].path' | grep <name>
```
실패(비-0)면 종료코드·stderr 를 그대로 노출한다.

## 에러 사전

| 코드 | 뜻 | 대처 |
|---|---|---|
| `E_SKILL_SHRINK` | `replace` 로 파일이 사라진다 | 의도한 삭제면 `--allow-delete`, 아니면 `upsert`(기본)로 |
| `E_SKILL_BADPLUGINPATH` | `_plugin/` 에 금지 경로 | `.claude-plugin/`·`MARKETPLACE.md`·`skills/` 제거 |
| `E_SKILL_WRITE_INVARIANT` | 대소문자·유니코드 별칭으로 파일이 합쳐짐 | 파일명 충돌 해소. 커밋은 안 됐다 |
| `E_SKILL_FILEBIG` / `E_SKILL_TOTALBIG` | 상한 초과 | 응답의 `limits` 확인. 상한은 시스템 설정 화면에서 조정 가능 |
| `E_SKILLS_DISABLED` | 서버에 `SKILLS_REPO` 미설정 | 서버 환경변수 — 관리자 |
| 401 / 403 | 키 없음·무효 / write 스코프 없음 | `LOGICRAFT_API_KEY` 확인(read 전용 키는 403) |

종료코드: **0** 성공 · **1** 인자 오류 · **2** HTTP/인증 오류 · **3** 파일 오류.

## 보안 메모
- 업로드된 본문도 **서버가 기존 sanitize + 봉인(ADR-025) 파이프라인을 그대로 경유** — 스크립트는 전송만.
- 데모/아티팩트 쓰기는 이 REST(api-key/세션) + MCP 만. 익명 업로드 불가(guard fail-closed).
- markdown 첨부는 sandbox/CSP 가 아니라 앱 DOM prose 렌더(rehype-raw 금지, XSS 원천차단, ADR-025 원칙 9).

## 설계 근거
- **트랙 A** — ADR-029(파일 업로드 채널) · DFEAT-060 · API-159~163 · CO-007. download-kit(ADR-026)의 대칭.
- **트랙 B** — CO-033(upsert 전환·소멸 가드·REST 직송·`plugin_files`·`dry_run`) · CO-034(실사용 채널화).
  서버 엔드포인트 `POST /api/skills/:name/publish`. MCP `publish_skill` 과 **같은 코어**(`publishSkill`)를
  경유하므로 결과가 동일하다.
