import os
from dotenv import load_dotenv

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
kakao_key = os.getenv("KAKAO_REST_API_KEY")

if not gemini_key:
    print("❌ GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
else:
    print(f"✅ GEMINI_API_KEY 로드 성공 (앞 4자리: {gemini_key[:4]}****)")

if not kakao_key:
    print("❌ KAKAO_REST_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
else:
    print(f"✅ KAKAO_REST_API_KEY 로드 성공 (앞 4자리: {kakao_key[:4]}****)")