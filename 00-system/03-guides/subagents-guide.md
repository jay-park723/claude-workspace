# Claude Code Subagents - Source of Truth

> **Source**: [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)
> **Updated**: 2026-11-16 (v2.1.325) - **포크 서브에이전트 기본 활성화**(`/subtask`), **중첩 기본 3단계·동시 실행 20개 상한**, 모델 결정 순서 재정의(`CLAUDE_CODE_SUBAGENT_MODEL`=기본값), frontmatter 신규(`omitClaudeMd`·`autoCompactWindow`·`experimental.cacheTtl`·`color`), Agent `mode` 파라미터 폐지·`TaskOutput`·`subagentStatusLine` 제거, 훅 `onFailure: "block"`·신규 이벤트, "언제 서브에이전트/메인 대화/스킬" 구분 추가
> **Previous**: 2026-07-13 (v2.1.207)
> **Purpose**: Subagent 작성 시 유일한 참조 문서

---

## 1. 개요

서브에이전트는 격리된 컨텍스트 윈도우에서 커스텀 시스템 프롬프트, 특정 도구 접근, 독립적 권한으로 작업을 처리하는 특화된 AI 어시스턴트.

### 핵심 특징

- 컨텍스트 보존: 탐색/구현 작업을 메인 대화와 분리
- 제약 강제: 서브에이전트별 도구 접근 제한
- 설정 재사용: 사용자 레벨로 프로젝트 간 공유
- 비용 절감: 빠른/저렴한 모델(Haiku)로 작업 라우팅
- 자동 위임: Description에 따라 Claude가 자동 호출

### 언제 쓰나: 서브에이전트 vs 메인 대화 vs 스킬 (공식 문서 기준)

| 선택지 | 이럴 때 | 핵심 |
|--------|---------|------|
| **서브에이전트** | ① 결과가 장황해서(검색 결과·로그·파일 내용) 메인 대화에 남길 필요가 없을 때 ② 특정 도구·권한 제한을 강제하고 싶을 때 ③ 독립적으로 끝내고 요약만 돌려주면 되는 작업 | 별도 컨텍스트에서 일하고 **요약만** 반환 |
| **메인 대화** | 주고받으며 반복 다듬기 / 기획·구현·테스트처럼 여러 단계가 맥락을 공유 / 빠르고 작은 수정 / **지연이 중요할 때**(포크가 아닌 서브에이전트는 맥락을 처음부터 모아야 해 느림) | 맥락 공유, 즉시 반응 |
| **스킬** | 재사용할 프롬프트·워크플로를 **메인 대화 컨텍스트 안에서** 돌리고 싶을 때 | 격리 없음, 절차 재사용 |
| **`/btw`** | 이미 대화에 있는 내용에 대한 곁가지 질문 | 서브에이전트 불필요 |

- **커스텀 서브에이전트를 정의할 시점**: 같은 지시로 같은 종류의 작업자를 반복해서 띄우게 될 때.
- 비유: 서브에이전트 = 별도 방에서 일하고 보고서만 내는 외주 담당자 / 스킬 = 내가 직접 보는 업무 매뉴얼.

---

## 2. 기본 제공 서브에이전트

| 에이전트 | 모델 | 도구 | 목적 |
|---------|------|------|------|
| **Explore** | 상속 (예외 있음) | 읽기 전용 (Write/Edit 거부) | 빠른 코드베이스 검색 및 분석 · **(v2.1.198)** haiku 고정에서 메인 세션 모델 상속으로 변경 · 현재 공식 문서: 구독·Console 등에선 `opus` 별칭 모델, Bedrock·Vertex·Foundry 등에선 Fable. 탐색 강도 quick / medium / very thorough. CLAUDE.md·git status 생략 |
| **Plan** | 상속 | 읽기 전용 | 계획 모드 중 리서치. CLAUDE.md·git status 생략 |
| **General-purpose** | 상속 | 모든 도구 | 복잡한 다단계 작업 |
| **claude** | 모델 결정 순서 따름 | 모든 도구 | 범용(catch-all). 백그라운드 세션 디스패치 기본값 |
| **Bash** | 상속 | 터미널 | 명령어 별도 실행 |
| **statusline-setup** | Sonnet | 설정 도구 | 상태줄 설정 |
| **Claude Code Guide** | Haiku | 읽기 전용 | Claude Code 사용법 안내 |

- Explore·Plan 끄기: `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` (v2.1.198+)
- `Bash` 행은 이전 문서 기재. 현재 공식 문서 내장 목록에는 없음(확인 필요).

---

## 3. 파일 구조

### 저장 위치 (우선순위 순)

| 우선순위 | 위치 | 적용 범위 |
|---------|------|----------|
| 1 | `--agents` CLI 플래그 | 현재 세션만 |
| 2 | `.claude/agents/` | 프로젝트 |
| 3 | `~/.claude/agents/` | 모든 프로젝트 |
| 4 | Plugin의 `agents/` | 플러그인 활성화된 곳 |

동일 이름 시 높은 우선순위 버전 적용.

**만드는 법 (현재)**: Claude에게 말로 "이런 에이전트 만들어줘"라고 요청하거나 위 폴더에 `.md` 파일을 직접 작성. `/agents`는 이제 이 안내만 출력(아래 §9 참조).

- 파일은 감시되어 수정 후 몇 초 안에 반영. 단, 해당 스코프에 `agents` 폴더를 **처음** 만들 때·`--add-dir` 폴더·`--disable-slash-commands` 세션은 재시작 필요.
- **(v2.1.296)** `claude --debug` 출력이 커스텀 에이전트 파일의 인식 안 된 frontmatter 필드 이름과 오타 힌트를 보여줌(알 수 없는 필드는 에러 없이 무시되므로 오타 점검용).
- **(v2.1.325)** 샌드박스가 추가 디렉토리의 `.claude` 설정·스킬·에이전트·커맨드·훅 쓰기를 거부(실행 폴더와 동일 규칙).

---

## 4. YAML Frontmatter 전체 필드

