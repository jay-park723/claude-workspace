# CLAUDE.md - Source of Truth

> **Source**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
> **Updated**: 2026-11-16 (v2.1.325) - AGENTS.md 직접 읽기(v2.1.277), @import 최대 깊이 4 hops로 정정, 하위 CLAUDE.md 크기 한도·로드 시점(Write/Edit/Bash cat), `autoMemoryEnabled`·`claudeMdExcludes`·관리형 `claudeMd`, `/doctor prompt-audit`, 서브에이전트 `omitClaudeMd`
> **Purpose**: CLAUDE.md 작성 시 유일한 참조 문서

---

## 1. 개요

CLAUDE.md는 Claude Code가 세션 시작 시 자동 로드하는 설정 파일. 프로젝트 컨텍스트, 작업 규칙, 코드 스타일을 정의.

---

## 2. 전체 계층 구조 (Hierarchy)

Claude Code는 다음 순서로 메모리를 로드 (모두 병합됨):

| 우선순위 | 위치 | 용도 |
|---------|------|------|
| 1 (최상위) | Managed Policy | 조직 전사 강제 규칙 |
| 2 | `~/.claude/CLAUDE.md` | 개인 전역 설정 |
| 3 | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 프로젝트 설정 |
| 4 | `./.claude/rules/*.md` | 프로젝트 규칙 (자동 로드) |
| 5 | `~/.claude/rules/*.md` | 개인 전역 규칙 (자동 로드) |
| 6 | `./CLAUDE.local.md` | 로컬 전용 (gitignore 권장) |
| 7 | Auto Memory | 세션 간 자동 학습 기록 |

> **주의 (공식 문서 기준, 2026-11 확인)**: 위 "우선순위"는 **로드 순서**에 가깝다. 발견된 파일은 서로 덮어쓰지 않고 **모두 이어붙여져(concatenate)** 컨텍스트에 들어간다. 디렉토리 트리에서는 루트 → 작업 디렉토리 순으로 쌓이고, 같은 디렉토리에서는 `CLAUDE.local.md`가 `CLAUDE.md` 뒤에 붙는다. 두 파일 지시가 충돌하면 Claude가 **임의로 하나를 고를 수 있으므로** 충돌 자체를 없애는 것이 원칙. (rules도 동일: 사용자 rules가 먼저, 프로젝트 rules가 나중에 로드되며 서로 덮어쓰지 않음)
>
> - 상위 디렉토리의 `CLAUDE.md`/`CLAUDE.local.md`는 시작 시 로드. **하위 디렉토리**의 것은 Claude가 그 폴더의 파일을 Read·Write·Edit(또는 Bash `cat`/`head` 같은 단일 파일 읽기)할 때 로드 (Write/Edit v2.1.288, Bash 읽기 v2.1.293)
> - CLAUDE.md 내용은 시스템 프롬프트가 아니라 **시스템 프롬프트 뒤의 user 메시지**로 전달됨 → 강제 규칙이 아님. 반드시 지켜야 하는 동작은 hook으로.

### Managed Policy (조직 전사)

조직 IT/DevOps가 관리하는 최상위 규칙. 개인 사용자가 변경 불가.

| OS | 경로 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

MDM, Group Policy, Ansible 등으로 배포.

**`claudeMd` 관리형 설정**: 파일 대신 `managed-settings.json`의 `claudeMd` 키에 내용을 직접 넣을 수 있음. 관리형/정책 설정에서만 유효(사용자·프로젝트 설정에 넣으면 무시). 서버 관리형 설정의 `claudeMd`는 보안 승인 다이얼로그를 띄우지 않음 (v2.1.260).

### 특정 CLAUDE.md 제외 (`claudeMdExcludes`)

대형 모노레포에서 다른 팀의 CLAUDE.md가 섞여 들어올 때 settings에서 경로·글로브로 제외:

```json
{
  "claudeMdExcludes": ["**/other-team/CLAUDE.md"]
}
```

- 절대 경로 기준 글로브 매칭. 사용자·프로젝트·로컬·관리형 어느 레이어에서든 설정 가능, 배열은 레이어 간 병합
- Managed Policy CLAUDE.md는 제외 불가
- 심링크된 `.claude/rules` 파일도 제외됨 (v2.1.239 수정)

### AGENTS.md 지원 (v2.1.277 신규)

다른 코딩 에이전트용 `AGENTS.md`가 있는 저장소에서 **CLAUDE.md 없이도** 그대로 읽는다.

