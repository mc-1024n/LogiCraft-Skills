# 흑백 와이어프레임 — 컬러·폰트·레이아웃 규칙

이 문서는 mc_wireframe_logicraft 의 모든 모드(A/B)에 무조건 적용되는 시각 규칙이다. wireframe_basic 의 규칙을 계승·정리한 것.

## 목차
- [컬러 (그레이스케일)](#컬러-그레이스케일)
- [폰트](#폰트)
- [타이포그래피 스케일](#타이포그래피-스케일)
- [행간](#행간)
- [오토레이아웃](#오토레이아웃)
- [레이아웃 기본값](#레이아웃-기본값)
- [이미지·아이콘 표현](#이미지아이콘-표현)
- [AI 느낌 배제 규칙](#ai-느낌-배제-규칙)

---

## 컬러 (그레이스케일)

**모든 색상은 그레이스케일만 사용.** Primary 컬러, 브랜드 컬러 일체 금지. 강조는 굵기(Weight)와 크기(Size)로만 표현한다.

| 용도 | HEX | RGB (Figma API) |
|------|-----|-----------------|
| 배경 White | `#FFFFFF` | `{ r: 1, g: 1, b: 1 }` |
| 배경 Light | `#F5F5F5` | `{ r: 0.96, g: 0.96, b: 0.96 }` |
| 배경 Gray | `#E5E5E5` | `{ r: 0.90, g: 0.90, b: 0.90 }` |
| 테두리 Light | `#D1D1D1` | `{ r: 0.82, g: 0.82, b: 0.82 }` |
| 테두리 | `#999999` | `{ r: 0.60, g: 0.60, b: 0.60 }` |
| 텍스트 Light | `#666666` | `{ r: 0.40, g: 0.40, b: 0.40 }` |
| 텍스트 Default | `#333333` | `{ r: 0.20, g: 0.20, b: 0.20 }` |
| 텍스트 Dark | `#1A1A1A` | `{ r: 0.10, g: 0.10, b: 0.10 }` |
| 플레이스홀더(이미지) | `#CCCCCC` | `{ r: 0.80, g: 0.80, b: 0.80 }` |

### 변종 표현
- **Primary 버튼**: 다크 필 (`#1A1A1A` 배경 + `#FFFFFF` 텍스트)
- **Secondary 버튼**: outline (`#999999` 테두리 + `#333333` 텍스트, 배경 투명)
- **Destructive 버튼**: outline 두꺼운 테두리 (강조는 굵기로) + `#1A1A1A` 텍스트
- **Disabled 상태**: `#D1D1D1` 텍스트 + `#F5F5F5` 배경
- **에러/경고 Alert**: `#F5F5F5` 배경 + 좌측 4px `#1A1A1A` 보더

---

## 폰트

| 언어 | 패밀리 | Weights |
|------|--------|---------|
| 한국어 | `Pretendard` | Regular / Medium / SemiBold / Bold |
| 영어/숫자 | `Poppins` | Regular / Medium / SemiBold / Bold |
| Pretendard 불가 시 fallback | `Noto Sans KR` | 동일 weights |

**Inter 등 다른 폰트 사용 금지.**

### 폰트 로드 (Figma API)
```javascript
await figma.loadFontAsync({ family: "Pretendard", style: "Regular" });
await figma.loadFontAsync({ family: "Pretendard", style: "Medium" });
await figma.loadFontAsync({ family: "Pretendard", style: "SemiBold" });
await figma.loadFontAsync({ family: "Pretendard", style: "Bold" });
await figma.loadFontAsync({ family: "Poppins", style: "Regular" });
await figma.loadFontAsync({ family: "Poppins", style: "Medium" });
await figma.loadFontAsync({ family: "Poppins", style: "SemiBold" });
await figma.loadFontAsync({ family: "Poppins", style: "Bold" });
```

Pretendard 로드 실패 시 try/catch 로 잡고 `Noto Sans KR` 로 재시도.

---

## 타이포그래피 스케일

| 용도 | Weight | Size | Color |
|------|--------|------|-------|
| Hero 타이틀 | Bold | 40~56px | `#1A1A1A` |
| 섹션 타이틀 | Bold | 32~40px | `#1A1A1A` |
| 페이지/모달 제목 | Bold | 24~32px | `#1A1A1A` |
| 서브헤딩 | SemiBold | 20~24px | `#333333` |
| 본문 | Regular | 16~18px | `#333333` |
| 라벨 (입력 필드) | Medium | 14px | `#333333` |
| Placeholder | Regular | 14~16px | `#999999` |
| 캡션·헬퍼 | Regular | 12~14px | `#666666` |
| 메타 캡션 (API ref 등) | Regular | 11~12px | `#999999` |

---

## 행간

- **140%**: 24px 이상 텍스트 (제목·헤드라인·강조)
- **180%**: 20px 이하 텍스트 (본문·라벨·캡션)

```javascript
// Figma API
t.lineHeight = { value: 140, unit: "PERCENT" };  // 큰 텍스트
t.lineHeight = { value: 180, unit: "PERCENT" };  // 작은 텍스트
```

---

## 오토레이아웃

**절대 좌표(x, y) 사용 금지.** 모든 프레임은 Auto Layout + Hug Contents.

```javascript
frame.layoutMode = "VERTICAL";     // 또는 "HORIZONTAL"
frame.primaryAxisSizingMode = "AUTO";    // 주축 Hug Contents
frame.counterAxisSizingMode = "FIXED";   // 교차축 고정
frame.itemSpacing = 16;
frame.paddingTop = 24;
frame.paddingBottom = 24;
frame.paddingLeft = 24;
frame.paddingRight = 24;
```

### 핵심 원칙
1. 루트 프레임: VERTICAL, `resize(1440, 10)` 후 `primaryAxisSizingMode = "AUTO"` 재설정 (resize 가 AUTO 를 깨므로)
2. 섹션: `layoutSizingHorizontal = "FILL"`, 세로 HUG
3. 카드: 균등 분배 시 `layoutGrow = 1`
4. 텍스트: `textAutoResize = "WIDTH_AND_HEIGHT"`
5. **resize() 후 반드시 `primaryAxisSizingMode = "AUTO"` 재설정**

---

## 레이아웃 기본값

- Desktop 기준 너비: **1440px**
- Content 좌우 패딩: **100px** (총 본문 영역 1240px)
- 섹션 간 수직 간격: **80~100px**
- 섹션 내부 패딩: **24~40px**
- 컴포넌트 간 간격: **8 / 12 / 16 / 24px** 만 사용 (4 의 배수)

### 다중 SCREEN 캔버스 배치 (모드 A 다중 입력 시)
- 가로 방향으로 1440 + 200 (간격) = **1640px** 단위로 배치
- SCREEN-001, SCREEN-002, ... 좌→우 순으로
- 캔버스 좌상단부터 시작

---

## 이미지·아이콘 표현

- **이미지 영역**: 회색(`#CCCCCC`) 박스 + 대각선 또는 중앙에 "IMG" 텍스트
- **아이콘**: 회색 원/사각형 플레이스홀더 (24x24 또는 32x32)
- **아바타**: 원형 회색 (`#CCCCCC`) + 이니셜 텍스트
- **차트 영역**: 회색 박스 + 중앙에 "CHART (line)" / "CHART (bar)" 등 라벨

---

## AI 느낌 배제 규칙

다음은 **사용 금지**:
- ❌ 이모지 아이콘 (✅ ⚠️ 🔔 💊 🤖 ✨ 🎉 등)
- ❌ 챗봇 말풍선 UI
- ❌ "AI가~", "에이전트가~", "스마트하게~" 카피
- ❌ 컬러 그라디언트, 글로우 효과, 네온
- ❌ 과도한 불릿 나열

다음은 **권장**:
- ✓ 아이콘은 회색 원/사각형 플레이스홀더
- ✓ 데이터 중심 레이아웃 (숫자, 표, 차트)
- ✓ 여백 활용, 명확한 정보 위계
- ✓ 단순한 타이포그래피 + 굵기·크기로 위계 표현

---

## 검증 체크리스트

와이어프레임 생성 후 `get_screenshot` 으로 확인할 때 다음 점검:

- [ ] 컬러: 그레이스케일만 사용 (RGB 채널 동일값 또는 #1A1A1A~#FFFFFF 범위)
- [ ] 폰트: Pretendard/Poppins/Noto Sans KR 만 사용
- [ ] 절대 좌표 없음: 모든 프레임이 Auto Layout
- [ ] 1440px 너비 (desktop 기본)
- [ ] 이모지 없음
- [ ] 그라디언트·글로우 없음
- [ ] 정보 위계가 굵기·크기로 명확
