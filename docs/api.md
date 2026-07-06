# FinFit API 명세

**Base URL**: `http://localhost:8000/api/`  
**인증**: `Authorization: Bearer <access_token>` (JWT)  
**Content-Type**: `application/json`

인증이 필요한 엔드포인트에 토큰 없이 요청하면 `401`이 돌아옵니다. 토큰은 만료 전에 `/accounts/refresh/`로 갱신해야 합니다. 관리자 전용(`IsAdminUser`) 엔드포인트는 데이터 수집용으로, 일반 사용자는 호출할 일이 없습니다.

---

## 인증 (Accounts)

### POST /accounts/signup/

회원가입. 가입 직후 access + refresh 토큰을 같이 내려줍니다.

```json
// Request
{
  "username": "finfit_user",
  "email": "user@example.com",
  "password": "password123!",
  "nickname": "핀핏유저",
  "birth_date": "2000-01-01"
}

// Response 201
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 1,
    "username": "finfit_user",
    "email": "user@example.com",
    "nickname": "핀핏유저",
    "birth_date": "2000-01-01",
    "financial_type": null,
    "profile_image": null,
    "bio": "",
    "address": ""
  }
}
```

오류: `400` username 또는 email 중복, 필드 유효성 실패

---

### POST /accounts/login/

SimpleJWT 기본 토큰 발급 엔드포인트.

```json
// Request
{ "username": "finfit_user", "password": "password123!" }

// Response 200
{ "access": "eyJ...", "refresh": "eyJ..." }
```

오류: `401` 자격증명 불일치

---

### POST /accounts/refresh/

```json
// Request
{ "refresh": "eyJ..." }

// Response 200
{ "access": "eyJ..." }
```

오류: `401` 만료되거나 블랙리스트에 있는 토큰

---

### POST /accounts/logout/ `인증 필요`

Refresh 토큰을 블랙리스트에 등록합니다. 등록 실패해도 200을 돌려줍니다 (로그만 남김).

```json
// Request
{ "refresh": "eyJ..." }

// Response 200
{ "message": "로그아웃 되었습니다." }
```

---

### GET /accounts/profile/ `인증 필요`

```json
// Response 200
{
  "id": 1,
  "username": "finfit_user",
  "email": "user@example.com",
  "nickname": "핀핏유저",
  "birth_date": "2000-01-01",
  "financial_type": "ARLN",
  "profile_image": "http://localhost:8000/media/profiles/photo.jpg",
  "bio": "안녕하세요",
  "address": "서울시 강남구"
}
```

---

### PUT /accounts/profile/ `인증 필요`

Partial update. 수정할 필드만 보내면 됩니다. 프로필 이미지는 `multipart/form-data`로 전송해야 합니다.

```json
// Request (예: 닉네임·주소만 변경)
{
  "nickname": "새닉네임",
  "address": "서울시 마포구"
}

// Response 200: GET /accounts/profile/ 응답과 동일 구조
```

---

### POST /mypage/password/ `인증 필요`

```json
// Request
{
  "current_password": "old_password123",
  "new_password": "new_password456!"
}

// Response 200
{ "message": "비밀번호가 변경됐습니다. 다시 로그인해주세요." }
```

오류: `400` 현재 비밀번호 불일치(`"현재 비밀번호가 올바르지 않습니다."`) / 새 비밀번호 8자 미만

---

## 마이페이지 (MyPage)

### GET /mypage/ `인증 필요`

```json
// Response 200
{
  "id": 1,
  "username": "finfit_user",
  "nickname": "핀핏유저",
  "email": "user@example.com",
  "financial_type": "ARLN",
  "profile_image": "http://localhost:8000/media/profiles/photo.jpg",
  "bio": "안녕하세요",
  "favorites_count": 5,
  "subscriptions_count": 2,
  "recent_count": 10,
  "stock_favorites_count": 3,
  "product_reviews_count": 4,
  "card_reviews_count": 1,
  "latest_test_result": { "score": 72, "result_type": "ARLN" },
  "address": "서울시 강남구"
}
```

검사 이력이 없으면 `latest_test_result`는 `null`입니다.

---

### GET /mypage/products/favorites/ `인증 필요`

```json
// Response 200
[
  {
    "id": 10,
    "product_name": "KB국민 스타 정기예금",
    "bank_name": "KB국민은행",
    "created_at": "2026-06-01T10:00:00+09:00"
  }
]
```

---

### GET /mypage/products/subscriptions/ `인증 필요`

