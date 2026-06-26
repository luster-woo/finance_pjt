<template>
  <div class="page-bg">
    <div class="container">
      <button class="back-btn" @click="router.back()">← 목록으로</button>

      <p v-if="loading" class="status">불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <article v-else-if="product">
        <!-- 상품 헤더 -->
        <div class="hero-card">
          <div class="badges">
            <span class="badge badge-bank">{{ product.bank_name }}</span>
            <span class="badge" :class="product.product_type === 'deposit' ? 'badge-deposit' : 'badge-saving'">
              {{ product.product_type === 'deposit' ? '예금' : '적금' }}
            </span>
          </div>
          <h1 class="product-title">{{ product.product_name }}</h1>
          <p class="product-desc">{{ product.description || '상품 설명이 없습니다.' }}</p>

          <div class="action-row">
            <button class="action-btn btn-fav" :class="{ active: isFav }" @click="toggle('favorite')">
              <span class="btn-icon">{{ isFav ? '★' : '☆' }}</span>
              {{ isFav ? '관심 등록됨' : '관심상품' }}
            </button>
            <button class="action-btn btn-sub" :class="{ active: isSub }" @click="toggle('subscribe')">
              <span class="btn-icon">{{ isSub ? '✓' : '+' }}</span>
              {{ isSub ? '가입 등록됨' : '가입상품' }}
            </button>
          </div>
        </div>

        <!-- 가입 정보 -->
        <section class="section">
          <h2 class="section-title">가입 정보</h2>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">가입 대상</span>
              <span class="info-value">{{ product.target_user || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">가입 방법</span>
              <span class="info-value">{{ product.join_way || '-' }}</span>
            </div>
          </div>
        </section>

        <!-- 금리 정보 -->
        <section class="section">
          <h2 class="section-title">금리 정보</h2>
          <div v-if="product.options?.length" class="rate-list">
            <div v-for="option in product.options" :key="option.id" class="rate-row">
              <div class="rate-term">
                <span class="term-number">{{ option.save_trm }}</span>
                <span class="term-unit">개월</span>
              </div>
              <div class="rate-values">
                <div class="rate-item">
                  <span class="rate-label">기본금리</span>
                  <span class="rate-value">{{ option.interest_rate ?? '-' }}<small>%</small></span>
                </div>
                <div class="rate-divider"></div>
                <div class="rate-item highlight">
                  <span class="rate-label">최고금리</span>
                  <span class="rate-value accent">{{ option.max_interest_rate ?? '-' }}<small>%</small></span>
                </div>
              </div>
            </div>
            <!-- 최고금리 우대 조건 -->
            <div v-if="product.special_condition" class="special-condition">
              <span class="condition-label">📋 최고금리 우대 조건</span>
              <p class="condition-text">{{ product.special_condition }}</p>
            </div>
          </div>
          <p v-else class="empty">등록된 금리 정보가 없습니다.</p>
        </section>

        <!-- 리뷰 섹션 -->
        <section class="section">
          <h2 class="section-title">리뷰 <span class="count-badge">{{ reviews.length }}</span></h2>

          <!-- 리뷰 작성 (로그인 필요) -->
          <div v-if="isLoggedIn && !myReview" class="review-form">
            <div class="star-row">
              <span
                v-for="n in 5" :key="n"
                class="star-btn"
                :class="{ on: n <= newReview.rating }"
                @click="newReview.rating = n"
              >★</span>
              <span class="star-count">{{ newReview.rating }}점</span>
            </div>
            <textarea v-model="newReview.content" class="review-textarea"
              placeholder="이 상품을 이용하신 경험을 공유해주세요." rows="3" maxlength="300"></textarea>
            <button class="submit-review-btn" @click="submitReview"
              :disabled="!newReview.content.trim() || newReview.rating === 0">
              리뷰 등록
            </button>
          </div>
          <div v-else-if="!isLoggedIn" class="login-hint">
            <RouterLink to="/login">로그인</RouterLink> 후 리뷰를 작성할 수 있습니다.
          </div>

          <!-- 리뷰 목록 -->
          <div v-if="reviews.length" class="review-list">
            <div v-for="r in reviews" :key="r.id" class="review-item" :class="{ mine: r.is_mine }">
              <div class="review-header">
                <div class="review-stars">
                  <span v-for="n in 5" :key="n" class="star" :class="{ on: n <= r.rating }">★</span>
                </div>
                <span class="review-author">{{ r.username || '익명' }}</span>
                <span class="review-date">{{ formatDate(r.created_at) }}</span>
                <button v-if="r.is_mine" class="del-review-btn" @click="deleteReview(r.id)">삭제</button>
              </div>
              <p class="review-content">{{ r.content }}</p>
              <div class="review-reactions">
                <button class="react-btn" :class="{ active: r.my_reaction === 'like' }" @click="reactReview(r, 'like')">
                  👍 도움돼요 {{ r.like_count ?? 0 }}
                </button>
                <button class="react-btn sad" :class="{ active: r.my_reaction === 'sad' }" @click="reactReview(r, 'sad')">
                  😢 아쉬워요 {{ r.sad_count ?? 0 }}
                </button>
              </div>
            </div>
          </div>
          <p v-else-if="!isLoggedIn || myReview || reviews.length === 0" class="empty">등록된 리뷰가 없습니다.</p>
        </section>
      </article>
    </div>

    <!-- 토스트 -->
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="{ 'toast-error': toast.isError }">
        {{ toast.msg }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const route = useRoute()
const router = useRouter()
const product = ref(null)
const loading = ref(true)
const error = ref('')
const isFav = ref(false)
const isSub = ref(false)
const toast = ref({ show: false, msg: '', isError: false })
let toastTimer = null

const reviews = ref([])
const newReview = ref({ rating: 5, content: '' })
const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))
const myReview = computed(() => reviews.value.find(r => r.is_mine))

const formatDate = v => v ? new Date(v).toLocaleDateString('ko-KR') : '-'

function showToast(msg, isError = false) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, msg, isError }
  toastTimer = setTimeout(() => { toast.value.show = false }, 2500)
}