| 상황 | Claude가 읽는 것 (기본값) |
|------|------|
| `AGENTS.md`만 있고 작업 디렉토리·상위에 `CLAUDE.md`/`CLAUDE.local.md` 없음 | `AGENTS.md` |
| `AGENTS.md`와 `CLAUDE.md`(또는 `CLAUDE.local.md`)가 함께 있음 | `CLAUDE.md`만 |
| `CLAUDE.md`가 `@AGENTS.md`를 import | `CLAUDE.md` + import된 `AGENTS.md` |

- `/config` → **Project instructions**에서 변경: `claude-md-or-agents-md`(기본) · `claude-md-and-agents-md`(둘 다) · `claude-md` · `managed-only`
- 주의: `CLAUDE.local.md` 하나만 추가해도 "CLAUDE.md 있음"으로 판정되어 `AGENTS.md`를 안 읽음 → 둘 다 원하면 `claude-md-and-agents-md`
- `~/.claude/CLAUDE.md`, 관리형 CLAUDE.md, `.claude/rules/`는 판정에 영향 없음(함께 로드)
- `AGENTS.local.md`, `AGENTS.override.md`, `.agents/` 폴더는 읽지 않음
- Bedrock·Vertex·Foundry·텔레메트리 비활성 세션도 지원 (v2.1.281). 지원 안 되는 환경에서는 `CLAUDE.md`에 `@AGENTS.md` 한 줄로 import

---

## 3. Auto Memory (v2.1.32, 신규)

Claude가 세션 작업 중 자동으로 패턴, 명령어, 선호도를 기록하는 시스템.

### 저장 위치

```
~/.claude/projects/<project>/memory/
├── MEMORY.md           # 인덱스 (매 세션 첫 200줄 자동 로드)
├── debugging.md        # 토픽별 상세 노트
└── api-conventions.md  # Claude가 자동 생성
```

- `<project>`는 git 저장소 루트에서 파생
- git worktree는 별도 디렉토리
- git 외부는 작업 디렉토리 기준

### 동작

- **세션 시작**: `MEMORY.md` 첫 200줄만 자동 로드
- **토픽 파일**: startup 미로드, Claude가 필요할 때 on-demand 읽기
- **기록 방식**: Claude가 작업 중 자동 기록 또는 직접 지시 ("remember that we use pnpm")

### 제어

기본값: 로컬 세션에서 **켜짐**.

- **권장**: `/memory`의 Auto-memory 토글 → `~/.claude/settings.json`에 `autoMemoryEnabled` 저장 (←/→ 키로 전환, v2.1.287)
- 특정 프로젝트만 끄기: 그 프로젝트 settings에 `"autoMemoryEnabled": false`
- 환경 변수로 끄기: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
- **(v2.1.285)** 백그라운드 세션이나 Claude Code가 띄운 하위 세션에서는 토글로 **켤 수 없음**(끄기만 가능). 다시 켜려면 터미널에서 `claude`를 직접 실행해 토글

`/memory` 커맨드로 파일 선택기 열기 가능 (CLAUDE.md + Auto Memory 포함).

### 저장되는 메모리 종류

Claude는 메모리 파일 frontmatter의 `type` 필드에 4종 중 하나를 기록: `user`(역할·선호) · `feedback`(교정·확인된 방식) · `project`(진행 중 업무·마감·결정) · `reference`(외부 정보 위치). 코드에서 유도 가능한 것(구조·경로)이나 CLAUDE.md에 이미 있는 내용은 저장하지 않음.

- 메인 대화의 auto memory는 **서브에이전트에 로드되지 않음**(fork 제외)
- auto memory는 **기기 로컬**. 다른 기기·클라우드 환경과 공유되지 않음

### Worktree 간 공유 (v2.1.63)

프로젝트 설정과 auto memory가 같은 git 저장소의 모든 worktree에서 공유됨.

### 커스텀 메모리 디렉토리 (v2.1.74)

```json
{
  "autoMemoryDirectory": "/path/to/custom/memory"
}
```

`settings.json`에서 auto-memory 저장 위치를 변경 가능.

### 메모리 파일 타임스탬프 (v2.1.75)

메모리 파일에 last-modified 타임스탬프가 추가되어, Claude가 최신/오래된 메모리를 구분 가능.

**(v2.1.214)** frontmatter가 있는 메모리 파일을 쓸 때 `modified` 필드에 **ISO 8601 타임스탬프**가 기록됨.

