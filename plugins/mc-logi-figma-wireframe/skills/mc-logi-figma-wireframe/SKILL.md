---
name: mc-logi-figma-wireframe
description: "Logicraft 의 SCREEN 화면정의서를 Figma 에 흑백 로우피델리티 와이어프레임으로 자동 렌더링하는 스킬. SCREEN-NNN ID 를 받으면 sections/components/role/layout/triggers_api 메타를 그대로 시각화하고, 결과 Figma 노드를 SCREEN.external_designs[] 에 자동 등록. PRD + IA 차트 텍스트로도 일반 와이어프레임 생성 가능. 사용자가 'SCREEN 와이어프레임', 'Logicraft 화면 그려줘', '화면정의서 시각화', '와이어프레임 만들어줘', 'figma 와이어프레임' 을 말하거나 SCREEN-NNN 같은 Logicraft ID 를 언급하며 시각화·다이어그램·Figma 출력을 요청할 때 반드시 이 스킬을 사용. 기획서·화면 설계·UI 와이어프레임·로우피델리티 디자인이 필요한 모든 경우에 트리거. 'wireframe 그려줘' 같은 짧은 요청에서도 적극 트리거."
user_invocable: true
metadata:
  version: 1.0.0
---

# mc-logi-figma-wireframe 스킬

Logicraft 의 SCREEN 화면정의서를 Figma 에 흑백 로우피델리티 와이어프레임으로 자동 렌더링한다. 보조 모드로 PRD + IA 차트 기반 일반 와이어프레임도 지원한다.

## 모드

- **모드 A (주)**: project_id + SCREEN-NNN → SCREEN.data 의 sections/components/role/layout 을 Figma 에 그대로 시각화 + external_designs[] 자동 등록 (--register 기본 ON).
- **모드 B**: PRD + IA 차트 → 일반 패턴 와이어프레임.

신호(SCREEN-NNN / project_id / 화면정의서 / wireframe) 명확 시 재확인 없이 바로 진행. 시작 시 모드 안내 출력.

## 공통 규칙 (필수)

- 컬러: 그레이스케일만. Primary·브랜드 컬러 금지. 강조는 굵기·크기로.
- 폰트: Pretendard(한국어)/Poppins(영어), 폴백 Noto Sans KR.
- 레이아웃: Auto Layout + Hug. 절대 좌표 금지. Desktop 1440px 기본.
- AI 느낌 배제: 이모지·그라디언트·글로우 금지.

전체 규칙·매핑·헬퍼는 references/ 문서 참조 (logicraft_mode / logicraft_mapping / prd_mode / grayscale_rules / figma_helpers).

## --register (기본 ON)

Figma 출력 후 mcp__logicraft__update_item 으로 SCREEN.data.external_designs[] 에 { source:'figma', url, label:'Auto-generated wireframe (mc-logi-figma-wireframe)', node_id, preview_image_url, synced_at } 추가. '--no-register' 명시 시 스킵.

## 한계

흑백 로우피델리티 전용. 특수 화면 단순화. Figma 노드 수 제한 시 섹션 분할. Custom 컴포넌트는 박스+라벨만.