가입 상품 목록. 각 상품의 최고 우대금리 기준 옵션을 함께 포함합니다.

```json
// Response 200
[
  {
    "id": 10,
    "product_name": "KB국민 스타 정기예금",
    "bank_name": "KB국민은행",
    "product_type": "deposit",
    "subscribed_at": "2026-05-15T09:00:00+09:00",
    "interest_rate": 3.20,
    "max_interest_rate": 3.80,
    "save_trm": 12
  }
]
```

---

### GET /mypage/products/recent/ `인증 필요`

```json
// Response 200
[
  {
    "id": 10,
    "product_name": "KB국민 스타 정기예금",
    "bank_name": "KB국민은행",
    "viewed_at": "2026-07-01T14:30:00+09:00"
  }
]
```

---

### GET /mypage/stocks/favorites/ `인증 필요`

```json
// Response 200
[
  {
    "id": 1,
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "created_at": "2026-06-10T08:00:00+09:00"
  }
]
```

---

### GET /mypage/reviews/ `인증 필요`

상품 리뷰와 카드 리뷰를 묶어서 돌려줍니다.

```json
// Response 200
{
  "product_reviews": [
    { "id": 3, "product_id": 10, "rating": 4, "content": "금리가 좋아요", "created_at": "..." }
  ],
  "card_reviews": [
    { "id": 1, "card_id": 5, "rating": 5, "content": "혜택이 다양해요", "created_at": "..." }
  ]
}
```

---

### GET /mypage/community/ `인증 필요`

내가 쓴 게시글과 댓글. 게시글 content는 앞 100자, 댓글은 80자만 잘라서 반환합니다.

```json
// Response 200
{
  "posts": [
    { "id": 7, "title": "삼성전자 전망", "content": "요즘 반도체...", "stock": 1, "likes_count": 3, "created_at": "..." }
  ],
  "comments": [
    { "id": 12, "content": "저도 같은...", "post_id": 5, "likes_count": 1, "created_at": "..." }
  ]
}
```

---

### GET /mypage/test-result/ `인증 필요`

마이페이지용 검사 결과 요약 (상세 결과는 `/tests/result/` 참고).

```json
// Response 200
{ "score": 72, "result_type": "ARLN", "created_at": "2026-06-15T13:00:00+09:00" }
```

오류: `404` 검사 이력 없음

---

## 금융성향 검사 & AI 추천

### POST /tests/ `인증 필요`

10문항 답변을 제출하면 점수 계산과 AI 해설이 생성됩니다.

```json
// Request
{ "answers": [4, 2, 5, 3, 4, 1, 5, 4, 2, 5] }

// Response 200
{
  "id": 42,
  "score": 72,
  "result_type": "ARLN",
  "type_name": "적극투자형 투자자",
  "description": "이성적 판단과 장기 투자를 선호하며...",
  "ai_generated": "당신의 투자 성향은 적극투자형으로...",
  "created_at": "2026-07-05T10:00:00+09:00",
  "axes": { "risk": 68, "rational": 74, "longterm": 80, "active": 65, "code": "ARLN" }
}
```

---

### GET /tests/result/ `인증 필요`

가장 최근 검사 결과를 돌려줍니다. `ai_generated` 필드는 없습니다.

오류: `404` 검사 이력 없음

---

### GET /tests/recommendations/products/ `인증 필요`
### GET /tests/recommendations/stocks/ `인증 필요`
### GET /tests/recommendations/cards/ `인증 필요`

세 엔드포인트 모두 같은 패턴입니다. DB에 캐시가 있으면 즉시 반환, 없으면 GMS API를 호출해서 생성합니다.

```json
// products 응답 예시
[
  {
    "product_id": 10, "product_name": "KB국민 스타 정기예금", "bank_name": "KB국민은행",
    "product_type": "deposit", "best_rate": 3.8,
    "score": 87, "reason": "12개월 우대금리 3.8%로 동기간 최고 수준이며..."
  }
]

// stocks 응답 예시
[
  {
    "stock_id": 1, "stock_name": "삼성전자", "stock_code": "005930",
    "score": 90, "reason": "반도체 대형주로 안정성과 성장성을 겸비..."
  }
]

// cards 응답 예시
[
  {
    "card_id": 3, "card_name": "신한 딥드림 카드", "company": "신한카드",
    "card_type": "credit", "annual_fee": 15000,
    "score": 85, "reason": "편의점·카페 혜택이 사회초년생 소비 패턴에 최적..."
  }
]
```