### MEMORY.md 크기 제한 (v2.1.83)

`MEMORY.md` 인덱스가 200줄 제한에 더해 **25KB 크기 제한**도 추가됨. 둘 중 먼저 도달하는 기준으로 잘림.

- **(v2.1.210)** 한도를 넘기는 쓰기는 조용히 잘리지 않고 **명시적 에러**로 Claude에게 인덱스 재작성을 요구 (쓰기 자체는 성공, 한도 밖은 다음 로드 때 누락)
- **(v2.1.211)** 한도 측정은 실제 로드되는 내용 기준(frontmatter·HTML 주석 제외)
- **(v2.1.268)** 잘림 경고에 잘린 줄 수와 잘린 지점 표시
- 이 200줄/25KB 한도는 `MEMORY.md`에만 해당. CLAUDE.md 한도는 아래 "CLAUDE.md 크기 한도" 참고

### MEMORY.md 자동 컴팩션 리마인더 (v2.1.186)

**(v2.1.186)** 메모리 개선: 에이전트가 **`MEMORY.md`를 스스로 정리(compact)하도록 리마인드**받음. 인덱스가 비대해지면 항목을 추리도록 유도해 위 크기 제한과 맞물려 동작. (참고: `Improved N memories` 라인은 verbose 모드 밖에서 개별 파일명을 나열하지 않도록 변경 — v2.1.181.)

### 팀 메모리 스토어 (v2.1.172)

**(v2.1.172)** `CLAUDE_MEMORY_STORES`로 마운트한 **팀 공유 메모리 스토어**를 원격 세션에서 recall하지 못하던 버그 수정 — 이제 팀 메모리도 정상 검색됨.

### "CLAUDE.md가 너무 김" 경고 (v2.1.169)

**(v2.1.169)** CLAUDE.md 과다 경고의 임계값이 고정값이 아니라 **모델의 컨텍스트 윈도우 크기에 비례**하도록 변경됨. 대용량 컨텍스트 모델에서는 더 관대하게 허용.

**(v2.1.281)** 경고가 파일 하나뿐 아니라 **여러 지시 파일 합계**도 셈. CLAUDE.md·rules 파일·`@import` 각각이 별도 파일로 카운트되어, 중간 크기 파일이 많아도 경고됨. `/status`에서도 확인 가능.

### CLAUDE.md 크기 한도 (v2.1.309)

| 파일 | 한도 | 초과 시 |
|------|------|---------|
| 시작 시 로드되는 CLAUDE.md | 파일당 4 MiB | 파일 전체 스킵 |
| 하위 디렉토리 CLAUDE.md·CLAUDE.local.md(및 그 import), 하위 `.claude/rules/`, 경로 조건부 rules | 200K 컨텍스트: 40,000자 / 1M 컨텍스트: 150,000자(Opus·Sonnet 4.6은 200,000자) | **앞부분만** 로드 + 나머지는 Read로 읽으라는 안내 |

글자 수 확인: `wc -m path/to/CLAUDE.md`. 넘으면 내용을 줄이거나 rules 파일로 나눔(파일별로 따로 계산).

---

## 4. @import 문법

외부 파일을 참조하여 CLAUDE.md를 모듈화:

```markdown
@30-knowledge/37-claude-code/skills-guide.md
@./docs/coding-standards.md
@~/.claude/my-project-instructions.md
```

### 규칙

- 상대 경로 또는 절대 경로 사용 가능. **상대 경로는 import하는 파일 위치 기준**(작업 디렉토리 기준 아님)
- 참조된 파일은 컨텍스트에 자동 포함 → import로 나눠도 **컨텍스트 절약 효과는 없음**(정리 목적)
- Code span/code block 내 `@`는 import 처리 안 됨
- **Recursive import 최대 깊이: 4 hops** (공식 문서 기준. 이전 판의 "5 hops"를 정정)
- 외부 import 포함 프로젝트 첫 실행 시 **승인 다이얼로그** 표시
- 바이너리 파일(이미지, PDF)은 자동 제외

### HTML 주석 처리 (v2.1.72)

CLAUDE.md 내 HTML 주석(`<!-- ... -->`)은 자동 주입 시 Claude에게 숨겨짐. Read 도구로 직접 읽을 때는 보임. 내부 메모를 Claude에게 노출하지 않으면서 유지 가능. (블록 단위 주석 기준이며, 코드 블록 안의 주석은 유지됨)

