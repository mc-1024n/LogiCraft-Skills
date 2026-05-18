# Figma MCP 패턴·헬퍼

## 도구

use_figma(JS Plugin API) / get_metadata / get_screenshot. prefix 환경별 상이. 한 호출당 노드 수 제한 → 큰 화면 분할. 분할 시 figma.currentPage.findOne(n=>n.name===...) 재참조. 매 호출 await figma.loadFontAsync 부터.

## 폰트 로드

Pretendard/Poppins Regular~Bold loadFontAsync. Pretendard 실패→Noto Sans KR 폴백(try/catch).

## 메인 프레임

widthByDevice={desktop:1440,mobile:375,tablet:768,responsive:1440}. createFrame→VERTICAL→resize(width,100)→primaryAxisSizingMode='AUTO' 재설정→fills #F5F5F5→x=maxX+200.

## 헬퍼

createText(parent,text,{family,weight,size,color,align}) fontName try/catch Noto, lineHeight ≥24→140 else180, WIDTH_AND_HEIGHT. createAutoFrame(parent,name,{direction,primarySize,counterSize,spacing,padding,fills,cornerRadius,strokes,strokeWeight}). createImagePlaceholder(#CCCCCC 박스 중앙 label). createButton(variant primary #1A1A1A/secondary outline/destructive/ghost, disabled .5). createInput(label+box 1px #999 r6 h40). createTable(헤더 #F5F5F5 SemiBold, 더미'—' layoutGrow1). createCustom(#F5F5F5 dash[4,4] 중앙 label/[Custom:name]/note).

## 분할 호출

1차 메인+Header+Hero / 2차 findOne 재참조 middleRow(HORIZONTAL primarySize FIXED **counterSize AUTO** layoutAlign STRETCH)+main+side / 3차 footer+modal(외부). 섹션>4 또는 Table/Grid 다수 시 분할.

## 렌더

renderComponent: Custom 우선, switch(type) Button/Input/Table/Heading/Text/Stat/Image/... default→Custom. renderWithApiCaption: triggers_api 있으면 HORIZONTAL wrap+'→ API'.

## 검증·에러

작업전 get_metadata / 작업후 get_screenshot(node_id). 폰트실패→Noto/기본. 노드초과→분할. 부모재참조실패→name 정확히. resize 후 AUTO 재설정 필수. ★ HORIZONTAL row height 잘림→counterSize:'AUTO'(복구 row.counterAxisSizingMode='AUTO').
