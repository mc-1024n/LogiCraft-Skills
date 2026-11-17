**협업 정찰**(게이트 직전) — CO 의 대상 코드 경로 glob·§6 예상 설계 ITEM 으로 겹치는 타 세션 작업을 조회한다:
`list_work_claims(project_id, overlapping={paths: [<CO §3 대상 경로 globs>], items: [<CO §6 예상 ITEM>]})`
겹치는 열린 claim 이 있으면 게이트 문구에 `⚠️ 협업 정찰: [겹치는 claim 없음 | ⚠️ <owner> 가 <intent> 로 <ITEM/경로> 점유 중]` 한 줄을 넣는다.
