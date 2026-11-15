#!/usr/bin/env python3
"""
Gemini OCR - 이미지 파일 직접 OCR 스크립트
웹 크롤링 없이 로컬 이미지 파일을 Gemini로 OCR 처리

사용법:
    python3 gemini-ocr.py <image_path> [output_path] [--prompt <custom_prompt>]

예시:
    # 기본 OCR
    python3 gemini-ocr.py image.png

    # 출력 파일 지정
    python3 gemini-ocr.py image.png result.md

    # 커스텀 프롬프트
    python3 gemini-ocr.py image.png --prompt "이 이미지의 표만 추출해주세요"
"""

import os
import sys
import argparse
import base64
import requests
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# Colors
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

def print_color(message, color):
    print(f"{color}{message}{Colors.NC}")

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def check_api_key():
    """API 키 확인"""
    if not GEMINI_API_KEY:
        print_color("❌ GEMINI_API_KEY가 설정되지 않았습니다.", Colors.RED)
        print_color("\n.env 파일에 다음을 추가하거나:", Colors.YELLOW)
        print_color("   GEMINI_API_KEY='your_key_here'", Colors.YELLOW)
        print_color("\n환경변수로 설정하세요:", Colors.YELLOW)
        print_color("   export GEMINI_API_KEY='your_key_here'", Colors.YELLOW)
        sys.exit(1)

def call_gemini_rest(prompt, image_path):
    """Gemini REST API 직접 호출 (경량화)"""
    # 이미지를 base64로 인코딩
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # 이미지 MIME 타입 결정
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    mime_type = mime_types.get(ext, 'image/jpeg')

    # REST API 호출
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
        headers={"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY},
        json={
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_data}}
                ]
            }]
        },
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"API 오류: {response.status_code} - {response.text}")

    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


def ocr_image(image_path, custom_prompt=None):
    """이미지 OCR 처리"""
    try:
        # 이미지 로드 및 검증
        print_color(f"📖 이미지 로드 중: {image_path}", Colors.BLUE)
        img = Image.open(image_path)
        img.verify()  # 이미지 무결성 검증

        # 프롬프트 설정
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = """이 이미지에서 **실제로 또렷하게 보이는 텍스트만** 정확히 추출하세요. 아래 규칙을 반드시 지키세요.

1. 또렷하게 읽을 수 있는 글자만 그대로 옮깁니다. 표·리스트는 마크다운으로 구조화, 제목/본문 구분.
2. 흐리거나 작아서 확실치 않은 부분은 **추측하지 말고 `[판독 불가]`** 로 표시합니다.
3. **로고·브랜드명은 특히 조심.** 확실히 읽히지 않으면 브랜드명을 지어내지 말고 `[로고 있으나 판독 불가 — 사람 확인 필요]` 라고만 씁니다.
4. 숫자·금액·모델명도 확실치 않으면 `[숫자 판독 불가]` 로 표시합니다.
5. 텍스트가 없으면 `텍스트 없음` 이라고만 쓰고, 이미지 설명은 1~2문장(보이는 그대로만, 추측 브랜드/용도 단정 금지).
6. 마지막 줄에 `신뢰도: 높음/보통/낮음` 표기. 로고·숫자가 불확실하면 반드시 `낮음`.

마크다운으로 출력하세요."""

        # OCR 실행 (REST API)
        print_color("🤖 Gemini OCR 처리 중...", Colors.BLUE)
        result = call_gemini_rest(prompt, image_path)

        return result

    except Exception as e:
        print_color(f"❌ OCR 실패: {e}", Colors.RED)
        return None

def save_result(content, output_path, image_path):
    """결과 저장"""
    try:
        # 기본 출력 경로 설정
        if not output_path:
            input_path = Path(image_path)
            output_path = input_path.with_suffix('.md')

        # 마크다운 헤더 추가
        header = f"""# OCR 결과 - {Path(image_path).name}

> 원본 이미지: {image_path}
> OCR 도구: Gemini 2.5 Flash
> 생성 시간: {Path(output_path).stat().st_mtime if Path(output_path).exists() else 'N/A'}

---

"""

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header + content)

        print_color(f"✅ 결과 저장 완료: {output_path}", Colors.GREEN)
        return output_path

    except Exception as e:
        print_color(f"❌ 저장 실패: {e}", Colors.RED)
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Gemini OCR - 이미지 파일 직접 OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 OCR
  python3 gemini-ocr.py image.png

  # 출력 파일 지정
  python3 gemini-ocr.py image.png result.md

  # 커스텀 프롬프트
  python3 gemini-ocr.py image.png --prompt "이 이미지의 표만 추출해주세요"
        """
    )

    parser.add_argument('image_path', help='OCR할 이미지 파일 경로')
    parser.add_argument('output_path', nargs='?', help='결과 저장 경로 (선택)')
    parser.add_argument('--prompt', help='커스텀 프롬프트 (선택)')

    args = parser.parse_args()

    # API 키 확인
    check_api_key()

    # 이미지 파일 존재 확인
    if not Path(args.image_path).exists():
        print_color(f"❌ 이미지 파일을 찾을 수 없습니다: {args.image_path}", Colors.RED)
        sys.exit(1)

    print_color("=" * 80, Colors.BLUE)
    print_color("🚀 Gemini OCR 시작", Colors.BLUE)
    print_color("=" * 80, Colors.BLUE)

    # OCR 처리
    result = ocr_image(args.image_path, args.prompt)

    if result:
        # 결과 출력
        print_color("\n" + "=" * 80, Colors.GREEN)
        print_color("📄 OCR 결과", Colors.GREEN)
        print_color("=" * 80, Colors.GREEN)
        print(result)

        # 파일 저장
        print_color("\n" + "=" * 80, Colors.BLUE)
        output_file = save_result(result, args.output_path, args.image_path)

        if output_file:
            print_color("=" * 80, Colors.GREEN)
            print_color(f"✅ 완료: {output_file}", Colors.GREEN)
            print_color("=" * 80, Colors.GREEN)
    else:
        print_color("\n❌ OCR 처리 실패", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
