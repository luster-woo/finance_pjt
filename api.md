# 👤 1. Accounts API (회원 관리)

| Method | URL                | 설명      |
| ------ | ------------------ | ------- |
| POST   | /accounts/signup/  | 회원가입    |
| POST   | /accounts/login/   | 로그인     |
| POST   | /accounts/logout/  | 로그아웃    |
| GET    | /accounts/profile/ | 내 정보 조회 |
| PUT    | /accounts/profile/ | 내 정보 수정 |

---

# 📝 2. Financial Test & AI API (성향 테스트 및 추천)

| Method | URL                              | 설명           |
| ------ | -------------------------------- | ------------ |
| POST   | /tests/                          | 금융 성향 테스트 제출 |
| GET    | /tests/result/                   | 금융 성향 결과 조회  |
| GET    | /tests/recommendations/products/ | AI 예적금 추천 조회 |
| GET    | /tests/recommendations/stocks/   | AI 주식 추천 조회  |

---

# 🏦 3. Financial Products API (예적금)

| Method | URL                                                   | 설명         |
| ------ | ----------------------------------------------------- | ---------- |
| GET    | /products/                                            | 전체 금융상품 조회 |
| GET    | /products/[int:product_id](int:product_id)/           | 상품 상세 조회   |
| POST   | /products/[int:product_id](int:product_id)/favorite/  | 관심상품 등록/취소 |
| POST   | /products/[int:product_id](int:product_id)/subscribe/ | 가입상품 등록/취소 |
| POST   | /products/[int:product_id](int:product_id)/recent/    | 최근 본 상품 기록 |

---

# ❤️ 4. Favorite & Subscription API

| Method | URL                             | 설명         |
| ------ | ------------------------------- | ---------- |
| GET    | /mypage/products/favorites/     | 관심 상품 조회   |
| GET    | /mypage/products/subscriptions/ | 가입 상품 조회   |
| GET    | /mypage/products/recent/        | 최근 본 상품 조회 |

---

# ✍️ 5. Product Review API

| Method | URL                                                 | 설명    |
| ------ | --------------------------------------------------- | ----- |
| GET    | /products/[int:product_id](int:product_id)/reviews/ | 리뷰 조회 |
| POST   | /products/[int:product_id](int:product_id)/reviews/ | 리뷰 작성 |
| PUT    | /reviews/products/[int:review_id](int:review_id)/   | 리뷰 수정 |
| DELETE | /reviews/products/[int:review_id](int:review_id)/   | 리뷰 삭제 |


# 💳 6. Card API

| Method | URL                                         | 설명       |
| ------ | ------------------------------------------- | -------- |
| GET    | /cards/                                     | 전체 카드 조회 |
| GET    | /cards/[int:card_id](int:card_id)/          | 카드 상세 조회 |
| GET    | /cards/[int:card_id](int:card_id)/benefits/ | 카드 혜택 조회 |

---

# ✍️ 7. Card Review API

| Method | URL                                            | 설명       |
| ------ | ---------------------------------------------- | -------- |
| GET    | /cards/[int:card_id](int:card_id)/reviews/     | 카드 리뷰 조회 |
| POST   | /cards/[int:card_id](int:card_id)/reviews/     | 카드 리뷰 작성 |
| PUT    | /reviews/cards/[int:review_id](int:review_id)/ | 카드 리뷰 수정 |
| DELETE | /reviews/cards/[int:review_id](int:review_id)/ | 카드 리뷰 삭제 |

---

# 📈 8. Stock API

| Method | URL                                                | 설명          |
| ------ | -------------------------------------------------- | ----------- |
| GET    | /stocks/                                           | 전체 종목 조회    |
| GET    | /stocks/[int:stock_id](int:stock_id)/              | 종목 상세 조회    |
| GET    | /stocks/[int:stock_id](int:stock_id)/latest-price/ | 최신 시세 조회    |
| GET    | /stocks/[int:stock_id](int:stock_id)/prices/       | 시세 이력 조회    |
| POST   | /stocks/[int:stock_id](int:stock_id)/favorite/     | 관심 종목 등록/취소 |

---

# ⭐ 9. Favorite Stock API

| Method | URL                       | 설명       |
| ------ | ------------------------- | -------- |
| GET    | /mypage/stocks/favorites/ | 관심 종목 조회 |

---

# 💬 10. Community API

| Method | URL                                               | 설명        |
| ------ | ------------------------------------------------- | --------- |
| GET    | /community/posts/                                 | 전체 게시글 조회 |
| POST   | /community/posts/                                 | 게시글 작성    |
| GET    | /community/posts/[int:post_id](int:post_id)/      | 게시글 상세 조회 |
| PUT    | /community/posts/[int:post_id](int:post_id)/      | 게시글 수정    |
| DELETE | /community/posts/[int:post_id](int:post_id)/      | 게시글 삭제    |
| POST   | /community/posts/[int:post_id](int:post_id)/like/ | 좋아요 등록/취소 |


# 💭 11. Comment API

| Method | URL                                                   | 설명    |
| ------ | ----------------------------------------------------- | ----- |
| GET    | /community/posts/[int:post_id](int:post_id)/comments/ | 댓글 조회 |
| POST   | /community/posts/[int:post_id](int:post_id)/comments/ | 댓글 작성 |
| PUT    | /community/comments/[int:comment_id](int:comment_id)/ | 댓글 수정 |
| DELETE | /community/comments/[int:comment_id](int:comment_id)/ | 댓글 삭제 |

---

# 🏢 12. Bank API

| Method | URL                                | 설명       |
| ------ | ---------------------------------- | -------- |
| GET    | /banks/                            | 은행 목록 조회 |
| GET    | /banks/nearby/?lat={lat}&lng={lng} | 주변 은행 조회 |

---

# 📰 13. News API

| Method | URL                               | 설명          |
| ------ | --------------------------------- | ----------- |
| GET    | /news/                            | 금융 뉴스 목록 조회 |
| GET    | /news/[int:news_id](int:news_id)/ | 금융 뉴스 상세 조회 |

---

# 🪙 14. Commodity API

| Method | URL           | 설명        |
| ------ | ------------- | --------- |
| GET    | /commodities/ | 원자재 시세 조회 |

---

# 🗂️ 15. MyPage API

| Method | URL                             | 설명              |
| ------ | ------------------------------- | --------------- |
| GET    | /mypage/                        | 마이페이지 정보 조회     |
| GET    | /mypage/products/favorites/     | 관심 상품 조회        |
| GET    | /mypage/products/subscriptions/ | 가입 상품 조회        |
| GET    | /mypage/products/recent/        | 최근 본 상품 조회      |
| GET    | /mypage/stocks/favorites/       | 관심 종목 조회        |
| GET    | /mypage/reviews/                | 내가 작성한 리뷰 조회    |
| GET    | /mypage/test-result/            | 금융 성향 테스트 결과 조회 |
