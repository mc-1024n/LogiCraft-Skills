# Logicraft SCREEN → Figma 매핑표

## section.role

header 최상단 FILL #FFF / navigation header아래 / hero main상단 #F5F5F5 / filter 240~280(좌) / main 남은폭 / side 300~360(우) / modal 별도 480~640 / footer 최하단. 명시 안되면 main. 배치 header→navigation→hero→(filter+main+side HORIZONTAL)→footer→modal(외부).

## section.layout

form=VERTICAL16 / list=VERTICAL0 Table / detail=VERTICAL24 / dashboard=HORIZONTAL Grid24 / grid=3~4열16 / tabs=Tabs상단 / stack=VERTICAL16(default).

## components[].type (43종)

**Display**: Text(Regular14~16 #333) / Heading(Bold20~32 #1A1A1A) / Image(#CCCCCC+IMG) / Avatar(원형) / Badge(라운드필, primary=#1A1A1A/#FFF) / Icon(24) / Divider(1px #D1D1D1).
**Inputs**: Input(label+박스 1px #999 h40) / Textarea(h96) / Select(▼) / RadioGroup(○첫●) / Checkbox(□) / Switch(36x20) / DatePicker / FileUpload(점선).
**Actions**: Button(h40; primary=#1A1A1A채움/secondary=outline/destructive=두꺼운테두리/ghost; disabled50%) / Link(underline) / IconButton(32) / Menu.
**Containers**: Card(1px #D1D1D1 r8) / Tabs(활성 2px #1A1A1A) / Accordion / Stack / Grid.
**Data**: Table(헤더 #F5F5F5, 더미3행'—') / List / KeyValue / Chart(#F5F5F5+CHART) / Stat(Bold32+라벨12) / Timeline / Tree.
**Feedback**: Alert(좌4px보더) / Toast(다크) / Dialog(480~640) / Drawer / Progress(60%) / Skeleton / Tooltip.
**Navigation**: Breadcrumb / Pagination / Stepper.
**Custom**: #F5F5F5 1px dashed #999, label Bold14 + [Custom:name]11 + note11.

## 메타

triggers_api → 우측 8px Poppins11 #999, >30자 아랫줄. binds_to → '← {binds_to}'10px(note 우선). note → 아래 11px #666. state: disabled50%/loading오버레이/error 1px #1A1A1A/readonly #F5F5F5/hidden 점선. variant → Button 참조.
