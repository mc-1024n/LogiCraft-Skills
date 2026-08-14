게이트 직전 **협업 정찰**: CO 의 대상 코드 경로 glob·§6 예상 설계 ITEM 으로 겹치는 타 세션 작업을 조회한다(2인+ 팀이 각자 AI 세션으로 동시 작업하므로).
```
list_work_claims(project_id, overlapping={
  paths: [<CO §3 대상 경로 globs>],
  items: [<CO §6 예상 설계 ITEM — 예 "SCREEN-020","NAV-001">],
})
```
`conflicts`/겹치는 열린 claim 이 있으면 게이트에 노출한다(누가·무슨 intent 로 점유 중). 게이트 문구에 `⚠️ 협업 정찰: [겹치는 claim 없음 | ⚠️ <owner> 가 <intent> 로 <ITEM/경로> 점유 중]` 한 줄 포함.
