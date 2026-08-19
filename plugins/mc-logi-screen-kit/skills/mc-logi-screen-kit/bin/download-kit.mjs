#!/usr/bin/env node
/**
 * download-kit.mjs — 키트 SYNC 무열화 결정적 다운로더 (ADR-026 / DFEAT-057 / API-152)
 *
 * LLM 0. LogiCraft 배치 export 엔드포인트(API-152)를 호출해 설계 ITEM 을
 * 원본 JSON(_raw/*.json) + 서버 결정적 스켈레톤(*.md) 으로 로컬 키트에 내려받는다.
 * 각 .md frontmatter 의 links: 는 [[ID]] wikilink 라 키트 루트를 Obsidian 볼트로 열면
 * 설계 그래프가 그대로 보인다(LINK_FORMAT 참조).
 * 델타(version/content_hash 비교)로 변경분만 페치하고, 디스크 쓰기 무결성을
 * 수신==기록 바이트 비교로 검증한다. content_hash 는 재계산하지 않는다(서버 함수
 * 복제 회피 = ADR-026 "드리프트 0" 정신 유지 — 서버 hash 를 델타 키로 그대로 사용).
 *
 * 인증: LOGICRAFT_API_KEY env → 없으면 ~/.claude.json 의 mcpServers(logicraft*) 에서 자동 조달.
 *       base 도 동일(--base-url > LOGICRAFT_API_BASE > MCP 설정). **로컬 기본값 없음**(CO-049).
 *       --server <name> 으로 MCP 항목을 지정할 수 있다(기본 logicraft → logicraft-dev).
 *
 * 사용:
 *   node download-kit.mjs --project <uuid> --out <kitdir>            # MCP 설정 자동 인식
 *   LOGICRAFT_API_KEY=lc_... LOGICRAFT_API_BASE=https://<host>/api \
 *   node download-kit.mjs --project <uuid> --out <kitdir> [--domain DOMAIN-003] \
 *        [--types adr,domain_feature] [--exclude-types code_module,rfp_item] [--dry-run]
 *
 * 타입 선택 (동적 fail-open 권장 — 신규 ITEM 타입 자동 포함):
 *   --types         포함 목록(CSV). 지정 시 그 타입만 받음 — 서버에 신규 타입이 늘어나도 자동 포함 안 됨.
 *   --exclude-types 제외 목록(CSV). --types 생략 + 이것만 지정하면 "도메인 전체 − 제외" 를 받음
 *                   → 서버에 ITEM 타입이 새로 추가되어도 키트에 자동 포함(fail-open). 둘 다 지정 시 둘 다 적용.
 *
 * 도메인 스코프 (--domain):
 *   서버 필터는 domain_id 컬럼 일치만 보므로, 도메인 귀속이 약한 횡단 타입은 전역으로 받는다.
 *   1순위 **.kit-scope.json**(스킬 LLM 판정 pin) → 없으면 **그래프 스코프**(자기 domain_id
 *   + 1-hop 이웃 · 옛 fetcher 재현율 약 90%) → --no-graph-scope 면 순수 domain_id.
 *   --scope-file <path>   pin 파일 경로 지정(기본 <out>/.kit-scope.json)
 *   --global-types        항상 전역 수집할 타입 CSV (기본 DEFAULT_ALWAYS_GLOBAL_TYPES)
 *   --no-graph-scope      그래프 폴백도 끄기 = 순수 domain_id 필터. 유실 위험 있으니 비권장.
 *   스코프 밖으로 빠진 핵심 타입은 실행 로그와 version-master.md 에 경고로 남는다.
 *
 * 종료코드: 0=성공, 1=인자/환경 오류, 2=네트워크/인증 오류(수정필요), 3=무결성 검증 실패,
 *          4=엔드포인트 미배포(404 — 서버에 /kit-export 없음, 스킬은 fetcher 폴백)
 */
import { promises as fs, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";

// ── 인자·환경 파싱 ────────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        out[key] = true; // 불리언 플래그
      } else {
        out[key] = next;
        i++;
      }
    } else {
      out._.push(a);
    }
  }
  return out;
}

function die(code, msg) {
  process.stderr.write(`✖ ${msg}\n`);
  process.exit(code);
}

/**
 * MCP 설정 폴백 — env/인자가 없을 때 ~/.claude.json 의 mcpServers 에서 api-key·base 를 읽는다.
 *
 * 왜 필요한가 (CO-049):
 *  - 예전 기본값 `http://localhost:14000/api` 는 **개발 머신의 dev 포트**였다. 마켓 발행본을
 *    받은 사람이 그대로 실행하면 자기 로컬(아무것도 없는)을 찔러 ECONNREFUSED 로 죽었고,
 *    "스킬이 서버 접속을 못 한다"로 보였다. → 기본값을 없애고 MCP 설정에서 실제 서버를 읽는다.
 *  - MCP 를 이미 쓰는 환경에서 같은 키를 쉘에 또 export 해야 하는 것도 불필요했다.
 *
 * 우선순위: --base-url / env > MCP 설정 > 에러(조용한 로컬 폴백 없음).
 * 키 값은 어떤 경로로도 로그에 출력하지 않는다(출처 이름만 표시).
 */
