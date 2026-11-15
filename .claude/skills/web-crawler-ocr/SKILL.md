---
name: web-crawler-ocr
description: 웹페이지 크롤링 + 이미지 OCR 자동 분석. "이 URL 분석해줘", "크롤링해줘", "웹사이트 분석", "사이트 크롤링", "경쟁사 분석", "페이지 추출", "analyze this URL", "crawl website", "competitor analysis", "extract webpage" 등을 언급하거나 https:// 또는 http:// URL을 제공하면 자동 실행. Claude의 5MB 이미지 제한을 Gemini OCR(20MB)로 우회.
context: fork
allowed-tools:
  - Bash
  - Read
  - Write
---

# Web Crawler + Gemini OCR Skill v3.1.0

Extract complete web page content (text + images) and save as markdown file.
Scrapling + Playwright + trafilatura + Gemini OCR. Fully local crawling.

## ⚠️ OCR 결과 검증 원칙 (필수)

OCR(비전 AI)은 **흐릿하거나 작은 부분을 만나면 그럴듯하게 지어냅니다(할루시네이션).** 특히 로고·브랜드명·숫자·금액이 위험합니다. 실제 사건: 흐린 ~20px 로고를 Gemini가 "KOHLER 변기"라고 문장까지 지어냈으나, 원본 확대 시 판독 불가한 얼룩이었음.

따라서 이 스킬은 다음을 지킵니다.
- **OCR 프롬프트가 불확실한 것을 지어내지 않도록** 설정됨: 확실치 않으면 `[판독 불가]` / 로고는 `[로고 있으나 판독 불가 — 사람 확인 필요]` / 숫자는 `[숫자 판독 불가]`, 마지막에 `신뢰도: 높음/보통/낮음` 표기.
- **Claude(이 스킬을 부른 쪽)의 후처리 의무**: OCR 결과에 `[판독 불가]`·`신뢰도: 낮음`·로고/브랜드/숫자 주장이 있으면 **그대로 사실로 옮기지 말 것.** 
  1) 먼저 **원본 이미지를 직접 확인**(크롭·확대)하거나 교차 근거로 **자체 추가 검증**을 시도한다.
  2) 그래도 불확실하면 **단정하지 말고 사용자에게 확인을 요청**한다("이 로고는 판독이 안 됩니다. 원본 확인 부탁드립니다").
- **되돌릴 수 없는 판단(보고·발송·의사결정) 앞에서는 반드시 사람 검증.**

## When to Use This Skill

This skill automatically activates when the user:
- Provides a URL: "https://example.com analyze this"
- Requests web crawling: "crawl this website", "extract webpage content"
- Mentions competitor analysis: "analyze competitor site"
- Needs image OCR from web: "OCR images from this page"
- Wants to bypass 5MB limit: "large images on this site"

## What This Skill Does

1. **3-Tier Fetcher**: HTTP -> Stealth (Camoufox) -> Playwright (with scroll)
2. **trafilatura + SPA Fallback**: Content extraction + RSC/JSON-LD/meta 구조화 데이터
3. **3-Source Image Extraction**: markdown + HTML img + regex (SPA/동적 사이트 범용)
4. **Gemini OCR**: Extract text from images (up to 20MB per image)
5. **OCR Inline Insert**: OCR results automatically placed at image positions

## Instructions

### Step 1: Identify the URL
Extract URL(s) from user message:
- Look for `https://` or `http://`
- Multiple URLs? Process each one

### Step 2: Determine Output Location

Based on user context, choose appropriate path within the workspace:

**Competitor Analysis:**
```
./50-resources/competitor-analysis/
```

**Project Reference:**
```
./10-projects/{project-folder}/
```

**General Web Research:**
```
./50-resources/web-research/
```

**Filename:** Use domain + timestamp or user-specified name.

### Step 3: Execute Web Crawler Script

```bash
# 1. Install dependencies (first time only)
cd .claude/skills/web-crawler-ocr/scripts && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
pip install playwright && playwright install chromium

# 2. Run crawler
cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py "<URL>" "<output-path>"

# 3. Dynamic/SPA sites (Olive Young, Coupang, Musinsa etc.)
python3 web-crawler.py "<URL>" "<output-path>" --wait 5000 --scroll --max-images 10
```

**Important:**
- Always use full absolute paths
- Quote URLs to handle special characters
- Ensure output directory exists (create with `mkdir -p` if needed)
- Virtual env is created locally in scripts/ folder (not committed to git)
- **SPA/동적 사이트는 반드시 `--wait` + `--scroll` 사용** (lazy-load 트리거 필수)

### Step 4: Read and Analyze Results

1. Use Read tool to open generated markdown file
2. OCR results are already inline at image positions (no manual rearrangement needed)
3. Extract key insights
4. Summarize for user

### Step 5: Suggest Next Steps

- Additional URLs to analyze?
- Comparative analysis needed?
- PKM organization suggestions?

## CLI Options

```bash
# Basic crawling (static sites)
python3 web-crawler.py <URL> [output.md]

# Dynamic/SPA sites (recommended for Korean e-commerce)
python3 web-crawler.py <URL> --wait 5000 --scroll --max-images 10

# JS rendering wait only (no scroll)
python3 web-crawler.py <URL> --wait 3000

# Force stealth mode (Cloudflare bypass)
python3 web-crawler.py <URL> --stealth

# Text only, no OCR
python3 web-crawler.py <URL> --no-ocr

# Limit OCR images
python3 web-crawler.py <URL> --max-images 5
```

### Option Details