async function loadReviews() {
  try {
    const { data } = await api.get(`/products/${route.params.id}/reviews/`)
    reviews.value = data
  } catch { /* 리뷰 없어도 무시 */ }
}

async function submitReview() {
  try {
    await api.post(`/products/${route.params.id}/reviews/`, {
      rating: newReview.value.rating,
      content: newReview.value.content,
    })
    newReview.value = { rating: 5, content: '' }
    showToast('리뷰가 등록됐습니다.')
    loadReviews()
  } catch (e) {
    showToast(getErrorMessage(e, '리뷰 등록에 실패했습니다.'), true)
  }
}

async function deleteReview(id) {
  try {
    await api.delete(`/reviews/products/${id}/`)
    showToast('리뷰가 삭제됐습니다.')
    loadReviews()
  } catch (e) {
    showToast(getErrorMessage(e, '삭제에 실패했습니다.'), true)
  }
}

async function reactReview(review, type) {
  try {
    const { data } = await api.post(`/reviews/products/${review.id}/react/`, { reaction_type: type })
    review.like_count = data.like_count
    review.sad_count = data.sad_count
    review.my_reaction = data.my_reaction
  } catch (e) {
    showToast(getErrorMessage(e, '로그인이 필요합니다.'), true)
  }
}

async function load() {
  try {
    const { data } = await api.get(`/products/${route.params.id}/`)
    product.value = data
    if (localStorage.getItem('token') || localStorage.getItem('accessToken')) {
      api.post(`/products/${route.params.id}/recent/`).catch(() => {})
      api.get(`/products/${route.params.id}/status/`)
        .then(({ data: s }) => {
          isFav.value = s.is_favorite
          isSub.value = s.is_subscribed
        })
        .catch(() => {})
    }
    loadReviews()
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function toggle(action) {
  try {
    const { data } = await api.post(`/products/${route.params.id}/${action}/`)
    if (action === 'favorite') {
      isFav.value = data.is_favorite
      showToast(isFav.value ? '관심상품에 추가했습니다.' : '관심상품에서 제거했습니다.')
    } else {
      isSub.value = data.is_subscribed
      showToast(isSub.value ? '가입상품으로 등록했습니다.' : '가입상품에서 제거했습니다.')
    }
  } catch (e) {
    showToast(getErrorMessage(e, '로그인이 필요합니다.'), true)
  }
}

onMounted(load)
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 720px; margin: 0 auto; }

.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 16px; margin-bottom: 28px;
  background: white; border: 1px solid #e7eaf0; border-radius: 10px;
  color: #616b7d; font-size: .9rem; font-weight: 600; cursor: pointer;
  transition: box-shadow .15s;
}
.back-btn:hover { box-shadow: 0 3px 10px rgba(0,0,0,.07); }

