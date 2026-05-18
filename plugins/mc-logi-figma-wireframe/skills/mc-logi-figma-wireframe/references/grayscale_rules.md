# 흑백 와이어프레임 규칙

mc-logi-figma-wireframe 의 모든 모드(A/B)에 무조건 적용.

## 컬러 (그레이스케일만)

White #FFFFFF / Light #F5F5F5 / Gray #E5E5E5 / 테두리Light #D1D1D1 / 테두리 #999999 / 텍스트Light #666666 / 텍스트 #333333 / Dark #1A1A1A. Primary 버튼=다크필(#1A1A1A/#FFF). Secondary=outline. Disabled=#D1D1D1/#F5F5F5. Primary·브랜드 컬러 금지, 강조는 굵기·크기로.

## 폰트

한국어 Pretendard / 영어 Poppins / 폴백 Noto Sans KR. Regular/Medium/SemiBold/Bold. Pretendard 실패 시 try/catch Noto 재시도.

## 타이포

Hero Bold40~56 / 섹션 Bold32~40 / 제목 Bold24~32 / 서브 SemiBold20~24 / 본문 Regular16~18 / 라벨 Medium14 / Placeholder Regular14~16 #999 / 캡션 12~14 #666 / 메타 11~12 #999.

## 행간

24px↑ 140%, 20px↓ 180%.

## 오토레이아웃

절대좌표 금지. 모든 프레임 Auto Layout + Hug. 루트 VERTICAL, resize() 후 primaryAxisSizingMode='AUTO' 재설정 필수. 섹션 layoutSizingHorizontal='FILL'. 텍스트 textAutoResize='WIDTH_AND_HEIGHT'.

## 레이아웃 기본

Desktop 1440px, 좌우 패딩 100px, 섹션간 80~100px, 내부 24~40px, 간격 8/12/16/24(4배수). 다중 SCREEN 가로 1640px 단위.

## 이미지·아이콘

이미지=회색 #CCCCCC 박스+'IMG'. 아이콘=회색 플레이스홀더. 아바타=원형 회색+이니셜. 차트=회색 박스+'CHART'.

## AI 느낌 배제

금지: 이모지·챗봇 말풍선·'AI가~' 카피·그라디언트·글로우. 권장: 회색 플레이스홀더·데이터 중심·여백·굵기/크기 위계.

## 체크리스트

그레이스케일 / 폰트 / Auto Layout / 1440px / 이모지·그라디언트 없음 / 위계 명확.