오류: `404` 검사 이력 없음

---

### POST /tests/recommendations/by-criteria/ `인증 필요`

금액과 기간을 직접 입력해서 받는 상품 추천. 금융성향 검사 없이도 사용 가능합니다.

```json
// Request
{ "amount": 5000000, "months": 12 }

// Response 200
[
  {
    "product_id": 10, "product_name": "KB국민 스타 정기예금",
    "bank_name": "KB국민은행", "product_type": "deposit",
    "best_rate": 3.8, "interest": 190000, "maturity_amount": 5190000,
    "score": 92, "reason": "500만원 12개월 기준 이자 19만원으로 최상위권",
    "score_breakdown": { "rate_score": 40, "interest_score": 28, "type_score": 14, "bank_score": 10 }
  }
]
```

---

### POST /tests/recommendations/cards/by-habits/ `인증 필요`

소비 습관 카테고리를 직접 선택해서 받는 카드 추천.

```json
// Request
{ "habits": ["편의점", "카페", "대중교통"] }

// Response 200
[
  {
    "card_id": 3, "card_name": "신한 딥드림 카드", "company": "신한카드",
    "card_type": "credit", "annual_fee": 15000, "min_performance": 300000,
    "score": 88, "reason": "편의점·카페·대중교통 3가지 혜택 매칭",
    "matched_benefits": ["편의점 5% 할인", "카페 10% 할인", "대중교통 월 5천원 캐시백"]
  }
]
```

---

### GET /tests/recommendations/stocks/page/ `인증 필요`

페이지네이션 적용 주식 추천. `page` 쿼리 파라미터로 페이지 지정.

---

### GET /tests/stats/similar-users/ `인증 필요`

나와 같은 성향 유형 / 같은 연령대 사용자들의 인기 상품·카드·종목 통계.

```json
// Response 200
{
  "my_type": "ARLN", "my_age": 25,
  "similar_type_cards": [{ "card_id": 3, "card_name": "신한 딥드림 카드", "count": 12 }],
  "similar_age_products": [{ "product_id": 10, "product_name": "KB국민 스타 정기예금", "count": 8 }],
  "similar_type_stocks": [{ "stock_id": 1, "stock_name": "삼성전자", "count": 20 }]
}
```

---

## 금융상품 (Products)

### GET /products/

`type=deposit` 또는 `type=saving` 쿼리 파라미터로 필터링.

```json
// Response 200
[
  {
    "id": 10, "fin_prdt_cd": "WR0001B",
    "bank_name": "KB국민은행", "product_name": "KB국민 스타 정기예금",
    "product_type": "deposit", "join_way": "인터넷, 스마트폰",
    "target_user": "실명의 개인", "special_condition": "급여이체 고객 우대",
    "options": [
      { "save_trm": 6, "interest_rate": 2.80, "max_interest_rate": 3.20 },
      { "save_trm": 12, "interest_rate": 3.20, "max_interest_rate": 3.80 }
    ]
  }
]
```

---

### GET /products/search/?keyword={keyword}

상품명 부분 일치 검색. 빈 keyword면 전체 반환.

---

### GET /products/compare/?ids=1,2,3

쉼표로 구분된 상품 ID를 받아서 비교용 데이터를 돌려줍니다. 각 상품의 모든 기간 옵션 중 최고 금리와 전체 기간 목록이 포함됩니다.

```json
// Response 200
[
  {
    "id": 10, "product_name": "KB국민 스타 정기예금", "bank_name": "KB국민은행",
    "interest_rate": 3.20, "max_interest_rate": 3.80, "periods": [6, 12, 24]
  }
]
```

오류: `400` ids가 숫자가 아닌 경우(`"ids는 쉼표로 구분된 숫자여야 합니다."`)

---

### POST /products/calculate/

만기 수령액 계산. 단리 기준.

```json
// Request
{ "amount": 5000000, "rate": 3.8, "months": 12 }

// Response 200
{ "principal": 5000000, "interest": 190000, "total": 5190000 }
```

오류: `400` 숫자 형식 오류 / amount·months가 0 이하

---

### GET /products/{product_id}/

오류: `404` 상품 없음

---

### GET /products/{product_id}/status/ `인증 필요`

해당 상품의 관심/가입 여부.

```json
// Response 200
{ "is_favorite": true, "is_subscribed": false }
```

---

### POST /products/{product_id}/favorite/ `인증 필요`

관심상품 토글. 등록되어 있으면 해제, 아니면 등록.