function readMcpConfig(preferred) {
  const home = homedir() || process.env.HOME || "";
  if (!home) return null;
  let cfg;
  try {
    cfg = JSON.parse(readFileSync(join(home, ".claude.json"), "utf8"));
  } catch {
    return null;
  }
  const pools = [];
  if (cfg && cfg.mcpServers) pools.push(cfg.mcpServers);
  for (const proj of Object.values((cfg && cfg.projects) || {})) {
    if (proj && proj.mcpServers) pools.push(proj.mcpServers);
  }
  const preferredNames = preferred ? [preferred] : ["logicraft", "logicraft-dev"];
  for (const pool of pools) {
    const ordered = [
      ...preferredNames.filter((n) => pool[n]),
      ...Object.keys(pool).filter((k) => /^logicraft/i.test(k) && !preferredNames.includes(k)),
    ];
    for (const name of ordered) {
      const srv = pool[name];
      if (!srv) continue;
      const env = srv.env || {};
      const argv = Array.isArray(srv.args) ? srv.args : [];
      let key = env.LOGICRAFT_API_KEY || env.AUTH_TOKEN || env.API_KEY || "";
      if (!key) {
        // '--header' 'Authorization:Bearer xxx' 형태 (env 치환 전 플레이스홀더는 걸러진다)
        const h = argv.find((a) => typeof a === "string" && /^authorization\s*:/i.test(a));
        if (h) key = h.slice(h.indexOf(":") + 1);
      }
      key = String(key).replace(/^\s*Bearer\s+/i, "").trim();
      if (/^\$\{.*\}$/.test(key)) key = ""; // 미치환 플레이스홀더는 키가 아니다
      const urlArg = argv.find((a) => typeof a === "string" && /^https?:\/\//.test(a));
      const base = urlArg ? urlArg.replace(/\/mcp\/?$/, "").replace(/\/$/, "") : "";
      if (key || base) return { name, key, base };
    }
  }
  return null;
}

const args = parseArgs(process.argv.slice(2));
// 인증·엔드포인트 결정 — env/인자 > MCP 설정 > 에러. 로컬 기본값은 두지 않는다(CO-049).
const _mcp =
  !process.env.LOGICRAFT_API_KEY || !(args["base-url"] || process.env.LOGICRAFT_API_BASE)
    ? readMcpConfig(typeof args.server === "string" ? args.server : null)
    : null;
const API_BASE = String(
  args["base-url"] || process.env.LOGICRAFT_API_BASE || (_mcp && _mcp.base) || "",
).replace(/\/$/, "");
const API_KEY = String(process.env.LOGICRAFT_API_KEY || (_mcp && _mcp.key) || "")
  .replace(/^\s*Bearer\s+/i, "")
  .trim();
const BASE_SOURCE = args["base-url"]
  ? "--base-url"
  : process.env.LOGICRAFT_API_BASE
    ? "env"
    : _mcp && _mcp.base
      ? `MCP(${_mcp.name})`
      : "없음";
const KEY_SOURCE = process.env.LOGICRAFT_API_KEY
  ? "env"
  : _mcp && _mcp.key
    ? `MCP(${_mcp.name})`
    : "없음";
const projectId = args.project;
const outDir = args.out;
const domain = args.domain; // 옵션
const types = args.types; // CSV 옵션 (포함 목록 — 지정 시 신규 타입 자동 포함 안 됨)
// 제외 목록(CSV) — --types 생략 + 이것만 지정하면 "전체 − 제외" (신규 타입 fail-open 자동 포함)
const excludeTypes =
  typeof args["exclude-types"] === "string"
    ? new Set(args["exclude-types"].split(",").map((t) => t.trim()).filter(Boolean))
    : null;
const idsFilter = typeof args.ids === "string" ? args.ids : null; // 특정 ID 집합 스코프(screen-kit)
const dryRun = Boolean(args["dry-run"]);
const reportPath = typeof args.report === "string" ? args.report : null; // 후처리(arranger)용 run 상태 출력

/**
 * ── 도메인 횡단(cross-cutting) 타입 ──────────────────────────────────
 * 서버의 --domain 필터는 items.domain_id **컬럼 정확 일치**만 본다(items.service.ts
 * listForExport). 그런데 아래 타입들은 애초에 도메인 귀속 개념이 약해 domain_id 가 비어
 * 있는 경우가 많고, 도메인과는 여러 hop 건너(예: DOMAIN ←belongs_to_domain— DFEAT
 * —specializes→ FEAT ←realizes— UC ←derived_from— AC) 링크로만 이어진다.
 * 이걸 도메인 필터로 거르면 **설계에 멀쩡히 있는데 키트에 안 내려오는** 조용한 유실이
 * 난다(2026-08 NexusSystem: nfr·permission_role·implementation_guideline·test_scenario 전멸).
 *
 * core-item-set.md 도 이들을 도메인 스코프로 규정하지 않는다 —
 * implementation_guideline "project-wide → 항상 포함", nfr·feature Tier 2 "항상 다운로드".
 *
 * adr 은 제외한다 — core-item-set.md 가 "전역 ADR 중 도메인 관련만" 으로 규정하고
 * 실제로 domain_id 로도 상당수 잡힌다. 대신 스코프 밖 ADR 건수는 아래 유실 경고로 알린다.
 *
 * ── 해법: 그래프 스코프(옛 LLM fetcher 재현) ──────────────────────────
 * 옛 fetcher 는 get_neighbors/get_related 로 **그래프를 따라가며** 카탈로그를 만들었다.
 * 그 산출물(NexusSystem git HEAD, 246건)을 정답지로 놓고 규칙을 역산한 결과, 옛 방식의
 * 실제 배치 원칙은 "domain_id 소속" 이 아니라 다음이었다:
 *
 *   **ITEM 은 자기 domain_id 도메인 + 1-hop 이웃이 속한 도메인 모두의 키트에 들어간다.**
 *
 * 예) EVT-003 은 domain_id=DOMAIN-001 이지만 이웃 DFEAT-022 가 D005 라서 D005 키트에도
 *     들어 있었다(옛 키트 중복 35건의 정체). 감사 도메인이 그 이벤트를 봐야 하기 때문이다.
 *
 * 정답지 대비 실측(246건 기준):
 *   domain_id 만        총161 / 누락101   ← 사고 당시(48% 유실)
 *   orphan 회수(구버전)  총345 / 누락 27 / 과포함126
 *   **이 규칙**          총318 / 누락 24 / 과포함 96   ← 세 지표 모두 개선
 *
 * 남는 차이는 옛 fetcher 의 케이스별 LLM 판단이라 결정적 규칙으로는 재현할 수 없다.
 * 유실(구현이 설계를 못 봄)이 과포함(노이즈)보다 위험하므로 넓은 쪽으로 기운다.
 *
 * ALWAYS_GLOBAL — 그래프로 소속을 못 정하는 타입은 전역. nfr·implementation_guideline 은
 * core-item-set.md 가 project-wide 로 못박았고, permission_role 은 링크가 전부 "역할을
 * 쓰는 쪽" 만 가리켜(requires 역참조) traversal 로 소속을 정할 수 없다.
 */
const DEFAULT_ALWAYS_GLOBAL_TYPES = ["nfr", "implementation_guideline", "permission_role"];
const csvArg = (name, fallback) =>
  typeof args[name] === "string"
    ? args[name].split(",").map((t) => t.trim()).filter(Boolean)
    : fallback;
/** 옛 동작(순수 domain_id 필터)로 되돌리는 탈출구. --no-cross-domain 은 구 이름 별칭. */
const noGraphScope = Boolean(args["no-graph-scope"] || args["no-cross-domain"]);
const alwaysGlobalTypes = new Set(noGraphScope ? [] : csvArg("global-types", DEFAULT_ALWAYS_GLOBAL_TYPES));

/**
 * ── 스코프 pin (.kit-scope.json) ─────────────────────────────────────
 * 무엇을 이 도메인 키트에 담을지의 **최종 진실원**. 스킬 Phase 2 의 LLM 이 그래프를 추적해
 * 판정한 결과를 여기 적어두면, 이후 SYNC 는 LLM 없이 이 목록 그대로 결정적으로 재현한다.
 *
 * 왜 pin 인가 — 스코프를 매번 LLM 이 새로 정하면 같은 설계인데도 실행할 때마다 키트 구성이
 * 흔들리고, 그 흔들림이 델타에 NEW/RETIRED 로 나타나 "설계가 바뀐 것" 처럼 보인다.
 * 판정은 한 번, 재현은 결정적으로.
 *
 * 이 파일은 키트와 함께 **git 커밋 대상**이다 — 그래야 다른 PC·다른 사람이 같은 키트를 얻는다.
 * pin 이 없으면 그래프 스코프(자기 domain_id + 1-hop 이웃)로 폴백하고 그 사실을 경고한다.
 */
const SCOPE_SCHEMA = 1;
const scopeFileArg = typeof args["scope-file"] === "string" ? args["scope-file"] : null;
const SCOPE_PATH = scopeFileArg || (outDir ? join(outDir, ".kit-scope.json") : null);

/**
 * 유실 경고 대상 — core-item-set.md Tier 1·2 중 "항상 다운로드" 로 규정된 타입.
 * 도메인 스코프 결과가 0건인데 프로젝트 전역에는 존재하면 조용한 유실 신호다.
 * (service_interface·module_api·library_api·data_pipeline 은 프로젝트 성격상 0건이
 *  정상이라 제외 — 경고 남발은 경고를 무력화한다.)
 */
const CORE_TYPES = [
  "domain_feature", "api_endpoint", "erd", "diagram_sequence", "screen_spec",
  "use_case", "domain_event", "acceptance", "permission_role", "constant",
  "adr", "nfr", "implementation_guideline", "feature",
];

if (typeof fetch !== "function") die(1, "이 node 는 global fetch 미지원 — node 18+ 필요.");
if (!projectId) die(1, "--project <uuid> 필수.");
if (!outDir) die(1, "--out <kitdir> 필수.");
if (!API_BASE)
  die(
    1,
    "API base 를 결정할 수 없습니다.\n" +
      "  · --base-url <url> 또는 LOGICRAFT_API_BASE env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers 에 logicraft 서버를 등록하세요(자동 인식).\n" +
      "  ※ 로컬 기본값(localhost:14000)은 제거됐습니다 — 남의 머신을 조용히 찌르지 않기 위함(CO-049).",
  );
if (!API_KEY)
  die(
    1,
    "API key 를 결정할 수 없습니다.\n" +
      "  · LOGICRAFT_API_KEY env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers.<logicraft>.env.AUTH_TOKEN 을 사용하세요(자동 인식).",
  );
// 키 값은 절대 출력하지 않는다 — 출처 이름만.
process.stdout.write(`🔑 base=${API_BASE} (${BASE_SOURCE}) · key=${KEY_SOURCE}\n`);

// ── HTTP ─────────────────────────────────────────────────────────────
async function exportCall(params) {
  const url = new URL(`${API_BASE}/projects/${encodeURIComponent(projectId)}/kit-export`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  }
  let res;
  try {
    res = await fetch(url, { headers: { authorization: `Bearer ${API_KEY}` } });
  } catch (e) {
    die(2, `네트워크 오류: ${e.message} (base=${API_BASE})`);
  }
  if (res.status === 401) die(2, "인증 실패(401) — LOGICRAFT_API_KEY 확인.");
  if (res.status === 403) die(2, `권한 없음(403) — 키 스코프에 프로젝트 ${projectId} read 없음.`);
  if (res.status === 404) {
    // /kit-export 라우트 자체가 없음 = 이 서버는 배치 export 미배포(구버전).
    // 스킬은 이 종료코드(4)를 보고 옛 fetcher 방식으로 폴백해야 한다.
    die(4, `엔드포인트 미배포(404) — 이 서버에 /kit-export 가 없습니다(구버전 서버). 스킬은 fetcher 폴백을 사용하세요.`);
  }
  if (res.status === 414) die(2, "URI 너무 김(414) — ids 집합이 너무 큼. exportChunked 청크 크기를 줄이세요.");
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    die(2, `HTTP ${res.status}: ${body.slice(0, 300)}`);
  }
  return res.json();
}

