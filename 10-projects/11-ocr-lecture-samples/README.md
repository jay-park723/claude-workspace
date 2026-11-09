# OCR 강의용 실물 영수증 샘플

> OCR 기능 테스트/강의 실습용 샘플 자료. AI 생성 이미지가 아닌 실제 촬영된 영수증 사진.

## 출처

- **데이터셋**: CORD (Consolidated Receipt Dataset for Post-OCR Parsing), NAVER Clova AI
- **원본 저장소**: https://github.com/clovaai/cord
- **다운로드 경로**: Hugging Face `naver-clova-ix/cord-v1`, test split (Hugging Face Datasets Server API 경유)
- **라이선스**: CC BY 4.0 (Creative Commons Attribution 4.0 International) — 출처 표시 시 영리·비영리 목적 사용 및 수정 가능
- **원 데이터 성격**: 인도네시아에서 실제 촬영된 영수증 사진 1,000여 장(학술 연구/OCR 벤치마크용으로 공개)

## 파일 목록

`receipts/` 폴더에 5개 이미지가 있으며, 각 파일명의 마지막 숫자는 원본 데이터셋의 test split 내 row 번호입니다.

| 파일 | 원본 row | 크기 |
|---|---|---|
| receipt-01-cord-test-0.jpg | 0 | 25.6KB |
| receipt-02-cord-test-1.jpg | 1 | 56.7KB |
| receipt-03-cord-test-2.jpg | 2 | 67.5KB |
| receipt-04-cord-test-3.jpg | 3 | 68.7KB |
| receipt-05-cord-test-4.jpg | 4 | 82.5KB |

각 이미지에 대응하는 OCR 정답 라벨(상호명, 품목, 금액 등 구조화 데이터)이 원본 데이터셋에 함께 제공되므로, 필요하면 `ground_truth` 필드도 받아 강의용 정답지로 활용할 수 있습니다. (이번 작업에서는 이미지만 다운로드함)

## 유의 사항

- 실물 영수증이지만 데이터셋 공개 과정에서 매장명 등 일부 정보가 블러 처리되어 있을 수 있습니다.
- 강의 자료로 배포 시 CC BY 4.0 조건에 따라 출처(CORD, NAVER Clova AI)를 표기해야 합니다.
