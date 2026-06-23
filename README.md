API Specification

1. Accounts API (회원 관리)

회원가입

* Method: POST
* URL: /accounts/signup/

로그인

* Method: POST
* URL: /accounts/login/

로그아웃

* Method: POST
* URL: /accounts/logout/

내 정보 조회

* Method: GET
* URL: /accounts/profile/

내 정보 수정

* Method: PUT
* URL: /accounts/profile/

---

2. Financial Test & AI API (성향 테스트 및 추천)

금융 성향 테스트 제출

* Method: POST
* URL: /tests/

금융 성향 결과 조회

* Method: GET
* URL: /tests/result/

AI 예적금 추천 조회

* Method: GET
* URL: /tests/recommendations/products/

AI 주식 추천 조회

* Method: GET
* URL: /tests/recommendations/stocks/

---

3. Financial Products API (예적금)

전체 금융상품 조회

* Method: GET
* URL: /products/

금융상품 상세 조회

* Method: GET
* URL: /products/[int:product_id](int:product_id)/

관심상품 등록/취소

* Method: POST
* URL: /products/[int:product_id](int:product_id)/favorite/

가입상품 등록/취소

* Method: POST
* URL: /products/[int:product_id](int:product_id)/subscribe/

최근 본 상품 기록

* Method: POST
* URL: /products/[int:product_id](int:product_id)/recent/

---

4. Favorite & Subscription API

관심 상품 조회

* Method: GET
* URL: /mypage/products/favorites/

가입 상품 조회

* Method: GET
* URL: /mypage/products/subscriptions/

최근 본 상품 조회

* Method: GET
* URL: /mypage/products/recent/

---

5. Product Review API

리뷰 조회

* Method: GET
* URL: /products/[int:product_id](int:product_id)/reviews/

리뷰 작성

* Method: POST
* URL: /products/[int:product_id](int:product_id)/reviews/

리뷰 수정

* Method: PUT
* URL: /reviews/products/[int:review_id](int:review_id)/

리뷰 삭제

* Method: DELETE
* URL: /reviews/products/[int:review_id](int:review_id)/

---

6. Card API

전체 카드 조회

* Method: GET
* URL: /cards/

카드 상세 조회

* Method: GET
* URL: /cards/[int:card_id](int:card_id)/

카드 혜택 조회

* Method: GET
* URL: /cards/[int:card_id](int:card_id)/benefits/

---

7. Card Review API

카드 리뷰 조회

* Method: GET
* URL: /cards/[int:card_id](int:card_id)/reviews/

카드 리뷰 작성

* Method: POST
* URL: /cards/[int:card_id](int:card_id)/reviews/

카드 리뷰 수정

* Method: PUT
* URL: /reviews/cards/[int:review_id](int:review_id)/

카드 리뷰 삭제

* Method: DELETE
* URL: /reviews/cards/[int:review_id](int:review_id)/

---

8. Stock API

전체 종목 조회

* Method: GET
* URL: /stocks/

종목 상세 조회

* Method: GET
* URL: /stocks/[int:stock_id](int:stock_id)/

최신 시세 조회

* Method: GET
* URL: /stocks/[int:stock_id](int:stock_id)/latest-price/

시세 이력 조회

* Method: GET
* URL: /stocks/[int:stock_id](int:stock_id)/prices/

관심 종목 등록/취소

* Method: POST
* URL: /stocks/[int:stock_id](int:stock_id)/favorite/

---

9. Favorite Stock API

관심 종목 조회

* Method: GET
* URL: /mypage/stocks/favorites/

---

10. Community API

전체 게시글 조회

* Method: GET
* URL: /community/posts/

게시글 작성

* Method: POST
* URL: /community/posts/

게시글 상세 조회

* Method: GET
* URL: /community/posts/[int:post_id](int:post_id)/

게시글 수정

* Method: PUT
* URL: /community/posts/[int:post_id](int:post_id)/

게시글 삭제

* Method: DELETE
* URL: /community/posts/[int:post_id](int:post_id)/

좋아요 등록/취소

* Method: POST
* URL: /community/posts/[int:post_id](int:post_id)/like/

---

11. Comment API

댓글 조회

* Method: GET
* URL: /community/posts/[int:post_id](int:post_id)/comments/

댓글 작성

* Method: POST
* URL: /community/posts/[int:post_id](int:post_id)/comments/

댓글 수정

* Method: PUT
* URL: /community/comments/[int:comment_id](int:comment_id)/

댓글 삭제

* Method: DELETE
* URL: /community/comments/[int:comment_id](int:comment_id)/
