# Figma MCP 사용 패턴·헬퍼 함수

`use_figma` 도구로 와이어프레임 그릴 때 자주 쓰는 JavaScript Plugin API 코드 모음.

## 목차
- [Figma MCP 도구 개요](#figma-mcp-도구-개요)
- [폰트 로드](#폰트-로드)
- [메인 프레임 생성](#메인-프레임-생성)
- [헬퍼 함수](#헬퍼-함수)
- [섹션별 분할 호출 전략](#섹션별-분할-호출-전략)
- [컴포넌트 렌더 패턴](#컴포넌트-렌더-패턴)
- [조회·검증 (get_metadata / get_screenshot)](#조회검증-get_metadata--get_screenshot)
- [에러 패턴](#에러-패턴)

---

## Figma MCP 도구 개요

| 도구 | 용도 |
|------|------|
| `mcp__*__use_figma` | JavaScript Plugin API 코드 실행 — 노드 생성·수정 |
| `mcp__*__get_metadata` | 현재 파일·페이지·노드 정보 조회 |
| `mcp__*__get_screenshot` | 노드/페이지 스크린샷 캡처 |

도구 prefix 는 환경마다 다름 (예: `mcp__50c5...__use_figma`). 어떤 prefix 든 같은 함수 시그니처.

### 호출 시 주의
- `use_figma` 는 한 번 호출당 노드 수 제한이 있음 → 큰 화면은 분할 호출
- 분할 호출 시 부모 프레임은 `figma.currentPage.findOne(n => n.name === "...")` 으로 재참조
- 모든 호출은 `await figma.loadFontAsync(...)` 부터 시작 (이전 호출에서 로드해도 다시 로드 필요)

---

## 폰트 로드

```javascript
// 매 use_figma 호출 시작 시 — 실패하면 Noto Sans KR 로 fallback
async function loadFonts() {
  const fonts = [
    { family: "Pretendard", style: "Regular" },
    { family: "Pretendard", style: "Medium" },
    { family: "Pretendard", style: "SemiBold" },
    { family: "Pretendard", style: "Bold" },
    { family: "Poppins", style: "Regular" },
    { family: "Poppins", style: "Medium" },
    { family: "Poppins", style: "SemiBold" },
    { family: "Poppins", style: "Bold" }
  ];
  for (const font of fonts) {
    try {
      await figma.loadFontAsync(font);
    } catch (e) {
      // Pretendard 실패 → Noto Sans KR 로 대체 (한국어 폰트만)
      if (font.family === "Pretendard") {
        await figma.loadFontAsync({ family: "Noto Sans KR", style: font.style });
      } else {
        throw e;
      }
    }
  }
}

await loadFonts();
```

폰트 fallback 사용 시 `createText` 안에서 `family` 를 체크해 적절한 패밀리 사용.

---

## 메인 프레임 생성

```javascript
// SCREEN 의 device 에 따라 너비 결정
const widthByDevice = { desktop: 1440, mobile: 375, tablet: 768, responsive: 1440 };
const width = widthByDevice[device] || 1440;

const screenFrame = figma.createFrame();
screenFrame.name = `[SCREEN-NNN] ${title}`;
screenFrame.layoutMode = "VERTICAL";
screenFrame.primaryAxisSizingMode = "AUTO";
screenFrame.counterAxisSizingMode = "FIXED";
screenFrame.resize(width, 100);
screenFrame.primaryAxisSizingMode = "AUTO"; // resize 가 AUTO 를 깨므로 재설정 필수
screenFrame.fills = [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }]; // page bg
screenFrame.itemSpacing = 0;

// 캔버스 빈 영역에 배치
const existingNodes = figma.currentPage.children;
const maxX = Math.max(0, ...existingNodes.map(n => n.x + n.width));
screenFrame.x = maxX + 200; // 200px 간격
screenFrame.y = 0;
```

---

## 헬퍼 함수

매 `use_figma` 호출에서 다시 정의. 컴팩트한 코드로 자주 쓰는 패턴 캡슐화.

### createText
```javascript
function createText(parent, text, opts = {}) {
  const t = figma.createText();
  const family = opts.family || "Pretendard";
  const style = opts.weight || "Regular";
  // fallback 처리
  try {
    t.fontName = { family, style };
  } catch (e) {
    t.fontName = { family: "Noto Sans KR", style };
  }
  t.characters = text;
  t.fontSize = opts.size || 14;
  t.fills = [{ type: 'SOLID', color: opts.color || { r: 0.2, g: 0.2, b: 0.2 } }];
  t.lineHeight = { value: t.fontSize >= 24 ? 140 : 180, unit: "PERCENT" };
  t.textAutoResize = "WIDTH_AND_HEIGHT";
  if (opts.align) t.textAlignHorizontal = opts.align;
  parent.appendChild(t);
  return t;
}
```

### createAutoFrame
```javascript
function createAutoFrame(parent, name, opts = {}) {
  const f = figma.createFrame();
  f.name = name;
  f.layoutMode = opts.direction || "VERTICAL";
  f.primaryAxisSizingMode = opts.primarySize || "AUTO";
  f.counterAxisSizingMode = opts.counterSize || "FIXED";
  f.itemSpacing = opts.spacing || 0;
  if (opts.padding != null) {
    f.paddingTop = f.paddingBottom = f.paddingLeft = f.paddingRight = opts.padding;
  } else {
    f.paddingTop = opts.paddingTop || 0;
    f.paddingBottom = opts.paddingBottom || 0;
    f.paddingLeft = opts.paddingLeft || 0;
    f.paddingRight = opts.paddingRight || 0;
  }
  f.fills = opts.fills || [];
  if (opts.cornerRadius) f.cornerRadius = opts.cornerRadius;
  if (opts.strokes) f.strokes = opts.strokes;
  if (opts.strokeWeight) f.strokeWeight = opts.strokeWeight;
  parent.appendChild(f);
  return f;
}
```

### createImagePlaceholder
```javascript
function createImagePlaceholder(parent, w, h, label = "IMG") {
  const wrap = createAutoFrame(parent, "img-placeholder", {
    direction: "VERTICAL",
    primarySize: "FIXED",
    counterSize: "FIXED",
    fills: [{ type: 'SOLID', color: { r: 0.8, g: 0.8, b: 0.8 } }],
    cornerRadius: 4
  });
  wrap.resize(w, h);
  wrap.primaryAxisAlignItems = "CENTER";
  wrap.counterAxisAlignItems = "CENTER";
  createText(wrap, label, { size: 12, color: { r: 0.4, g: 0.4, b: 0.4 } });
  return wrap;
}
```

### createButton
```javascript
function createButton(parent, label, opts = {}) {
  const variant = opts.variant || "primary";
  const fillColors = {
    primary: { r: 0.10, g: 0.10, b: 0.10 },        // #1A1A1A
    secondary: { r: 1, g: 1, b: 1 },                // #FFFFFF
    destructive: { r: 1, g: 1, b: 1 },              // #FFFFFF (보더로 강조)
    outline: { r: 1, g: 1, b: 1 },                  // #FFFFFF
    ghost: null                                      // 배경 없음
  };
  const textColors = {
    primary: { r: 1, g: 1, b: 1 },                  // #FFFFFF
    secondary: { r: 0.20, g: 0.20, b: 0.20 },       // #333333
    destructive: { r: 0.10, g: 0.10, b: 0.10 },     // #1A1A1A
    outline: { r: 0.20, g: 0.20, b: 0.20 },         // #333333
    ghost: { r: 0.40, g: 0.40, b: 0.40 }            // #666666
  };
  const fills = fillColors[variant] ? [{ type: 'SOLID', color: fillColors[variant] }] : [];
  const strokes = (variant === "secondary" || variant === "outline" || variant === "destructive")
    ? [{ type: 'SOLID', color: { r: 0.60, g: 0.60, b: 0.60 } }]
    : [];

  const btn = createAutoFrame(parent, `btn-${label}`, {
    direction: "HORIZONTAL",
    primarySize: "AUTO",
    counterSize: "AUTO",
    paddingTop: 10, paddingBottom: 10, paddingLeft: 16, paddingRight: 16,
    fills: fills,
    strokes: strokes,
    strokeWeight: variant === "destructive" ? 2 : 1,
    cornerRadius: 6
  });
  btn.primaryAxisAlignItems = "CENTER";
  btn.counterAxisAlignItems = "CENTER";

  createText(btn, label, {
    weight: "Medium",
    size: 14,
    color: textColors[variant]
  });

  if (opts.state === "disabled") btn.opacity = 0.5;
  return btn;
}
```

### createInput
```javascript
function createInput(parent, label, opts = {}) {
  const wrap = createAutoFrame(parent, `input-${label}`, {
    direction: "VERTICAL",
    primarySize: "AUTO",
    counterSize: "FIXED",
    spacing: 6
  });

  // label
  createText(wrap, label, {
    weight: "Medium",
    size: 14,
    color: { r: 0.20, g: 0.20, b: 0.20 }
  });

  // input box
  const box = createAutoFrame(wrap, `box-${label}`, {
    direction: "HORIZONTAL",
    primarySize: "FIXED",
    counterSize: "FIXED",
    paddingLeft: 12, paddingRight: 12,
    fills: [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }],
    strokes: [{ type: 'SOLID', color: { r: 0.60, g: 0.60, b: 0.60 } }],
    strokeWeight: 1,
    cornerRadius: 6
  });
  box.resize(opts.width || 320, opts.height || 40);
  box.counterAxisAlignItems = "CENTER";

  if (opts.placeholder) {
    createText(box, opts.placeholder, {
      size: 14,
      color: { r: 0.60, g: 0.60, b: 0.60 }
    });
  }
  return wrap;
}
```

### createTable
```javascript
function createTable(parent, columns, rows = 3) {
  const table = createAutoFrame(parent, "table", {
    direction: "VERTICAL",
    primarySize: "AUTO",
    counterSize: "FIXED",
    spacing: 0,
    strokes: [{ type: 'SOLID', color: { r: 0.82, g: 0.82, b: 0.82 } }],
    strokeWeight: 1,
    cornerRadius: 4
  });

  // header row
  const header = createAutoFrame(table, "header", {
    direction: "HORIZONTAL",
    primarySize: "FIXED",
    counterSize: "FIXED",
    spacing: 0,
    paddingTop: 12, paddingBottom: 12, paddingLeft: 16, paddingRight: 16,
    fills: [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }]
  });
  for (const col of columns) {
    const cell = createAutoFrame(header, `h-${col}`, {
      direction: "HORIZONTAL", primarySize: "FILL", counterSize: "AUTO"
    });
    cell.layoutGrow = 1;
    createText(cell, col, { weight: "SemiBold", size: 13, color: { r: 0.10, g: 0.10, b: 0.10 } });
  }

  // dummy rows
  for (let r = 0; r < rows; r++) {
    const row = createAutoFrame(table, `row-${r}`, {
      direction: "HORIZONTAL",
      primarySize: "FIXED",
      counterSize: "FIXED",
      spacing: 0,
      paddingTop: 12, paddingBottom: 12, paddingLeft: 16, paddingRight: 16,
      fills: [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }],
      strokes: [{ type: 'SOLID', color: { r: 0.82, g: 0.82, b: 0.82 } }],
      strokeWeight: 1
    });
    row.strokeTopWeight = 1;
    row.strokeBottomWeight = 0;
    row.strokeLeftWeight = 0;
    row.strokeRightWeight = 0;
    for (const col of columns) {
      const cell = createAutoFrame(row, `c-${col}`, {
        direction: "HORIZONTAL", primarySize: "FILL", counterSize: "AUTO"
      });
      cell.layoutGrow = 1;
      createText(cell, "—", { size: 13, color: { r: 0.60, g: 0.60, b: 0.60 } });
    }
  }
  return table;
}
```

### createCustom (Custom 컴포넌트 표현)
```javascript
function createCustom(parent, label, customName, note) {
  const wrap = createAutoFrame(parent, `custom-${customName}`, {
    direction: "VERTICAL",
    primarySize: "AUTO",
    counterSize: "FIXED",
    paddingTop: 24, paddingBottom: 24, paddingLeft: 24, paddingRight: 24,
    spacing: 4,
    fills: [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }],
    strokes: [{ type: 'SOLID', color: { r: 0.60, g: 0.60, b: 0.60 } }],
    strokeWeight: 1,
    cornerRadius: 4
  });
  wrap.dashPattern = [4, 4]; // 점선
  wrap.primaryAxisAlignItems = "CENTER";
  wrap.counterAxisAlignItems = "CENTER";

  createText(wrap, label, { weight: "Bold", size: 14, color: { r: 0.20, g: 0.20, b: 0.20 } });
  createText(wrap, `[Custom: ${customName}]`, {
    family: "Poppins", weight: "Regular", size: 11, color: { r: 0.60, g: 0.60, b: 0.60 }
  });
  if (note) {
    createText(wrap, note, { size: 11, color: { r: 0.40, g: 0.40, b: 0.40 } });
  }
  return wrap;
}
```

---

## 섹션별 분할 호출 전략

복잡한 페이지는 다음과 같이 나눠 `use_figma` 호출:

### 1차 — 메인 프레임 + Header + Hero
```javascript
// (헬퍼 정의 + 폰트 로드 후)
const screenFrame = ... // 메인 프레임 생성

// Header 섹션
const header = createAutoFrame(screenFrame, "header-section", {...});
// ... header 콘텐츠

// Hero 섹션 (있을 때만)
const hero = createAutoFrame(screenFrame, "hero-section", {...});
// ... hero 콘텐츠
```

### 2차 — Main + Side
```javascript
// 부모 프레임 재참조
const screenFrame = figma.currentPage.findOne(n => n.name === "[SCREEN-NNN] ...");

const middleRow = createAutoFrame(screenFrame, "middle-row", {
  direction: "HORIZONTAL",
  primarySize: "FIXED",   // 가로는 부모 폭 고정
  counterSize: "AUTO",    // ★ 세로는 children 높이만큼 — FIXED면 높이 잘림
  spacing: 24,
  ...
});
// 부모가 VERTICAL Auto Layout 이면 가로 FILL 도 권장
middleRow.layoutAlign = "STRETCH";

const main = createAutoFrame(middleRow, "main-section", {...});
// ... main 콘텐츠

const side = createAutoFrame(middleRow, "side-section", {...});
// ... side 콘텐츠
```

### 3차 — Footer + Modal
```javascript
const screenFrame = figma.currentPage.findOne(n => n.name === "[SCREEN-NNN] ...");

const footer = createAutoFrame(screenFrame, "footer-section", {...});
// ... footer 콘텐츠

// Modal 은 메인 프레임 외부에 별도 생성
const modal = figma.createFrame();
modal.name = "modal-...";
modal.x = screenFrame.x + screenFrame.width + 200;
modal.y = screenFrame.y;
// ... modal 콘텐츠
```

분할 기준: 섹션 수가 많거나 (>4) Table·Grid 같은 노드 다수 생성 시 무조건 분할.

---

## 컴포넌트 렌더 패턴

ComponentSpec 객체를 받아 적절한 헬퍼 호출:

```javascript
function renderComponent(parent, comp) {
  // Custom 우선 처리
  if (comp.type === 'Custom') {
    return createCustom(parent, comp.label, comp.custom_name || comp.label, comp.note);
  }

  // type 별 분기
  switch (comp.type) {
    case 'Button':
      return createButton(parent, comp.label, { variant: comp.variant, state: comp.state });
    case 'Input':
    case 'Textarea':
      return createInput(parent, comp.label, { placeholder: comp.placeholder });
    case 'Table':
      return createTable(parent, comp.columns || []);
    case 'Heading':
      return createText(parent, comp.label, { weight: "Bold", size: 24, color: { r: 0.10, g: 0.10, b: 0.10 } });
    case 'Text':
      return createText(parent, comp.label, { size: 14 });
    case 'Stat':
      const wrap = createAutoFrame(parent, "stat", { direction: "VERTICAL", spacing: 4 });
      createText(wrap, comp.label.split('\n')[0] || "1,234", { weight: "Bold", size: 32, color: { r: 0.10, g: 0.10, b: 0.10 } });
      createText(wrap, comp.label.split('\n')[1] || comp.note || "라벨", { size: 12, color: { r: 0.60, g: 0.60, b: 0.60 } });
      return wrap;
    case 'Alert':
      // ... Alert 패턴
    case 'Image':
      return createImagePlaceholder(parent, 320, 180);
    // ... 나머지 type 들
    default:
      // 알려지지 않은 type → Custom 처리
      return createCustom(parent, comp.label, comp.type, comp.note);
  }

  // triggers_api 추가 (HORIZONTAL wrap 으로 옆에)
  // 호출자가 처리
}
```

`triggers_api` 가 있으면 컴포넌트 + 캡션을 HORIZONTAL Auto Layout 으로 묶기:

```javascript
function renderWithApiCaption(parent, comp) {
  if (!comp.triggers_api) return renderComponent(parent, comp);

  const wrap = createAutoFrame(parent, "with-api", {
    direction: "HORIZONTAL", spacing: 8, primarySize: "AUTO", counterSize: "AUTO"
  });
  wrap.counterAxisAlignItems = "CENTER";
  renderComponent(wrap, comp);
  createText(wrap, `→ ${comp.triggers_api}`, {
    family: "Poppins", weight: "Regular", size: 11, color: { r: 0.60, g: 0.60, b: 0.60 }
  });
  return wrap;
}
```

---

## 조회·검증 (get_metadata / get_screenshot)

### 작업 전: 캔버스 상태 파악
```
mcp__*__get_metadata
```
→ 응답에서 `currentPage.children` 으로 기존 노드 위치 확인. 새 SCREEN 을 어디에 배치할지 결정.

### 작업 후: 결과 캡처
```
mcp__*__get_screenshot(node_id="<screenFrame.id>")
```
→ 캡처 이미지 URL 또는 Base64. 사용자에게 전달.

다중 SCREEN 일 때는 각 frame 별 또는 전체 페이지 스크린샷 둘 다 가능.

---

## 에러 패턴

### 폰트 로드 실패
- Pretendard / Poppins 둘 다 실패 시 → Noto Sans KR 만 사용
- Noto Sans KR 도 실패 시 → 기본 폰트로 fallback (시각 결과는 다소 다를 수 있음). 사용자에게 안내.

### 노드 수 초과 (use_figma 단일 호출 한도)
- 에러 메시지에서 노드 수 한도 확인 → 작업 분할
- 한 호출에 헬퍼 정의 + 큰 섹션 1~2개 정도가 안전

### 부모 프레임 재참조 실패
```javascript
const screenFrame = figma.currentPage.findOne(n => n.name === "[SCREEN-NNN] ...");
if (!screenFrame) throw new Error("부모 프레임을 찾을 수 없음. name 확인 필요");
```
- 이전 호출에서 name 이 정확히 일치하는지 확인. 공백·괄호·하이픈 모두 정확히.

### Auto Layout 재설정 누락
- `resize()` 후 `primaryAxisSizingMode = "AUTO"` 잊으면 프레임이 fixed height 로 굳어짐
- 모든 resize 호출 후 이 라인 추가 잊지 말 것

### HORIZONTAL row 의 height 잘림 (★ 자주 발생)
**증상**: middle-row 같은 HORIZONTAL Auto Layout 안에 main / side 컬럼을 넣었는데, row 높이가 children 보다 작게 잘림 → 콘텐츠가 row 바깥으로 삐져나감.

**원인**: `createAutoFrame` 의 `counterSize` 기본값이 `"FIXED"`. HORIZONTAL 방향이면 counter axis = 세로 → children 높이를 무시하고 부모가 준 height(또는 100) 로 고정됨.

**해결**: HORIZONTAL row 만들 때는 `counterSize: "AUTO"` 를 **반드시 명시**.

```javascript
// ❌ 잘못 — height 잘림
const row = createAutoFrame(parent, "row", { direction: "HORIZONTAL", spacing: 24 });

// ✅ 올바름
const row = createAutoFrame(parent, "row", {
  direction: "HORIZONTAL",
  primarySize: "FIXED",   // 가로는 부모/지정 폭 고정
  counterSize: "AUTO",    // 세로는 children hug
  spacing: 24
});
row.layoutAlign = "STRETCH"; // 부모(VERTICAL Auto Layout)에 가로 꽉 채우기
```

**복구 (이미 잘린 frame 보정)**: 2차 `use_figma` 호출로
```javascript
const row = figma.currentPage.findOne(n => n.name === "middle-row");
row.counterAxisSizingMode = "AUTO";
```
만 보내면 즉시 height 자동 보정됨.

VERTICAL Auto Layout 의 row(가로) 폭 잘림도 같은 원리 — `primarySize: "AUTO"` (세로 hug) + 가로는 `layoutAlign = "STRETCH"` 권장.
