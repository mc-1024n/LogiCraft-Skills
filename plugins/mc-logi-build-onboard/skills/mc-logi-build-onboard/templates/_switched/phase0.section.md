
### Phase B — 공통 기반 (Phase 0)
`core/`·`db/migrations`·앱 골격은 도메인 경계를 넘으므로 **메인이 직접**(또는 전용 1 에이전트로) 순차 구현한다.
- **0a. DB 스키마**: 각 도메인 키트의 ERD 요약 + `_raw` DDL 을 근거로 마이그레이션 작성·적용{{foundation_schema_note}}.
- **0b. 앱 골격**: `core/`(config·db·events·security·observability) + 앱 진입점 + 프로젝트 초기화.
→ 전 도메인의 전제. 여기서 실패하면 도메인 구현 불가. **도메인 fan-out 전에 완료**.
