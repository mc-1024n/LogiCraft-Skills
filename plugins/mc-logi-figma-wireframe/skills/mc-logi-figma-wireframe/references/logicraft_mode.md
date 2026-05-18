# 모드 A — Logicraft SCREEN 기반 워크플로우

## 전제

mcp__logicraft__get_item / update_item + Figma MCP(use_figma/get_metadata/get_screenshot). 도구 부재 시 보고 후 중단.

## 1. 입력

project_id(필수, 없으면 요청) + SCREEN-NNN. 'SCREEN-001~005'=5개, 'SCREEN-001,003'=지정, 'DOMAIN-001 SCREEN 다'=list_items 후 추출. --register 기본 ON.

## 2. SCREEN 조회

get_item(project_id,'SCREEN-NNN') → data.{title,route,purpose,device,sections[],realizes_use_cases,consumes_apis,required_roles,external_designs}. sections 비면 생성불가 보고. 옛 문자열 components → {type:'Custom',label,custom_name}.

## 3. 캔버스

다중 가로 200px 간격. get_metadata 로 기존 노드 파악.

## 4. 프레임

루트 VERTICAL + resize 후 AUTO 재설정. 메타헤더(SCREEN-NNN·title·route·Realizes·Consumes). role: header상단→navigation→hero→(filter240~280+main FILL+side300~360 HORIZONTAL)→footer→modal별도. layout: form/list/detail/dashboard/grid/tabs/stack.

## 5. 메타 캡션

triggers_api → 우측 '→ API-NNN' Poppins 11px #999 HORIZONTAL 8px.

## 6. 검증

get_screenshot → URL+이미지+개수+등록결과. 그레이스케일/폰트/AutoLayout/누락없음 체크.

## 7. external_designs 등록 (--register 기본 ON)

get_item → data.external_designs 에 { source:'figma', url:'<URL>?node-id=<id>', label:'Auto-generated wireframe (mc-logi-figma-wireframe)', node_id, preview_image_url, synced_at } 추가 → update_item(base_version, change_summary='v<N>: external_designs 자동 등록 (mc-logi-figma-wireframe, Figma node <id>)', data). 충돌 1회 재시도. 동일 node_id면 synced_at 갱신.

## 에러

Figma MCP 부재/sections 비음/노드 초과(분할)/base_version 충돌(1회 재시도 후 보고).