### Worktree 환경 권장 패턴

```markdown
# CLAUDE.local.md에서 home directory import로 공유
@~/.claude/my-project-instructions.md
```

worktree마다 `CLAUDE.local.md`가 별도 존재하므로 home directory import 활용.

---

## 5. .claude/rules/ 자동 로드

`.claude/rules/` 내 모든 `.md` 파일 자동 로드. 서브디렉토리 재귀 탐색 지원.

```
.claude/
├── CLAUDE.md
├── rules/
│   ├── git.md
│   ├── security.md
│   ├── frontend/
│   │   └── react.md
│   └── backend/
│       └── api.md
└── settings.json
```

조건부 규칙은 [[rules-guide]] 참조.

---

## 6. --add-dir + CLAUDE.md 로딩 (v2.1.20)

`--add-dir`로 추가된 디렉토리의 CLAUDE.md와 rules도 로드 가능:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

로드 대상: `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md` (단, `paths`가 있는 조건부 rules는 제외. 추가 디렉토리의 `AGENTS.md`도 로드 안 됨)

기본값은 비활성화. 환경변수 설정 필요.

---

## 7. 권장 포함 내용

### 필수

1. **프로젝트 개요**: 목적, 기술 스택
2. **폴더 구조**: 주요 디렉토리 설명
3. **코딩 규칙**: 스타일 가이드, 네이밍 컨벤션
4. **작업 규칙**: 파일 작업, Git, 보안 규칙

### 선택

- 사용자 프로필 / 작업 스타일
- 도구 설정 (MCP, 외부 도구)
- 자주 쓰는 명령어

---

## 8. settings.json과의 관계

| 항목 | CLAUDE.md | settings.json |
|------|-----------|---------------|
| 프로젝트 지침 | O | X |
| 코딩 스타일 | O | X |
| 도구 권한 | X | O |
| 모델 설정 | X | O |
| 환경 변수 | X | O |

**원칙**: 지침은 CLAUDE.md, 설정은 settings.json

---

## 9. 작성 팁

### 간결하게 유지

- 목표: 150줄 이하 (공식 권장: 파일당 **200줄 미만**)
- 상세 내용은 @import 또는 rules/ 활용
- 반복 방지: 한 곳에만 정의

### 명확한 규칙

```markdown
# Good
- **커밋 전**: `npm test` 실행 필수

# Bad
- 커밋 전에 테스트를 실행하면 좋을 것 같아요
```

### 주의사항

1. 민감정보 제외 (API 키, 비밀번호 절대 금지)
2. 경로 일관성 (팀 공유 시 상대 경로 권장)
3. CLAUDE.local.md는 .gitignore에 추가
4. 정기적으로 프로젝트 변화에 맞춰 갱신

### 점검 도구

- **`/doctor prompt-audit`** (v2.1.283): CLAUDE.md·CLAUDE.local.md·AGENTS.md와 `.claude/`·`~/.claude/`의 rules·skills·commands·subagents를 점검. 구형 모델용 프롬프트 패턴, 존재하지 않는 파일·명령 참조, 서로 모순되는 지시 파일을 리포트. 특정 경로만: `/doctor prompt-audit .claude/skills/deploy`
- **`/context all`**: **Memory files** 목록에서 시작 시 로드된 CLAUDE.md 확인. 하위 디렉토리 CLAUDE.md는 온디맨드라 여기 안 나오고, 로드될 때 `Loaded` 줄로 표시
- **`/doctor`**: 체크인된 CLAUDE.md의 축소 제안(코드에서 유도 가능한 구조·의존성 설명 제거)
- CLAUDE.md의 커밋/PR 규칙이 기본 동작과 충돌하면 settings의 `includeGitInstructions`·`attribution`으로 내장 지침을 끔

### 서브에이전트에서 CLAUDE.md 끄기 (v2.1.271)

에이전트 frontmatter(또는 `--agents` JSON)에 `omitClaudeMd: true`를 두면 사용자·프로젝트·로컬 CLAUDE.md 없이 실행. 관리형 정책 파일은 그대로 로드.

### 알려진 수정