| Option | Description |
|--------|------------|
| `--wait <ms>` | JS 렌더링 대기 (Playwright 사용). SPA 필수 |
| `--scroll` | 페이지 스크롤하여 lazy-load 트리거. `--wait`과 함께 사용 |
| `--stealth` | Camoufox 브라우저로 Cloudflare 우회 |
| `--max-images N` | OCR 처리할 최대 이미지 수 (기본 15) |
| `--no-ocr` | OCR 건너뛰기 (텍스트만 추출) |

## Examples

### Example 1: Competitor Cafe Analysis

**User:** "Analyze this competitor cafe website: https://competitor-cafe.com"

**Claude Actions:**
```bash
mkdir -p ./50-resources/competitor-analysis

cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py \
    "https://competitor-cafe.com" \
    ./50-resources/competitor-analysis/competitor-cafe-20260315.md
```

### Example 2: Multiple URLs

**User:** "Analyze these 3 competitor sites"

**Claude:** Process each URL sequentially, then provide comparative analysis.

## Environment Setup

### Required Environment Variables

Only GEMINI_API_KEY is required (for OCR). Crawling is fully local.

```bash
export GEMINI_API_KEY="your_gemini_key_here"
```

> **키 형식 안내**: 2025~26년 신규 발급 Google AI Studio 키는 `AQ.`로 시작할 수 있습니다(과거 `AIzaSy` 형식과 다름). 둘 다 정상이며, 이 스킬은 `X-goog-api-key` **헤더 방식**으로 호출하므로 두 형식 모두 지원합니다. 모델은 무료 티어에서 동작하는 `gemini-flash-lite-latest` 사용(구형 `gemini-2.5-flash`는 신규 키에 미제공 → 404). 무료 티어 속도제한(429)은 요청 간 1.5초 간격 + 지수 백오프 재시도로 완화하며, 많은 이미지 처리 시 `--max-images`를 줄이세요.

### Alternative: .env File

Create `.claude/skills/web-crawler-ocr/scripts/.env`:
```
GEMINI_API_KEY=your_gemini_key_here
```

### Optional: Stealth/Dynamic Fetchers

For Cloudflare-protected or JS-heavy sites:
```bash
cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
pip install -r requirements-stealth.txt && \
scrapling install
```

This installs Playwright + Camoufox browser (~300MB+).

## Limitations

- **Gemini Free Tier**: 15 requests per minute
- **Image Limit**: Maximum 15 images per page (configurable)
- **File Size**: 20MB per image maximum
- **Stealth/Dynamic**: Requires separate install (`requirements-stealth.txt`)

## Troubleshooting

### Blocked by Cloudflare

Install stealth fetchers:
```bash
pip install -r requirements-stealth.txt && scrapling install
```

Or use `--stealth` flag.

### Python Package Errors

```bash
cd .claude/skills/web-crawler-ocr/scripts
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Script Location

- **Main Script**: `.claude/skills/web-crawler-ocr/scripts/web-crawler.py`
- **Helper Script**: `.claude/skills/web-crawler-ocr/scripts/gemini-ocr.py`
- **Config Template**: `.claude/skills/web-crawler-ocr/scripts/.env.example`
- **Requirements**: `.claude/skills/web-crawler-ocr/scripts/requirements.txt`
- **Stealth Requirements**: `.claude/skills/web-crawler-ocr/scripts/requirements-stealth.txt`
- **Virtual Env**: `.claude/skills/web-crawler-ocr/scripts/venv/` (created on first run)

## Version History

- **v3.0.1 (2026-03-15)**: 동적 사이트 범용 개선
  - Playwright 직접 사용 (DynamicFetcher 대체) + 실제 스크롤 구현
  - SPA 구조화 데이터 추출 (JSON-LD, __NEXT_DATA__, RSC payload, meta)
  - 3소스 이미지 추출 (markdown + HTML img + regex fallback)
  - thumbnail exclude 패턴 정밀화 (한국 이커머스 호환)
  - DynamicFetcher/StealthyFetcher bytes->str 변환 수정
  - RSC payload 한글 인코딩 수정

- **v3.1.0 (2026-07-19)**: 신규 키 형식·모델·할루시네이션 대응
  - Gemini 인증을 `X-goog-api-key` 헤더 방식으로 전환 (신규 `AQ.` 키 + 구형 `AIzaSy` 키 모두 지원)
  - 모델 `gemini-2.5-flash` → `gemini-flash-lite-latest` (신규 키 무료 티어 동작)
  - 429(할당량/속도제한) 지수 백오프 재시도 + 요청 간 1.5초 간격
  - **OCR 할루시네이션 차단 프롬프트**: 불확실하면 지어내지 말고 `[판독 불가]`·`신뢰도` 표기 (실제 "KOHLER" 오독 사건 반영)

- **v3.0.0 (2026-03-15)**: Scrapling + trafilatura로 전환
  - Firecrawl API 의존 완전 제거 (로컬 크롤링)
  - 3단계 fetcher 에스컬레이션 (HTTP -> Stealth -> Dynamic)
  - trafilatura로 콘텐츠 정제 + markdown 변환
  - OCR 인라인 자동 삽입 (Step 5 수동 재배치 제거)
  - 비동기 이미지 다운로드 (aiohttp)
  - --stealth 옵션 추가
  - GEMINI_API_KEY만 필요 (FIRECRAWL_API_KEY 제거)

- **v2.0.0 (2026-01-29)**: 외부 CDN 이미지 OCR 자동 처리

- **v1.3.0 (2025-01-17)**: venv 경량화 (203MB -> 54MB)

- **v1.2.0 (2025-11-28)**: OCR 재배치 로직 추가

- **v1.1.0 (2025-11-10)**: Skill 구조 정리

- **v1.0.0 (2025-10-29)**: Initial skill creation
