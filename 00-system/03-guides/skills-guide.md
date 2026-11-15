# Claude Code Skills - Source of Truth

> **Source**: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), [platform.claude.com Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
> **Updated**: 2026-11-16 (v2.1.325) - `context: fork` 기본 백그라운드 실행·`background: false`(v2.1.218), frontmatter 필드 보강(`when_to_use`·`arguments`·`paths`·`disallowed-tools`·`shell`), `allowed-tools`는 호출 턴 한정 사전승인, 중첩 스킬 로딩 제한(v2.1.319~325), claude.ai 스킬 동기화(v2.1.275), `/skill-doctor`(v2.1.261), 예약 작업·`/loop`의 스킬 실행 확인(v2.1.325)
> **Purpose**: Skills 개발 시 유일한 참조 문서. 이 파일이 source of truth.

---

## 1. Skills 개요

**Skills**는 Claude Code의 기능을 확장하는 모듈형 컴포넌트. `SKILL.md` 파일 하나로 Claude가 새로운 능력을 갖추게 됨.

### 핵심 특성

- Claude가 **자동으로 판단하여 실행** (model-invoked)
- 사용자가 `/skill-name`으로 **직접 호출**도 가능 (user-invoked)
- 스크립트 번들링으로 **결정론적 코드** 실행 가능
- [Agent Skills](https://agentskills.io) 오픈 스탠다드 준수

### Slash Commands와의 관계

- `.claude/commands/review.md`와 `.claude/skills/review/SKILL.md`는 동일하게 `/review` 생성
- 기존 `.claude/commands/` 파일은 계속 작동
- **같은 이름일 경우 Skill이 우선**
- Skills가 상위 호환: 지원 파일 디렉토리, frontmatter 호출 제어, 자동 로드

---

## 2. 파일 구조

### 기본 구조

```
my-skill/
├── SKILL.md           # 메인 인스트럭션 (필수, 유일한 필수 파일)
├── reference.md       # 상세 API 문서 (필요 시 로드)
├── examples.md        # 사용 예시 (필요 시 로드)
└── scripts/
    └── helper.py      # 유틸리티 스크립트 (실행만, 컨텍스트에 로드 안 됨)
```

### Skill 저장 위치

| 위치 | 경로 | 적용 범위 |
|------|------|----------|
| Enterprise | 관리 설정 참조 | 조직의 모든 사용자 |
| Personal | `~/.claude/skills/<name>/SKILL.md` | 모든 프로젝트 |
| Project | `.claude/skills/<name>/SKILL.md` | 해당 프로젝트만 |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | 플러그인 활성화된 곳 |

**우선순위**: enterprise > personal > project
동일 이름 시 높은 우선순위가 승리. Plugin은 `plugin-name:skill-name` 네임스페이스로 충돌 없음.

### 자동 발견

- 중첩 디렉토리: `packages/frontend/` 편집 시 `packages/frontend/.claude/skills/`도 탐색 (모노레포 지원)
- `--add-dir`로 추가된 디렉토리의 `.claude/skills/`도 자동 로드
- 라이브 변경 감지: 세션 재시작 없이 SKILL.md 편집 즉시 반영
- **(v2.1.178)** 중첩 `.claude/skills`의 스킬은 해당 파일을 작업할 때 로드됨. **이름 충돌 시 중첩 스킬은 `<dir>:<name>` 형태로 표시**되어 둘 다 사용 가능 (예: `packages/frontend:review`). non-interactive 실행에서 디렉토리 한정 이름이 권한 프롬프트에 막히던 버그도 수정.
- **(v2.1.157)** `.claude/skills` 디렉토리에 놓인 **플러그인이 마켓플레이스 없이 자동 로드**됨. `claude plugin init <name>`으로 `.claude/skills`에 새 플러그인 스캐폴딩 생성 가능.
- **(v2.1.246)** `/cd`로 디렉토리를 옮기면 그 위치의 프로젝트 스킬·에이전트·설정이 즉시 적용됨 (`--resume` 불필요).

### 중첩 스킬 로딩 제한 (v2.1.319~v2.1.325)

- 시작 폴더 **아래** `.claude/skills`의 스킬은 시작 시 로드되지 않고, Claude가 그 하위 폴더의 파일을 처음 읽거나 편집할 때 로드됨 (공식 문서 기준).
- **(v2.1.319)** Bash 샌드박스가 켜져 있으면 하위 폴더 스킬은 **그 폴더에서 Claude Code를 시작하거나 `/cd`로 이동했을 때만** 로드.
- **(v2.1.321)** `~/.claude/plugins` 안의 `.claude/skills`는 그 파일을 작업해도 더 이상 로드되지 않음.
- **(v2.1.325)** `--plugin-dir` 플러그인 내부 `.claude/skills`는 그보다 위에서 시작한 세션에서 로드되지 않음 → 플러그인 폴더에서 시작할 것.
- **(v2.1.325)** 샌드박스는 추가 디렉토리(`--add-dir`)의 `.claude` 설정·스킬·에이전트·커맨드·훅 쓰기도 거부 (시작 폴더와 동일 규칙).

### claude.ai 스킬 동기화 (v2.1.275)

- 터미널 세션이 claude.ai 계정에서 켜둔 스킬·플러그인을 `~/.claude/skills/synced/`로 내려받음. 로컬에서는 **읽기 전용** — 수정해도 다음 동기화 때 덮어써짐.
- 끄기: 설정 `syncClaudeAiSkills: false` / `syncClaudeAiPlugins: false`. 비대화형 실행에서 다운로드를 기다리려면 `CLAUDE_CODE_SYNC_SKILLS=1`.
- **(v2.1.228)** 동기화된 스킬은 로컬 커맨드·MCP 프롬프트를 가리지 않으며, 본문의 `!` 명령 실행과 `@` 파일 확장이 되지 않음.
- **(v2.1.281)** `/` 메뉴·`/skills`에서 다른 커맨드와 겹치지 않으면 짧은 이름으로 표시(`anthropic-skills:<name>` 대신).

### 예약된 이름·금지 문자

- **(v2.1.282)** `anthropic-skills` 네임스페이스의 스킬 폴더·커맨드 파일은 로드되지 않음 (플러그인은 예외). `synced`도 폴더명으로 예약됨. (`claude-ai` 예약은 v2.1.283에서 되돌림)
- **(v2.1.299)** 파일/폴더명에 숨김·방향 전환·공백류 문자, `<`, `>`가 있는 스킬은 이름을 바꾸기 전까지 제공되지 않음. 그런 `name:` 값은 무시.

### 번들 스킬 비활성화 (v2.1.169)

`disableBundledSkills` 설정(또는 `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` 환경 변수)으로 **내장 스킬·워크플로우·빌트인 슬래시 커맨드를 모델에게서 숨길 수 있음**. 커스텀 스킬만 노출하고 싶거나 컨텍스트를 아끼려는 환경에 유용. `--safe-mode`(또는 `CLAUDE_CODE_SAFE_MODE`)는 CLAUDE.md·플러그인·스킬·훅·MCP를 전부 끄고 시작하는 문제 진단용 플래그.

---

## 3. YAML Frontmatter 전체 필드

```yaml
---
name: my-skill
description: What this skill does and when to use it
when_to_use: Trigger phrases or example requests
argument-hint: [issue-number]
arguments: [issue, branch]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob
disallowed-tools: AskUserQuestion
model: sonnet
effort: high
context: fork
agent: Explore
background: true
paths: "src/**/*.ts"
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check.sh"
---
```

### 필드 상세

| 필드 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `name` | 권장 | 디렉토리명 | 소문자, 숫자, 하이픈만. 최대 64자. "anthropic", "claude" 예약어 금지. XML 태그 금지. |
| `description` | 권장 | 마크다운 첫 비어있지 않은 줄 | Claude가 언제 사용할지 판단 기준. 핵심 용도를 앞에 둘 것. 스킬 목록에서는 `description`+`when_to_use` 합쳐 **1,536자에서 잘림**. (Agent Skills 스펙 기준 1024자 이내 권장) |
| `when_to_use` | - | 없음 | 트리거 문구·예시 요청 등 추가 호출 조건. 목록에서 `description` 뒤에 붙고 1,536자 한도에 포함. |
| `argument-hint` | - | 없음 | 자동완성 시 보이는 힌트. 예: `[issue-number]`, `[filename] [format]` |
| `arguments` | - | 없음 | 이름 있는 위치 인자. 공백 구분 문자열 또는 YAML 리스트. 본문에서 `$name`으로 치환. **(v2.1.301)** 앞 64개 이름(각 64자)까지만 채워짐. |
| `disable-model-invocation` | - | `false` | `true`: Claude 자동 실행 차단. `/name`으로만 호출 가능. 서브에이전트 프리로드·세션 예약 작업 실행도 막힘. |
| `user-invocable` | - | `true` | `false`: `/` 메뉴에서 숨기고 사용자가 `/name`을 쳐도 실행 안 됨. Claude만 호출. 배경 지식 스킬용. |
| `allowed-tools` | - | 없음 | 스킬을 **호출한 턴 동안** 권한 확인 없이 쓸 수 있는 도구(사전 승인). 다음 메시지를 보내면 해제. 공백/쉼표 구분 문자열 또는 YAML 리스트. 다른 도구를 막지는 않음. |
| `disallowed-tools` | - | 없음 | 스킬 활성 중 Claude의 도구 목록에서 **제거**할 도구. 예: 무인 루프에서 `AskUserQuestion` 제거. 다음 메시지에서 해제. |
| `model` | - | 상속 | 스킬 활성 시 사용할 모델(현재 턴 한정). `/model`과 같은 값 또는 `inherit`. `context: fork`면 서브에이전트 모델. **(v2.1.259)** 대화형 세션에서 무시되던 버그 수정. |
| `context` | - | 인라인 | `fork`: 분기된 서브에이전트 컨텍스트에서 실행 |
| `agent` | - | `general-purpose` | `context: fork` 시 사용할 에이전트. 내장: `Explore`, `Plan`, `general-purpose`. 커스텀: `.claude/agents/`의 에이전트. |
| `background` | - | `true` | **(v2.1.218)** `context: fork`에서만 적용. `false`면 백그라운드 대신 호출한 턴에서 결과를 기다림. 8장 참조. |
| `paths` | - | 없음 | 스킬 자동 활성을 특정 파일 작업으로 한정하는 glob 패턴(쉼표 구분 또는 YAML 리스트). 현재 작업 디렉토리 기준. |
| `shell` | - | `bash` | `!` 명령 실행 셸. `bash` 또는 `powershell`. |
| `effort` | - | 없음 | **(v2.1.80)** 호출 시 모델 노력 수준 오버라이드(현재 턴). `low`, `medium`, `high`, `xhigh`, `max` (모델별 지원 상이). **(v2.1.267)** 기본 effort가 고정된 모델에서 무시되던 버그 수정. |
| `keep-coding-instructions` | - | `false` | **(v2.1.94)** Plugin output style 스킬에서 코딩 인스트럭션 유지 여부 |
| `display-name` | - | `name` | **(v2.1.186)** `/skills` 메뉴 등에 표시할 사람이 읽기 좋은 이름 |
| `default-enabled` | - | `true` | **(v2.1.186)** `false`면 스킬이 기본 비활성(사용자가 `/skills`에서 켜야 로드) |
| `fallback` | - | 없음 | **(v2.1.186)** 이 스킬을 쓸 수 없을 때 안내할 대체 경로/스킬 |
| `metadata.*` | - | 없음 | **(v2.1.186)** 임의의 사용자 정의 메타데이터 네임스페이스 (`metadata.author` 등). 공식 문서: 자유 형식 YAML 맵, Claude Code는 내용을 쓰지 않으며 맵이 아니면 버림. |
| `license` / `compatibility` | - | 없음 | Agent Skills 스펙 필드. Claude Code는 받기만 하고 동작에 쓰지 않음. `compatibility`는 500자 이내. |
| `hooks` | - | 없음 | 스킬 라이프사이클 범위의 훅. 스킬 종료 시 자동 정리. |

> [!warning] 2026-11-16 공식 문서 대조 결과, `display-name`·`default-enabled`·`fallback`은 공식 frontmatter 표에 **없음**. 교육용 예시·템플릿에는 쓰지 말 것 (확인 전까지 보류).

**불리언 값 (v2.1.218)**: `true`/`false` 외에 `yes`/`no`/`on`/`off`/`1`/`0`(대소문자 무관)도 허용.

### disableSkillShellExecution (v2.1.91)

`disableSkillShellExecution` 설정으로 Skills, 커스텀 슬래시 커맨드, Plugin 커맨드 내 인라인 셸 실행(`!`command``)을 비활성화할 수 있음. 보안이 중요한 환경에서 유용.

### keep-coding-instructions (v2.1.94)

Plugin output style 스킬에서 `keep-coding-instructions` frontmatter 필드 사용 가능. 코딩 인스트럭션을 유지하면서 출력 스타일만 변경하는 Plugin 스킬에 유용.

### 호출 제어 매트릭스

| Frontmatter | 사용자 호출 | Claude 호출 | 설명 로드 |
|-------------|------------|------------|----------|
| (기본값) | O | O | 설명 항상 컨텍스트에 |
| `disable-model-invocation: true` | O | X | 설명이 컨텍스트에 없음 |
| `user-invocable: false` | X | O | 설명 항상 컨텍스트에 |

---

## 4. 3단계 로딩 메커니즘

Skills는 토큰 효율을 위해 3단계로 로딩됨.

### Level 1: Metadata (항상 로드)
- YAML frontmatter의 `name`과 `description`
- 세션 시작 시 시스템 프롬프트에 포함
- 스킬당 약 100 토큰

### Level 2: Instructions (트리거 시 로드)
- `SKILL.md`의 메인 바디
- 관련 요청이 있을 때만 로드
- **5,000 토큰 미만 권장**

### Level 3: Resources (필요 시 로드)
- 번들된 지원 파일 (reference.md, examples.md 등)
- 스크립트는 실행만 되고 컨텍스트에 로드 안 됨
- 실질적 제한 없음

### SKILL.md에서 지원 파일 참조

```markdown
## Additional resources
- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

**SKILL.md는 500줄 미만 유지 권장.**

---

## 5. Context Budget

- 스킬 설명 로딩 예산: **컨텍스트 윈도우의 2%**, fallback 16,000자
- 스킬이 많으면 예산 초과 가능
- `/context`로 제외된 스킬 경고 확인
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 환경 변수로 재정의 가능
- **(v2.1.86)** 스킬 description이 `/skills` 목록에서 250자로 제한되어 컨텍스트 사용량 감소
- **(v2.1.105)** 스킬 description 목록 상한이 **250자 → 1,536자로 상향**. 설명이 잘리면 시작 시 경고 표시
- **(v2.1.86)** `/skills` 메뉴가 **알파벳 순 정렬**로 변경
- **(v2.1.111)** `/skills` 메뉴에 **추정 토큰 수 정렬** 옵션 추가 — `t` 키로 토글
- **(v2.1.261)** `/skill-doctor`: 스킬별 컨텍스트 비용·사용 빈도를 보여주고 한 번도 안 쓰인 스킬을 표시 → 정리용. 대화형에서는 `/plugin` 관리자의 **Stats** 탭으로 열림 (번들·엔터프라이즈 스킬 제외)
- **(v2.1.304)** 컴팩션 후 스킬 목록을 Claude에게 다시 보냄. `/reload-skills`는 새로 생기거나 바뀐 스킬만 보냄. 기존 스킬 디렉토리 변경은 실시간 반영되므로 `/reload-skills`는 세션 시작 후 새로 만든 최상위 스킬 디렉토리에만 필요
- **(v2.1.295)** 서브에이전트의 `skills` 프리로드는 최대 32개
- **(v2.1.111)** `/less-permission-prompts` 빌트인 스킬 추가 — 트랜스크립트를 스캔하여 자주 쓰는 read-only Bash/MCP 호출을 우선순위 정렬된 allowlist로 `.claude/settings.json`에 제안

---

## 6. String Substitutions

SKILL.md 콘텐츠 내에서 사용 가능한 변수들.

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 스킬 호출 시 전달된 모든 인자. 콘텐츠에 없으면 `ARGUMENTS: <value>`로 끝에 자동 추가. |
| `$ARGUMENTS[N]` | 0-based 인덱스로 특정 인자 접근. 예: `$ARGUMENTS[0]` = 첫 번째 인자 |
| `$N` | `$ARGUMENTS[N]`의 단축형. `$0` = 첫 번째, `$1` = 두 번째 |
| `$name` | `arguments` frontmatter에 선언한 이름 있는 인자 |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID. 로깅, 세션별 파일 생성에 유용. |
| `${CLAUDE_EFFORT}` | 현재 effort 수준 (`low`~`max`) |
| `${CLAUDE_SKILL_DIR}` | **(v2.1.69)** 현재 스킬의 디렉토리 경로. SKILL.md에서 자신의 파일 참조에 유용. |
| `${CLAUDE_PROJECT_DIR}` | 프로젝트 루트 디렉토리 |
| `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` | 플러그인 설치 디렉토리 / 영구 데이터 디렉토리 (플러그인 스킬 전용) |

**(v2.1.233)** 인자 값이 다시 템플릿 마커로 재확장되지 않도록 수정됨.

### 사용 예시

```markdown
---
name: review-pr
description: Review a pull request
argument-hint: [pr-number]
---

Review pull request #$0:
1. Fetch PR diff
2. Analyze changes
3. Provide feedback
```

---

## 7. Dynamic Context Injection

`!`command`` 문법으로 셸 커맨드를 실행하고 결과를 주입.

```markdown
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`
```

**동작 방식**:
- 스킬 콘텐츠가 Claude에게 전송되기 **전에** 실행
- 커맨드 출력이 플레이스홀더를 대체
- Claude는 전처리된 최종 결과만 봄
- 셸은 `shell` frontmatter로 지정 (`bash` 기본, `powershell`)

**권한·제약 (변경사항)**:
- **(v2.1.271)** auto mode에서도 `!` 명령은 분류기가 아닌 **기본 모드 권한 규칙**을 따름. 규칙으로 결정되지 않는 명령은 검토되는 도구 호출로 실행.
- **(v2.1.290)** 탭·줄바꿈 외의 제어 문자가 들어간 `!` 명령은 거부됨.
- **(v2.1.299)** `UserPromptSubmit` 훅이 스킬 확장 **전에** 실행 → 훅이 프롬프트를 막으면 내장 셸 명령도 실행 안 됨.
- **(v2.1.323)** bare 저장소 worktree 등 특수 폴더에서는 인라인 git 명령이 허용 전까지 멈춤 (auto mode·bypass 제외).

---

## 8. Subagent 실행 (context: fork)

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**동작**:
- `context: fork`: 격리된 컨텍스트에서 실행. 대화 히스토리 접근 불가.
- 결과는 메인 대화로 반환
- `agent` 생략 시 `general-purpose` 사용

**주의**: `context: fork`는 명시적 인스트럭션이 있는 스킬에서만 의미 있음. 가이드라인만 있는 스킬은 동작 없이 반환됨.

### 백그라운드 실행 기본값 (v2.1.218) — 동작 변경

- `context: fork` 스킬은 **기본적으로 백그라운드에서 실행**되고, 결과는 완료 시 도착함.
- 호출한 턴에서 결과를 기다리게 하려면 `background: false`.
- 백그라운드 fork는 **더 좁은 도구 세트**를 씀 → 그 밖의 도구가 필요한 단계가 있으면 `background: false` 지정.
- 비대화형(`-p`, Agent SDK), `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, 같은 스킬의 이전 호출이 실행 중일 때, 세션 예약 작업으로 실행될 때는 자동으로 결과를 기다림.
- **(v2.1.323)** 안전장치가 fork 스킬을 멈추면 Claude는 직접 대신 하지 않고, 더 좁은 프롬프트로 재시도하거나 사용자에게 알림.

```yaml
---
name: build-report
description: Build the weekly report and return the summary
context: fork
background: false   # 결과를 받아 바로 이어서 작업해야 할 때
---
```

---

## 9. Subagents에 Skills 프리로드

서브에이전트에서 스킬을 사용하려면 명시적으로 `skills` 필드를 지정해야 함.

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions and patterns from the preloaded skills.
```

- `skills` 필드: 서브에이전트 시작 시 전체 스킬 콘텐츠를 컨텍스트에 주입
- 호출용이 아닌 직접 주입
- 서브에이전트는 부모 대화에서 스킬을 **상속받지 않음**
- **(v2.1.295)** 프리로드는 최대 32개(각 1회). Skill 도구가 있는 서브에이전트는 나머지를 호출 가능
- `disable-model-invocation: true` 스킬은 프리로드되지 않음

---

## 10. Hooks

스킬 라이프사이클 범위의 훅. 스킬 활성 시에만 실행, 종료 시 자동 정리.

```yaml
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
          once: true
---
```

| 이벤트 | 실행 시점 |
|--------|----------|
| PreToolUse | 도구 실행 전 |
| PostToolUse | 도구 실행 후 |
| PreCompact | **(v2.1.105)** 컨텍스트 압축 전. exit code 2 또는 `{"decision":"block"}` 반환으로 압축 차단 가능 |
| Stop | 스킬 종료 시 (SubagentStop으로 자동 변환) |
| StopFailure | **(v2.1.78)** API 에러(rate limit, auth 실패 등)로 턴이 종료될 때 |
| PostCompact | **(v2.1.76)** 컨텍스트 압축 완료 후 |
| InstructionsLoaded | **(v2.1.69)** CLAUDE.md / rules 파일이 컨텍스트에 로드될 때 |
| PermissionDenied | **(v2.1.88)** auto mode classifier가 권한 거부 후 발생. `{retry: true}` 반환으로 재시도 지시 가능 |
| TaskCreated | **(v2.1.84)** `TaskCreate`로 태스크 생성 시 발생 |
| CwdChanged | **(v2.1.83)** 작업 디렉토리 변경 시 (예: direnv) |
| FileChanged | **(v2.1.83)** 파일 변경 감지 시 |

**옵션**:
- `matcher`: 특정 도구 이름과 매칭 (예: `"Bash"`, `"*"`)
- `once: true`: 세션에서 한 번만 실행 (스킬 전용, 에이전트에서는 미지원)
- `if`: **(v2.1.85)** 조건부 실행. permission rule 문법 사용 (예: `Bash(git *)`). 프로세스 스폰 오버헤드 감소. **(v2.1.89 수정)** compound commands 및 env-var 접두사 명령도 정상 매칭.

**제한 (v2.1.299·v2.1.304)**:
- 한 출처(저장소·개인 폴더·플러그인)의 스킬들은 세션당 훅 최대 1,024개, matcher 합계 16,384자.
- 스킬 frontmatter의 `UserPromptSubmit` 훅은 스킬을 호출한 프롬프트가 아니라 **그 다음 프롬프트부터** 실행.
- 플러그인 훅만 허용하는 정책에서 훅이 차단된 스킬은 `allowed-tools`도 적용되지 않음 (v2.1.304).

### "defer" Permission Decision (v2.1.89)

**(v2.1.89)** PreToolUse 훅에서 `permissionDecision: "defer"` 반환 가능. Headless 세션(`-p`)에서 도구 호출을 일시 중지하고, `-p --resume`으로 재개하여 재평가. CI/CD 승인 워크플로우에 유용.

### Hook 입력 (v2.1.88)

**(v2.1.88)** PreToolUse/PostToolUse 훅에서 Write/Edit/Read 도구의 `file_path`가 **절대 경로**로 제공됨.

### HTTP Hooks (v2.1.63)

셸 커맨드 대신 HTTP POST로 훅을 실행할 수 있음:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: http
          url: "https://example.com/webhook"
```

JSON 입력을 URL로 POST하고, JSON 응답을 받음. 셸 환경 의존성 없이 외부 서비스 연동 가능.

---

## 11. Extended Thinking & Effort

스킬 콘텐츠 어디서든 **"ultrathink"** 단어를 포함하면 확장 사고(extended thinking) 모드가 활성화됨.

### Effort Levels (v2.1.72)

`/effort` 명령으로 모델 노력 수준 조절 가능:
- `low` (○): 빠른 응답, 간단한 작업
- `medium` (◐): 대부분의 작업
- `high` (●): 복잡한 분석, 정교한 작업 **(v2.1.94부터 API-key, Bedrock/Vertex/Foundry, Team, Enterprise의 기본값)**
- `/effort auto`: 기본값으로 리셋

**(v2.1.80)** 스킬/슬래시 커맨드 frontmatter에 `effort` 필드로 호출 시 자동 오버라이드 가능.

### Thinking Summaries (v2.1.88)

**(v2.1.89)** Thinking summaries가 인터랙티브 세션에서 **기본 비활성화**로 변경됨. 복원하려면 `showThinkingSummaries: true`를 settings에 설정.

---

## 12. Skill Permission Control

### 모든 스킬 비활성화
```
# /permissions deny 규칙에 추가:
Skill
```

### 특정 스킬 허용/차단
```
# 특정 스킬만 허용
Skill(commit)
Skill(review-pr *)

# 특정 스킬 차단 (deny에 추가)
Skill(deploy *)
```

**문법**:
- `Skill(name)`: 정확한 이름 매치
- `Skill(name *)`: 접두사 매치 (인자 포함)

`user-invocable`은 메뉴 표시만 제어. 프로그래밍 방식 호출 차단은 `disable-model-invocation: true` 사용.

**(v2.1.222)** Claude가 `disable-model-invocation` 스킬을 호출하려 하면, 워크플로를 흉내 내지 말고 사용자에게 직접 실행을 요청하라는 안내를 받음.

### 예약 작업·`/loop`에서의 스킬 (v2.1.325) — 동작 변경

예약 작업과 `/loop`은 `allowed-tools`나 훅을 선언한 스킬을 실행하기 전에 **확인을 요청**함. 무인 실행하려면 `permissions.allow`에 `Skill(name)` 추가.

### `anthropic-skills` 규칙 (v2.1.282·v2.1.283)

- `Skill(anthropic-skills:*)` allow 규칙은 claude.ai에서 동기화된 스킬에만 적용 (같은 이름을 쓰는 플러그인 등은 미포함).
- `Skill(anthropic-skills:<name>)` deny 규칙은 Claude Desktop이 플러그인으로 전달한 같은 스킬도 차단.
- 관리 설정 `allowManagedPermissionRulesOnly` 아래에서는 저장소·사용자·`--add-dir` 스킬과 비공식 출처 플러그인의 `allowed-tools` 사전 승인이 적용되지 않음 (v2.1.282·v2.1.284 수정).

---

## 13. Description 작성 Best Practice

Description은 **가장 중요한 필드**. Claude가 언제 스킬을 사용할지 결정하는 유일한 기준 (body는 트리거 후에만 로드).

### 필수 규칙

1. **3인칭으로 작성** (시스템 프롬프트에 주입되므로)
   - Good: `Processes Excel files and generates reports`
   - Bad: `I can help you process Excel files`
   - Bad: `You can use this to process Excel files`

2. **무엇 + 언제** 둘 다 포함
   - 무엇을 하는지 + 언제 사용해야 하는지

3. **트리거 키워드 포함**
   - 사용자가 자연스럽게 말할 표현을 description에 포함
   - 한국어 스킬이면 한국어 키워드 필수

4. **1024자 이내**

5. **"When to Use" 정보는 description에**
   - body에 "When to Use This Skill" 섹션을 넣어도 트리거 판단에 도움 안 됨
   - description에 있어야 Claude가 판단 가능

### 좋은 예시

```yaml
description: Google Calendar 일정 조회, 검색, 등록. "오늘 일정", "이번 주 일정", "일정 검색", "미팅 잡아줘" 등을 언급하면 자동 실행.
```

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

### 나쁜 예시

```yaml
description: Helps with documents  # 너무 모호
description: Calendar management    # 키워드 부족
description: A useful tool          # 정보 없음
```

---

## 14. Naming Conventions

### 규칙

- **소문자, 숫자, 하이픈만** 허용
- 최대 64자
- "anthropic", "claude" 포함 금지 (예약어)
- XML 태그 금지

> 위 규칙은 [Agent Skills](https://agentskills.io) 스펙 기준(다른 제품과 호환). Claude Code 자체는 숨김·제어 문자·`<`·`>` 등만 거부하고, 이름 비교 시 대소문자·공백을 무시함. **(v2.1.292)** 256자를 넘는 `name`은 무시. 교육·실무에서는 스펙 규칙(소문자·하이픈·64자)을 따르는 것이 안전.

### 권장 형식

- Gerund: `processing-pdfs`, `analyzing-spreadsheets`
- 명사구: `pdf-processing`, `spreadsheet-analysis`
- 액션: `process-pdfs`, `analyze-spreadsheets`

### 피해야 할 이름

`helper`, `utils`, `tools`, `documents`, `data`, `files` (너무 모호)

---

## 15. Skill Content Types

### Reference Content (참조형)

Claude가 현재 작업에 적용하는 지식. 인라인 실행 (대화 컨텍스트와 함께 사용).

```yaml
---
name: api-conventions
description: API design patterns and conventions for this codebase. Loaded when writing API endpoints.
---

When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation
```

적합한 경우: 컨벤션, 패턴, 스타일 가이드, 도메인 지식

### Task Content (작업형)

단계별 인스트럭션. 직접 호출이 적합.

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---

Deploy the application:
1. Run the test suite
2. Build the application
3. Push to the deployment target
```

적합한 경우: 배포, 데이터 처리, 복잡한 워크플로우

---

## 16. allowed-tools 사용법

### 기본

```yaml
allowed-tools: Read, Grep, Glob
```

`allowed-tools`는 **사전 승인**이다: 스킬을 호출한 턴 동안 나열한 도구를 권한 확인 없이 쓰게 할 뿐, 나머지 도구를 막지는 않음 (나머지는 평소 권한 규칙대로 확인). 다음 메시지를 보내면 해제. 도구를 아예 빼려면 `disallowed-tools`.

### Bash 범위 지정

```yaml
allowed-tools: Bash(gh *), Read
```

`Bash(gh *)`: `gh`로 시작하는 명령을 확인 없이 실행 (다른 Bash 명령은 평소대로 권한 확인)

### 사용 가능한 주요 도구

`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `Task`, `Skill`, `NotebookEdit`

MCP 도구: `mcp__server-name__tool-name` 형식

---

## 17. @file 참조 및 !command 문법 (콘텐츠 내)

Skills/Commands 콘텐츠에서 사용 가능한 전처리 문법들.

### @file 참조

```markdown
Review these configuration files:

@package.json
@tsconfig.json
@.eslintrc.js
```

`@` 접두사가 붙은 파일 내용이 프롬프트에 포함됨.

### !command 실행

```markdown
Recent changes:
!git log --oneline -5
!git diff HEAD~1
```

`!` 접두사가 붙은 명령어 출력이 프롬프트에 포함됨. 스킬 콘텐츠가 Claude에게 전송되기 전에 실행.

### Plugin/MCP 네임스페이스

- **Plugin Commands**: `/plugin-name:command-name` (충돌 없으면 접두사 생략 가능)
- **MCP Slash Commands**: `/mcp__<server-name>__<prompt-name>` (MCP 서버 연결 시 자동 생성)

---

## 18. Troubleshooting

### 스킬이 트리거되지 않음

1. description에 사용자가 말할 키워드 포함 여부 확인
2. `What skills are available?`로 존재 확인
3. `/skill-name`으로 직접 호출하여 스킬 자체 동작 확인
4. description을 더 구체적으로 수정
5. **(v2.1.69)** description에 콜론(`:`)이 있으면 YAML 파싱 실패할 수 있었음 - 수정됨
6. **(v2.1.69)** `description:` 없는 프로젝트 스킬이 목록에 안 나오던 버그 - 수정됨

7. **(v2.1.299)** 폴더/파일명에 숨김 문자·`<`·`>`가 있으면 목록에서 빠짐 → 이름 변경
8. 세션 시작 후 새 최상위 스킬 디렉토리를 만들었으면 `/reload-skills`
9. 하위 폴더 스킬이면 2장 「중첩 스킬 로딩 제한」 확인 (샌드박스 켜짐 시 해당 폴더에서 시작하거나 `/cd`)

### 진단 도구

- **(v2.1.233)** `claude plugin validate`: `.claude/skills` 디렉토리에서 frontmatter 파싱 실패한 SKILL.md 보고
- **(v2.1.261)** `/skill-doctor`: 안 쓰이는 스킬과 컨텍스트 비용
- **(v2.1.283)** `/doctor prompt-audit`(= `/checkup prompt-audit`): CLAUDE.md·스킬·에이전트·커맨드에서 구형 모델용 프롬프트 패턴 점검
- **(v2.1.296)** `--debug`가 커스텀 에이전트 파일의 인식 안 되는 frontmatter 필드를 오타 힌트와 함께 표시

### 스킬이 너무 자주 트리거됨

1. description을 더 좁게 수정
2. `disable-model-invocation: true` 추가

### Claude가 모든 스킬을 보지 못함

- 스킬이 너무 많으면 context budget 초과
- `/context`로 제외된 스킬 경고 확인
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 환경 변수로 한도 조정

### 파일 경로 확인

- YAML `---`가 반드시 1번째 줄 (앞에 빈 줄 없음)
- frontmatter와 내용 사이에 `---`로 구분
- 들여쓰기에 탭이 아닌 스페이스

---

## 19. Skills vs 다른 옵션

| 방법 | 목적 | 실행 시점 |
|------|------|----------|
| **Skills** | 전문 지식/기능 추가 | Claude 자동 판단 + 사용자 호출 |
| **Slash Commands** | 재사용 프롬프트 | `/command` 입력 시 |
| **CLAUDE.md** | 프로젝트 전체 지침 | 모든 대화에 항상 로드 |
| **Subagents** | 별도 컨텍스트 위임 | Claude 위임 또는 직접 호출 |
| **Hooks** | 이벤트 기반 스크립트 | 특정 도구 이벤트 시 |
| **MCP** | 외부 도구/데이터 연결 | Claude 필요시 호출 |

---

## 20. Best Practice Checklist

### DO

- [ ] description에 트리거 키워드 포함 (사용자가 실제로 말할 표현)
- [ ] description을 3인칭으로 작성
- [ ] SKILL.md 500줄, 5k 토큰 미만 유지
- [ ] 상세 문서는 지원 파일로 분리 (progressive disclosure)
- [ ] 스크립트를 번들링하여 결정론적 실행 활용
- [ ] 민감한 작업에 `disable-model-invocation: true` 설정
- [ ] `allowed-tools`로 최소 권한 원칙 적용
- [ ] 배포 전 트리거 테스트

### DON'T

- [ ] 모호한 description 사용 (helper, utils, tools)
- [ ] body에 "When to Use" 섹션만 두고 description 비움
- [ ] 모든 문서를 SKILL.md 한 파일에 몰아넣음
- [ ] "anthropic", "claude" 이름 사용
- [ ] 깊게 중첩된 파일 참조 (A -> B -> C)
- [ ] 외부 패키지 의존성 미언급

---

## 21. Practical Template

새 스킬 생성 시 시작점.

```yaml
---
name: skill-name
description: [3인칭] [무엇을 하는지] [언제 사용하는지 + 트리거 키워드]
allowed-tools: [최소 필요 도구]
---

# [Skill Name]

## Overview
[한 문단: 이 스킬이 하는 일]

## Instructions
[Claude가 따를 단계별 가이드]

## Additional Resources
- For details, see [reference.md](reference.md)

## Examples
[입력/출력 예시]
```

---

## Sources

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) - 메인 공식 문서
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) - 플랫폼 문서
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - 작성 가이드
- [Subagents](https://code.claude.com/docs/en/sub-agents) - 서브에이전트 연동
- [github.com/anthropics/skills](https://github.com/anthropics/skills) - 공식 스킬 저장소

---

## Update History

- **2026-11-16**: v2.1.208~v2.1.325 변경사항 반영 + 공식 문서 대조
  - **[동작 변경] `context: fork` 기본 백그라운드 실행** (v2.1.218), `background: false`로 opt-out. frontmatter 불리언에 `yes`/`no`/`on`/`off`/`1`/`0` 허용
  - **[동작 변경] 예약 작업·`/loop`이 `allowed-tools`/훅 선언 스킬 실행 전 확인** (v2.1.325) — `Skill(name)` allow로 무인 실행
  - **[동작 변경] 중첩 `.claude/skills` 로딩 제한** (v2.1.319 샌드박스, v2.1.321 `~/.claude/plugins`, v2.1.325 `--plugin-dir`)
  - frontmatter 표 보강(공식 문서 기준): `when_to_use`, `arguments`/`$name`, `paths`, `disallowed-tools`, `shell`, `license`, `compatibility`, effort `xhigh`/`max`, `allowed-tools` 의미 정정(호출 턴 한정 사전 승인, 제한 아님)
  - 치환 변수 추가: `${CLAUDE_EFFORT}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`
  - claude.ai 스킬 동기화 (v2.1.275), 동기화 스킬 하드닝 (v2.1.228), `anthropic-skills` 네임스페이스 예약 (v2.1.282, `claude-ai`는 v2.1.283에서 되돌림)
  - `/skill-doctor` (v2.1.261), `/doctor prompt-audit` (v2.1.283), `claude plugin validate`의 `.claude/skills` 검사 (v2.1.233)
  - 컴팩션 후 스킬 목록 재전송·`/reload-skills` 변경분만 (v2.1.304), 서브에이전트 프리로드 최대 32개 (v2.1.295), 스킬 훅 한도 (v2.1.304)
  - auto mode의 `!` 명령은 기본 권한 규칙 적용 (v2.1.271), 제어 문자 포함 `!` 거부 (v2.1.290), `UserPromptSubmit` 훅이 스킬 확장 전 실행 (v2.1.299)
  - 버그 수정: frontmatter `model:` 무시 (v2.1.259), `effort:` 무시 (v2.1.267), `-p`에서 `allowed-tools`/`effort` 누락 (v2.1.295)
  - **보류**: `display-name`·`default-enabled`·`fallback`은 공식 frontmatter 표에서 확인되지 않아 경고 표시만 추가
- **2026-07-13**: v2.1.120~2.1.207 변경사항 반영
  - **스킬 frontmatter 확장** (v2.1.186): `display-name`, `default-enabled`, `fallback`, `metadata.*` 필드 추가
  - **중첩 `.claude/skills` 이름 충돌 규칙** (v2.1.178): 충돌 시 중첩 스킬이 `<dir>:<name>`로 표시되어 공존. non-interactive에서 디렉토리 한정 이름 권한 프롬프트 버그 수정
  - `disableBundledSkills` 설정 + `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` 환경 변수 추가 (v2.1.169) — 내장 스킬/워크플로우/빌트인 커맨드 숨김
  - `--safe-mode` 플래그 추가 (v2.1.169) — 모든 커스터마이징(CLAUDE.md·플러그인·스킬·훅·MCP) 비활성화 진단 모드
  - `.claude/skills`의 플러그인 마켓플레이스 없이 자동 로드 + `claude plugin init <name>` 스캐폴딩 (v2.1.157)
  - **이미 로드된 스킬 재호출 시 인스트럭션이 컨텍스트에 중복 append되던 버그 수정** (v2.1.202)
  - `/plugin` Installed 탭에 "Skills" 섹션 추가 (v2.1.186)
  - `!` bash 커맨드 출력에 Claude가 자동 응답하도록 변경 (v2.1.186, `respondToBashCommands: false`로 종전 동작 유지)
  - user-level 스킬이 자동완성에 중복 표시 / non-interactive 권한 프롬프트 등 다수 버그 수정 (v2.1.181·183)
- **2026-04-19**: v2.1.110~2.1.114 변경사항 반영
  - `/less-permission-prompts` 빌트인 스킬 추가 (v2.1.111) — 트랜스크립트 스캔 후 read-only Bash/MCP 호출을 prioritized allowlist로 제안
  - `/skills` 메뉴 토큰 수 정렬 옵션 추가 (v2.1.111) — `t` 키로 토글
  - `/ultrareview` 슬래시 커맨드 추가 (v2.1.111) — 클라우드에서 parallel multi-agent 코드 리뷰. `/ultrareview <PR#>`로 GitHub PR 직접 리뷰
  - `/ultrareview` 개선 (v2.1.114) — 병렬 실행으로 launch 속도 개선, launch 다이얼로그에 diffstat 표시
  - 존재하지 않는 `commit` 스킬 호출로 "Unknown skill: commit" 오류 발생하던 버그 수정 (v2.1.111)
  - Skill 호출 시 `commit` 누락 사용자 대상 fallback 처리 (v2.1.111)
- **2026-04-15**: v2.1.105~2.1.109 변경사항 반영
  - 스킬 description 목록 상한 250자 → **1,536자**로 상향, 잘림 시 시작 경고 (v2.1.105)
  - **PreCompact hook 차단 지원**: exit code 2 또는 `{"decision":"block"}`로 압축 거부 가능 (v2.1.105)
  - 모델이 Skill tool로 내장 슬래시 커맨드(`/init`, `/review`, `/security-review`) 발견/호출 가능 (v2.1.108)
  - `/proactive`가 `/loop`의 alias로 추가 (v2.1.105)
  - `/undo`가 `/rewind`의 alias로 추가 (v2.1.108)
  - 플러그인 `monitors` manifest 키로 백그라운드 모니터 자동 arm (v2.1.105)
  - Agent tool auto mode에서 safety classifier transcript가 컨텍스트 초과 시 권한 요청하던 버그 수정 (v2.1.108)
- **2026-04-13**: v2.1.93~2.1.101 변경사항 반영
  - `keep-coding-instructions` frontmatter 필드 추가 (v2.1.94) - Plugin output style 코딩 인스트럭션 유지
  - 기본 effort 수준이 medium에서 high로 변경 (v2.1.94, API-key/Bedrock/Vertex/Foundry/Team/Enterprise)
  - Plugin skills `"skills": ["./"]` 선언 시 frontmatter `name`으로 호출 (v2.1.94)
  - `/reload-plugins`가 세션 재시작 없이 스킬 변경사항 즉시 반영 (v2.1.98)
  - Plugin skill hooks YAML frontmatter 무시 수정 (v2.1.94)
  - Hook 에러에 stderr 포함으로 자가 진단 개선 (v2.1.98)
- **2026-04-04**: v2.1.90~2.1.92 변경사항 반영
  - `disableSkillShellExecution` 설정 추가 (v2.1.91) - 인라인 셸 실행 비활성화
  - `/powerup` 커맨드 추가 (v2.1.90) - 인터랙티브 학습 + 애니메이션 데모
  - `/tag`, `/vim` 커맨드 제거 (v2.1.92)
  - Edit 도구 shorter `old_string` anchors로 출력 토큰 감소 (v2.1.91)
- **2026-04-01**: v2.1.89 변경사항 반영
  - `"defer"` PreToolUse permission decision 추가 (headless 세션 일시중지/재개)
  - hooks `if` 조건 compound commands 및 env-var 접두사 매칭 수정
  - Thinking summaries 기본 비활성화 시점 정정 (v2.1.89)
- **2026-03-31**: v2.1.79~2.1.88 변경사항 반영
  - `effort` frontmatter 필드 추가 (v2.1.80, skills/slash commands)
  - Hook 이벤트 4종 추가: PermissionDenied (v2.1.88), TaskCreated (v2.1.84), CwdChanged/FileChanged (v2.1.83)
  - 조건부 훅 `if` 필드 (v2.1.85)
  - PreToolUse/PostToolUse `file_path` 절대 경로 제공 (v2.1.88)
  - 스킬 description 250자 제한, `/skills` 알파벳 정렬 (v2.1.86)
- **2026-03-18**: v2.1.51~2.1.78 변경사항 반영
  - `${CLAUDE_SKILL_DIR}` 변수 추가 (v2.1.69)
  - Hook 이벤트 3종 추가: StopFailure (v2.1.78), PostCompact (v2.1.76), InstructionsLoaded (v2.1.69)
  - HTTP Hooks 지원 (v2.1.63)
  - Effort levels 섹션 추가 (v2.1.72)
  - description 콜론 파싱 버그 + description 없는 스킬 목록 누락 수정 기록
- **2026-02-22**: 공식 문서 전면 재정리 (source of truth 목적)
  - String substitutions 섹션 신규
  - Dynamic context injection (`!`command``) 신규
  - 3단계 로딩 메커니즘 정식화
  - Context budget (2% 규칙) 신규
  - Description best practice 상세화 (3인칭, 1024자)
  - argument-hint 필드 추가
  - Extended thinking (ultrathink) 추가
  - Skill permission control 문법 추가
  - Practical template 추가
  - @file 참조, !command, Plugin/MCP namespace 항목 추가 (slash-commands에서 이관)
- **2026-01-16**: v2.1.x 기능 반영 (context: fork, hooks, progressive disclosure)
- **2025-10-22**: 초기 작성
