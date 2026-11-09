# Claude Code 실무 교육 — 실습 워크스페이스

2일 과정(Claude Code 실무 교육)에서 쓰는 **실습용 작업 폴더**입니다.
내 PC로 받아서 그대로 내 작업 공간으로 쓰면 됩니다. 교육이 끝난 뒤에도 계속 쓰셔도 됩니다.

> 아직 설치 전이라면 교육 전에 받은 **「사전 준비 안내」 PDF**를 먼저 따라 하세요.

## 받기 (교육 전에 1번)

터미널(Windows는 PowerShell)에서:

```
cd ~/Documents
git clone https://github.com/jay-park723/claude-workspace.git
cd claude-workspace
claude
```

대화 화면이 뜨면 아래를 입력합니다. 이름·역할·업무를 물어보고 `CLAUDE.md`를 채워 줍니다.

```
워크스페이스 세팅해줘
```

## 들어 있는 것

| 위치 | 내용 |
|------|------|
| `CLAUDE.md` | **가장 중요한 파일.** Claude가 매번 가장 먼저 읽는 나의 설명서 |
| `.claude/skills/` | 기본 스킬 17종 (문서 변환·기록·기획·지식 축적·Notion 연동) |
| `10-projects/11-ocr-lecture-samples/` | 실물 영수증 사진 5장 (OCR 실습용) |
| `10-projects/12-sales-lecture-samples/` | 가상 매출 데이터 1년치 엑셀 (분석·대시보드 실습용) |
| `00-system/02-forms/` | 기안지 Word 양식 (양식 채우기 실습용) |
| `00-system/01-templates/` | 데일리 노트·회의록·프로젝트 템플릿 |
| `30-knowledge/00-wiki/` | 지식을 쌓는 위키 (빈 상태로 시작) |

## 폴더 구조 — 숫자로 정리된 서랍 (Johnny Decimal)

```
00-inbox/      임시 보관 (아직 분류 안 한 것)
00-system/     템플릿·양식·설정
10-projects/   시작과 끝이 있는 일
20-operations/ 끝나지 않고 계속 돌리는 일
30-knowledge/  쌓아두는 지식
40-personal/   개인 기록 (daily·todo 등)
50-resources/  참고자료·첨부파일
90-archive/    끝나서 보관하는 것
```

## 주의

- **실제 회사 데이터(원가·고객사·단가·계약·개인정보)는 이 폴더에 넣어 실습하지 마세요.** 실습은 들어 있는 샘플이나 가짜 데이터로 합니다.
- 비밀번호·토큰·API 키는 파일에 적지 않습니다. (`.gitignore`에 기본 차단 규칙이 들어 있습니다.)
- 스킬은 고쳐 쓰라고 있는 것입니다. "이 스킬 이렇게 고쳐줘"라고 말하면 됩니다.

## 출처

- 영수증 이미지: CORD (Consolidated Receipt Dataset), NAVER Clova AI — CC BY 4.0 · https://github.com/clovaai/cord
- 폴더 구조·기본 스킬: Do Better Workspace (AX 교육, 이림 강사 제공)를 교육용으로 정리
- 매출 데이터: 교육용으로 만든 가상 데이터 (실제 거래 아님)