```yaml
---
name: agent-name
description: When to use this agent and what it does
tools: Tool1, Tool2, Tool3
disallowedTools: Bash, Write
model: sonnet
effort: medium
skills: skill-1, skill-2
permissionMode: acceptEdits
memory: project
background: false
isolation: worktree
mcpServers: server-1, server-2
maxTurns: 50
autoCompactWindow: 200000
omitClaudeMd: false
color: blue
experimental:
  cacheTtl: 1h
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
| `name` | **필수** | - | 소문자, 하이픈 권장. 최대 256자, `-`로 시작 불가, `:` 포함 불가. |
| `description` | **필수** | - | Claude가 언제 이 에이전트에 위임할지 판단 기준. 전체 에이전트 description 합계 15,000토큰 예산 안에서 서로 구분되게 작성. |
| `tools` | - | 모든 도구 | 허용 목록 (allowlist). 쉼표 구분. 생략 시 서브에이전트가 쓸 수 있는 도구 전부 상속. |
| `disallowedTools` | - | 없음 | 거부 목록 (denylist). 상속/지정 목록에서 제거. |
| `model` | - | 모델 결정 순서(§7) | `sonnet`, `opus`, `haiku`, `fable`, 전체 모델 ID, `inherit`. ⚠️ 이전 문서의 "기본값 sonnet"은 현재 공식 문서와 다름 — 생략 시 §7 순서로 결정(최종적으로 메인 대화 모델). |
| `skills` | - | 없음 | 프리로드할 Skills. 전체 콘텐츠가 시작 시 주입됨. **(v2.1.295)** 최대 32개(중복 제외), `disable-model-invocation: true` 스킬은 프리로드 불가. |
| `permissionMode` | - | 메인 대화 상속 | 권한 동작 방식 (아래 참조). |
| `memory` | - | 없음 | **(신규 v2.1.33)** 세션 간 지속 메모리 스코프. |
| `background` | - | false | **(신규 v2.1.49)** `true`: 항상 백그라운드 실행. |
| `isolation` | - | 없음 | **(신규 v2.1.49)** `worktree`: 임시 git worktree 격리 실행. |
| `mcpServers` | - | 없음 | 사용할 MCP 서버(이름 또는 인라인 정의). 플러그인 에이전트에선 무시. |
| `maxTurns` | - | 없음 | 최대 에이전틱 턴 수 제한. **(v2.1.246)** 한도 도달 시 결과가 "부분(partial)"으로 표시되고 `SendMessage`로 이어가기 가능. |
| `hooks` | - | 없음 | 에이전트 라이프사이클 훅. 플러그인 에이전트에선 무시. |
| `initialPrompt` | - | 없음 | **(v2.1.83)** 에이전트를 **메인 세션 에이전트로**(`--agent`) 실행할 때 자동 제출할 첫 턴. 플러그인 에이전트에선 무시. |
| `effort` | - | 세션 수준 | `low`/`medium`/`high`/`xhigh`/`max`. (v2.1.78 플러그인용으로 도입 → 현재 일반 필드.) `CLAUDE_CODE_EFFORT_LEVEL`이 우선. |
| `autoCompactWindow` | - | 없음 | **(v2.1.296)** 이 에이전트만 더 일찍 자동 압축. `100000`~`1000000` 정수. `200k`처럼 쓰면 200으로 읽혀 무시됨. `CLAUDE_CODE_AUTO_COMPACT_WINDOW`보다 **낮추기만** 가능(v2.1.312). |
| `omitClaudeMd` | - | false | **(v2.1.271)** `true`면 사용자·프로젝트·로컬 CLAUDE.md 없이 시작(관리형 정책 파일은 로드). |
| `color` | - | 없음 | UI 표시색: red/blue/green/yellow/purple/orange/pink/cyan. `--agents` JSON에선 무시. |
| `experimental.cacheTtl` | - | 없음 | **(v2.1.248)** 이 에이전트의 프롬프트 캐시 TTL `5m`/`1h`. 반드시 `experimental:` 아래에 작성. |

### tools vs disallowedTools

| 방식 | 설명 | 사용 시점 |
|------|------|----------|
| `tools` | 허용 목록 (allowlist) | 소수 도구만 허용 |
| `disallowedTools` | 거부 목록 (denylist) | 대부분 허용, 일부 제외 |

두 필드를 동시에 사용하지 않음.

### permissionMode

| 모드 | 설명 |
|------|------|
| `default` (별칭 `manual`) | 각 작업에 사용자 확인 |
| `acceptEdits` | 파일 편집 자동 승인 |
| `auto` | auto mode(분류기가 판단) |
| `dontAsk` | 모든 작업 자동 승인 |
| `bypassPermissions` | 모든 권한 우회 |
| `plan` | 계획 모드에서 실행 |

`dontAsk`, `bypassPermissions`는 신뢰할 수 있는 환경에서만 사용.

**상속 규칙 (공식 문서)**: 비워두면 메인 대화 모드를 상속.
- 메인이 `bypassPermissions`·`acceptEdits`·auto면 → 서브에이전트도 같은 모드, 설정값 **무시**.
- 메인이 `plan`이면 → 서브에이전트도 plan 유지(에이전트 팀 팀원 제외).
- 메인이 `default`·`dontAsk`면 → 설정값 적용(단 `bypassPermissions`는 v2.1.267+, auto 미지원 환경의 `auto`는 메인 모드 유지).
- **(v2.1.212 Deprecated)** Agent 도구의 `mode` 파라미터는 무시됨. 서브에이전트는 기본적으로 부모 세션 권한 모드 상속.
- **(v2.1.319)** `permissions.denyInsteadOfPrompting` 설정: 권한 프롬프트를 기다릴 호출을 바로 거부하고 턴을 계속(서브에이전트·팀원 포함). 무인 실행용.

### memory (v2.1.33, 신규)

세션 간 지속 메모리. 에이전트가 학습한 패턴, 디버깅 인사이트 등을 축적.

```yaml
memory: project    # 프로젝트 스코프
memory: user       # 사용자 전역 스코프
memory: local      # 로컬 스코프
```

### Monitor Tool (v2.1.98)

`Monitor` 도구 추가: 백그라운드 스크립트의 이벤트를 스트리밍으로 수신. 백그라운드 에이전트/태스크의 진행 상황을 실시간으로 추적하는 데 유용.

### background (v2.1.49, 신규)

```yaml
background: true   # Claude가 기다리려 해도 백그라운드 유지
```

### isolation (v2.1.49, 신규)

```yaml
isolation: worktree  # 임시 git worktree에서 격리 실행
```

- 변경사항 없으면 worktree 자동 정리
- 변경사항 있으면 worktree 경로와 브랜치 반환
- **(v2.1.325)** 격리 worktree 세션/에이전트에서는 `git bisect run`, `git maintenance register|start`, `scalar` 설정 명령이 거부됨
- **(v2.1.323)** `.git`이 링크이거나 하드링크를 가진 체크아웃(git-new-workdir, `cp -al` 복사본)에서는 worktree 생성 거부 → 일반 clone 사용

### Agent(agent_type) 스폰 제한 (v2.1.33, 신규)

에이전트가 스폰할 수 있는 서브에이전트를 화이트리스트로 제한 (현재 도구 이름은 `Agent`. 이전 문서의 `Task(...)` 표기는 구 이름):

```yaml
tools: Agent(worker, researcher), Read, Write
```

`claude --agent`로 실행되는 에이전트에만 적용.

### `--print` / `--agent` 모드 frontmatter 준수 (v2.1.119)

- `--print` 모드가 이제 에이전트 정의의 `tools:`와 `disallowedTools:` frontmatter를 interactive 모드와 동일하게 준수
- `--agent <name>`으로 built-in agent 실행 시 에이전트 정의의 `permissionMode`를 준수

이전 버전에서는 headless/print 모드에서 이 필드들이 무시되어 예상치 못한 도구 호출이 가능했던 문제가 수정됨.

### MCP 서버 병렬 연결 (v2.1.119)

서브에이전트와 SDK MCP 서버의 reconfiguration이 직렬 → 병렬로 바뀌어 시작 속도 개선. 다수의 MCP 서버를 쓰는 서브에이전트일수록 체감 차이 큼.

---

## 5. Hooks

### 이벤트 유형

| 이벤트 | 매처 | 설명 |
|--------|------|------|
| `PreToolUse` | 도구 이름 | 도구 실행 전 |
| `PostToolUse` | 도구 이름 | 도구 실행 후 |
| `Stop` | 없음 | 에이전트 종료 시 |
| `SubagentStart` | 에이전트 이름 | 서브에이전트 시작 시 (프로젝트 레벨) |
| `SubagentStop` | 에이전트 이름 | 서브에이전트 완료 시 (프로젝트 레벨) |
| `TeammateIdle` | - | **(신규 v2.1.33)** Agent Teams용. exit 2로 작업 계속 강제. |
| `TaskCompleted` | - | **(신규 v2.1.33)** 태스크 완료 시. exit 2로 차단 및 피드백. |
| `WorktreeCreate` | - | **(v2.1.50)** isolation worktree 생성 시. |
| `WorktreeRemove` | - | **(v2.1.50)** isolation worktree 삭제 시. |
| `PermissionDenied` | - | **(v2.1.88)** auto mode 권한 거부 후. `{retry: true}` 반환 가능. |
| `TaskCreated` | - | **(v2.1.84)** `TaskCreate`로 태스크 생성 시. |
| `CwdChanged` | - | **(v2.1.83)** 작업 디렉토리 변경 시 (예: direnv 연동). |
| `FileChanged` | - | **(v2.1.83)** 파일 변경 감지 시. |
| `StopFailure` | - | **(v2.1.78)** API 에러(rate limit, auth 실패 등)로 턴 종료 시. |
| `PostCompact` | - | **(v2.1.76)** 컨텍스트 압축 완료 후. |
| `InstructionsLoaded` | - | **(v2.1.69)** CLAUDE.md / rules 로드 시. |
| `Elicitation` | - | **(v2.1.76)** MCP 서버가 구조화된 입력을 요청할 때. |
| `DirectoryAdded` | - | **(v2.1.219)** `/add-dir` 등으로 작업 디렉토리가 세션 중 추가된 뒤. |
| `PreModelSwitch` / `PostModelSwitch` | - | **(v2.1.251)** 모델 전환 차단·확인·주석. |

### Hook 동작

- exit code `0`: 통과
- exit code `2`: 작업 차단 (stderr 메시지 표시)
- 입력은 stdin으로 JSON 형식 전달
- **(v2.1.69)** `agent_id` (서브에이전트) 및 `agent_type` (서브에이전트 + `--agent`) 필드가 훅 이벤트에 포함
- **(v2.1.85)** `if` 필드: 조건부 실행. permission rule 문법 사용 (예: `Bash(git *)`). **(v2.1.89 수정)** compound commands 및 env-var 접두사 매칭 정상화.
- **(v2.1.88)** PreToolUse/PostToolUse에서 Write/Edit/Read의 `file_path`가 절대 경로로 제공
- **(v2.1.85)** `PreToolUse` 훅이 `AskUserQuestion`에 `updatedInput` + `permissionDecision: "allow"` 반환 가능 (headless 연동)
- **(v2.1.89)** `PreToolUse` 훅에서 `permissionDecision: "defer"` 반환 가능. Headless 세션에서 도구 호출 일시 중지 후 `-p --resume`으로 재개.
- **(v2.1.214 동작 변경)** `if:`의 한 단계 `dir/**`는 이제 `<cwd>/dir`만 매칭. 어느 깊이든 매칭하려면 `**/dir/**`로 작성. (`deny`/`ask` 권한 규칙은 기존처럼 모든 깊이 매칭)
- **(v2.1.214)** 포크로 시작된 세션의 SessionStart 훅 source가 `"resume"` 대신 `"fork"`.
- **(v2.1.295)** `onFailure: "block"` (command·HTTP 훅): 훅이 시작 실패·타임아웃·예상 외 exit code면 작업을 **통과 대신 차단**. 보안용 훅에 권장. (Agent SDK 콜백은 v2.1.317)
- **(v2.1.299)** `UserPromptSubmit` 훅이 스킬·커스텀 슬래시 커맨드 **확장 전**에 실행 → 차단 시 내장 셸 명령도 멈춤.
- **(v2.1.300)** PreToolUse·PermissionRequest의 `updatedInput`이 일반 입력처럼 검증됨: 알 수 없는 키는 버려지고, 도구가 거부하는 입력이면 호출 거부.
- **(v2.1.280)** `PermissionRequest`에는 agent 타입 훅을 쓸 수 없음(command/http 사용).
- **(v2.1.292)** 훅 출력의 `<system-reminder>` 태그는 이스케이프되어 Claude에 전달.
- **(v2.1.302 / v2.1.312)** prompt·agent 타입 훅 동시 실행 상한: 이벤트당 12개, 세션 전체(서브에이전트 포함) 24개. `timeout` 1초 미만은 1초로 처리.
- **(v2.1.319)** 새 메시지로 턴이 끊긴 뒤 끝난 도구 호출에도 PostToolUse 훅이 실행(최대 10초).
- **(v2.1.286)** `/hooks`가 이벤트별로 묶인 훅 목록으로 바로 열림. 상세 화면에 훅 종류와 수정 위치 표시(v2.1.281).

### HTTP Hooks (v2.1.63)

셸 커맨드 대신 HTTP POST로 훅 실행 가능:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: http
          url: "https://example.com/webhook"
```

### MCP Tool Hooks (v2.1.118)

훅이 셸 커맨드/HTTP 대신 MCP 도구를 직접 호출 가능:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: mcp_tool
          server: my-mcp-server
          tool: validate_command
```

MCP 서버에 정의된 도구로 검증/처리 로직을 위임할 수 있음.

### PostToolUse 실행 시간 측정 (v2.1.119)

`PostToolUse`와 `PostToolUseFailure` 훅 입력에 `duration_ms` 필드가 포함 (permission prompt와 PreToolUse 훅 시간 제외한 순수 도구 실행 시간).

### Stop/SubagentStop 훅 (v2.1.47 추가)

`last_assistant_message` 필드: 에이전트 최종 응답 텍스트를 훅에서 직접 접근 가능 (트랜스크립트 파싱 불필요).

**(v2.1.181)** Stop·SubagentStop 훅이 `hookSpecificOutput.…`을 반환할 수 있게 확장됨(추가 컨텍스트를 다음 턴으로 전달하는 용도).

**(v2.1.294)** Stop·SubagentStop의 `prompt` 훅을 지시문("빌드가 깨져 있으면 계속해")으로 써도 더 정확히 판정되어 조기 종료가 줄어듦.

### 예시

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
          onFailure: block   # (v2.1.295) 스크립트가 실패해도 통과시키지 않음
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup.sh"
```

---

## 6. 실행 모드

### Background (v2.1.198부터 기본값)

**(v2.1.198)** 서브에이전트는 이제 **기본적으로 백그라운드에서 실행**됨. Claude는 서브에이전트가 도는 동안 다른 작업을 계속하고, 완료되면 알림을 받음(과거엔 점진적 롤아웃이었으나 이제 전면 적용).

```yaml
background: true  # YAML로 항상 백그라운드 강제 (기본 동작과 동일)
```

또는:
- Agent 도구의 `run_in_background: true` (기본값이 true로 동작)
- 동기적으로 기다려야 하면 `run_in_background: false`로 명시 — ⚠️ **포크 모드가 켜져 있으면(v2.1.232 터미널, v2.1.302부터 전 환경 기본)** 인터랙티브 터미널·VS Code·데스크톱에서 Claude가 서브에이전트를 기다릴 수 없음. 기다리게 하려면 `CLAUDE_CODE_FORK_SUBAGENT=0`. `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`은 백그라운드 명령까지 함께 끔.
- 실행 중 `Ctrl+B`로 백그라운드 전환

**동작**: ESC로 메인 취소 시 백그라운드는 계속 실행. `Ctrl+F`로 강제 종료. 백그라운드 서브에이전트의 권한 프롬프트는 메인 세션에 뜨며, Esc는 그 호출 하나만 거부(서브에이전트는 계속). `Ctrl+X Ctrl+K`로 모든 백그라운드 에이전트 중지(v2.1.290 프롬프트에 표시). 백그라운드 서브에이전트는 포그라운드보다 작은 내장 도구 세트를 받음.

- **(v2.1.232)** 인터랙티브 세션에서 팀원이 아닌 에이전트 스폰은 기본 백그라운드. **(v2.1.302)** 데스크톱·VS Code도 메인 대화의 서브에이전트를 항상 백그라운드 실행.
- **(v2.1.260)** 서브에이전트가 띄운 백그라운드 명령의 1시간 제한 제거. **(v2.1.318)** 백그라운드 서브에이전트의 셸 명령은 3분 후 자동으로 백그라운드로 이동(캐시 만료 방지).
- **(v2.1.317)** 실행 중인 백그라운드 에이전트에 `SendMessage`하면 실행 중 명령을 백그라운드로 넘기고 메시지를 먼저 읽게 함. 서브에이전트 화면에서 `Ctrl+Enter`도 동일(v2.1.286).
- **(v2.1.208 / v2.1.319)** 완료된 백그라운드 에이전트는 `/tasks`에 남고, "Earlier in this session" 행에서 재시작 후에도 다시 열어 메시지 가능.
- **(v2.1.211)** Claude가 아직 실행 중인 에이전트의 결과를 지어내지 않고 실제 완료를 기다리도록 개선.
- **(v2.1.323)** 진행 요약 끄기: `CLAUDE_CODE_DISABLE_AGENT_PROGRESS_SUMMARIES=1`.

**(v2.1.76)** 백그라운드 에이전트를 kill하면 부분 결과가 대화 컨텍스트에 보존됨.

**(v2.1.198)** `claude agents`에서 백그라운드 에이전트 알림 추가 — 입력이 필요하거나 완료되면 `Notification` 훅 발생(`agent_needs_input` / `agent_completed`). `claude agents`에서 띄운 백그라운드 에이전트는 worktree에서 코드 작업을 마치면 멈춰 묻지 않고 **commit·push 후 draft PR을 자동 생성**.

### Foreground

`run_in_background: false`로 명시하면 서브에이전트 완료까지 메인 대화가 대기. 결과 즉시 확인.

### 병렬 실행

여러 서브에이전트를 동시에 실행 가능. Agent 도구를 한 메시지에서 여러 번 호출. 동시 실행 상한은 기본 20개(§11).

### 포크 서브에이전트 (v2.1.212 `/subtask`, v2.1.232 기본 활성화)

포크 = **지금까지의 대화 전체를 물려받는** 서브에이전트. 다른 서브에이전트에게 배경 설명이 너무 많이 필요할 때, 같은 출발점에서 여러 방법을 병렬로 시도할 때 사용.

| | 포크 | 일반 서브에이전트 |
|--|------|------------------|
| 컨텍스트 | 대화 전체 이력 | 넘겨준 프롬프트만으로 새로 시작 |
| 시스템 프롬프트·도구 | 부모와 동일 | 에이전트 정의 파일 기준 |
| 모델 | 부모와 동일 | 모델 결정 순서(§7) |
| 프롬프트 캐시 | 부모와 공유 → 같은 맥락 작업이면 더 저렴 | 별도 |

```text
/subtask draft unit tests for the parser changes so far
```

- 직접 시작: `/subtask <작업>` (포크 모드와 무관하게 사용 가능). Claude도 Agent 도구의 `subagent_type: "fork"`로 스스로 포크 가능.
- **(v2.1.212 동작 변경)** `/fork`는 이제 대화를 **별도 백그라운드 세션**으로 복사(`claude agents`에 행 생성, v2.1.221부터 자체 worktree). 세션 안 포크는 `/subtask`. (agent view를 끈 경우 `/fork`가 포크 서브에이전트 시작)
- 프롬프트 아래 패널: `↑/↓` 이동, `Enter` 트랜스크립트 열기·후속 메시지, `x` 중지/닫기, `Esc` 복귀.
- `isolation: "worktree"`로 포크의 편집을 별도 worktree에 쓰기 가능. 포크는 다시 포크 불가.
- 끄기: 포크만 막기 `permissions.deny`에 `"Agent(fork)"` / 포크 모드 전체 끄기 `CLAUDE_CODE_FORK_SUBAGENT=0`.
- **(v2.1.302)** `claude -p`, Agent SDK, 데스크톱, VS Code에서도 기본 활성화.

---

## 7. 모델 선택 가이드

| 모델 | 용도 | 속도 | 비용 |
|------|------|------|------|
| `haiku` | 파일 검색, 간단한 포맷팅 | 매우 빠름 | 저렴 |
| `sonnet` | 대부분의 작업 | 빠름 | 보통 |
| `opus` | 복잡한 아키텍처, 정교한 분석 | 느림 | 비쌈 |
| `fable` | 공식 문서에 별칭으로 등재 | - | - |
| `'inherit'` | 메인 대화 모델 상속 | 가변 | 가변 |

### 모델 결정 순서 (공식 문서, 위가 우선)

1. 호출별 Agent 도구 `model` 파라미터 (별칭만)
2. 에이전트 정의의 `model:` (`inherit` 포함)
3. `CLAUDE_CODE_SUBAGENT_MODEL` 환경변수 — **(v2.1.251 동작 변경)** 전체 강제가 아니라 "기본값"으로 바뀜
4. 메인 대화 모델(중첩이면 스폰한 서브에이전트의 모델)

- 모든 서브에이전트에 한 모델 강제: `CLAUDE_CODE_SUBAGENT_MODEL` + `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` **(v2.1.257)**. 포크와 `model: inherit` 스킬은 여전히 부모 모델.
- **(v2.1.296)** `CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL`: 워크플로우 에이전트만 한 모델로.
- **(v2.1.234)** `/config`의 "Default teammate model" 제거 → 팀원은 스폰 시 지정 없으면 리더 모델.

### Effort(추론 노력) 결정

- **(v2.1.292)** Agent 도구에 `effort` 파라미터 추가 — "낮은 노력으로 돌려줘"처럼 요청 가능.
- **(v2.1.316)** `CLAUDE_CODE_SUBAGENT_EFFORT`: 아무것도 지정 안 됐을 때 서브에이전트 기본 effort.
- **(v2.1.317)** 메인과 다른 모델을 쓰는 서브에이전트·팀원은 세션 effort가 아니라 그 모델의 저장된 effort(또는 기본값) 사용.
- **(v2.1.243)** `/tasks`·에이전트 상세에 각 서브에이전트의 모델·effort 표시.

---

## 8. Skills 연동

### 서브에이전트에 Skills 프리로드

```yaml
skills: seo-optimizer, ghost-validator
```

- 지정된 Skills 전체 콘텐츠가 시작 시 주입
- 서브에이전트는 부모 스킬을 **상속받지 않음** (명시적 지정 필수)
- 내장 에이전트 (Explore, Plan, general-purpose)는 Skills 접근 불가
- **(v2.1.295)** 프리로드는 최대 32개. Skill 도구가 있으면 나머지는 실행 중 호출 가능.
- **(v2.1.218)** `context: fork` 스킬은 기본 백그라운드 실행(스킬별 `background: false`로 해제).

> 스킬 vs 서브에이전트 구분은 §1 "언제 쓰나" 표 참조. 스킬 = 메인 컨텍스트에서 도는 재사용 워크플로, 서브에이전트 = 격리 컨텍스트 + 요약 반환.

---

## 9. CLI 사용법

### JSON 플래그로 정의

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  }
}'
```

- **(v2.1.281)** `-p`와 함께 쓸 때 인라인 JSON 대신 **JSON 파일 경로** 지정 가능, 빈 `prompt` 허용.
- **(v2.1.261)** `--append-subagent-system-prompt-file`: 큰 서브에이전트 시스템 프롬프트를 파일에서 읽기.
- **(v2.1.211)** `--forward-subagent-text` / `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT`: stream-json 출력에 서브에이전트 텍스트·thinking 포함(v2.1.219부터 2단계 이상 중첩도).

### 에이전트 목록 확인 (v2.1.50)

```bash
claude agents  # 인터랙티브 세션 없이 에이전트 목록
```

**(v2.1.98)** `/agents` 커맨드가 탭 레이아웃으로 변경: **Running** 탭(실행 중인 에이전트)과 **Library** 탭(사용 가능한 에이전트)으로 분리.

**(v2.1.97)** `/agents`에 `N running` 인디케이터가 표시되어 현재 실행 중인 서브에이전트 수를 즉시 확인 가능.

> **⚠️ `/agents` 위저드 제거**: 에이전트를 만들거나 관리하는 대화형 위저드가 사라짐. 공식 문서 기준 **v2.1.197까지** 위저드(Running/Library 탭)였고, 이후 `/agents`는 "Claude에게 요청하거나 `.claude/agents/`·`~/.claude/agents/`를 직접 편집하라"는 **안내만 출력**. (이전 문서는 v2.1.202로 기재. 실행 중 에이전트를 보는 `claude agents` 뷰와 `/tasks`는 그대로.) **(v2.1.281)** 명령 메뉴·`/help`의 "(removed)" 항목도 정리.
>
> 교육용 한 줄: "에이전트는 메뉴로 만들지 않는다. Claude에게 '○○ 하는 에이전트 만들어줘'라고 말한다."

### 세션 간 메시지 (v2.1.224)

`SendMessage`가 서브에이전트뿐 아니라 **다른 Claude Code 세션**(같은 머신·다른 머신의 Remote Control 세션)에도 메시지를 보낼 수 있음. `ListAgents`(`/list-agents`)로 대상 확인, 프롬프트에서 `@세션이름`으로 지정(v2.1.232). Windows는 v2.1.239부터. 서브에이전트가 다른 세션에 보낸 메시지의 답장은 부모 세션으로 옴(v2.1.248).

### Named Subagents in @ Mention (v2.1.88)

**(v2.1.88)** 커스텀 에이전트가 `@` mention typeahead 자동완성에 표시됨. `@agent-name`으로 직접 참조 가능.

### --bare 플래그 (v2.1.81)

스크립트용 `-p` 호출에서 hooks, LSP, plugin sync, skill walks를 건너뛰는 경량 모드:

```bash
claude --bare -p "prompt"  # ANTHROPIC_API_KEY 또는 apiKeyHelper 필요
```

- OAuth/keychain 인증 비활성화
- Auto-memory 완전 비활성화
- ~14% 빠른 API 요청 (v2.1.83)

### Worktree 모드 실행 (v2.1.49)

```bash
claude --worktree  # 또는 -w
```

### EnterWorktree `path` 파라미터 (v2.1.105)

`EnterWorktree` 도구에 `path` 파라미터 추가. 현재 저장소의 **기존** worktree로 전환할 때 사용. 새로 생성하지 않고 기존 worktree를 재사용.

### Stale Worktree 자동 정리 (v2.1.105)

Squash-merge된 PR의 worktree가 무기한 남아있던 동작이 수정됨. PR이 squash merge되면 해당 에이전트 worktree도 정리 대상으로 포함.

### 특정 에이전트 비활성화

```json
{
  "permissions": {
    "deny": ["Agent(Explore)", "Agent(my-custom-agent)", "Agent(fork)"]
  }
}
```

(이전 문서 표기 `Task(...)`는 구 도구 이름.)

**(v2.1.178)** 권한 규칙에 `Tool(param:value)` 문법이 추가되어 도구의 입력 파라미터로 매칭 가능(`*` 와일드카드 지원). 예: `Agent(model:opus)`로 Opus 서브에이전트 차단.

### Fallback 모델 (v2.1.166)

`fallbackModel` 설정으로 기본 모델이 과부하/이용 불가일 때 순서대로 시도할 **대체 모델을 최대 3개** 지정 가능. `--fallback-model`이 인터랙티브 세션에도 적용됨. 컴팩션도 과부하·모델 이용불가 시 이 fallback 체인을 따름(v2.1.178).

---

## 9-1. Agent Teams (v2.1.178)

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 설정 시 모든 세션이 **하나의 암묵적 팀**을 갖는다.

- **(v2.1.178)** `TeamCreate`·`TeamDelete` 도구 **제거**. 별도 셋업 없이 **Agent 도구의 `name` 파라미터로 팀원을 직접 스폰**. (`team_name` 파라미터는 여전히 받되 무시됨.)
- **(v2.1.207)** API 에러로 죽은 팀원은 리드에게 "failed"로 보고하고, 멈춘 팀원에게 메시지를 보내면 깨어나 즉시 재시도.
- 팀원 간·세션 간 연속성은 `SendMessage({to: agentId})`로 처리 (아래 §10 참조).
- **(v2.1.234)** 팀원 기본 모델 = 리더 모델("Default teammate model" 설정 제거).
- **(v2.1.290)** in-process 팀원의 `agent_id`는 에이전트 ID(`name@team` 주소는 `teammate_id`). TeammateIdle 훅은 팀원의 서브에이전트·포크에서는 발생 안 함.
- **(v2.1.323)** 분할 창 팀원은 요청이 자기 리더에게서 왔는지 확인. 리더보다 오래 살아남은 팀원의 요청은 거부, `/clear`·`/resume` 후엔 계획 승인 재전송 필요.

---

## 9-2. 동적 워크플로우 (v2.1.154)

**(v2.1.154)** Claude에게 워크플로우 생성을 요청하면, 백그라운드에서 **수십~수백 개 에이전트에 작업을 오케스트레이션**한다. 대규모·복잡 작업을 한 번에 처리하는 용도.

- `/workflows`로 실행 목록 확인
- **(v2.1.202)** `/config`에 "Dynamic workflow size" 설정(small/medium/large 에이전트 수) — 강제 상한이 아닌 권고 가이드라인
- **(v2.1.178)** 워크플로우 트리거는 "run a workflow" / "workflow:" 같은 명시 표현에만 반응(단순히 단어 언급으로는 트리거 안 됨)
- `workflow.run_id`·`workflow.name` OTel 속성으로 실행 활동 재구성 가능 (v2.1.202)
- **(v2.1.265)** `/workflows` 에이전트 상세에 도구 호출 상태(실행 중·실패·완료)와 태스크 목록 표시
- **(v2.1.296)** `CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL`로 워크플로우 에이전트 모델 일괄 지정

---

## 10. 컨텍스트 관리

### Resume (재개)

서브에이전트는 전체 히스토리를 유지하며 재개 가능.

**(v2.1.77 Breaking)**: Agent tool의 `resume` 파라미터 제거됨. 대신 `SendMessage({to: agentId})`로 이전 에이전트를 계속. `SendMessage`는 중지된 에이전트를 백그라운드에서 자동 재개.

- **(v2.1.299)** 재시작 후에도 마지막 컴팩션 이후 붙인 이름으로 메시지 가능. 안 되면 에이전트 ID로 보내면 이름이 다시 작동. ID는 `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.meta.json`에서 확인.
- **(v2.1.259)** 중첩 백그라운드 서브에이전트의 결과는 부모 서브에이전트 트랜스크립트에 저장되어 재개 시 유지.

### Auto-Compaction

컨텍스트 윈도우 임계치 도달 시 자동 요약. 중요 정보 보존. 서브에이전트도 자기 컨텍스트 기준으로 자동 압축하며 `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`도 적용. 에이전트별로 더 일찍 압축하려면 frontmatter `autoCompactWindow`(§4).

### Transcript 저장

```
~/.claude/projects/[project-hash]/sessions/[session-id].jsonl
```

`cleanupPeriodDays` 후 자동 정리 (기본 30일).

---

## 11. 제한사항

1. **중첩 기본 3단계** — ⚠️ 이전 문서의 "최대 5단계"에서 **변경됨**. 경과: (v2.1.172) 최대 5단계 허용 → **(v2.1.217)** 기본 중첩 금지로 전환 → **(v2.1.219)** 기본 3단계(메인 대화 아래 세 층)로 재허용. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`로 층수 지정, `1`이면 중첩 끔. 한도에 닿으면 Agent 도구가 빠짐(포크는 도구는 보이나 에러 반환).
   - **동시 실행 상한 20개 (v2.1.217)**: 넘으면 `Concurrent subagent limit reached`. `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`로 조정. 세션 누적 스폰 수 상한(v2.1.212 도입, 200개)은 **v2.1.224에서 제거**.
2. **Agent tool `model` 파라미터 복원** (v2.1.72): 호출별 모델 오버라이드 가능
3. **스킬 상속 불가**: 부모 대화 스킬을 상속받지 않음. `skills` 필드로 명시 필요.
4. **트랜스크립트 격리**: 각 호출은 새로운 컨텍스트 (재개하지 않는 한)
5. **`TaskOutput` 도구 Deprecated** (v2.1.83) → **v2.1.277 완전 제거**: `Read`로 백그라운드 태스크 출력 파일을 읽음. `taskOutputMaxChars` 설정·`TASK_MAX_OUTPUT_LENGTH`도 효과 없음
6. **WorktreeCreate HTTP hook** (v2.1.84): `type: "http"` 지원. `hookSpecificOutput.worktreePath`로 생성된 worktree 경로 반환
7. **(v2.1.92 수정)** tmux 윈도우가 삭제/재번호화된 후 서브에이전트 스폰이 영구 실패하던 버그 수정 ("Could not determine pane count")
8. **(v2.1.90 수정)** `--resume` 시 deferred tools, MCP 서버, 커스텀 에이전트가 있는 사용자에게 프롬프트 캐시 전체 미스 발생하던 회귀 버그 수정 (v2.1.69 이후)
9. **(v2.1.98 수정)** 서브에이전트가 동적 주입된 MCP 서버의 도구를 상속받지 못하던 버그 수정
10. **(v2.1.98 수정)** 격리된 worktree의 서브에이전트가 자체 worktree에 대한 Read/Edit 접근이 거부되던 버그 수정
11. **(v2.1.101 수정)** `--resume`/`--continue` 시 대형 세션에서 컨텍스트 유실되던 버그 수정
12. **(v2.1.101 수정)** `--resume` 체인 복구 시 관련 없는 서브에이전트 대화로 잘못 연결되던 버그 수정
13. **(v2.1.323 제거)** `subagentStatusLine` 설정 제거 — 서브에이전트 행은 항상 기본 모양(설정 파일에 키가 남아 있어도 로드는 됨)
14. **(v2.1.323 Deprecated)** 플러그인의 `agent` 설정 — 아직 적용되지만 시작 시·`claude plugin list`·`validate`에서 경고
15. **(v2.1.277 / v2.1.271)** 서브에이전트 결과는 "서브에이전트 출력" 헤더 아래 들여쓰기로 전달되어 세션 지시로 오인되지 않음. auto mode에선 전용 hand-back 호출로 보고하고 분류기가 검토(v2.1.285부터 보고 즉시 종료)
16. **(v2.1.319)** 안전장치가 서브에이전트를 멈추면 Claude는 직접 대신 하지 않고 더 좁은 프롬프트로 재시도하거나 사용자에게 알림
17. **(v2.1.325)** 출력 토큰 한도에 잘린 서브에이전트는 끝부분만 돌려주지 않고 전체 답을 더 짧게 다시 요청받음

---

## 12. Best Practice

### DO

- 단일 책임 원칙: 하나의 명확한 역할
- 상세한 프롬프트: 예제와 제약사항 포함
- 최소 권한: `tools` 또는 `disallowedTools`로 제한
- Description에 트리거 키워드 포함 ("use proactively", "when user mentions X"). 다른 에이전트와 겹치지 않게 하나를 콕 집도록 작성
- 맥락이 많이 필요한 곁가지 작업은 새 서브에이전트보다 포크(`/subtask`) 고려
- 반복 다듬기·지연 민감 작업은 서브에이전트에 넘기지 말고 메인 대화에서
- Claude와 협업하여 초안 생성 후 반복 개선
- 프로젝트 에이전트는 Git 커밋

### DON'T

- 모호한 description ("Help with code")
- 불필요하게 `opus` 모델 사용
- 모든 도구 허용 (필요 없는 경우)
- 민감한 작업에 `bypassPermissions` 사용

---

## Sources

- [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## Related

- [[skills-guide]] - Skills 시스템 가이드
- [[claude-md-guide]] - CLAUDE.md 가이드

---

## Update History

- **2026-11-16**: v2.1.208~2.1.325 변경사항 반영 + 공식 문서 대조
  - "언제 쓰나: 서브에이전트 vs 메인 대화 vs 스킬(+`/btw`)" 표 신설 (§1)
  - **포크 서브에이전트**: `/fork`→백그라운드 세션 복사, 세션 내 포크는 `/subtask` (v2.1.212), 기본 활성화 (v2.1.232 터미널, v2.1.302 전 환경), 포크 모드에선 Claude가 서브에이전트를 기다리지 못함
  - **중첩 한도 변경**: 기본 중첩 금지(v2.1.217) → 기본 3단계(v2.1.219). 이전 문서의 "최대 5단계" 정정. 동시 실행 20개 상한(v2.1.217), 세션 200개 상한 도입(v2.1.212) 후 제거(v2.1.224)
  - **모델 결정 순서**: `CLAUDE_CODE_SUBAGENT_MODEL`이 기본값으로 바뀜(v2.1.251), `_FORCE`(v2.1.257), `CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL`(v2.1.296). frontmatter `model` 기본값 "sonnet" 기재 정정
  - **Effort**: Agent 도구 `effort` 파라미터(v2.1.292), `CLAUDE_CODE_SUBAGENT_EFFORT`(v2.1.316), 다른 모델은 그 모델 effort(v2.1.317)
  - **frontmatter 신규**: `omitClaudeMd`(v2.1.271), `autoCompactWindow`(v2.1.296), `experimental.cacheTtl`(v2.1.248), `color`. `name`·`description` 필수, `skills` 최대 32개(v2.1.295), `permissionMode` `auto`·`manual` 및 상속 규칙
  - **폐지/제거**: Agent `mode` 파라미터 deprecated(v2.1.212), `TaskOutput` 제거(v2.1.277), `subagentStatusLine` 제거(v2.1.323), 플러그인 `agent` 설정 deprecated(v2.1.323), "Default teammate model" 제거(v2.1.234)
  - **훅**: `DirectoryAdded`(v2.1.219), `PreModelSwitch`/`PostModelSwitch`(v2.1.251), `onFailure: "block"`(v2.1.295), `if` `dir/**` 매칭 변경(v2.1.214), SessionStart source `"fork"`(v2.1.214), UserPromptSubmit 스킬 확장 전 실행(v2.1.299), `updatedInput` 검증(v2.1.300), prompt/agent 훅 동시 실행 상한(v2.1.302/312)
  - 세션 간 `SendMessage`/`ListAgents`(v2.1.224), `maxTurns` 부분 결과(v2.1.246), `--agents` 파일 경로(v2.1.281), `denyInsteadOfPrompting`(v2.1.319), worktree 제약(v2.1.323/325)
  - `/agents` 위저드 종료 시점을 공식 문서 기준 "v2.1.197까지"로 정정, 권한 규칙 예시 `Task(...)`→`Agent(...)`

- **2026-07-13**: v2.1.120~2.1.207 변경사항 반영
  - **서브에이전트 기본 백그라운드 실행** (v2.1.198): Claude가 서브에이전트 실행 중 다른 작업 지속, 완료 시 알림. `agent_needs_input`/`agent_completed` Notification 훅 추가. `claude agents`발 백그라운드 에이전트는 worktree 코드 작업 후 commit·push·draft PR 자동 생성
  - **중첩 제한 반전 — 서브에이전트가 서브에이전트 스폰 가능(최대 5단계)** (v2.1.172), foreground도 동일 5단계 상한 (v2.1.181)
  - **`/agents` 위저드 제거** (v2.1.202): 말로 요청하거나 `.claude/agents/` 직접 편집
  - **Agent Teams 재편** (v2.1.178): `TeamCreate`/`TeamDelete` 제거, 암묵적 팀 + Agent 도구 `name` 파라미터로 팀원 스폰. 죽은/멈춘 팀원 복구 개선 (v2.1.207)
  - **동적 워크플로우 도입** (v2.1.154): 수십~수백 에이전트 백그라운드 오케스트레이션, `/workflows`. 크기 설정·OTel 속성 추가 (v2.1.202)
  - `fallbackModel` 설정 (v2.1.166): 대체 모델 최대 3개, 인터랙티브·컴팩션에도 적용 (v2.1.178)
  - 권한 규칙 `Tool(param:value)` 문법 (v2.1.178): 예 `Agent(model:opus)`로 Opus 서브에이전트 차단
  - Explore 에이전트가 haiku 고정에서 **메인 모델 상속(opus 상한)**으로 변경 (v2.1.198)
  - 서브에이전트·컴팩션이 세션의 extended thinking 설정 상속 (v2.1.198)
  - Stop/SubagentStop 훅 `hookSpecificOutput` 반환 지원 (v2.1.181)
  - Sonnet 5 세션이 mid-conversation system role 미사용 (v2.1.201), `availableModels` 제한이 서브에이전트 모델 오버라이드/디스패치 피커에 적용 (v2.1.172)
- **2026-04-19**: v2.1.110~2.1.114 변경사항 반영
  - **서브에이전트 stall timeout 도입 (v2.1.114)**: 서브에이전트가 mid-stream에서 멈추면 10분 후 명확한 에러로 실패 (기존: 무한 hang)
  - 사용자가 실행 중 서브에이전트를 보면서 입력한 메시지가 트랜스크립트에서 사라지고 부모 AI에게 misattributed 되던 버그 수정 (v2.1.114)
  - Remote Control 세션이 서브에이전트 트랜스크립트를 스트리밍하지 못하던 버그 수정 (v2.1.114)
  - Remote Control 세션이 Claude Code 종료 시 archive 되지 않던 버그 수정 (v2.1.114)
  - `/ultrareview` 클라우드 기반 코드 리뷰 추가 (v2.1.111) — 병렬 multi-agent 분석/비평. `/ultrareview <PR#>`로 GitHub PR 직접 리뷰
  - `CLAUDE_CODE_EXTRA_BODY`의 `output_config.effort`가 effort 미지원 모델/Vertex AI 서브에이전트 호출 시 400 에러 내던 버그 수정 (v2.1.114)
- **2026-04-15**: v2.1.105~2.1.109 변경사항 반영
  - `EnterWorktree`에 `path` 파라미터 추가 - 기존 worktree 전환 (v2.1.105)
  - Squash-merge된 PR의 stale 에이전트 worktree 자동 정리 (v2.1.105)
  - Agent tool auto mode에서 safety classifier transcript 컨텍스트 초과 시 권한 요청 버그 수정 (v2.1.108)
  - `--resume`이 자기 참조 메시지 포함 트랜스크립트 시 세션 잘림 수정 (v2.1.108)
- **2026-04-13**: v2.1.93~2.1.101 변경사항 반영
  - Monitor 도구 추가 (v2.1.98) - 백그라운드 스크립트 이벤트 스트리밍
  - `/agents` 탭 레이아웃으로 변경: Running + Library (v2.1.98)
  - `/agents`에 `N running` 인디케이터 추가 (v2.1.97)
  - 서브에이전트 동적 MCP 도구 상속 수정 (v2.1.98)
  - 격리된 worktree 서브에이전트 Read/Edit 접근 수정 (v2.1.98)
  - `--resume`/`--continue` 대형 세션 컨텍스트 유실 수정 (v2.1.101)
  - `--resume` 체인 복구 시 잘못된 서브에이전트 연결 수정 (v2.1.101)
  - `/team-onboarding` 커맨드 추가 (v2.1.101) - 팀원 온보딩 가이드 생성
- **2026-04-04**: v2.1.90~2.1.92 변경사항 반영
  - tmux 윈도우 kill/재번호화 후 서브에이전트 스폰 실패 수정 (v2.1.92)
  - `--resume` 프롬프트 캐시 미스 회귀 수정 (v2.1.90)
  - prompt-type Stop 훅 소형 모델 `ok:false` 시 오류 수정 (v2.1.92)
  - MCP tool result persistence override `_meta["anthropic/maxResultSizeChars"]` 최대 500K (v2.1.91)
- **2026-04-01**: v2.1.89 변경사항 반영
  - `"defer"` PreToolUse permission decision 추가 (headless 세션 일시중지/재개)
  - hooks `if` 조건 compound commands 및 env-var 접두사 매칭 수정
- **2026-03-31**: v2.1.79~2.1.88 변경사항 반영
  - Named subagents in `@` mention typeahead (v2.1.88)
  - `initialPrompt` frontmatter (v2.1.83)
  - `--bare` 경량 모드 (v2.1.81)
  - Hook 이벤트 4종 추가: PermissionDenied, TaskCreated, CwdChanged, FileChanged
  - 조건부 훅 `if` 필드 (v2.1.85)
  - PreToolUse `AskUserQuestion` 훅 응답 (v2.1.85)
  - `TaskOutput` deprecated, `Read` 사용 (v2.1.83)
  - WorktreeCreate HTTP hook (v2.1.84)
- **2026-03-18**: v2.1.51~2.1.78 변경사항 반영
  - `effort` frontmatter 필드 추가 (v2.1.78, plugin-shipped agents)
  - Agent tool `resume` 파라미터 제거 → `SendMessage` 사용 (v2.1.77 Breaking)
  - Agent tool `model` 파라미터 복원 (v2.1.72)
  - Hook 이벤트 4종 추가: StopFailure, PostCompact, InstructionsLoaded, Elicitation
  - HTTP Hooks 지원 (v2.1.63)
  - `agent_id`, `agent_type` 훅 이벤트 필드 (v2.1.69)
  - 백그라운드 에이전트 kill 시 부분 결과 보존 (v2.1.76)
  - 프로젝트 설정/auto memory가 git worktree 간 공유 (v2.1.63)
- **2026-02-22**: 전면 갱신 (source of truth 목적)
  - 신규 YAML 필드 5개: memory, background, isolation, mcpServers, maxTurns
  - Task(agent_type) 스폰 제한 문법
  - 신규 Hook 이벤트 4개: TeammateIdle, TaskCompleted, WorktreeCreate, WorktreeRemove
  - Stop/SubagentStop last_assistant_message 필드
  - claude agents CLI, --worktree 플래그
  - 빌트인 에이전트 추가 (statusline-setup, Claude Code Guide)
  - 불필요한 예시 축소, 핵심 레퍼런스에 집중
- **2026-01-16**: 초기 작성
