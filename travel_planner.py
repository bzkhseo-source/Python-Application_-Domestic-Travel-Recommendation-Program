"""
travel_planner.py
국내 여행 추천 CLI 프로그램
- Gemini API로 지역/날씨/행사 추천 (복수 지역, 보너스1)
- Kakao Local API로 맛집 검색
- 결과 캐싱 (보너스2)
- 최종 여행 리포트를 Markdown으로 생성 및 저장
"""

import argparse
import os
import sys
import json
from datetime import datetime

from dotenv import load_dotenv

from llm_client import get_initial_recommendation, generate_final_report
from map_client import search_restaurants
from cache_manager import load_cache, save_cache

RESULTS_DIR = "results"


def parse_args():
    """CLI 인자를 파싱하고 날짜 형식을 검증한다."""
    parser = argparse.ArgumentParser(
        prog="travel_planner.py",
        description="국내 여행 추천 프로그램 (LLM + 지도 API 연동)",
    )
    parser.add_argument(
        "--date",
        required=True,
        help='여행 날짜 (형식: "YYYY-MM-DD", 예: 2026-03-15)',
    )
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.print_usage(sys.stderr)
        print(
            f'오류: 날짜 형식이 올바르지 않습니다 -> "{args.date}"\n'
            '올바른 형식: --date "YYYY-MM-DD" (예: --date "2026-03-15")',
            file=sys.stderr,
        )
        sys.exit(1)

    return args


def check_api_keys():
    """API 키 미설정 시 즉시 종료 + 설정 방법 안내 (필수 정책)."""
    missing = []
    if not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    if not os.getenv("KAKAO_REST_API_KEY"):
        missing.append("KAKAO_REST_API_KEY")

    if missing:
        print("❌ 다음 API 키가 설정되지 않았습니다:", ", ".join(missing))
        print()
        print("설정 방법:")
        print('  1) 프로젝트 폴더에 ".env" 파일을 만드세요.')
        print("  2) 아래 형식으로 키를 추가하세요:")
        print("     GEMINI_API_KEY=발급받은_Gemini_키")
        print("     KAKAO_REST_API_KEY=발급받은_Kakao_REST_API_키")
        print("  3) 절대 키 값을 코드나 README, 결과물에 직접 작성하지 마세요.")
        sys.exit(1)


def build_raw_data(date_str: str, errors: list) -> dict:
    """
    1차 추천(LLM) + 맛집 검색(지도 API)을 수행하여 원본 데이터를 구성한다.
    (results/ 저장용 최소 스키마를 만족)
    """
    print("[1/3] 1차 추천 생성 중(LLM)...")
    rec_data = get_initial_recommendation(date_str, errors)
    recommendations = rec_data.get("recommendations", [])

    for rec in recommendations:
        print(f"  - recommended_city: \"{rec.get('city', '')}\"")

    print("[2/3] 맛집 검색 중(지도/장소 API)...")
    for rec in recommendations:
        rec["restaurants"] = search_restaurants(rec["city"], errors)

    raw_data = {
        "date": date_str,
        "recommendations": recommendations,  # 1차 추천 + 맛집 검색 결과 포함
        "errors": errors,
    }
    return raw_data


def main():
    load_dotenv()
    args = parse_args()
    date_str = args.date

    print(f"여행 계획을 시작합니다. (여행 날짜: {date_str})")

    check_api_keys()

    errors = []

    # 보너스 2: 캐시 확인 - 같은 날짜로 재실행 시 API 호출 건너뛰기
    cached = load_cache(date_str)
    if cached is not None:
        raw_data = cached
        errors = raw_data.get("errors", [])
    else:
        raw_data = build_raw_data(date_str, errors)
        save_cache(date_str, raw_data)

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    recommendations = raw_data.get("recommendations", [])
    report_text = generate_final_report(date_str, recommendations, errors)

    # 최종 오류 목록 갱신 (리포트 생성 단계 오류 포함)
    raw_data["errors"] = errors
    save_cache(date_str, raw_data)  # 오류 정보 최신화하여 재저장

    os.makedirs(RESULTS_DIR, exist_ok=True)
    report_path = os.path.join(RESULTS_DIR, f"{date_str}_travel_plan.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print("- 리포트 생성 완료")
    print()
    print(f"완료! {report_path} 를 확인하세요.")


if __name__ == "__main__":
    main()