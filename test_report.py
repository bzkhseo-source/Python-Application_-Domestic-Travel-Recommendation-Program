from dotenv import load_dotenv
from llm_client import get_initial_recommendation, generate_final_report
from map_client import search_restaurants

load_dotenv()

errors = []
date_str = "2026-03-15"

# 1차 추천
rec_data = get_initial_recommendation(date_str, errors)
recommendations = rec_data.get("recommendations", [])

# 맛집 검색 (지역별)
for rec in recommendations:
    rec["restaurants"] = search_restaurants(rec["city"], errors)

# 최종 리포트 생성
report = generate_final_report(date_str, recommendations, errors)

print(report)

# 파일로도 저장해서 확인
with open("test_report_output.md", "w", encoding="utf-8") as f:
    f.write(report)
print("\n\n✅ test_report_output.md 파일로도 저장했습니다.")
