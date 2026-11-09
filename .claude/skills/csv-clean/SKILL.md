---
name: csv-clean
description: CSV 데이터 품질 정리. 소계행 제거, 숫자 정리, 날짜 정규화, unpivot 등. "데이터 정리", "CSV 정리", "소계 제거", "숫자 정리", "날짜 통일", "unpivot", "csv clean", "데이터 클리닝" 등을 언급하면 자동 실행.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
---

# CSV Data Quality Cleaner

CSV 파일의 데이터 품질 문제를 정리. Excel 없이도 독립 사용 가능 (은행 CSV, API 내보내기 등).

## Script Location

`.claude/skills/csv-clean/scripts/csv-clean.py` (워크스페이스 루트 기준)

## Prerequisites

```bash
pip install -r .claude/skills/csv-clean/scripts/requirements.txt
```

또는:
```bash
pip install "pandas>=2.0.0"
```

설치 여부를 먼저 확인하고, 없으면 설치 안내.

## Workflow

### Step 1: CSV 파일 경로 확인

사용자로부터 CSV 파일 경로 확인.
경로가 명확하지 않으면 Glob으로 `.csv` 파일 스캔.

### Step 2: 데이터 품질 분석

```bash
python .claude/skills/csv-clean/scripts/csv-clean.py <파일경로> --info
```

출력:
- 소계/합계 행 감지 (SUBTOTAL_ROWS)
- 텍스트 형식 숫자 감지 (TEXT_NUMBERS)
- 날짜 형식 불일치 감지 (DATE_FORMATS)
- 크로스탭 구조 감지 (CROSSTAB)

### Step 3: 옵션 제안

| 감지 항목 | 제안 옵션 |
|----------|----------|
| SUBTOTAL_ROWS | `--remove-subtotals` |
| TEXT_NUMBERS | `--clean-numbers` 또는 `--clean-numbers-cols 열1,열2` |
| DATE_FORMATS | `--normalize-dates --date-cols 열명` |
| KR_WEEK_DATES | `--normalize-kr-weeks --kr-week-cols 열명` (예: `3월 2주차` → `2026-03-W2`) |
| CROSSTAB | `--unpivot ID열1,ID열2` |

### Step 4: 정리 실행

```bash
# 소계 행 제거
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --remove-subtotals

# 숫자 정리 (자동 감지)
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --clean-numbers

# 특정 열만 숫자 정리
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --clean-numbers-cols 금액,단가

# 날짜 정규화
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --normalize-dates --date-cols 날짜

# 한국어 주차/부분 날짜 데이터화 (표시 원본 유지 + '(데이터)' 코드 열 추가)
#   "3월 2주차"→2026-03-W2, "3/20"→2026-03-20, "2월"→2026-02, "7월 2~4주차"→2026-07-W2~4
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --normalize-kr-weeks --kr-week-cols 제품기획,인증접수,출시 --year 2026

# 크로스탭 → tidy data
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --unpivot 지역,제품

# 복합 옵션
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --remove-subtotals --clean-numbers --normalize-dates

# 원본 덮어쓰기
python .claude/skills/csv-clean/scripts/csv-clean.py <파일> --inplace
```

### Step 5: 결과 확인

1. 변경 사항 요약 (행 수 변화, 정리된 값 수)
2. **정합성 검증(Verification) 리포트 확인** — 변환 실패·잔여 오염값이 `⚠`로 표시됨. 자동 처리 못 한 값은 사람이 확인(자동화 80% + 사람 20% 원칙). `--no-verify`로 생략 가능
3. Read 도구로 첫 5행 미리보기
4. 원본과 비교하여 의도치 않은 변경 없는지 확인

## Pipeline Usage

`excel-to-csv`와 연결:

```bash
python .claude/skills/excel-to-csv/scripts/excel-to-csv.py file.xlsx --all --flatten-headers
python .claude/skills/csv-clean/scripts/csv-clean.py file.csv --remove-subtotals --clean-numbers
```

## CLI Options

| 옵션 | 설명 |
|------|------|
| `--info` | 품질 분석만 (변환 안 함) |
| `--remove-subtotals` | 소계/합계 행 제거 |
| `--clean-numbers` | 숫자 정리 (자동 감지) |
| `--clean-numbers-cols COLS` | 특정 열만 숫자 정리 |
| `--normalize-dates` | 날짜 형식 통일 |
| `--date-format FMT` | 날짜 출력 형식 (기본: %Y-%m-%d) |
| `--date-cols COLS` | 날짜 대상 열 |
| `--normalize-kr-weeks` | 한국어 주차/부분 날짜 데이터화. 원본(표시) 유지 + `{열}(데이터)` 코드 열 추가 (`3월 2주차`→`2026-03-W2`) |
| `--kr-week-cols COLS` | 주차 데이터화 대상 열 (생략 시 자동 감지) |
| `--year YYYY` | 연도 없는 날짜에 부여할 연도 (기본: 당해연도) |
| `--no-verify` | 정합성 검증 리포트 생략 |
| `--unpivot ID_COLS` | 크로스탭 unpivot |
| `--value-name NAME` | unpivot 값 열 이름 |
| `--variable-name NAME` | unpivot 변수 열 이름 |
| `--normalize-text COL=MAPFILE` | 텍스트 표현 통일 (CSV 매핑 파일) |
| `--output PATH` | 출력 경로 |
| `--inplace` | 원본 덮어쓰기 |

## Output Naming

| 조건 | 파일명 |
|------|--------|
| 기본 | `{원본}_cleaned.csv` |
| `--output` 지정 | 지정된 경로 |
| `--inplace` | 원본 덮어쓰기 |

## Error Handling

- `pandas` 미설치 시: 설치 명령 안내
- 파일 못 찾음: 경로 확인
- 열 이름 오류: 사용 가능한 열 목록 표시