```json
// Response 200
{ "is_favorite": true, "message": "관심상품 추가" }
```

---

### POST /products/{product_id}/subscribe/ `인증 필요`

가입상품 토글.

```json
// Response 200
{ "is_subscribed": true, "message": "가입상품 등록" }
```

---

### POST /products/{product_id}/recent/ `인증 필요`

최근 본 상품 기록. 이미 기록이 있으면 `viewed_at`만 갱신합니다 (`update_or_create`).

### DELETE /products/{product_id}/recent/ `인증 필요`

최근 본 상품에서 삭제.

---

### GET /products/{product_id}/reviews/

### POST /products/{product_id}/reviews/ `인증 필요`

```json
// POST Request
{ "rating": 4, "content": "금리가 좋아요" }

// GET Response 200
[
  {
    "id": 3, "user": { "id": 1, "nickname": "핀핏유저" },
    "rating": 4, "content": "금리가 좋아요",
    "reactions": { "like": 5, "sad": 1 },
    "created_at": "2026-06-20T11:00:00+09:00"
  }
]
```

---

### GET /products/save-products/ `관리자 전용`
### GET /products/save-saving-products/ `관리자 전용`

FSS Finlife API에서 예금/적금 상품 데이터를 가져와 DB에 저장합니다.

```json
// Response 200
{ "message": "예금 저장 완료", "created": 50, "updated": 120, "options": 340 }
```

---

## 관심/가입/최근상품 (Favorites)

마이페이지 서브 엔드포인트 외 별도 API.

### GET /favorites/ `인증 필요`

```json
// Response 200
[{ "id": 10, "name": "KB국민 스타 정기예금", "bank": "KB국민은행" }]
```

---

### POST /favorites/{product_id}/ `인증 필요`

관심상품 토글 (`/products/{id}/favorite/`와 같은 기능, 다른 경로).

```json
// Response 200 / 201
{ "message": "관심상품 추가", "is_favorite": true }
```

---

## 리뷰 (Reviews)

### PUT /reviews/products/{review_id}/ `인증 필요`
### DELETE /reviews/products/{review_id}/ `인증 필요`

작성자 본인만 수정·삭제 가능합니다. DELETE는 `204 No Content` 반환.

오류: `403` 본인이 아닌 경우(`"권한이 없습니다."`)

---

### POST /reviews/products/{review_id}/react/ `인증 필요`

좋아요/아쉬워요 반응.

```json
// Request
{ "reaction_type": "like" }
```

---

### PUT /reviews/cards/{review_id}/ `인증 필요`
### DELETE /reviews/cards/{review_id}/ `인증 필요`

카드 리뷰 수정·삭제. 상품 리뷰와 동일 규칙.

---

## 주식 (Stocks)

### GET /stocks/

최신 시세 포함. DB의 `StockPrice` 중 최신값을 서브쿼리로 가져옵니다.

```json
// Response 200
[
  {
    "id": 1, "stock_code": "005930", "stock_name": "삼성전자",
    "description": "반도체·스마트폰·가전 제조 글로벌 선도 기업",
    "latest_price": "78500", "latest_change_rate": "1.23"
  }
]
```

---

### GET /stocks/{stock_id}/latest-price/

DB에 시세가 있으면 반환, 없으면 yfinance `fast_info`로 실시간 조회합니다. 실시간 조회 결과는 DB에 저장하지 않습니다.

```json
// Response 200
{
  "id": 150, "stock": 1, "price": "78500",
  "change_rate": "1.23", "volume": 15234500,
  "recorded_at": "2026-07-04T15:30:00+09:00"
}
```

오류: `404` yfinance 조회 실패 또는 데이터 없음

---

### GET /stocks/{stock_id}/prices/

시세 이력 전체 (최신순).

---

### GET /stocks/{stock_id}/favorite/ `인증 필요`
### POST /stocks/{stock_id}/favorite/ `인증 필요`

GET은 현재 관심 여부 확인, POST는 토글.

```json
// GET Response
{ "is_favorite": true }

// POST Response
{ "message": "관심종목 추가", "is_favorite": true }
```

---

### GET /stocks/{stock_id}/news/

yfinance에서 해당 종목의 최신 뉴스를 가져옵니다. 제목은 GMS로 한국어 번역됩니다. 최대 10건.

```json
// Response 200
[
  {
    "title": "삼성전자, 3분기 반도체 흑자 전환 전망",
    "title_en": "Samsung Electronics expected to return to profit...",
    "summary": "Analysts forecast...",
    "url": "https://...", "publisher": "Reuters", "published_at": "2026-07-04T10:00:00"
  }
]
```

