# scenario_sketch ITEM 스키마 (요약)

> 출처: `mcp__logicraft__get_item_schema(type='scenario_sketch')` v2026-05-21 기준.
> 스키마 변경 의심 시 도구로 재확인 — 본 문서는 캐시.

## ID 규칙
- prefix: `SKETCH`
- pattern: `^SKETCH-\d+$`
- level: project (domain_id 선택)

## 필수 필드 (3)
- `title` (string ≤200)
- `date` (ISO date 또는 datetime 문자열, 예: `2026-05-21`)
- `narrative_text` (markdown ≤20000자) — ★ **원문 verbatim 보존**

## allowed_fields
`title, date, author, domain_id, narrative_text, actors, steps, chapters, assumptions, outcomes, tags, status, linked_items, notes`

> **chapters 가 도입되면서 steps 는 chapters[].steps 로 이동됨**. flat steps 도 호환 가능하나 chapters 권장.

## chapters[]

```ts
chapters: [{
  key: string;            // 'setup' | 'main' | 'decisions' | 'alt1' ...
  name: string;           // 표시명
  role: enum;             // ★ 아래 6종만
  steps: Step[];
}]
```

### chapters[].role enum (★ 6종)
| role | 용도 |
|---|---|
| `prerequisite` | 선행 작업 (setup, genai 엔드포인트 등록 등) |
| `main` | 본 시나리오 흐름 |
| `alternative` | 대안 흐름 |
| `followup` | 후속 작업 |
| `error_handling` | 에러·복구 |
| `context` | 결정 hotspot, 미해결 질문 |

★ `decisions` / `context_info` 같은 자유 키 금지 — `context` 로 통일.

## actors[]

```ts
actors: [{
  key: string (≤64);
  label: string (≤120);
  kind: 'human' | 'our_system' | 'external_system' | 'ui' | 'data_store' | 'other';
  note?: string (≤500);
  mapped_to?: string;       // EXTSYS-NNN / SCREEN-NNN / ROLE-NNN / DOMAIN-NNN
}]
```

## steps[] (chapters[].steps 내)

```ts
steps: [{
  step_no: integer ≥1;
  actor_key: string;        // actors[].key 참조
  kind: 'command' | 'event' | 'policy' | 'read_model' | 'hotspot' | 'note';
  action: string (≤500);
  target_actor_key?: string;
  artifact?: string (≤200);  // 예: "API 신규 (D001 outbound)"
  condition?: string (≤500);
  note?: string (≤1000);
}]
```

Event Storming sticky 색: 자세히는 `event_storming_kinds.md` 참조.

## status (data.status, 내부)
- `draft` (default) | `reviewed` | `promoted` | `archived`

(외부 status 와 별개. 외부는 draft|approved|deprecated|superseded.)

## documented_emitters / documented_consumers (domain_event 항목, sketch 는 미해당)
※ SKETCH 가 아니라 EVT 등록 시 주의 — 패턴 `^[A-Z]+-\d+$` 만 허용 (자유 텍스트 거부).

## linked_items[]
```
pattern: ^[A-Z]+-\d+$
```
양방향 인덱싱 (backref 자동).

## patch_paths (update_item 시 사용 가능 경로)
- `actors` (index/predicate by `key`)
- `steps` (index)
- `assumptions` (index)
- `outcomes` (index)
- `tags` (index)
- `linked_items` (index)

★ `chapters` 는 patch_paths 미명시 — chapters 부분 갱신 시 `data_mode=replace` 또는 `merge` 사용 (array 통째 교체).

## create_item 최소 payload

```json
{
  "project_id": "{uuid}",
  "type": "scenario_sketch",
  "title": "...",
  "change_summary": "...",
  "status": "draft",
  "data": {
    "title": "...",
    "date": "2026-05-21",
    "narrative_text": "{사용자 원문 verbatim}",
    "actors": [],
    "chapters": [{
      "key": "main",
      "name": "본 시나리오",
      "role": "main",
      "steps": []
    }],
    "tags": ["scenario-sketch", "auto-registered"],
    "status": "draft"
  }
}
```

## 흔한 검증 오류
1. `chapters[N].role` enum 위반 → 6종 외 사용 (예: `decisions` X → `context` O)
2. `documented_emitters/consumers` 자유 텍스트 → 빈 배열로 등록, 본문에 자유 텍스트 보존
3. `narrative_text < 1자` → 최소 1자 필수
4. `actors[].kind` 누락 → default `other` 자동
5. `steps[].step_no` 누락 → 1부터 순차
