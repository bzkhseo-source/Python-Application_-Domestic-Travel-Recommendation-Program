# 국내 여행 추천 프로그램 (Travel Planner)

Gemini API와 Kakao Local API를 조합하여, 입력한 날짜에 어울리는 국내 여행지를 추천하고
맛집 정보를 검색한 뒤 최종 여행 리포트(Markdown)를 생성하는 CLI 프로그램입니다.

## 1. 프로그램 개요

여행 날짜를 입력하면 아래 순서로 동작합니다.

1. **1차 추천 (Gemini API)**: 입력한 날짜를 기준으로 여행하기 좋은 국내 지역 2~3곳을
   날씨/행사/추천 이유와 함께 JSON으로 추천받습니다. (보너스: 복수 지역 추천)
2. **맛집 검색 (Kakao Local API)**: 추천받은 각 지역의 맛집을 5곳씩 검색합니다.
3. **최종 리포트 생성 (Gemini API)**: 위 데이터를 종합하여 지역별 여행 리포트를
   Markdown 형식으로 생성하고 저장합니다.

같은 날짜로 재실행하면, 이미 저장된 원본 데이터가 있을 경우 API 호출을 건너뛰고
캐시된 데이터를 재사용합니다. (보너스: 결과 캐싱)

## 2. 실행 환경

- Python 3.10 이상
- 필요 패키지: `google-genai`, `requests`, `python-dotenv`

## 3. 설치 및 실행 방법

### 3-1. 가상환경 생성 및 활성화

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3-2. 패키지 설치

```powershell
pip install google-genai requests python-dotenv
```

### 3-3. 프로그램 실행

```powershell
python travel_planner.py --date "2026-03-15"
```

- `--date` 옵션은 필수이며, 형식은 반드시 `"YYYY-MM-DD"` 이어야 합니다.
- 날짜 형식이 올바르지 않으면 사용법 안내와 함께 프로그램이 종료됩니다.

## 4. API 키 설정 방법 (필수)

이 프로그램은 아래 2개의 API 키가 필요합니다.

| 키 이름 | 발급처 |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `KAKAO_REST_API_KEY` | https://developers.kakao.com/ (내 애플리케이션 > 앱 키 > REST API 키) |

> ⚠️ Kakao 애플리케이션 생성 후, **"카카오맵(로컬)" 서비스를 반드시 활성화**해야 합니다.
> 활성화하지 않으면 `403 disabled OPEN_MAP_AND_LOCAL service` 오류가 발생합니다.

### 설정 절차

1. 프로젝트 루트 폴더에 `.env` 파일을 생성합니다. (`.env.example` 참고)
2. 아래 형식으로 발급받은 키 값을 채워 넣습니다.
- GEMINI_API_KEY=발급받은_Gemini_API_키
- KAKAO_REST_API_KEY=발급받은_Kakao_REST_API_키
3. 따옴표나 공백 없이 `키이름=값` 형식으로 작성해야 합니다.

API 키가 설정되지 않은 상태로 실행하면, 프로그램은 즉시 종료되며 위와 동일한
설정 방법 안내 메시지를 출력합니다.

## 5. 결과물 확인 방법

프로그램 실행이 완료되면 `results/` 폴더에 아래 2개 파일이 생성됩니다.

- `results/{날짜}_raw_data.json` : 1차 추천 결과 + 맛집 검색 결과 + 오류 요약이 담긴 원본 데이터
- `results/{날짜}_travel_plan.md` : 사람이 읽기 좋은 최종 여행 리포트 (Markdown)

리포트에는 아래 항목이 포함됩니다: 추천 지역/이유, 날씨 요약, 행사/축제, 맛집 리스트
(0건이면 "데이터 없음"), 1일 일정 제안, 오류 요약.

## 6. 오류 처리 정책

| 상황 | 처리 방식 |
|---|---|
| API 키 미설정 | 즉시 종료 + 설정 방법 안내 출력 |
| 맛집 검색 API 실패(네트워크/인증/쿼터) | 해당 지역 맛집을 "데이터 없음"으로 처리하고 리포트 생성은 계속 진행 |
| 검색 결과 0건 | 프로그램 중단 없이 "데이터 없음"으로 다음 단계 진행 |
| LLM JSON 파싱 실패 | 최대 1회 재시도 후에도 실패하면 오류를 기록하고 계속 진행 |

모든 오류는 원본 데이터 JSON의 `errors` 배열과 리포트의 `## 오류 요약(errors)` 섹션에
기록됩니다.

## 7. ⚠️ 보안 주의사항 (API 키 유출 방지)

- **API 키는 코드에 절대 직접 작성하지 않습니다.** 반드시 `.env` 파일 또는
  환경변수를 통해 읽어옵니다. (`python-dotenv` 사용)
- **`.env` 파일은 `.gitignore`에 등록되어 있어 Git/GitHub에 커밋되지 않습니다.**
  커밋 전 `git status`로 `.env`가 목록에 없는지 반드시 확인하세요.
- 협업 시에는 `.env.example`(값 없이 형식만 있는 파일)을 공유하고,
  실제 키 값이 담긴 `.env`는 절대 공유하지 않습니다.
- 키가 실수로 노출된 경우, 즉시 해당 콘솔(Google AI Studio / Kakao Developers)에서
  키를 재발급(회전)하세요.
- 이 저장소의 README, 로그, 결과 파일(`results/` 하위 파일 포함) 어디에도
  실제 키 값이 포함되어 있지 않습니다.

## 8. 프로젝트 구조
Travel_planner/
├── travel_planner.py # 메인 CLI 프로그램
├── llm_client.py # Gemini API 연동 (1차 추천 + 최종 리포트 생성)
├── map_client.py # Kakao Local API 연동 (맛집 검색)
├── cache_manager.py # 결과 캐싱 (보너스)
├── .env # API 키 (Git 미포함, 직접 생성 필요)
├── .env.example # API 키 형식 예시 (Git 포함)
├── .gitignore # .env, venv 등 제외 설정
├── README.md # 프로젝트 설명 문서
└── results/ # 실행 결과 저장 폴더
├── {날짜}_raw_data.json
└── {날짜}_travel_plan.md
## 9. 보너스 과제 구현 내역

- **보너스 1 (복수 지역 추천)**: 1차 추천에서 `recommendations` 배열로 2~3개 지역을
  동시에 추천받고, 지역별로 맛집 검색 및 리포트 섹션을 반복 생성합니다.
- **보너스 2 (결과 캐싱)**: 같은 `--date`로 재실행 시, `results/{날짜}_raw_data.json`이
  이미 존재하면 Gemini/Kakao API 호출을 건너뛰고 저장된 데이터를 재사용하여
  리포트만 재생성합니다.