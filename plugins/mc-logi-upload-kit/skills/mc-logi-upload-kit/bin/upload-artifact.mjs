#!/usr/bin/env node
/**
 * mc-logi-upload-kit — 로컬 파일을 LogiCraft REST 업로드 엔드포인트로 직송.
 *
 * download-kit.mjs(키트 다운로더)의 역방향. 파일 본문이 AI 컨텍스트를 거치지 않으므로
 * 5MB 데모도 토큰 0 으로 등록된다(ADR-029, CO-007).
 *
 * 대상 타입(--type)별 엔드포인트:
 *   app_demo          POST /projects/:project/demos/upload                         (JSON {html})
 *   app_demo_version  POST /projects/:project/demos/:parent/versions/upload        (JSON {html})
 *   project_artifact  POST /projects/:project/artifacts/upload                     (JSON {html})
 *   attachment        POST /projects/:project/artifacts/:parent/attachments/upload (JSON {markdown})
 *   design_render     POST /projects/:project/items/:parent/design-render/upload   (multipart html[+css])
 *
 * 인증: LOGICRAFT_API_KEY env → 없으면 ~/.claude.json 의 mcpServers(logicraft*) 에서 자동 조달.
 *       base 도 동일(LOGICRAFT_API_BASE > MCP 설정). **로컬 기본값 없음**(CO-049).
 *       --server <name> 으로 MCP 항목 지정 가능(기본 logicraft → logicraft-dev).
 *
 * 종료코드: 0 성공 · 1 인자 오류 · 2 HTTP/인증 오류 · 3 파일 오류.
 *
 * 사용:
 *   node upload-artifact.mjs --type app_demo --project <uuid> --file demo.html --title "글래스모피즘 버전"
 *   node upload-artifact.mjs --type app_demo_version --project <uuid> --parent <demoId> --file v2.html --change-note "리디자인"
 *   node upload-artifact.mjs --type project_artifact --project <uuid> --file report.html --title "월간 보고"
 *   node upload-artifact.mjs --type attachment --project <uuid> --parent <artifactId> --file notes.md --title "근거 문서"
 *   node upload-artifact.mjs --type design_render --project <uuid> --parent SD-012 --file design.html --css design.css --surface main
 */
import { readFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// ── 인자 파싱 ─────────────────────────────────────────────
function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        out[key] = true;
      } else {
        out[key] = next;
        i++;
      }
    }
  }
  return out;
}

function die(code, msg) {
  process.stderr.write(`✖ ${msg}\n`);
  process.exit(code);
}

const args = parseArgs(process.argv.slice(2));
const type = args.type;
const project = args.project;
const file = args.file;

const VALID = [
  "app_demo",
  "app_demo_version",
  "project_artifact",
  "attachment",
  "design_render",
];
if (!type || !VALID.includes(type)) {
  die(1, `--type 은 ${VALID.join(" | ")} 중 하나. (받음: ${type ?? "없음"})`);
}
if (!project) die(1, "--project <uuid> 필수.");
if (!file) die(1, "--file <경로> 필수.");
if ((type === "app_demo_version" || type === "attachment" || type === "design_render") && !args.parent) {
  die(1, `--type ${type} 은 --parent <${type === "attachment" ? "artifactId" : type === "design_render" ? "SD-ID" : "demoId"}> 필수.`);
}

