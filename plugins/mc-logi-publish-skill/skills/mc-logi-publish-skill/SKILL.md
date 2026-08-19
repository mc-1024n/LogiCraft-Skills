---
name: mc-logi-publish-skill
description: 로컬 스킬 폴더(~/.claude/skills/<name>/)를 LogiCraft 마켓플레이스에 발행·갱신하는 스킬. 결정적 스크립트가 파일을 직접 REST 로 보내 본문이 AI 컨텍스트를 거치지 않으므로 잘림·줄번호 오염·재타이핑 오타가 없고, 파일이 많거나 큰 스킬도 한 번에 올라간다. 실발행은 예행연습(dry-run) 토큰 없이는 스크립트가 거부한다. 사용자가 "이 스킬 올려줘", "스킬 마켓에 발행", "스킬 업데이트해서 올려줘", "마켓플레이스에 배포", "스킬 버전 올려서 발행", "/mc-logi-publish-skill" 등 Claude Code 스킬을 마켓에 올리려 할 때 실행.
license: MIT
metadata:
  version: 1.1.0
  domain: logicraft-skills
---

# mc-logi-publish-skill — 스킬 마켓플레이스 발행기

로컬 스킬 폴더를 LogiCraft 마켓(`mc-1024n/LogiCraft-Skills`)에 발행한다.
`POST {BASE}/skills/:name/publish` 직송이며, MCP `publish_skill` 과 **같은 서버 코어**를 거치므로
결과(커밋 형식·`plugin.json` 구조)가 동일하다.

산출물 업로드(HTML 데모·아티팩트·디자인 렌더·md 첨부)는 이 스킬이 아니라 **`mc-logi-upload-kit`** 이다.

## When to Use
- 로컬 스킬을 마켓에 처음 올리거나 갱신할 때
- 로컬과 마켓이 벌어져 정합이 필요할 때
- 동봉 서브에이전트를 스킬과 함께 배포할 때

## When NOT to Use
- 산출물 파일 업로드 → `mc-logi-upload-kit`
- 스킬 **삭제** → MCP `delete_skill` (이 스킬은 발행만 한다. ⚠️ 삭제엔 dry_run 이 없으니 주의)
- 스킬 **내용 작성·수정** 자체 (그건 일반 편집 작업)

## ★★ 왜 MCP `publish_skill` 대신 이 스킬인가

MCP 도구는 호출하는 AI 가 **모든 파일 본문을 한 tool call 에 실어야** 한다. 그래서 세 가지가 터졌다:

| 실패 모드 | 실제로 벌어진 일 |
|---|---|
| 모델 출력 한도에서 잘림 | 잘린 채 발행 → 나머지 파일 소멸 → 손으로 git 수습(커밋 이력에 5건) |
| `Read` 줄번호 prefix 오염 | `   123→` 가 본문에 섞임 |
| AI 재타이핑 오타 | 마켓본에 `컬럼→컴럼`(7곳)·`과잉→과익`·`뜰→뜸`·`오프로젝트→오프프로젝트` |

이 스킬의 스크립트는 **파일을 직접 읽어 multipart 로 보낸다.** 본문이 대화 컨텍스트를 통과하지
않으므로 위 세 가지가 **구조적으로 불가능**하다. MCP 도구는 파일 1~2개짜리 소형 스킬에만 쓴다.

## ★ dry-run 은 스크립트가 강제한다 (건너뛸 수 없음)

발행은 **공개 레포에 커밋을 남기는 되돌리기 번거로운 행위**다. 그래서 실발행은
`--confirm <토큰>` 없이는 스크립트가 **거부**한다. 토큰은 `--dry-run` 이 찍어 준다.

토큰은 **보낼 내용 전체의 해시**(파일 본문·경로·삭제목록·category·mode·summary·listing·서버 주소)라,
하나라도 바뀌면 무효가 되어 dry-run 을 다시 타야 한다.

> **이 장치가 보장하지 않는 것** — 보장하는 건 "dry-run 이 돌았다"까지다.
> **"사용자에게 보여주고 승인받았다"는 스크립트가 강제할 수 없다.** 그건 아래 Phase 3 의 몫이며,
> 반드시 지켜야 한다. 토큰이 통과했다고 안전한 게 아니다.

## 사전 준비 (환경) — ★ MCP 를 쓰면 설정 없이 동작한다 (CO-049)

키·서버는 **자동 조달**된다. 우선순위는 `--api-key`/`--api-base` > env > **MCP 설정** > 에러.