/* 헤더 카드 */
.hero-card {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 22px; padding: 32px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
  margin-bottom: 20px;
}
.badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.badge { padding: 5px 12px; border-radius: 20px; font-size: .78rem; font-weight: 700; }
.badge-bank { background: #f0f2f7; color: #364153; }
.badge-deposit { background: #eef3ff; color: #0046ff; }
.badge-saving { background: #f0faf6; color: #00a984; }

.product-title { margin: 0 0 10px; font-size: 1.75rem; letter-spacing: -.03em; color: #191f2b; font-weight: 800; line-height: 1.25; }
.product-desc { margin: 0 0 28px; font-size: .95rem; color: #616b7d; line-height: 1.7; }

.action-row { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 11px 22px; border-radius: 12px;
  font-size: .9rem; font-weight: 700; cursor: pointer;
  transition: transform .15s, box-shadow .15s, background .2s, border-color .2s, color .2s;
}
.action-btn:hover { transform: translateY(-2px); }
.btn-icon { font-size: 1rem; line-height: 1; }

/* 관심상품 버튼 */
.btn-fav { background: white; border: 1.5px solid #e7eaf0; color: #616b7d; }
.btn-fav:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); border-color: #f5a623; color: #f5a623; }
.btn-fav.active { background: #fff8eb; border-color: #f5a623; color: #d48800; }

/* 가입상품 버튼 */
.btn-sub { background: #0046ff; border: 1.5px solid transparent; color: white; box-shadow: 0 6px 16px rgba(0,70,255,.2); }
.btn-sub:hover { background: #0036cc; box-shadow: 0 8px 20px rgba(0,70,255,.28); }
.btn-sub.active { background: #00a984; border-color: transparent; box-shadow: 0 6px 16px rgba(0,169,132,.25); }

/* 토스트 */
.toast {
  position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%);
  padding: 13px 24px; border-radius: 12px;
  background: #191f2b; color: white;
  font-size: .9rem; font-weight: 600;
  box-shadow: 0 8px 24px rgba(0,0,0,.18);
  white-space: nowrap; z-index: 9999;
  pointer-events: none;
}
.toast-error { background: #c62828; }
.toast-enter-active { transition: opacity .2s ease, transform .2s ease; }
.toast-leave-active { transition: opacity .3s ease, transform .3s ease; }
.toast-enter-from { opacity: 0; transform: translate(-50%, 12px); }
.toast-leave-to { opacity: 0; transform: translate(-50%, 8px); }

/* 섹션 공통 */
.section { background: white; border: 1px solid #e7eaf0; border-radius: 22px; padding: 28px 32px; margin-bottom: 20px; box-shadow: 0 5px 18px rgba(28,39,65,.045); }
.section-title { margin: 0 0 20px; font-size: 1.05rem; font-weight: 800; color: #191f2b; }

/* 가입 정보 */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { padding: 16px 18px; background: #f7f8fb; border-radius: 14px; }
.info-label { display: block; font-size: .75rem; color: #98a2b3; font-weight: 700; letter-spacing: .04em; margin-bottom: 6px; }
.info-value { font-size: .9rem; color: #364153; font-weight: 600; line-height: 1.5; }

/* 금리 정보 */
.rate-list { display: flex; flex-direction: column; gap: 10px; }
.rate-row {
  display: flex; align-items: center; gap: 20px;
  padding: 18px 22px; border: 1px solid #edf0f5;
  border-radius: 14px; background: #fafbfc;
  transition: border-color .15s, box-shadow .15s;
}
.rate-row:hover { border-color: #c9d7ff; box-shadow: 0 3px 12px rgba(0,70,255,.06); }

.rate-term { display: flex; align-items: baseline; gap: 3px; min-width: 64px; }
.term-number { font-size: 1.6rem; font-weight: 800; color: #191f2b; }
.term-unit { font-size: .8rem; color: #98a2b3; font-weight: 600; }

.rate-values { display: flex; align-items: center; gap: 20px; flex: 1; }
.rate-item { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.rate-label { font-size: .72rem; color: #98a2b3; font-weight: 700; letter-spacing: .03em; }
.rate-value { font-size: 1.2rem; font-weight: 800; color: #364153; }
.rate-value small { font-size: .65em; font-weight: 600; margin-left: 1px; }
.rate-value.accent { color: #0046ff; }
.rate-divider { width: 1px; height: 32px; background: #e7eaf0; }

.empty { color: #98a2b3; font-size: .9rem; text-align: center; padding: 24px 0; }

/* 우대 조건 */
.special-condition {
  margin-top: 16px; padding: 14px 16px;
  background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px;
}
.condition-label { display: block; font-size: .8rem; font-weight: 700; color: #92400e; margin-bottom: 6px; }
.condition-text { margin: 0; font-size: .88rem; color: #78350f; line-height: 1.6; white-space: pre-wrap; }
.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

/* 리뷰 */
.review-form { background: #fafbfc; border: 1px solid #e7eaf0; border-radius: 14px; padding: 20px; margin-bottom: 20px; }
.star-row { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; }
.star-btn { font-size: 1.6rem; cursor: pointer; color: #e7eaf0; transition: color .12s; }
.star-btn.on { color: #f5a623; }
.star-count { font-size: .88rem; color: #616b7d; margin-left: 6px; font-weight: 600; }
.review-textarea {
  width: 100%; padding: 12px 14px; border: 1px solid #e7eaf0; border-radius: 10px;
  font-size: .92rem; color: #191f2b; resize: vertical; outline: none;
  font-family: inherit; box-sizing: border-box;
}
.review-textarea:focus { border-color: #0046ff; }
.submit-review-btn {
  margin-top: 10px; padding: 10px 22px; background: #0046ff; color: white;
  border: none; border-radius: 10px; font-size: .9rem; font-weight: 700; cursor: pointer;
}
.submit-review-btn:disabled { background: #c4d0f5; cursor: not-allowed; }
.login-hint { padding: 14px; background: #fafbfc; border-radius: 12px; border: 1px solid #e7eaf0; color: #616b7d; font-size: .9rem; margin-bottom: 16px; }
.login-hint a { color: #0046ff; font-weight: 700; }

.review-list { display: flex; flex-direction: column; gap: 14px; }
.review-item { padding: 16px 18px; border: 1px solid #edf0f5; border-radius: 14px; background: white; }
.review-item.mine { border-color: #c9d7ff; background: #fafcff; }
.review-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.review-stars .star { color: #e7eaf0; font-size: 1rem; }
.review-stars .star.on { color: #f5a623; }
.review-author { font-size: .82rem; font-weight: 700; color: #364153; }
.review-date { font-size: .78rem; color: #98a2b3; margin-left: auto; }
.del-review-btn {
  padding: 3px 10px; border: 1px solid #fca5a5; border-radius: 6px;
  background: #fff5f5; color: #dc2626; font-size: .75rem; cursor: pointer;
}
.review-content { margin: 0 0 8px; font-size: .9rem; color: #364153; line-height: 1.6; }
.review-reactions { display: flex; gap: 8px; }
.react-btn {
  padding: 4px 12px; border-radius: 16px; border: 1px solid #e7eaf0;
  background: white; font-size: .8rem; cursor: pointer; color: #616b7d; transition: all .15s;
}
.react-btn:hover { border-color: #0046ff; color: #0046ff; }
.react-btn.active { background: #eef3ff; border-color: #0046ff; color: #0046ff; font-weight: 700; }
.react-btn.sad:hover { border-color: #f59e0b; color: #f59e0b; }
.react-btn.sad.active { background: #fffbeb; border-color: #f59e0b; color: #d97706; font-weight: 700; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .hero-card, .section { padding: 22px 20px; }
  .product-title { font-size: 1.4rem; }
  .info-grid { grid-template-columns: 1fr; }
  .rate-row { gap: 14px; }
  .term-number { font-size: 1.3rem; }
}
</style>