/**
 * ids 스코프가 크면 GET URL 이 414 가 나므로 청크로 나눠 호출·병합.
 * idsCsv 가 없으면 domain/types 기준 단일 호출. 결과 items 를 합쳐 반환.
 */
const IDS_CHUNK = 40;
async function exportChunked(baseParams, idsCsv) {
  if (!idsCsv) {
    const r = await exportCall(baseParams);
    return Array.isArray(r.items) ? r.items : [];
  }
  const ids = String(idsCsv).split(",").map((s) => s.trim()).filter(Boolean);
  const merged = [];
  for (let i = 0; i < ids.length; i += IDS_CHUNK) {
    const chunk = ids.slice(i, i + IDS_CHUNK).join(",");
    const r = await exportCall({ ...baseParams, ids: chunk });
    if (Array.isArray(r.items)) merged.push(...r.items);
  }
  return merged;
}

// ── manifest ─────────────────────────────────────────────────────────
const MANIFEST_PATH = join(outDir, ".kit-manifest.json");

/**
 * frontmatter links 표기 포맷 버전. 이 값이 로컬 manifest 와 다르면 body 가 그대로여도
 * 전건 재렌더한다(델타 skip 이 구 포맷 파일을 영구 고착시키는 것을 막는 마이그레이션 키).
 * wikilink-v1 = 값이 "[[ID]]", backward 키가 `_backward` 접미.
 */
