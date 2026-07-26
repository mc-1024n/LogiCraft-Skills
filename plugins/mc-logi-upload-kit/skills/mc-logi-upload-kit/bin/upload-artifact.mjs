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
 * 인증: LOGICRAFT_API_KEY (MCP 와 동일한 lc_ 키) → Authorization: Bearer.
 * 서버: LOGICRAFT_API_BASE (기본 http://localhost:14000/api).
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

// ── 인자 파싱 ────────────────────────────────
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

const API_KEY = process.env.LOGICRAFT_API_KEY;
if (!API_KEY) die(2, "LOGICRAFT_API_KEY 환경변수 필요(MCP 와 동일한 lc_ 키).");
const BASE = (process.env.LOGICRAFT_API_BASE || "http://localhost:14000/api").replace(/\/$/, "");

// ── 파일 읽기 ─────────────────────────────────
let body;
try {
  body = await readFile(file, "utf8");
} catch (e) {
  die(3, `파일 읽기 실패: ${file} — ${e.message}`);
}

// ── 쿼리스트링 조립 ───────────────────────────
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

// ── 타입별 요청 구성 ──────────────────────────
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

// ── 전송 ──────────────────────────────────
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