- **자동(권장)** — `~/.claude.json` 의 `mcpServers`(`logicraft` → `logicraft-dev` 순, `--server <이름>` 으로 지정 가능)에서
  api-key(`env.AUTH_TOKEN` 등)와 base(URL 의 끝 `/mcp` 제거)를 읽는다. **아무 env 없이 실행된다.**
- **수동** — `LOGICRAFT_API_KEY`(**write 권한 필수** — read 전용 키는 403) ·
  `LOGICRAFT_API_BASE`(**`/api` 포함**. 상용 `https://logicraft.cudo.co.kr:10000/api`).

⚠️ **로컬 기본값(`localhost:14000`)은 제거됐다.** 셋 다 없으면 종료코드 1 로 중단한다 —
발행 대상 서버를 추측해서 **엉뚱한 서버에 커밋을 남기지 않기 위함**이다.
실행 첫 줄에 `🔑 base=… (출처) · key=출처` 만 찍고 **키 값은 절대 출력하지 않는다**.

## 워크플로

### Phase 1 — 대상 확정 · 현재 상태 확인
발행할 스킬 폴더와 서버를 확정한다. `SKILL.md` frontmatter 의 `name` 이 **폴더명과 같아야** 한다.

**갱신이라면 마켓 현재 상태를 먼저 읽는다** — 다음 두 값을 여기서 확보한다(Phase 2·4 에서 필요):
```bash
gh api repos/mc-1024n/LogiCraft-Skills/contents/plugins/<name>/.claude-plugin/plugin.json \
  --jq '.content' | base64 -d
```
또는 MCP `list_skills` 로 `category`·`version` 확인.

### Phase 2 — 버전 범프 · 보존값 확보

**① 버전** — 기존 스킬은 `metadata.version` 이 semver 로 **증가해야** 발행된다(안 올리면 서버가 거부).
- 오타·문구 수정만 → patch
- 내용 추가·절차 변경·동봉 에이전트 추가 → minor

> ⚠️ 셸로 버전을 치환할 때 `perl -pe "s/…/\$1$new/"` 같은 형태를 쓰지 말 것.
> `$1` 뒤에 숫자가 붙어 `$11`(없는 캡처그룹)로 파싱돼 **frontmatter 가 날아간다.**
> `${1}` 로 쓰거나 그냥 Edit 도구로 고칠 것. (2026-08-12 실사고)

**② `--category` 를 추정하지 말 것** — Phase 1 에서 읽은 **현재 값을 그대로** 쓴다.
틀리면 카탈로그 분류가 조용히 바뀐다. (실제로 한 번 틀렸고 dry-run 이 잡았다)

**③ ★ `--summary` 를 생략하면 기존 요약이 소멸한다** — `plugin.json` 은 발행마다 새로 쓰이는데
`summary` 만 "생략 = 삭제"로 비대칭이다(`listing`/MARKETPLACE.md 는 "생략 = 보존").
**dry-run 응답에도 안 드러난다.** 요약을 바꿀 게 아니라면 Phase 1 에서 읽은 기존 값을 그대로 넘긴다.

### Phase 3 — dry-run  🚦게이트 (생략 금지)
```bash
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<서버 base> \
  node <publish-skill.mjs> <스킬디렉터리> --category <카테고리> [옵션] --dry-run
```
스크립트 위치는 설치 무관하게 `Glob("**/mc-logi-publish-skill/bin/publish-skill.mjs")` 로 탐색.

출력의 **`written` / `kept` / `deleted` / `plugin`** 을 **사용자에게 그대로 보여주고 승인을 받는다.**
- `deleted` 에 의도하지 않은 경로가 하나라도 있으면 **중단하고 사용자에게 확인**한다.
- 출력 끝의 `--confirm <토큰>` 을 다음 단계에 쓴다.

### Phase 4 — 실발행
```bash
… node <publish-skill.mjs> <디렉터리> --category <카테고리> [옵션] --confirm <토큰>
```
성공 시 `✅ <name>@<version> — commit <sha>` 와 설치 명령이 나온다.

### Phase 5 — 검증
**파일 목록만 보면 손상을 놓친다. 바이트로 대조한다:**
```bash
gh repo clone mc-1024n/LogiCraft-Skills /tmp/_m -- --depth 1 -q
cd /tmp/_m && for f in $(cd plugins/<name>/skills/<name> && find . -type f | sed 's|^\./||'); do
  cmp -s "plugins/<name>/skills/<name>/$f" "$HOME/.claude/skills/<name>/$f" || echo "❌ $f"
done
```
`plugin.json` 의 `summary`·`category` 가 의도대로인지도 함께 확인한다.

## 인자