const LINK_FORMAT = "wikilink-v1";

async function loadManifest() {
  try {
    const txt = await fs.readFile(MANIFEST_PATH, "utf-8");
    const m = JSON.parse(txt);
    return m && typeof m === "object" && m.items ? m : { items: {} };
  } catch {
    return { items: {} }; // 최초 SYNC
  }
}

// ── 파일 경로 (기존 키트 구조: <out>/<type>/<id>.md + <out>/<type>/_raw/<id>.json) ──
function mdPath(item) {
  return join(outDir, item.type, `${item.id}.md`);
}
function rawPath(item) {
  return join(outDir, item.type, "_raw", `${item.id}.json`);
}

/** 쓰기 + 즉시 read-back 무결성 검증(수신==기록). 불일치 시 종료코드 3. */
async function writeVerified(path, content) {
  await fs.mkdir(dirname(path), { recursive: true });
  await fs.writeFile(path, content, "utf-8");
  const back = await fs.readFile(path, "utf-8");
  if (back !== content) {
    die(3, `무결성 검증 실패(수신≠기록): ${path}`);
  }
}

// ── frontmatter 재구성 (기존 키트 형식 정합) ─────────────────────────
// 서버 스켈레톤 body(=설계 내용, verbatim)는 보존하고, frontmatter 만
// 동기화 메타(synced_at·status·prev_version·raw·domain)+그래프 links 로 재작성.

/** 서버 스켈레톤의 앞 frontmatter 블록(---...---)을 떼고 body 만 반환. */
function stripFrontmatter(md) {
  if (md.startsWith("---\n")) {
    const end = md.indexOf("\n---\n", 4);
    if (end !== -1) return md.slice(end + 5).replace(/^\n+/, "");
  }
  return md.replace(/^\n+/, "");
}

/**
 * ITEM id → Obsidian wikilink 리터럴.
 * YAML flow sequence 안에서 [[X]] 를 그대로 두면 중첩 배열로 파싱되므로 반드시 quote 한다.
 * 키트 파일명이 {ID}.md 이고 볼트 내 ID 는 유일하므로 폴더 무관하게 해석된다.
 */
const wikilink = (id) => `"[[${String(id).trim()}]]"`;

/**
 * 서버 links {forward:{rel:[ids]}, backward:{rel:[ids]}} → frontmatter YAML. 없으면 "".
 * 값은 wikilink 로 기록해 docs/design 을 Obsidian 볼트로 열면 설계 그래프가 그대로 보인다.
 * backward 는 ` (backward)` 대신 `_backward` 접미 — 공백·괄호 없는 키여야 Obsidian
 * properties 로 정상 표시된다(YAML 자체는 둘 다 유효).
 */
function renderLinks(links) {
  if (!links || typeof links !== "object") return "";
  const lines = ["links:"];
  let any = false;
  for (const [dir, suffix] of [["forward", ""], ["backward", "_backward"]]) {
    const grp = links[dir];
    if (grp && typeof grp === "object") {
      for (const [rel, ids] of Object.entries(grp)) {
        if (Array.isArray(ids) && ids.length) {
          lines.push(`  ${rel}${suffix}: [${ids.map(wikilink).join(", ")}]`);
          any = true;
        }
      }
    }
  }
  return any ? lines.join("\n") + "\n" : "";
}

// host origin (API_BASE 에서 끝의 /api 제거) — html 내 '/api/static/...' 는 host 루트 절대경로.
const ORIGIN = API_BASE.replace(/\/api\/?$/, "");

/** 임의 full URL 텍스트 fetch. 공개 정적 서빙이라도 Bearer 붙여 무해. 실패 시 null. */
async function fetchText(full) {
  try {
    const r = await fetch(full, { headers: { authorization: `Bearer ${API_KEY}` } });
    if (!r.ok) return null;
    return await r.text();
  } catch {
    return null;
  }
}

/** 렌더 자산 URL fetch — '/uploads/...'(상대, API_BASE 하위) 또는 절대. */
async function fetchAsset(url) {
  const full = /^https?:\/\//.test(url) ? url : `${API_BASE}${url}`;
  return fetchText(full);
}

/**
 * ITEM data 의 렌더 메타(static_renders[]·renders[])를 따라 실제 렌더 파일을
 * /api/uploads/ 에서 받아 {type}/{ID}/{render_id}.{html,css} 로 기록. 전부 결정적·LLM 0.
 * html 이 참조하는 host-절대 정적 css(예: /api/static/wireframe/wireframe.css)는
 * 같은 폴더에 basename 으로 self-contain 하고 링크를 상대경로로 치환(오프라인 렌더 가능).
 */
