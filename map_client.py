"""
map_client.py
Kakao Local API 연동 모듈
- 키워드 기반 장소(맛집) 검색
"""

import os
import requests

KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def search_restaurants(city: str, errors: list, size: int = 5) -> list:
    """
    지역명을 기준으로 맛집을 검색한다.

    반환: [{name, address, category, url, x, y}, ...]  (실패/0건이면 빈 리스트)
    """
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key:
        print("❌ KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        print('   .env 파일에 KAKAO_REST_API_KEY=발급받은키 형식으로 추가해주세요.')
        raise SystemExit(1)

    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {
        "query": f"{city} 맛집",
        "category_group_code": "FD6",  # 음식점 카테고리
        "size": size,
    }

    try:
        response = requests.get(
            KAKAO_LOCAL_URL, headers=headers, params=params, timeout=10
        )

        # 인증 실패 (401/403)
        if response.status_code in (401, 403):
            print(f"⚠️  오류: 인증 실패({response.status_code}). 키 설정을 확인하세요.")
            print("   맛집 섹션은 '데이터 없음'으로 처리하고 계속 진행합니다.")
            errors.append({
                "step": "place_search",
                "type": "AUTH_ERROR",
                "message": f"HTTP {response.status_code} (city={city})",
            })
            return []

        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])

        # 0건인 경우
        if len(documents) == 0:
            print(f"   - '{city}' 검색 결과 0건 (다음 단계로 진행)")
            errors.append({
                "step": "place_search",
                "type": "EMPTY_RESULT",
                "message": f"0 results for query={city} 맛집",
            })
            return []

        restaurants = []
        for doc in documents:
            restaurants.append({
                "name": doc.get("place_name", ""),
                "address": doc.get("road_address_name") or doc.get("address_name", ""),
                "category": doc.get("category_name", ""),
                "url": doc.get("place_url", ""),
                "x": doc.get("x", ""),  # 경도
                "y": doc.get("y", ""),  # 위도
            })

        print(f"   - '{city}' 맛집 {len(restaurants)}곳 검색 완료")
        return restaurants

    except requests.exceptions.RequestException as e:
        print(f"⚠️  오류: 네트워크 오류로 맛집 검색에 실패했습니다. ({e})")
        print("   맛집 섹션은 '데이터 없음'으로 처리하고 계속 진행합니다.")
        errors.append({
            "step": "place_search",
            "type": "NETWORK_ERROR",
            "message": str(e),
        })
        return []