---

### POST /stocks/import/issues/ `관리자 전용`

yfinance에서 KOSPI/KOSDAQ 주요 종목 정보를 수집합니다. `?codes=005930,000660`으로 특정 종목만 지정 가능.

```json
// Response 200
{ "imported": 65, "created": 30, "updated": 35, "errors": [] }
```

---

### POST /stocks/import/prices/ `관리자 전용`

`?stock_code=005930&period=1mo` 형식. period 선택지: `1d 5d 1mo 3mo 6mo 1y 2y` (기본 `1mo`).

```json
// Response 200
{ "stock_code": "005930", "period": "1mo", "rows_in_response": 22, "saved": 18 }
```

---

## 카드 (Cards)

### GET /cards/

```json
// Response 200
[
  {
    "id": 3, "card_name": "신한 딥드림 카드", "company": "신한카드",
    "card_type": "credit", "annual_fee": 15000, "min_performance": 300000,
    "image_url": "http://localhost:8000/media/cards/shinhan_deepdream.png"
  }
]
```

---

### GET /cards/{card_id}/benefits/

```json
// Response 200
[
  { "id": 10, "benefit_category": "편의점", "benefit_detail": "GS25·CU·세븐일레븐 5% 할인 (월 최대 5천원)" }
]
```

---

### GET /cards/{card_id}/reviews/

### POST /cards/{card_id}/reviews/ `인증 필요`

```json
// POST Request
{ "rating": 4, "content": "혜택이 알차네요" }
```

---

### POST /cards/import/ `관리자 전용`

카드 데이터 수동 등록.

---

## 커뮤니티 (Community)

### GET /community/posts/

최신순 게시글 목록. 인증 없이 조회 가능.

```json
// Response 200
[
  {
    "id": 7, "user": { "id": 1, "nickname": "핀핏유저" },
    "stock": { "id": 1, "stock_name": "삼성전자" },
    "title": "삼성전자 전망 어때요?", "content": "요즘 반도체 업황이...",
    "likes_count": 3, "comments_count": 5, "is_liked": false,
    "created_at": "2026-07-01T09:00:00+09:00"
  }
]
```

---

### POST /community/posts/ `인증 필요`

```json
// Request
{ "title": "삼성전자 전망 어때요?", "content": "요즘 반도체 업황이...", "stock": 1 }
```

`stock`은 선택사항. 종목과 관계없는 일반 게시글도 작성 가능합니다.

---

### GET /community/posts/{post_id}/
### PUT /community/posts/{post_id}/ `인증 필요`
### DELETE /community/posts/{post_id}/ `인증 필요`

PUT/DELETE는 작성자 본인만 가능. `403 "권한이 없습니다."` 반환. DELETE는 `204`.

---

### POST /community/posts/{post_id}/like/ `인증 필요`

```json
// Response 200
{ "is_liked": true, "likes_count": 4 }
```

---

### GET /community/posts/{post_id}/comments/

최상위 댓글만 반환하고 대댓글은 `replies` 필드에 포함됩니다.

```json
// Response 200
[
  {
    "id": 12, "user": { "id": 2, "nickname": "다른유저" },
    "content": "저도 긍정적으로 봅니다", "likes_count": 1, "is_liked": false,
    "created_at": "2026-07-01T10:00:00+09:00",
    "replies": [
      { "id": 13, "user": { "id": 1, "nickname": "핀핏유저" }, "content": "동의해요!", "likes_count": 0, "created_at": "..." }
    ]
  }
]
```

---

### POST /community/posts/{post_id}/comments/ `인증 필요`

`parent`에 댓글 ID를 넣으면 대댓글, `null`이거나 생략하면 최상위 댓글.

```json
// Request
{ "content": "댓글 내용", "parent": null }
```

---

### PUT /community/comments/{comment_id}/ `인증 필요`
### DELETE /community/comments/{comment_id}/ `인증 필요`

작성자 본인만. DELETE는 `204`.

---

### POST /community/comments/{comment_id}/like/ `인증 필요`

```json
// Response 200
{ "is_liked": true, "likes_count": 2 }
```

---

## 은행 지도 (Banks)

### GET /banks/

전체 은행 목록.

### GET /banks/nearby/?lat={lat}&lng={lng}

카카오 Maps API를 통한 주변 은행 지점 검색. `radius` 파라미터로 검색 반경 지정 (기본 1000m).

