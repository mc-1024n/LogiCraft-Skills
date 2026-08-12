# download-kit.mjs — 소스 캐리어 (배포-안전 단일 진실원)

> 이 파일은 `bin/download-kit.mjs` 의 **정본 소스**다. 스킬 배포 시 `bin/` 이 누락돼도
> 이 `.md` 는 포함되므로, 스크립트가 없을 때 Phase 3 가용성 게이트가 이 코드블록을
> 그대로 `bin/download-kit.mjs` 로 써서 재생성한다. **bin/ 을 수정하면 이 파일도 동기화할 것.**

```js
#!/usr/bin/env node
/**
 * download-kit.mjs — 키트 SYNC 무열화 결정적 다운로더 (ADR-026 / DFEAT-057 / API-152)
 *
 * LLM 0. LogiCraft 배치 export 엔드포인트(API-152)를 호출해 설계 ITEM 을
 * 원본 JSON(_raw/*.json) + 서버 결정적 스켈레톤(*.md) 으로 로컬 키트에 내려받는다.
 * 델타(version/content_hash 비교)로 변경분만 페치하고, 디스크 쓰기 무결성을
 * 수신==기록 바이트 비교로 검증한다. content_hash 는 재계산하지 않는다(서버 함수
 * 복제 회피 = ADR-026 "드리프트 0" 정신 유지 — 서버 hash 를 델타 키로 그대로 사용).
 *
 * 인증: MCP 와 동일한 lc_ api-key 를 LOGICRAFT_API_KEY env 에서 읽어 Bearer 로.
 *
 * 사용:
 *   LOGICRAFT_API_KEY=lc_... LOGICRAFT_API_BASE=http://localhost:3001/api \
 *   node download-kit.mjs --project <uuid> --out <kitdir> [--domain DOMAIN-003] \
 *        [--types adr,domain_feature] [--exclude-types code_module,rfp_item] [--dry-run]
 *
 * 타입 선택 (동적 fail-open 권장 — 신규 ITEM 타입 자동 포함):
 *   --types         포함 목록(CSV). 지정 시 그 타입만 받음 — 서버에 신규 타입이 늘어나도 자동 포함 안 됨.
 *   --exclude-types 제외 목록(CSV). --types 생략 + 이것만 지정하면 "도메인 전체 − 제외" 를 받음
 *                   → 서버에 ITEM 타입이 새로 추가되어도 키트에 자동 포함(fail-open). 둘 다 지정 시 둘 다 적용.
 *
 * 종료코드: 0=성공, 1=인자/환경 오류, 2=네트워크/인증 오류(수정필요), 3=무결성 검증 실패,
 *          4=엔드포인트 미배포(404 — 서버에 /kit-export 없음, 스킬은 fetcher 폴백)
 */
import { promises as fs } from "node:fs";
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

const args = parseArgs(process.argv.slice(2));
const API_BASE = (args["base-url"] || process.env.LOGICRAFT_API_BASE || "http://localhost:14000/api").replace(/\/$/, "");
const API_KEY = process.env.LOGICRAFT_API_KEY || "";
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

if (typeof fetch !== "function") die(1, "이 node 는 global fetch 미지원 — node 18+ 필요.");
if (!projectId) die(1, "--project <uuid> 필수.");
if (!outDir) die(1, "--out <kitdir> 필수.");
if (!API_BASE) die(1, "LOGICRAFT_API_BASE (또는 --base-url) 필수. 예: http://localhost:3001/api");
if (!API_KEY) die(1, "LOGICRAFT_API_KEY env 필수 (MCP 와 동일한 lc_ 키).");

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

/** 서버 links {forward:{rel:[ids]}, backward:{rel:[ids]}} → frontmatter YAML. 없으면 "". */
function renderLinks(links) {
  if (!links || typeof links !== "object") return "";
  const lines = ["links:"];
  let any = false;
  for (const [dir, suffix] of [["forward", ""], ["backward", " (backward)"]]) {
    const grp = links[dir];
    if (grp && typeof grp === "object") {
      for (const [rel, ids] of Object.entries(grp)) {
        if (Array.isArray(ids) && ids.length) {
          lines.push(`  ${rel}${suffix}: [${ids.join(", ")}]`);
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

// ── main ─────────────────────────────────────────────────────────────
async function main() {
  const started = Date.now();
  const local = await loadManifest();

  // 1) 경량 manifest (본문 없이 델타 판별) — ids 스코프면 청크로 나눠 호출
  let serverItems = await exportChunked({ domain, types, include_bodies: "false" }, idsFilter);
  // 제외 목록 적용(클라이언트 필터) — 서버 export 는 포함 필터만 지원
  if (excludeTypes) serverItems = serverItems.filter((s) => !excludeTypes.has(s.type));

  // 2) 델타 판별 — version 또는 content_hash 변화, 신규
  const changed = [];
  const deltaMeta = {}; // id → {status, prev_version}
  for (const s of serverItems) {
    const l = local.items[s.id];
    if (!l || l.version !== s.version || l.content_hash !== s.content_hash) {
      changed.push(s);
      deltaMeta[s.id] = { status: l ? "CHANGED" : "NEW", prev_version: l ? l.version : null };
    }
  }
  // 삭제 감지 — 이번 필터 범위(domain/types/ids)에서 로컬에 있으나 서버에 없는 것
  const serverIds = new Set(serverItems.map((s) => s.id));
  const idsSet = idsFilter ? new Set(String(idsFilter).split(",").map((s) => s.trim()).filter(Boolean)) : null;
  const inScope = (id, l) =>
    (idsSet ? idsSet.has(id) : true) &&
    (!domain || l.domain_id === domain) &&
    (!types || String(types).split(",").map((t) => t.trim()).includes(l.type)) &&
    (!excludeTypes || !excludeTypes.has(l.type));
  const deleted = Object.entries(local.items)
    .filter(([id, l]) => inScope(id, l) && !serverIds.has(id))
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

  // 3) 변경분 본문 페치 (있을 때만) — 청크로 나눠 호출(414 회피)
  let bodies = [];
  if (changed.length) {
    bodies = await exportChunked({ domain, types, include_bodies: "true" }, changed.map((c) => c.id).join(","));
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
    count: serverItems.length,
    items: nextItems,
  };
  await writeVerified(MANIFEST_PATH, JSON.stringify(manifest, null, 2));

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
    .map((s) => `| ${s.id} | ${s.type} | ${s.version} | ${statusAll[s.id]} |`)
    .join("\n");
  const changelog =
    [
      ...changed.filter((s) => deltaMeta[s.id]?.status === "NEW").map((s) => `- NEW ${s.id}`),
      ...changed
        .filter((s) => deltaMeta[s.id]?.status === "CHANGED")
        .map((s) => `- CHANGED ${s.id} (prev v${deltaMeta[s.id].prev_version})`),
      ...deleted.map((id) => `- RETIRED ${id} → _retired/`),
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
    `| 생성 | download-kit.mjs (결정적 다운로드, LLM 0) |\n\n` +
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
```
