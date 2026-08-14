# mc-logi-publish-skill — 스킬 마켓플레이스 발행기

로컬 스킬 폴더(`~/.claude/skills/<name>/`)를 LogiCraft 마켓플레이스에 **발행·갱신**하는 스킬. 파일 본문이 AI 컨텍스트를 거치지 않고, 실발행은 예행연습을 거치지 않으면 **스크립트가 거부**한다.

## 왜 필요한가 — MCP `publish_skill` 로는 세 가지가 터졌다

MCP 도구는 호출하는 AI 가 **모든 파일 본문을 한 tool call 에 실어야** 한다.

| 실패 모드 | 실제로 벌어진 일 |
|---|---|
| 모델 출력 한도에서 잘림 | 잘린 채 발행 → 나머지 파일 소멸 → 손으로 git 수습(수습 커밋 5건) |
| `Read` 줄번호 prefix 오염 | `   123→` 가 본문에 섞여 발행 |
| AI 재타이핑 오타 | 발행본에 `컬럼→컴럼`(7곳) · `과잉→과익` · `뜰→뜸` |

이 스킬의 스크립트는 **파일을 직접 읽어 multipart 로 전송**한다. 본문이 대화 컨텍스트를 통과하지 않으므로 위 세 가지가 **구조적으로 불가능**하다. 의존성 0 의 순수 node 스크립트라 어느 프로젝트 세션에서든 동작한다.

## ★ 예행연습이 강제된다

발행은 **공개 레포에 커밋을 남기는 되돌리기 번거로운 행위**다. 그래서 실발행은 `--confirm <토큰>` 없이는 거부되고, 토큰은 `--dry-run` 만 발급한다.

```bash
# 1) 무엇이 쓰이고 사라지고 보존되는지 확인 (원격 무변경)
node publish-skill.mjs <스킬디렉터리> --category design --dry-run
   written : 3건  SKILL.md, checklist.md, cascade-patterns.md
   kept    : 1건
   deleted : 0건
   → 실발행: --confirm a3f9c1e2d0b4

# 2) 확인했으면 발행
node publish-skill.mjs <스킬디렉터리> --category design --confirm a3f9c1e2d0b4
```

토큰은 **보낼 내용 전체의 해시**(파일 본문 · 경로 · 삭제목록 · category · mode · summary · listing · 서버 주소)다. 하나라도 바뀌면 무효가 되어 다시 예행연습을 타야 한다. 서버 주소가 해시에 들어가므로 **개발 서버에서 만든 토큰이 상용 발행을 승인할 수 없다.**

> 이 장치가 보장하는 것은 "예행연습이 돌았다"까지다. **"사람에게 보여주고 승인받았다"는 강제할 수 없다** — 그건 스킬 절차의 몫이다. 다만 서버가 검증한 정확한 예측이 최소 한 번은 산출되므로 **모르는 새 파일이 사라지는 사고**는 막힌다.

## 안전장치

- **upsert 가 기본** — 넘긴 파일만 갱신하고 나머지는 보존. 삭제는 `--delete` 로 명시.
- **소멸 가드** — `--mode replace` 로 파일이 사라지면 `E_SKILL_SHRINK` 로 거부(의도한 삭제는 `--allow-delete`).
- **`--list-only`** — 네트워크·키 없이 보낼 목록만 확인(토큰은 나오지 않는다).

## ★ 동봉 서브에이전트 — `_plugin/` 규칙

Claude Code 플러그인은 서브에이전트를 **`plugins/<name>/agents/`** 에서 로드한다. `skills/<name>/agents/` 에 두면 설치해도 **에이전트로 잡히지 않는 죽은 파일**이다.

스킬 폴더의 `_plugin/` 아래가 그 자리로 간다:

```
~/.claude/skills/my-skill/
  SKILL.md                      → plugins/my-skill/skills/my-skill/SKILL.md
  _plugin/agents/helper.md      → plugins/my-skill/agents/helper.md   ★
```

`_plugin/` 이 없으면 플러그인 레벨 파일을 건드리지 않으므로 **기존 에이전트가 보존**된다.

## 놓치기 쉬운 것

- **버전** — 기존 스킬은 `metadata.version` 이 semver 로 증가해야 발행된다.
- **`--category` 를 추정하지 말 것** — 마켓의 현재 값을 확인하고 그대로 쓴다. 틀리면 카탈로그 분류가 조용히 바뀐다.
- **`--summary` 를 생략하면 기존 요약이 소멸한다** — `plugin.json` 은 발행마다 새로 쓰이는데 `summary` 만 "생략 = 삭제"로 비대칭이다(`listing` 은 "생략 = 보존"). 예행연습 응답에도 드러나지 않는다.
- **발행 후에는 바이트로 대조한다** — 파일 목록만 보면 손상을 놓친다.

## 사전 준비

- `LOGICRAFT_API_KEY` — MCP 와 동일한 `lc_` 키. **write 권한 필수**(read 전용은 403).
- `LOGICRAFT_API_BASE` — 대상 서버(`/api` 포함).

종료코드: 0 성공 / 1 인자·토큰 / 2 HTTP·인증 / 3 파일.