async function fetchRenders(item) {
  const data = item.raw_json?.data ?? {};
  const list = [
    ...(Array.isArray(data.static_renders) ? data.static_renders : []),
    ...(Array.isArray(data.renders) ? data.renders : []),
  ];
  let n = 0;
  const dir = join(outDir, item.type, item.id);
  for (const r of list) {
    const rid = String(r.id ?? r.surface ?? "render");
    if (r.url) {
      let html = await fetchAsset(String(r.url));
      if (html != null) {
        // html 이 링크하는 host-절대 정적 css 를 self-contain (예: 공통 wireframe.css)
        const refs = [...html.matchAll(/(?:href|src)="(\/api\/static\/[^"]+\.css)"/g)].map((m) => m[1]);
        for (const ref of [...new Set(refs)]) {
          const css = await fetchText(`${ORIGIN}${ref}`);
          if (css != null) {
            const base = ref.split("/").pop();
            await writeVerified(join(dir, base), css);
            html = html.split(`"${ref}"`).join(`"${base}"`);
            n++;
          }
        }
        await writeVerified(join(dir, `${rid}.html`), html);
        n++;
      }
    }
    if (r.css_url) {
      const css = await fetchAsset(String(r.css_url));
      if (css != null) {
        await writeVerified(join(dir, `${rid}.css`), css);
        n++;
      }
    }
  }
  return n;
}

/** 최종 .md = 재구성 frontmatter + 서버 body. */
function buildMd(item, status, prevVersion) {
  const head = [
    "---",
    `logicraft_item: ${item.id}`,
    `type: ${item.type}`,
    `version: ${item.version}`,
    `domain: ${item.domain_id ?? "null"}`,
    `project_id: ${projectId}`,
    `synced_at: ${new Date().toISOString()}`,
    `status: ${status}`,
    `prev_version: ${prevVersion ?? "null"}`,
    `content_hash: ${item.content_hash}`,
    `stale: ${item.stale}`,
    `raw: ./_raw/${item.id}.json`,
  ].join("\n");
  const linksBlock = renderLinks(item.links);
  const body = stripFrontmatter(item.skeleton_md);
  return `${head}\n${linksBlock}---\n\n${body}`;
}

/** .kit-scope.json 읽기. 없거나 깨졌으면 null. */
async function loadScopePin() {
  if (!SCOPE_PATH) return null;
  try {
    const m = JSON.parse(await fs.readFile(SCOPE_PATH, "utf-8"));
    if (!m || !Array.isArray(m.items)) return null;
    if (m.schema != null && m.schema > SCOPE_SCHEMA) {
      die(1, `.kit-scope.json schema ${m.schema} 는 이 다운로더(지원 ${SCOPE_SCHEMA})보다 최신입니다 — 스킬을 업데이트하세요: ${SCOPE_PATH}`);
    }
    if (m.domain && domain && m.domain !== domain) {
      die(1, `.kit-scope.json 의 domain(${m.domain}) 이 --domain(${domain}) 과 다릅니다: ${SCOPE_PATH}`);
    }
    return m;
  } catch {
    return null;
  }
}

/**
 * pin 갱신 — 서버에 새로 생겨 아직 판정되지 않은 ID 를 pending 에 적어둔다.
 * 스킬(LLM)이 다음 실행에서 이 목록만 보고 판정해 items 로 승격시킨다.
 * items 자체는 다운로더가 건드리지 않는다 — 판정은 스킬의 책임이다.
 */
async function updateScopePin(pin, pendingIds) {
  if (!SCOPE_PATH || !pin) return;
  const next = { ...pin, pending: pendingIds, last_sync_at: new Date().toISOString() };
  if (JSON.stringify(next) === JSON.stringify(pin)) return;
  await writeVerified(SCOPE_PATH, JSON.stringify(next, null, 2));
}

/**
 * 각 ITEM 이 어느 도메인 키트에 들어가는지 계산 — 옛 fetcher 의 그래프 추적을 결정적으로 재현.
 *
 * 배정 = {자기 domain_id} ∪ {1-hop 이웃들의 domain_id}
 *
 * 이웃의 도메인은 **이웃 자신의 domain_id 만** 전파한다(전파된 값을 다시 전파하지 않는다).
 * 2-hop 이상 전파는 실측상 결과가 같으면서 계산만 늘고, 무한 확산 위험도 있다.
 */
function assignDomains(all) {
  const own = new Map(); // id → 자기 domain_id (도메인 노드 자신은 자기 자신)
  for (const s of all) {
    if (s.id.startsWith("DOMAIN-")) own.set(s.id, s.id);
    else if (s.domain_id) own.set(s.id, s.domain_id);
  }
  const assigned = new Map();
  const add = (id, dm) => {
    if (!dm) return;
    let set = assigned.get(id);
    if (!set) assigned.set(id, (set = new Set()));
    set.add(dm);
  };
  for (const s of all) add(s.id, own.get(s.id));
  // links 를 무방향으로 훑어 이웃의 고유 도메인을 양쪽에 더한다.
  for (const s of all) {
    const L = s.links;
    if (!L || typeof L !== "object") continue;
    for (const dir of ["forward", "backward"]) {
      const grp = L[dir];
      if (!grp || typeof grp !== "object") continue;
      for (const ids of Object.values(grp)) {
        if (!Array.isArray(ids)) continue;
        for (const other of ids) {
          add(s.id, own.get(other)); // 이웃의 도메인 → 나
          add(other, own.get(s.id)); // 내 도메인 → 이웃
        }
      }
    }
  }
  return assigned;
}

