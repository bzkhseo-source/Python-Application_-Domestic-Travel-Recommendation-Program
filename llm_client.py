"""
llm_client.py
Google Gemini API 연동 모듈
- 1차 추천(지역/날씨/행사) JSON 생성
- 최종 여행 리포트(Markdown) 생성
"""

import os
import json
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.5-flash-lite"


def _get_client():
    """환경변수에서 API 키를 읽어 Gemini 클라이언트를 생성한다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        print('   .env 파일에 GEMINI_API_KEY=발급받은키 형식으로 추가해주세요.')
        raise SystemExit(1)
    return genai.Client(api_key=api_key)


def get_initial_recommendation(date_str: str, errors: list) -> dict:
    """
    날짜를 기반으로 여행지 2~3곳을 추천받는다. (보너스: 복수 지역 추천)

    반환 형식:
    {
      "recommendations": [
        {"city": str, "weather": str, "events": [str, ...], "reason": str},
        ...
      ]
    }
    """
    client = _get_client()

    prompt = f"""당신은 국내 여행 전문가입니다. 아래 날짜에 여행하기 좋은
대한민국 국내 지역을 2~3곳 추천해주세요.

여행 날짜: {date_str}

반드시 아래 JSON 형식으로만 응답하세요. 다른 설명 문구는 절대 포함하지 마세요.

{{
  "recommendations": [
    {{
      "city": "지역명 (예: 제주, 강릉)",
      "weather": "해당 시기 일반적인 날씨 요약 (한 문장)",
      "events": ["행사/축제 후보 1", "행사/축제 후보 2"],
      "reason": "추천 근거 2~4문장"
    }}
  ]
}}
"""

    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )

    # LLM JSON 파싱 실패 시 최대 1회 재시도
    last_error = None
    for attempt in range(2):  # 1회 시도 + 1회 재시도 = 총 2회
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=generation_config,
            )
            data = json.loads(response.text)

            # 최소 스키마 검증
            if "recommendations" not in data or not isinstance(data["recommendations"], list):
                raise ValueError("recommendations 키가 없거나 리스트가 아닙니다.")
            if len(data["recommendations"]) == 0:
                raise ValueError("recommendations가 비어 있습니다.")

            return data

        except (json.JSONDecodeError, ValueError, Exception) as e:
            last_error = e
            if attempt == 0:
                print(f"⚠️  1차 추천 JSON 파싱 실패, 재시도합니다... ({e})")
                # 재시도 시 프롬프트를 더 강하게 지시
                prompt += "\n\n반드시 유효한 JSON만 출력하세요. 마크다운 코드블록(```)도 사용하지 마세요."
            continue

    # 재시도까지 실패한 경우
    errors.append({
        "step": "llm_recommendation",
        "type": "PARSING_ERROR",
        "message": f"1차 추천 JSON 파싱 실패: {last_error}",
    })
    print(f"❌ 1차 추천 생성에 최종 실패했습니다: {last_error}")
    return {"recommendations": []}

def generate_final_report(date_str: str, recommendations_with_restaurants: list, errors: list) -> str:
    """
    최종 여행 리포트를 Markdown으로 생성한다.

    recommendations_with_restaurants 형식:
    [
      {
        "city": str, "weather": str, "events": [str,...], "reason": str,
        "restaurants": [{"name","address","category","url","x","y"}, ...]  # 0건 가능
      },
      ...
    ]
    """
    client = _get_client()

    # 프롬프트에 넣을 요약 데이터 구성
    cities_summary = []
    for rec in recommendations_with_restaurants:
        restaurant_lines = "\n".join(
            f"  - {r['name']} ({r.get('category','')}) - {r.get('address','')}"
            for r in rec.get("restaurants", [])
        ) or "  - 데이터 없음"

        cities_summary.append(
            f"### {rec['city']}\n"
            f"- 날씨: {rec['weather']}\n"
            f"- 행사/축제: {', '.join(rec.get('events', [])) or '데이터 없음'}\n"
            f"- 추천 이유: {rec['reason']}\n"
            f"- 맛집:\n{restaurant_lines}"
        )

    errors_summary = json.dumps(errors, ensure_ascii=False) if errors else "없음"

    prompt = f"""당신은 국내 여행 리포트를 작성하는 전문가입니다.
아래 데이터를 바탕으로 "{date_str}" 여행을 위한 최종 여행 리포트를
Markdown 형식으로 작성해주세요.

[지역별 데이터]
{chr(10).join(cities_summary)}

[오류 요약]
{errors_summary}

반드시 아래 Markdown 구조를 정확히 따르세요 (지역이 여러 곳이면 지역별로 섹션을 반복):

# {date_str} 국내 여행 추천 리포트

## 추천 지역
(지역 목록 요약)

## 추천 이유
(지역별 추천 이유)

## 날씨 요약
(지역별 날씨)

## 행사/축제
(지역별 행사·축제, 없으면 "데이터 없음")

## 맛집 추천
(지역별 맛집 리스트, 0건이면 "데이터 없음"으로 표기)

## (선택) 1일 일정 제안
(지역별로 오전/오후/저녁 수준의 간단한 일정 제안)

## 오류 요약(errors)
(오류가 있으면 목록으로, 없으면 "없음"으로 표기)

다른 설명 문구 없이 위 Markdown 문서만 출력하세요.
"""

    last_error = None
    for attempt in range(2):  # 1회 시도 + 1회 재시도
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            report_text = response.text.strip()

            # 코드블록으로 감싸져 나온 경우 제거
            if report_text.startswith("```"):
                report_text = report_text.strip("`")
                if report_text.lower().startswith("markdown"):
                    report_text = report_text[len("markdown"):].strip()

            if not report_text or "#" not in report_text:
                raise ValueError("생성된 리포트가 비어있거나 형식이 올바르지 않습니다.")

            return report_text

        except Exception as e:
            last_error = e
            if attempt == 0:
                print(f"⚠️  최종 리포트 생성 실패, 재시도합니다... ({e})")
            continue

    errors.append({
        "step": "report_generation",
        "type": "PARSING_ERROR",
        "message": f"최종 리포트 생성 실패: {last_error}",
    })
    print(f"❌ 최종 리포트 생성에 최종 실패했습니다: {last_error}")

    # 최소한의 폴백 리포트 (완전히 빈 결과 방지)
    return (
        f"# {date_str} 국내 여행 추천 리포트\n\n"
        f"## 오류 요약(errors)\n"
        f"리포트 생성 중 오류가 발생했습니다: {last_error}\n"
    )