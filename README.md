# FinFit — 사회초년생을 위한 금융성향 기반 추천 서비스

사회초년생 입장에서 금융은 시작부터 막막합니다. 예·적금 상품만 300개가 넘고, 카드는 수십 종, 주식 종목은 어디서부터 봐야 할지도 모릅니다. 정보가 없어서가 아니라 오히려 너무 많아서 뭘 선택해야 할지 모르는 상황입니다.

FinFit은 그 출발점을 "검색"이 아니라 "성향 파악"으로 잡았습니다. 10문항 금융성향 검사로 투자 성향을 먼저 파악하고, 그 결과를 기준으로 예·적금 상품, 주식 종목, 카드를 AI가 추천하는 구조입니다.

<br>

## 시연 화면

| 홈 화면 | 금융성향 검사 결과 & AI 추천 |
|:---:|:---:|
| ![홈](./screenshots/00_home_guest.png) | ![검사결과](./screenshots/13_test_result.png) |

| 목표 저축 플래너 | AI 금융 상담 챗봇 |
|:---:|:---:|
| ![플래너](./screenshots/17_planner.png) | ![챗봇](./screenshots/21_ai_chatbot_open.png) |

<br>

## 기술 스택

![Vue.js](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D)
![Pinia](https://img.shields.io/badge/Pinia-FFD859?style=for-the-badge&logo=vuedotjs&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)

<br>

## 팀원

| 이름 | 역할 |
|------|------|
| 이윤우 | 백엔드 전체 (Django API 설계 및 구현) |
| 이진웅 | 프론트엔드 전체 (Vue 3 UI/UX 구현) |

**개발 기간**: 2026.05 ~ 2026.06

<br>

## 주요 기능

- **금융성향 검사 & AI 추천** — 10문항으로 4축 성향 코드 산출, 코드 기반으로 예·적금·주식·카드 AI 추천
- **목표 저축 플래너** — 목표 달성 가능 여부 계산, 달성 못 할 때 필요 납입액·필요 기간 역산
- **주식 · 뉴스** — KOSPI/KOSDAQ 시세 조회, 관심 종목 등록, 종목 뉴스 한국어 번역
- **AI 주간 브리핑** — RSS 7개 금융 뉴스 자동 수집, 매주 월요일 경제 요약 자동 생성
- **AI 금융 상담 챗봇** — 비로그인 가능, 예·적금·주식·카드·세금 등 자유 질문
- **그 외** — 주변 은행 지도, 금·은 원자재 시세, 상품·카드 리뷰, 커뮤니티 게시판

<br>

## 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 백엔드
cd BE
python manage.py migrate
python manage.py runserver

# 프론트엔드 (새 터미널)
cd FE
npm install
npm run dev
```

루트 디렉토리의 `.env`에 아래 항목을 설정해야 합니다. `.env.example`을 참고하세요.

```
SECRET_KEY=
FINLIFE_API_KEY=
GMS_API_KEY=
GMS_API_URL=
GEMINI_API_KEY=
KAKAO_REST_API_KEY=
VITE_KAKAO_MAP_KEY=
```

금융상품 데이터는 서버 실행 후 관리자 계정으로 `/products/save-products/`와 `/products/save-saving-products/`를 호출하면 FSS API에서 수집됩니다.

<br>

## 문서

| 문서 | 내용 |
|------|------|
| [설계서](./docs/설계서.md) | 서비스 기획 의도, 기능 설계, 흐름도, DB 모델링 |
| [API 명세](./docs/api.md) | 전체 엔드포인트 요청·응답 예시 |
| [기술 스택](./docs/tech-stack.md) | 기술 선택 이유 |
| [트러블슈팅](./docs/trouble-shooting.md) | 개발 중 막혔던 문제와 해결 과정 |

<br>

## 회고

### 아쉬운 점

배포를 못 한 게 제일 아쉽습니다. SQLite3를 그대로 쓴 건 로컬 포트폴리오라는 전제 아래 내린 선택이었는데, 막상 완성하고 나니 누군가한테 URL 하나로 보여줄 수 없다는 게 아쉬움으로 남습니다. PostgreSQL 전환은 ORM 코드를 건드릴 게 거의 없어서, 처음부터 배포 환경을 염두에 두고 시작했다면 어렵지 않게 올릴 수 있었을 것 같습니다.

주식 거래 기능도 못 넣었습니다. 종목 조회, 관심 종목 등록, 시세 차트까지는 됐는데 모의 매수·매도 기능은 개발 기간 안에 넣지 못했어요. 거래 내역과 포트폴리오 수익률 같은 기능이 붙었다면 주식 섹션이 훨씬 완결성이 있었을 텐데 하는 생각이 남습니다.

실시간 데이터도 한계가 있었습니다. FSS Finlife API는 응답이 3~5초씩 걸려서 실시간 호출을 포기하고 DB 캐싱 방식으로 전환했고, yfinance는 비공식 라이브러리라 개발 중에 응답 구조가 바뀌는 일도 있었습니다. 공식 금융 데이터 API를 활용할 수 있는 환경이었다면 더 안정적인 서비스가 됐을 것 같습니다.

### 잘 됐다고 생각하는 것

**추천 시스템 설계**가 제일 만족스럽습니다. "AI가 추천해줍니다"에서 끝내지 않고, 금리 경쟁력 40% · 수익 절대액 30% · 상품 유형 적합성 15% · 은행 신뢰도 및 인근 여부 15%로 채점 기준을 직접 설계해서 프롬프트에 담았습니다. 기준을 명확하게 써줬을 때 AI 추천 결과의 일관성이 눈에 띄게 좋아졌고, 각 상품이 왜 추천됐는지 이유도 자연스럽게 함께 나왔습니다. AI한테 그냥 맡기는 게 아니라 도메인 로직을 프롬프트로 녹여내는 과정이 이 프로젝트에서 제일 재미있었던 부분이었습니다.

**금융성향 검사 설계**도 잘 됐다고 생각합니다. 단순히 "공격적인 투자를 선호하시나요?" 같은 직접 질문 대신 상황 기반 질문으로 구성했고, 역방향 문항(Q2, Q6, Q9)을 넣어서 응답이 솔직하지 않을 때도 보정이 되도록 했습니다. 검사 결과가 4자리 코드로 나오고, 이 코드가 AI 추천 프롬프트와 유사 사용자 통계, 저축 플래너 상품 필터링까지 서비스 전반에 맥락을 만들어주는 구조가 의도한 대로 잘 동작했습니다.

**장애 대응 구조**도 실제로 효과를 봤습니다. GMS API가 테스트 중에 한 번 응답이 없었는데, Gemini 1.5 Flash로 폴백이 자동으로 동작했습니다. 외부 서비스에 의존하는 기능이 많다 보니 어느 하나가 장애가 나도 500이 올라오지 않게 방어적으로 설계한 부분이 실제 상황에서 유효했습니다.