// ── main ─────────────────────────────────────────────────────────────
async function main() {
  const started = Date.now();
  const local = await loadManifest();

  // 1) 경량 manifest (본문 없이 델타 판별) — ids 스코프면 청크로 나눠 호출
  //
  //    도메인 스코프일 때는 서버에 domain 을 넘기지 않고 **프로젝트 전역 경량 manifest** 를
  //    받아 클라이언트에서 스코프를 판정한다. 왕복은 그대로 1회이면서
  //      ① 횡단 타입을 도메인 무관하게 건져오고(유실 방지)
  //      ② 스코프 밖으로 빠진 건수를 세어 경고할 수 있다(조용한 유실 차단).
  //    경량 응답이라 전역이어도 본문이 없다(id/type/domain_id/version/hash 뿐).
  const scopePin = await loadScopePin();
  const scopeByClient = Boolean(domain) && !idsFilter && !noGraphScope;
  let globalItems = null;
  let serverItems;
  let bodyById = null; // 그래프 스코프 경로에서 이미 받아둔 본문(재페치 불필요)
  let scopeSource = "domain_id"; // domain_id | graph | pin
  let pendingIds = [];
  if (scopeByClient) {
    // 그래프가 필요하므로 본문 포함으로 받는다 — links 는 include_bodies=true 응답에만 실린다.
    // 실측(NexusSystem 285건): 경량 53KB/177ms vs 본문포함 2.1MB/237ms — 차이가 무시할 수준이고,
    // 대신 변경분 본문을 다시 받는 2차 왕복이 사라져 총 호출 수는 오히려 줄어든다.
    globalItems = await exportChunked({ types, include_bodies: "true" }, null);
    if (excludeTypes) globalItems = globalItems.filter((s) => !excludeTypes.has(s.type));
    bodyById = new Map(globalItems.map((s) => [s.id, s]));
    if (scopePin) {
      // ── pin 우선: 스킬(LLM)이 판정해 둔 목록을 그대로 재현 (결정적) ──
      scopeSource = "pin";
      const want = new Set(scopePin.items);
      serverItems = globalItems.filter((s) => want.has(s.id));
      // 판정 후보는 **그래프가 이 도메인과 연결된다고 보는 것 중 pin 에 없는 것** 으로 좁힌다.
      // 프로젝트 전역을 그대로 pending 에 넣으면 다른 도메인 ITEM 까지 섞여 신호가 죽는다.
      const assigned = assignDomains(globalItems);
      pendingIds = globalItems
        .filter(
          (s) =>
            !want.has(s.id) &&
            s.type !== "domain" && // 도메인 노드 자체는 판정 대상이 아니다(_domain.md 로 별도 처리)
            (alwaysGlobalTypes.has(s.type) || assigned.get(s.id)?.has(domain)),
        )
        .map((s) => s.id);
    } else {
      scopeSource = "graph";
      const assigned = assignDomains(globalItems);
      serverItems = globalItems.filter(
        (s) => alwaysGlobalTypes.has(s.type) || assigned.get(s.id)?.has(domain),
      );
    }
  } else {
    serverItems = await exportChunked({ domain, types, include_bodies: "false" }, idsFilter);
    // 제외 목록 적용(클라이언트 필터) — 서버 export 는 포함 필터만 지원
    if (excludeTypes) serverItems = serverItems.filter((s) => !excludeTypes.has(s.type));
  }

  // 1.5) 유실 경고 — "프로젝트엔 있는데 이번 스코프엔 0건" 인 핵심 타입을 드러낸다.
  //      다운로더가 성공만 출력해 48% 유실이 묻혔던 사고(NexusSystem 2026-08)의 재발 방지.
  const lostWarnings = [];
  if (globalItems) {
    const scopedIds = new Set(serverItems.map((s) => s.id));
    const outsideByType = {}; // type → {total, orphan} (orphan = domain_id 비어있음)
    for (const s of globalItems) {
      if (scopedIds.has(s.id)) continue;
      const e = (outsideByType[s.type] ||= { total: 0, orphan: 0 });
      e.total++;
      if (!s.domain_id) e.orphan++;
    }
    const scopedByType = {};
    for (const s of serverItems) scopedByType[s.type] = (scopedByType[s.type] || 0) + 1;
    for (const t of CORE_TYPES) {
      const out = outsideByType[t];
      if (!out) continue;
      const inside = scopedByType[t] || 0;
      const orphanNote = out.orphan ? ` (그중 domain_id 없음 ${out.orphan}건)` : "";
      if (inside === 0) {
        lostWarnings.push(
          `  🚨 ${t}: 이번 키트 0건 / 프로젝트 전역 ${out.total}건${orphanNote} — 전량 누락`,
        );
      } else {
        lostWarnings.push(`  ℹ️  ${t}: 이번 키트 ${inside}건 / 스코프 밖 ${out.total}건${orphanNote}`);
      }
    }
    if (lostWarnings.length) {
      const critical = lostWarnings.filter((l) => l.includes("🚨")).length;
      console.log(
        `\n⚠️  도메인 스코프(${domain}) 밖에 남은 핵심 ITEM 이 있습니다` +
          `${critical ? ` — 그중 ${critical}개 타입은 이번 키트에 0건` : ""}:`,
      );
      console.log(lostWarnings.join("\n"));
      console.log(
        `  ↳ 전역 수집: ${[...alwaysGlobalTypes].join(", ") || "없음"}\n` +
          `  ↳ 스코프 결정: ${scopeSource === "pin" ? ".kit-scope.json (스킬 LLM 판정 · 결정적 재현)" : "그래프 폴백 — 자기 domain_id + 1-hop 이웃"}\n` +
          `  ↳ 🚨 가 뜬 타입이 필요하면 logicraft 에서 domain_id 를 채우거나 --global-types 에 추가하세요.\n`,
      );
    }
  }

  // 1.7) 스코프 pin 상태 알림 — 미판정 신규가 남아 있으면 스킬이 처리해야 한다.
  if (scopeByClient && scopeSource === "pin" && pendingIds.length) {
    console.log(
      `\n🆕 스코프 미판정 ${pendingIds.length}건 — 서버에 새로 생겼지만 .kit-scope.json 에 없습니다.\n` +
        `  ${pendingIds.slice(0, 12).join(", ")}${pendingIds.length > 12 ? ` … 외 ${pendingIds.length - 12}건` : ""}\n` +
        `  ↳ 이번 키트에는 포함되지 않았습니다. mc-logi-implement-kit 스킬을 실행하면\n` +
        `     Phase 2 가 이 목록만 판정해 .kit-scope.json 에 반영합니다.\n`,
    );
  } else if (scopeByClient && scopeSource === "graph") {
    console.log(
      `\nℹ️  .kit-scope.json 없음 — 그래프 스코프로 폴백했습니다(옛 fetcher 재현율 약 90%).\n` +
        `  ↳ 스킬 Phase 2 를 거치면 LLM 판정 결과가 pin 으로 남아 이후 실행이 결정적으로 재현됩니다.\n`,
    );
  }

  // 2) 델타 판별 — version 또는 content_hash 변화, 신규
  //    링크 포맷이 바뀐 키트는 body 가 그대로여도 전건 재렌더 대상에 넣되(frontmatter 갱신),
  //    status 는 실제 변경 기준을 유지한다 — 포맷 마이그레이션이 changelog 를 오염시키면 안 된다.
  const formatMigration = Object.keys(local.items).length > 0 && local.link_format !== LINK_FORMAT;
  const changed = [];
  const deltaMeta = {}; // id → {status, prev_version}
  for (const s of serverItems) {
    const l = local.items[s.id];
    if (!l || l.version !== s.version || l.content_hash !== s.content_hash) {
      changed.push(s);
      deltaMeta[s.id] = { status: l ? "CHANGED" : "NEW", prev_version: l ? l.version : null };
    } else if (formatMigration) {
      changed.push(s); // 재렌더만 — 설계 내용은 그대로
      deltaMeta[s.id] = { status: "UNCHANGED", prev_version: null };
    }
  }
  if (formatMigration) {
    console.log(`🔗 링크 포맷 마이그레이션 (${local.link_format ?? "legacy"} → ${LINK_FORMAT}) — 전건 재렌더`);
  }
  // 삭제 감지 — 이번 필터 범위(domain/types/ids)에서 로컬에 있으나 서버에 없는 것
  const serverIds = new Set(serverItems.map((s) => s.id));
  const idsSet = idsFilter ? new Set(String(idsFilter).split(",").map((s) => s.trim()).filter(Boolean)) : null;
  const inScope = (id, l) =>
    (idsSet ? idsSet.has(id) : true) &&
    (!domain || l.domain_id === domain || alwaysGlobalTypes.has(l.type)) &&
    (!types || String(types).split(",").map((t) => t.trim()).includes(l.type)) &&
    (!excludeTypes || !excludeTypes.has(l.type));
  // 그래프 스코프에서는 배정이 links 로 정해져 로컬 manifest 만으로 재현할 수 없다.
  // 그래서 "서버 프로젝트 전체에서 사라진 것" 만 RETIRED 로 본다 — 스코프가 좁아져
  // 이번에 안 담긴 ITEM 을 삭제로 오인해 지우는 사고를 막는다(유실 방지 우선).
  const globalIds = globalItems ? new Set(globalItems.map((s) => s.id)) : null;
  const deleted = Object.entries(local.items)
    .filter(([id, l]) => (globalIds ? !globalIds.has(id) : inScope(id, l) && !serverIds.has(id)))
    .map(([id]) => id);

  console.log(
    `📊 서버 ${serverItems.length}건 · 변경 ${changed.length} · 유지 ${serverItems.length - changed.length}` +
      (deleted.length ? ` · 삭제 ${deleted.length}` : ""),
  );

  if (dryRun) {
    if (changed.length) console.log("  변경:", changed.map((c) => `${c.id}(v${c.version})`).join(", "));
    if (deleted.length) console.log("  삭제:", deleted.join(", "));
    console.log("— dry-run, 디스크 미변경 —");
    return;
  }

  // 3) 변경분 본문 — 그래프 스코프에서는 1) 에서 이미 본문까지 받았으므로 재페치하지 않는다.
  let bodies = [];
  if (changed.length) {
    bodies = bodyById
      ? changed.map((c) => bodyById.get(c.id)).filter(Boolean)
      : await exportChunked({ domain, types, include_bodies: "true" }, changed.map((c) => c.id).join(","));
  }

  // 4) 디스크 기록 + 무결성 검증 (+ 렌더 정적파일 페치)
  let wrote = 0;
  let renders = 0;
  for (const item of bodies) {
    if (item.skeleton_md == null || item.raw_json == null) {
      process.stderr.write(`⚠ ${item.id}: 본문 누락(skeleton/raw) — 건너뜀\n`);
      continue;
    }
    // 기존 키트 _raw 포맷과 동일하게 {item: ...} 래핑
    const rawStr = JSON.stringify({ item: item.raw_json }, null, 2);
    await writeVerified(rawPath(item), rawStr);
    // frontmatter 재구성(동기화 메타 + links) + 서버 body 보존
    const meta = deltaMeta[item.id] || { status: "CHANGED", prev_version: null };
    await writeVerified(mdPath(item), buildMd(item, meta.status, meta.prev_version));
    wrote++;
    // 렌더(와이어프레임·SD 디자인) 정적파일도 URL 따라 받음 (있는 ITEM 만)
    renders += await fetchRenders(item);
  }

  // 5) RETIRED 반영 — 삭제 대신 _retired/ 로 이동(키트 컨벤션: 원본 보존)
  async function moveIfExists(from, to) {
    try {
      await fs.mkdir(dirname(to), { recursive: true });
      await fs.rename(from, to);
    } catch {
      /* 없으면 무시 */
    }
  }
  for (const id of deleted) {
    const l = local.items[id];
    if (!l) continue;
    await moveIfExists(join(outDir, l.type, `${id}.md`), join(outDir, "_retired", l.type, `${id}.md`));
    await moveIfExists(
      join(outDir, l.type, "_raw", `${id}.json`),
      join(outDir, "_retired", l.type, "_raw", `${id}.json`),
    );
  }

  // 6) manifest 갱신 — 서버 메타를 진실로 기록
  const nextItems = {};
  for (const s of serverItems) {
    nextItems[s.id] = {
      type: s.type,
      domain_id: s.domain_id ?? null,
      version: s.version,
      content_hash: s.content_hash,
    };
  }
  const manifest = {
    project_id: projectId,
    domain: domain ?? null,
    synced_at: new Date().toISOString(),
    source: `${API_BASE}/projects/${projectId}/items/export`,
    link_format: LINK_FORMAT,
    global_types: [...alwaysGlobalTypes],
    scope_mode: scopeSource,
    count: serverItems.length,
    items: nextItems,
  };
  await writeVerified(MANIFEST_PATH, JSON.stringify(manifest, null, 2));

  // 6.5) pin 의 pending 갱신 — 판정은 스킬 몫이므로 items 는 건드리지 않는다.
  //      pin 이 없을 때 그래프 폴백 결과를 pin 으로 굳히지도 않는다(LLM 판정을 건너뛴 채
  //      90% 결과가 영구 고착되면 pin 의 의미가 사라진다).
  if (scopeSource === "pin") await updateScopePin(scopePin, pendingIds);

  // 7) version-master.md — 다운스트림 mc-logi-implement 소비(신선도 게이트·changelog·ITEM 표)
  const mode = Object.keys(local.items).length === 0 ? "INITIAL" : "SYNC";
  const statusAll = {};
  for (const s of serverItems) statusAll[s.id] = deltaMeta[s.id]?.status || "UNCHANGED";
  const nNew = Object.values(statusAll).filter((v) => v === "NEW").length;
  const nChanged = Object.values(statusAll).filter((v) => v === "CHANGED").length;
  const nUnchanged = Object.values(statusAll).filter((v) => v === "UNCHANGED").length;
  const rows = serverItems
    .slice()
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((s) => `| [[${s.id}]] | ${s.type} | ${s.version} | ${statusAll[s.id]} |`)
    .join("\n");
  const changelog =
    [
      ...changed.filter((s) => deltaMeta[s.id]?.status === "NEW").map((s) => `- NEW [[${s.id}]]`),
      ...changed
        .filter((s) => deltaMeta[s.id]?.status === "CHANGED")
        .map((s) => `- CHANGED [[${s.id}]] (prev v${deltaMeta[s.id].prev_version})`),
      ...deleted.map((id) => `- RETIRED [[${id}]] → _retired/`),
    ].join("\n") || "- (변경 없음)";
  const vm =
    `# Version Master${domain ? ` — ${domain}` : ""}\n\n` +
    `| 항목 | 값 |\n|---|---|\n` +
    `| project_id | ${projectId} |\n` +
    `| Domain | ${domain ?? "(전체)"} |\n` +
    `| Last sync | ${manifest.synced_at} |\n` +
    `| Mode | ${mode} — NEW ${nNew} / CHANGED ${nChanged} / UNCHANGED ${nUnchanged}` +
    `${deleted.length ? ` / RETIRED ${deleted.length}` : ""} |\n` +
    `| 출력 루트 | ${outDir} |\n` +
    `| 생성 | download-kit.mjs (결정적 다운로드, LLM 0) |\n` +
    `| 링크 포맷 | ${LINK_FORMAT} — frontmatter \`links:\` 가 \`[[ID]]\` wikilink |\n` +
    (domain
      ? `| 스코프 | ${domain} — ${{ pin: ".kit-scope.json (스킬 LLM 판정)", graph: "그래프 폴백(자기 domain_id + 1-hop 이웃)", domain_id: "domain_id 일치만" }[scopeSource]} |\n` +
        `| 전역 수집 | ${[...alwaysGlobalTypes].join(", ") || "없음"} |\n` +
        (pendingIds.length ? `| ⚠️ 미판정 | ${pendingIds.length}건 — 스킬 Phase 2 판정 필요(이번 키트 미포함) |\n` : "")
      : "") +
    "\n" +
    (lostWarnings.length
      ? `## ⚠️ 스코프 밖 ITEM (유실 점검)\n\n` +
        `도메인 필터는 \`domain_id\` 컬럼 일치만 본다. 아래는 이번 스코프에 들어오지 않은 핵심 타입이다.\n` +
        `**🚨 = 프로젝트엔 있는데 이번 키트엔 0건** — 구현이 그 설계를 못 본다.\n\n` +
        "```\n" + lostWarnings.join("\n") + "\n```\n\n" +
        `해소: logicraft 에서 해당 ITEM 의 \`domain_id\` 를 채우거나, 다운로드 시\n` +
        `\`--cross-domain-types\` 에 그 타입을 추가한다.\n\n`
      : "") +
    `> 💡 이 키트 루트를 Obsidian 볼트로 열면 ITEM 관계가 그래프로 보인다.\n` +
    `> 그래프뷰 → 필터 → *Existing files only* 를 켜면 키트 밖 ITEM(MOD·LEGACY 등)의\n` +
    `> 유령 노드가 사라진다.\n\n` +
    `## Changelog (this run)\n\n${changelog}\n\n` +
    `## ITEM 표\n\n| ID | type | version | status |\n|---|---|---|---|\n${rows}\n`;
  await writeVerified(join(outDir, "version-master.md"), vm);

  // 7.5) run-report (옵션) — 후처리 스크립트(arrange-screen-kit)가 이번 run 의
  //      per-item status·삭제·모드를 네트워크 없이 읽도록 기록. 본문 페치와 무관.
  if (reportPath) {
    const reportItems = {};
    for (const s of serverItems) {
      reportItems[s.id] = {
        type: s.type,
        version: s.version,
        content_hash: s.content_hash,
        status: statusAll[s.id],
        prev_version: deltaMeta[s.id]?.prev_version ?? null,
      };
    }
    await writeVerified(
      reportPath,
      JSON.stringify({ mode, synced_at: manifest.synced_at, project_id: projectId, domain: domain ?? null, items: reportItems, deleted }, null, 2),
    );
  }

  const secs = ((Date.now() - started) / 1000).toFixed(1);
  console.log(
    `✅ SYNC 완료 — 기록 ${wrote}건${renders ? ` · 렌더 ${renders}파일` : ""}` +
      `${deleted.length ? ` · 삭제 ${deleted.length}` : ""} · ${secs}s · 무열화 검증 통과`,
  );
}

main().catch((e) => die(2, e && e.stack ? e.stack : String(e)));
