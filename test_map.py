import json
from dotenv import load_dotenv
from map_client import search_restaurants

load_dotenv()

errors = []
result = search_restaurants("제주", errors)

print(json.dumps(result, ensure_ascii=False, indent=2))
print("\n오류 목록:", errors)