| 인자 | 설명 |
|---|---|
| `<스킬디렉터리>` | 필수. 발행할 폴더 |
| `--category` | 필수. `design` \| `feature_impl` \| `screen_impl` \| `operations` \| `review` \| `other` |
| `--name` | 스킬명. 기본 = 디렉터리명 |
| `--mode` | `upsert`(기본, 넘긴 파일만 갱신·나머지 보존) \| `replace`(전체 교체) |
| `--allow-delete` | `replace` 에서 파일 소멸 허용(소멸 가드 해제) |
| `--delete <경로>` | upsert 에서 지울 **스킬** 파일. 반복 지정 |
| `--delete-plugin <경로>` | 지울 **플러그인 레벨** 파일. 반복 지정 |
| `--changelog` / `--summary` | 커밋 메시지 요약 / 카드 한 줄 요약(§Phase 2 ③ 주의) |
| `--listing <파일>` | 카드 상세(MARKETPLACE.md). 생략 시 기존 상세 보존 |
| `--dry-run` | 예행연습 + 토큰 발급 |
| `--confirm <토큰>` | 실발행 필수 |
| `--list-only` | 전송 없이 목록만 (네트워크·키 불필요, 토큰 안 나옴) |
| `--api-key` / `--api-base` | 기본값 = 환경변수 |

## ★ 동봉 서브에이전트 — `_plugin/` 규칙

Claude Code 플러그인은 서브에이전트를 **`plugins/<name>/agents/`** 에서 로드한다.
`skills/<name>/agents/` 에 두면 설치해도 **에이전트로 안 잡히는 죽은 파일**이다.

스킬 폴더의 **`_plugin/` 아래**가 그 자리로 간다:
```
~/.claude/skills/mc-logi-update/
  SKILL.md                        → plugins/mc-logi-update/skills/mc-logi-update/SKILL.md
  _plugin/agents/specialist.md    → plugins/mc-logi-update/agents/specialist.md   ★
```
- `_plugin/` 이 없으면 `plugin_files` 를 **안 보내고**, 서버는 기존 플러그인 레벨 파일을 **보존**한다.
- `_plugin/` 안에 `.claude-plugin/` · `MARKETPLACE.md` · `skills/` 는 금지(`E_SKILL_BADPLUGINPATH`).
- ⚠️ **사본이다.** 진실원은 유저레벨 `~/.claude/agents/<agent>.md` 이고 `_plugin/` 은 배포용 복사본.
  **원본을 고치면 `_plugin/` 사본도 같이 갱신**해야 설치자에게 최신이 간다.
  원본을 `_plugin/` 으로 **옮기지 말 것** — 현재 세션의 에이전트가 원본에서 로드된다.
- 제외 대상: `.git` · `node_modules` · `.DS_Store`

## 에러 사전

| 코드 | 뜻 | 대처 |
|---|---|---|
| `--confirm 없음/불일치` | dry-run 미실행 또는 내용 변경 | `--dry-run` 재실행 후 새 토큰 사용 |
| `E_SKILL_VERSION` | 버전을 안 올림 | `metadata.version` 증가 |
| `E_SKILL_SHRINK` | `replace` 로 파일이 사라짐 | 의도면 `--allow-delete`, 아니면 `upsert`(기본) |
| `E_SKILL_BADPLUGINPATH` | `_plugin/` 금지 경로 | `.claude-plugin/`·`MARKETPLACE.md`·`skills/` 제거 |
| `E_SKILL_WRITE_INVARIANT` | 대소문자·유니코드 별칭으로 파일이 합쳐짐 | 파일명 충돌 해소. 커밋은 안 됐다 |
| `E_SKILL_FILEBIG` / `E_SKILL_TOTALBIG` | 상한 초과 | 응답 `limits` 확인. 상한은 시스템 설정 화면에서 조정 |
| `E_SKILLS_DISABLED` | 서버에 `SKILLS_REPO` 미설정 | 서버 환경변수 — 관리자 |
| 401 / 403 | 키 없음·무효 / write 스코프 없음 | `LOGICRAFT_API_KEY` 확인 |

종료코드: **0** 성공 · **1** 인자 오류(토큰 미비 포함) · **2** HTTP/인증 오류 · **3** 파일 오류.

## 설계 근거
CO-033(upsert 전환·소멸 가드·REST 직송·`plugin_files`·`dry_run`) ·
CO-034(실사용 채널화, 마켓 8건 정합, 에이전트 위치 교정) ·
CO-035(전용 스킬 분리 + confirm 토큰 강제).
서버 엔드포인트 `POST /api/skills/:name/publish` — MCP `publish_skill` 과 같은 코어(`publishSkill`).
