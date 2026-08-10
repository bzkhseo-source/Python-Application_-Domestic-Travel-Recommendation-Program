"""
cache_manager.py
결과 캐싱 모듈 (보너스 2)
- 같은 --date로 재실행 시, 이미 저장된 원본 JSON이 있으면
  API 호출을 건너뛰고 캐시된 데이터를 재사용한다.
"""

import os
import json

CACHE_DIR = "results"


def get_cache_path(date_str: str) -> str:
    """날짜 기준 캐시(원본 데이터 JSON) 파일 경로를 반환한다."""
    return os.path.join(CACHE_DIR, f"{date_str}_raw_data.json")


def load_cache(date_str: str):
    """
    캐시 파일이 있으면 읽어서 반환하고, 없으면 None을 반환한다.
    캐시가 있으면 recommendations와 restaurants_by_city를 그대로 재사용한다.
    """
    path = get_cache_path(date_str)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"💾 캐시 발견: {path}")
        print("   기존 원본 데이터를 재사용합니다. (Gemini/Kakao API 호출을 건너뜁니다)")
        return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  캐시 파일을 읽는 중 오류가 발생해 새로 생성합니다. ({e})")
        return None


def save_cache(date_str: str, raw_data: dict):
    """원본 데이터(1차 추천 + 맛집 검색 + 오류 목록)를 JSON으로 저장한다."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = get_cache_path(date_str)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 원본 데이터 저장 완료: {path}")
    return path