- **(v2.1.312)** 하위 디렉토리의 매우 큰 CLAUDE.md·rules·import 파일을 앞부분만 보고 덮어쓰던 문제 수정 (Write가 전체 읽기 또는 Edit 유도)
- **(v2.1.311)** 자동 컴팩션 직후 세션 중 수정한 MEMORY.md·CLAUDE.md의 옛 내용이 보이던 버그 수정
- **(v2.1.287)** 재개(resume)·컴팩션 후 폴더 CLAUDE.md가 두 번 붙던 버그 수정
- **(v2.1.284)** `MEMORY.md`·recall 노트 안의 보이지 않는 문자와 Claude Code 마크업 흉내 태그를 무력화 (프롬프트 인젝션 방지)
- **(v2.1.269)** 기본 attribution 리마인더가 CLAUDE.md·메모리의 "커밋 attribution 금지" 규칙을 덮어쓰던 버그 수정
- **(v2.1.236)** 세션 recap(자동·`/recap`)을 400자로 제한. **(v2.1.284)** 채팅 스레드·routine·webhook에서 중계된 `/recap`은 거절
- **(v2.1.101)** 인식되지 않는 hook 이벤트 이름에 대한 settings 내구성 개선 (설정 파일에 미래 hook 이벤트가 있어도 크래시하지 않음)
- **(v2.1.94)** `forceRemoteSettingsRefresh` 정책과 함께 기본 effort 수준이 medium에서 high로 변경 (API-key, Bedrock/Vertex/Foundry, Team, Enterprise)
- **(v2.1.90)** 도구 호출 중 CLAUDE.md 자동 로드 시 축소된 search/read 요약 배지가 fullscreen 스크롤백에서 여러 번 표시되던 버그 수정
- **(v2.1.88)** 긴 세션에서 중첩 CLAUDE.md 파일이 수십 번 재주입되는 버그 수정
- **(v2.1.86)** Read 도구가 compact line-number 포맷 사용 + 변경 없는 재읽기 중복 제거 (토큰 절약)

---

## Sources

