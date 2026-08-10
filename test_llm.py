import json
from dotenv import load_dotenv
from llm_client import get_initial_recommendation

load_dotenv()

errors = []
result = get_initial_recommendation("2026-03-15", errors)

print(json.dumps(result, ensure_ascii=False, indent=2))
print("\n오류 목록:", errors)