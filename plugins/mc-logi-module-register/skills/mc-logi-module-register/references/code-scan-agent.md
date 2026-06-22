# code-scan-agent.md — Phase 3 코드 전수 스캔 에이전트 프롬프트 골격

`Explore`(권장, read-only) 또는 `general-purpose` 에이전트로 호출. 목적은 **logicraft code_module 등록 갭 분석용 클래스 인벤토리** — 파일을 다 읽지 말고 Glob+Grep 로 빠르게.

## 호출 패턴
```
Agent(subagent_type="Explore", description="<DOMAIN> 코드 클래스 전수 스캔", prompt=<아래>)
```

## 프롬프트 골격
```
<DOMAIN 한 줄 설명> 의 배포 모듈 코드에서 **2차/신규 구현 클래스**를 전수 조사해줘.
logicraft code_module 등록 갭 분석이 목적이라 정확한 파일경로+클래스명+역할이 필요해.

# 대상 경로 (cwd 기준)
- <배포모듈1 경로> — <책임>
- <배포모듈2 경로> — <책임>

# 조사 범위 (very thorough)
각 모듈의 Java/소스에서 2차 신규 위주(1차 보존은 카운트만):
1. 컨트롤러 (@RestController / Api*) — 주요 @RequestMapping path 포함
2. 서비스 (ServiceImpl* / Manage* / *Service)
3. 워커/스케줄러 (@Scheduled, *Worker / *Processor / *Job)
4. 엔티티/리포 (@Entity Entity*, @Repository Repo*) — v2/신규 계층만
5. 설정/유틸 (Config*, 듀얼 데이터소스, 프로토콜 유틸, 예외)

# (있으면) 특히 확인할 클래스
<changelog/키트 근거로 존재가 예상되는 클래스명 + API 매핑 나열 — 실재/경로 확인>

# 출력 (구조화)
모듈별 → 종류별:
- <상대 패키지경로>/<클래스>.java — <역할 1줄> (관련 API/DFEAT)
1차 보존은 종류별 카운트만.

Glob+Grep 로 클래스명·경로·@어노테이션·주요 path 만 수집. 클래스 단위로 빠짐없이.
```

## 메인이 받은 뒤
- 종류별 인벤토리를 logicraft 현재 카탈로그(Phase 2)와 대조해 미등록/domain미연결/死모듈 3 버킷 산출.
- "복사본" 클래스(듀얼 데이터소스로 모듈마다 같은 엔티티 복제 등)는 file_path 가 다르면 별도 MOD 로 등록하되 description 에 원본 MOD 를 명시(depends_on_modules).