```json
// Response 200
[
  {
    "name": "KB국민은행 강남지점", "address": "서울 강남구 테헤란로 123",
    "phone": "02-1234-5678", "lat": 37.4985, "lng": 127.0285, "distance": 350
  }
]
```

---

### GET /banks/route/ `인증 필요`

카카오 Mobility API 경로 안내. `origin_lat`, `origin_lng`, `dest_lat`, `dest_lng` 파라미터 필요.

```json
// Response 200
{ "duration": 8, "distance": 1200, "summary": "도보 약 8분 (1.2km)" }
```

---

## 뉴스 (News)

### GET /news/

금융 뉴스 목록 (최신순).

```json
// Response 200
[
  {
    "id": 55, "title": "한국은행, 기준금리 동결 결정",
    "url": "https://news.example.com/article",
    "publisher": "연합뉴스", "published_at": "2026-07-04T09:00:00+09:00"
  }
]
```

---

### GET /news/{news_id}/

### GET /news/briefing/

AI 주간 브리핑. 매주 월요일 09:00 자동 생성.

```json
// Response 200
{
  "id": 12, "week_start": "2026-06-30",
  "economy_summary": "이번 주 국내 증시는 반도체 섹터 강세로...",
  "tip": "ISA 계좌를 활용하면 이자·배당 소득에서 최대 200만원까지 비과세...",
  "created_at": "2026-06-30T09:00:00+09:00"
}
```

---

### POST /news/briefing/generate/ `관리자 전용`

브리핑 즉시 생성. 스케줄 외 수동 트리거용.

### GET /news/import/ `관리자 전용`

RSS 피드 수집. `startDate`, `endDate` 파라미터 (YYYYMMDD 형식).

```json
// Response 200
{ "created": 45, "updated": 12, "skipped": 8, "errors": [] }
```

---

## 원자재 (Commodities)

### GET /commodities/

금·은 시세 전체 이력.

### GET /commodities/summary/

최신 시세 요약.

```json
// Response 200
{
  "gold": { "price": 2340.50, "change_rate": 0.82, "recorded_at": "2026-07-04T15:00:00+09:00" },
  "silver": { "price": 29.15, "change_rate": -0.34, "recorded_at": "2026-07-04T15:00:00+09:00" }
}
```

---

### POST /commodities/import/ `관리자 전용`

시세 데이터 수집.

---

## 저축 플래너 (Planner)

### POST /planner/ `인증 필요`

```json
// Request
{ "goal_amount": 10000000, "monthly_savings": 500000, "months": 24 }

// Response 200
{
  "goal_amount": 10000000, "monthly_savings": 500000, "months": 24,
  "best_rate": 3.8, "total_principal": 12000000, "total_interest": 456000,
  "maturity_amount": 12456000,
  "achievable": true, "shortfall": 0,
  "required_monthly": null,
  "months_needed": null,
  "monthly_data": [
    { "month": 1, "principal": 500000, "total": 500950 },
    { "month": 2, "principal": 1000000, "total": 1003800 }
  ],
  "recommended_products": [
    {
      "product_id": 10, "product_name": "KB국민 스타 정기예금",
      "bank_name": "KB국민은행", "product_type": "deposit",
      "rate": 3.8, "term": 24, "maturity_amount": 12456000, "estimated_interest": 456000
    }
  ]
}
```

목표 달성이 안 되는 경우 `achievable: false`, `shortfall`에 부족액, `required_monthly`에 필요 월납입액, `months_needed`에 필요 기간이 들어옵니다.

오류: `400` 숫자 형식 오류(`"올바른 숫자를 입력해주세요."`) / 0 이하 값

---

## AI 챗봇 (Chat)

### POST /chat/

비로그인 사용자도 사용 가능합니다. `history`는 최근 6턴까지만 반영됩니다.

```json
// Request
{
  "message": "ISA 계좌가 뭔가요?",
  "history": [
    { "role": "user", "content": "안녕하세요" },
    { "role": "assistant", "content": "안녕하세요! 금융 상담을 도와드릴게요." }
  ]
}

// Response 200
{
  "reply": "ISA(개인종합자산관리계좌)는 예금, 펀드, 주식을 하나의 계좌에서 관리하고 이자·배당 소득에 대해 최대 200만원까지 비과세 혜택을 받을 수 있는 계좌입니다."
}
```

오류: `400` message 누락(`"메시지를 입력해주세요."`)