- [Manage Claude's memory](https://code.claude.com/docs/en/memory)
- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## Related

- [[rules-guide]] - .claude/rules/ 상세 가이드
- [[skills-guide]] - Skills 시스템 가이드
- [[subagents-guide]] - Subagent 가이드

---

## Update History

- **2026-11-16**: v2.1.208~2.1.325 변경사항 반영 + 공식 문서 대조 정정
  - **AGENTS.md 직접 읽기** (v2.1.277, 비1P 환경 v2.1.281) + `/config` Project instructions 4개 값
  - **정정**: @import 최대 깊이 5 → **4 hops**, 상대 경로는 import하는 파일 기준, 계층 표는 덮어쓰기가 아닌 이어붙이기
  - 하위 CLAUDE.md·조건부 rules **크기 한도**(40,000자 등, v2.1.309), 시작 시 파일 4 MiB 한도
  - 하위 CLAUDE.md 로드 시점에 Write/Edit(v2.1.288)·Bash 단일 파일 읽기(v2.1.293) 추가
  - `autoMemoryEnabled`·`/memory` 토글, 백그라운드 세션에서 켜기 불가 (v2.1.285), 메모리 4종 `type`, `modified` 타임스탬프 (v2.1.214)
  - MEMORY.md 한도 초과 시 명시적 에러 (v2.1.210), 측정 기준·잘림 경고 개선 (v2.1.211, v2.1.268)
  - `claudeMdExcludes`, 관리형 `claudeMd` (v2.1.260 승인 다이얼로그 제외)
  - `/doctor prompt-audit` (v2.1.283), 대형 CLAUDE.md 경고가 파일 합계도 계산 (v2.1.281)
  - 서브에이전트 `omitClaudeMd` (v2.1.271), recap 400자 제한 (v2.1.236)
- **2026-07-13**: v2.1.120~2.1.207 변경사항 반영
  - **MEMORY.md 자동 컴팩션 리마인더** (v2.1.186): 에이전트가 인덱스를 스스로 정리하도록 유도
  - 마운트된 팀 메모리 스토어(`CLAUDE_MEMORY_STORES`) recall 버그 수정 (v2.1.172)
  - "CLAUDE.md가 너무 김" 경고 임계값이 모델 컨텍스트 윈도우에 비례하도록 변경 (v2.1.169)
  - `!` bash 커맨드 출력에 Claude가 자동 응답 (v2.1.186, `respondToBashCommands: false`로 종전 동작 유지) — CLAUDE.md 내 `!`command`` 사용 시 참고
  - `Improved N memories` 라인이 verbose 밖에서 개별 파일명 미표시 (v2.1.181)
- **2026-04-19**: v2.1.110~2.1.114 — CLAUDE.md/Memory 시스템 자체 변경 없음, 버전만 동기화
  - 관련 환경 변경: `Ctrl+A`/`Ctrl+E` readline 기본 동작 복원 (v2.1.113), `Ctrl+U` 입력 버퍼 전체 삭제 (v2.1.111, `Ctrl+Y`로 복원), `Ctrl+L` 전체 화면 redraw (v2.1.111)
  - Auto mode가 Max 구독자에게 Opus 4.7 사용 시 기본 제공 (v2.1.111) — `--enable-auto-mode` 플래그 불필요
  - Opus 4.7 `xhigh` effort level 추가 (v2.1.111, `high`와 `max` 사이)
  - `/effort` 인터랙티브 슬라이더 (v2.1.111) — 인자 없이 호출 시
  - 세션 복귀 시 자동 recap이 미발신 입력 작성 중 발화하던 버그 수정 (v2.1.114)
- **2026-04-15**: v2.1.105~2.1.109 변경사항 반영
  - **Recap 기능 추가 (v2.1.108)**: 세션 복귀 시 자동 요약 컨텍스트 제공. `/config`에서 설정, `/recap`으로 수동 호출. 텔레메트리 disabled 환경은 `CLAUDE_CODE_ENABLE_AWAY_SUMMARY`로 강제 활성화
  - `ENABLE_PROMPT_CACHING_1H` 환경 변수 (v2.1.108) - API key/Bedrock/Vertex/Foundry에서 1시간 prompt cache TTL opt-in (기존 `ENABLE_PROMPT_CACHING_1H_BEDROCK` deprecated). `FORCE_PROMPT_CACHING_5M`로 5분 TTL 강제 가능
  - `DISABLE_PROMPT_CACHING*` 설정 시 시작 경고 표시 (v2.1.108)
  - `DISABLE_TELEMETRY` 설정한 구독자가 5분 TTL로 떨어지던 버그 수정 (v2.1.108)
  - `/undo`가 `/rewind` alias로 추가 (v2.1.108)
  - `CLAUDE_ENV_FILE`(예: `~/.zprofile`)이 `#` 주석 줄로 끝나면 Bash 도구 출력 사라지던 버그 수정 (v2.1.108)
- **2026-04-13**: v2.1.93~2.1.101 변경사항 반영
  - 기본 effort 수준 medium에서 high로 변경 (v2.1.94, API-key/Bedrock/Vertex/Foundry/Team/Enterprise)
  - settings 내구성 개선: 인식되지 않는 hook 이벤트 이름 처리 (v2.1.101)
  - OS CA certificate store 기본 신뢰 (v2.1.101) - 엔터프라이즈 TLS 프록시 지원
- **2026-04-04**: v2.1.90~2.1.92 변경사항 반영
  - CLAUDE.md 자동 로드 시 축소 배지 다중 표시 수정 (v2.1.90)
  - `forceRemoteSettingsRefresh` 정책: 원격 managed settings 강제 갱신, 실패 시 종료 (v2.1.92)
  - `managed-settings.d/` drop-in과 관련된 조직 정책 강화
- **2026-03-31**: v2.1.79~2.1.88 변경사항 반영
  - `MEMORY.md` 25KB 크기 제한 추가 (v2.1.83)
  - 중첩 CLAUDE.md 재주입 버그 수정 (v2.1.88)
  - Read 도구 compact format + 중복 제거 (v2.1.86)
- **2026-03-18**: v2.1.51~2.1.78 변경사항 반영
  - Worktree 간 프로젝트 설정/auto memory 공유 (v2.1.63)
  - `autoMemoryDirectory` 설정 (v2.1.74)
  - 메모리 파일 last-modified 타임스탬프 (v2.1.75)
  - HTML 주석 자동 주입 시 숨김 처리 (v2.1.72)
  - `InstructionsLoaded` 훅 이벤트 (v2.1.69)
- **2026-02-22**: 전면 갱신 (source of truth 목적)
  - Auto Memory 시스템 신규 섹션 (v2.1.32)
  - Managed Policy 계층 추가 (최상위)
  - Hierarchy 표 전면 수정 (7단계)
  - --add-dir + CLAUDE.md 로딩 (v2.1.20)
  - Import 안전 동작 (승인 다이얼로그, 5 hops 제한)
  - MCP 섹션 제거 (별도 문서로 분리)
- **2026-01-19**: 초기 작성