/**
 * MCP 설정 폴백 — env 가 없을 때 ~/.claude.json 의 mcpServers 에서 api-key·base 를 읽는다.
 * 예전 기본값 `localhost:14000` 은 개발 머신 포트라, 다른 환경에서는 자기 빈 로컬을 찔러
 * "서버 접속 불가"로 죽었다. 기본값을 없애고 MCP 설정에서 실제 서버를 읽는다(CO-049).
 * 키 값은 로그에 출력하지 않는다(출처 이름만).
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
        const h = argv.find((a) => typeof a === "string" && /^authorization\s*:/i.test(a));
        if (h) key = h.slice(h.indexOf(":") + 1);
      }
      key = String(key).replace(/^\s*Bearer\s+/i, "").trim();
      if (/^\$\{.*\}$/.test(key)) key = "";
      const urlArg = argv.find((a) => typeof a === "string" && /^https?:\/\//.test(a));
      const base = urlArg ? urlArg.replace(/\/mcp\/?$/, "").replace(/\/$/, "") : "";
      if (key || base) return { name, key, base };
    }
  }
  return null;
}

const _mcp =
  !process.env.LOGICRAFT_API_KEY || !process.env.LOGICRAFT_API_BASE
    ? readMcpConfig(typeof args.server === "string" ? args.server : null)
    : null;
const API_KEY = String(process.env.LOGICRAFT_API_KEY || (_mcp && _mcp.key) || "")
  .replace(/^\s*Bearer\s+/i, "")
  .trim();
const BASE = String(process.env.LOGICRAFT_API_BASE || (_mcp && _mcp.base) || "").replace(/\/$/, "");
const KEY_SOURCE = process.env.LOGICRAFT_API_KEY ? "env" : _mcp && _mcp.key ? `MCP(${_mcp.name})` : "없음";
const BASE_SOURCE = process.env.LOGICRAFT_API_BASE ? "env" : _mcp && _mcp.base ? `MCP(${_mcp.name})` : "없음";
if (!BASE)
  die(
    1,
    "API base 를 결정할 수 없습니다.\n" +
      "  · LOGICRAFT_API_BASE env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers 에 logicraft 서버를 등록하세요(자동 인식).\n" +
      "  ※ 로컬 기본값(localhost:14000)은 제거됐습니다 — 남의 머신을 조용히 찌르지 않기 위함(CO-049).",
  );
if (!API_KEY)
  die(
    2,
    "API key 를 결정할 수 없습니다.\n" +
      "  · LOGICRAFT_API_KEY env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers.<logicraft>.env.AUTH_TOKEN 을 사용하세요(자동 인식).\n" +
      "  ※ 업로드는 write 권한이 필요합니다 — read 전용 키면 403 이 납니다.",
  );
// 키 값은 절대 출력하지 않는다 — 출처 이름만.
process.stdout.write(`🔑 base=${BASE} (${BASE_SOURCE}) · key=${KEY_SOURCE}\n`);

// ── 파일 읽기 ─────────────────────────────────────────────
let body;
try {
  body = await readFile(file, "utf8");
} catch (e) {
  die(3, `파일 읽기 실패: ${file} — ${e.message}`);
}

// ── 쿼리스트링 조립 ───────────────────────────────────────
function qs(params) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== true && v !== "") u.set(k, String(v));
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

const enc = encodeURIComponent;
const auth = { Authorization: `Bearer ${API_KEY}` };

// ── 타입별 요청 구성 ──────────────────────────────────────
let url, init;
switch (type) {
  case "app_demo":
    url = `${BASE}/projects/${enc(project)}/demos/upload` +
      qs({ title: args.title, description: args.description, tags: args.tags });
    init = { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ html: body }) };
    if (!args.title) die(1, "--type app_demo 은 --title 필수.");
    break;
  case "app_demo_version":
    url = `${BASE}/projects/${enc(project)}/demos/${enc(args.parent)}/versions/upload` +
      qs({ change_note: args["change-note"] });
    init = { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ html: body }) };
    break;
  case "project_artifact":
    url = `${BASE}/projects/${enc(project)}/artifacts/upload` +
      qs({ title: args.title, category_id: args["category-id"], description: args.description, tags: args.tags });
    init = { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ html: body }) };
    if (!args.title) die(1, "--type project_artifact 은 --title 필수.");
    break;
  case "attachment":
    url = `${BASE}/projects/${enc(project)}/artifacts/${enc(args.parent)}/attachments/upload` +
      qs({ title: args.title });
    init = { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ markdown: body }) };
    if (!args.title) die(1, "--type attachment 은 --title 필수.");
    break;
  case "design_render": {
    url = `${BASE}/projects/${enc(project)}/items/${enc(args.parent)}/design-render/upload` +
      qs({ surface: args.surface });
    const form = new FormData();
    form.set("html", new Blob([body], { type: "text/html" }), "design.html");
    if (args.css) {
      let css;
      try {
        css = await readFile(args.css, "utf8");
      } catch (e) {
        die(3, `CSS 파일 읽기 실패: ${args.css} — ${e.message}`);
      }
      form.set("css", new Blob([css], { type: "text/css" }), "design.css");
    }
    init = { method: "POST", headers: { ...auth }, body: form }; // Content-Type 은 FormData 가 boundary 포함해 자동 설정
    break;
  }
}

// ── 전송 ─────────────────────────────────────────────────
let res;
try {
  res = await fetch(url, init);
} catch (e) {
  die(2, `요청 실패(네트워크): ${e.message} — BASE=${BASE} 확인.`);
}

const text = await res.text();
let json;
try {
  json = JSON.parse(text);
} catch {
  json = text;
}

if (!res.ok) {
  const code = typeof json === "object" && json?.code ? json.code : res.status;
  const msg = typeof json === "object" && json?.message ? json.message : text.slice(0, 300);
  die(2, `업로드 실패 [${res.status} ${code}]: ${msg}`);
}

process.stdout.write(`✅ ${type} 업로드 완료\n`);
process.stdout.write(JSON.stringify(json, null, 2) + "\n");
process.exit(0);
