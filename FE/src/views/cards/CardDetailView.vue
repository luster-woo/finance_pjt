<template>
  <div class="page-bg">
    <div class="container">
      <button class="back-btn" @click="router.back()">← 목록으로</button>

      <p v-if="loading" class="status">불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <!-- 카드 헤더 -->
        <div class="hero-card">
          <div class="badges">
            <span class="badge badge-company">{{ card.company }}</span>
            <span class="badge badge-type">{{ card.card_type }}카드</span>
          </div>
          <h1 class="card-title">{{ card.card_name }}</h1>
          <div class="stats-row">
            <div class="stat">
              <span class="stat-label">연회비</span>
              <span class="stat-value">{{ card.annual_fee === 0 ? '없음' : formatMoney(card.annual_fee) + '원' }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat">
              <span class="stat-label">전월실적</span>
              <span class="stat-value">{{ card.min_performance ? formatMoney(card.min_performance) + '원' : '조건 없음' }}</span>
            </div>
          </div>
        </div>

        <!-- 주요 혜택 -->
        <section class="section">
          <h2 class="section-title">주요 혜택</h2>
          <div class="benefits-grid">
            <div v-for="b in benefits" :key="b.id" class="benefit-card">
              <span class="benefit-tag">{{ b.benefit_category }}</span>
              <p class="benefit-detail">{{ b.benefit_detail }}</p>
            </div>
            <p v-if="!benefits.length" class="empty">등록된 혜택 정보가 없습니다.</p>
          </div>
        </section>

        <!-- 리뷰 -->
        <section class="section">
          <h2 class="section-title">리뷰 <span class="count-badge">{{ reviews.length }}</span></h2>

          <div v-if="!isLoggedIn" class="login-hint">
            <RouterLink to="/login">로그인</RouterLink> 후 리뷰를 작성할 수 있습니다.
          </div>
          <form v-else class="review-form" @submit.prevent="submit">
            <div class="rating-row">
              <span class="rating-label">별점</span>
              <div class="stars">
                <button
                  v-for="n in 5"
                  :key="n"
                  type="button"
                  class="star-btn"
                  :class="{ on: n <= form.rating }"
                  @click="form.rating = n"
                >★</button>
              </div>
            </div>
            <textarea v-model.trim="form.content" required placeholder="사용 후기를 남겨주세요"></textarea>
            <button type="submit" class="submit-btn">등록하기</button>
          </form>

          <div class="review-list">
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
            </div>
            <p v-if="!reviews.length" class="empty">등록된 리뷰가 없습니다.</p>
          </div>
        </section>
      </template>
    </div>

    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="{ 'toast-error': toast.isError }">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const isLoggedIn = computed(() => !!localStorage.getItem('accessToken'))
const formatDate = v => v ? new Date(v).toLocaleDateString('ko-KR') : '-'

const route = useRoute()
const router = useRouter()
const card = ref({})
const benefits = ref([])
const reviews = ref([])
const loading = ref(true)
const error = ref('')
const form = ref({ rating: 5, content: '' })
const toast = ref({ show: false, msg: '', isError: false })
let toastTimer = null

function showToast(msg, isError = false) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, msg, isError }
  toastTimer = setTimeout(() => { toast.value.show = false }, 2500)
}

const formatMoney = v => Number(v || 0).toLocaleString()

async function load() {
  try {
    const [a, b, c] = await Promise.all([
      api.get(`/cards/${route.params.id}/`),
      api.get(`/cards/${route.params.id}/benefits/`),
      api.get(`/cards/${route.params.id}/reviews/`),
    ])
    card.value = a.data
    benefits.value = b.data
    reviews.value = c.data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function submit() {
  try {
    const { data } = await api.post(`/cards/${route.params.id}/reviews/`, form.value)
    reviews.value.unshift(data)
    form.value = { rating: 5, content: '' }
    showToast('리뷰가 등록되었습니다.')
  } catch (e) {
    showToast(getErrorMessage(e, '리뷰 등록에 실패했습니다.'), true)
  }
}

async function deleteReview(id) {
  try {
    await api.delete(`/reviews/cards/${id}/`)
    reviews.value = reviews.value.filter(r => r.id !== id)
    showToast('리뷰가 삭제됐습니다.')
  } catch (e) {
    showToast(getErrorMessage(e, '삭제에 실패했습니다.'), true)
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
.badges { display: flex; gap: 8px; margin-bottom: 14px; }
.badge { padding: 5px 12px; border-radius: 20px; font-size: .78rem; font-weight: 700; }
.badge-company { background: #eef3ff; color: #0046ff; }
.badge-type { background: #f0faf6; color: #00a984; }
.card-title { margin: 0 0 24px; font-size: 1.7rem; letter-spacing: -.03em; color: #191f2b; font-weight: 800; }

.stats-row {
  display: flex; align-items: center; gap: 0;
  background: #f7f8fb; border-radius: 14px; overflow: hidden;
}
.stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 18px 16px; }
.stat-label { font-size: .78rem; color: #98a2b3; font-weight: 600; letter-spacing: .04em; }
.stat-value { font-size: 1.15rem; font-weight: 800; color: #191f2b; }
.stat-divider { width: 1px; height: 40px; background: #e7eaf0; }

/* 섹션 공통 */
.section { background: white; border: 1px solid #e7eaf0; border-radius: 22px; padding: 28px 32px; margin-bottom: 20px; box-shadow: 0 5px 18px rgba(28,39,65,.045); }
.section-title { margin: 0 0 20px; font-size: 1.1rem; font-weight: 800; color: #191f2b; display: flex; align-items: center; gap: 10px; }
.login-hint { padding: 14px; background: #fafbfc; border-radius: 12px; border: 1px solid #e7eaf0; color: #616b7d; font-size: .9rem; margin-bottom: 16px; }
.login-hint a { color: #0046ff; font-weight: 700; }
.count-badge { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; background: #eef3ff; color: #0046ff; font-size: .75rem; font-weight: 800; }

/* 혜택 그리드 */
.benefits-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.benefit-card { padding: 16px 18px; border: 1px solid #edf0f5; border-radius: 14px; background: #fafbfc; }
.benefit-tag { display: inline-block; padding: 3px 10px; border-radius: 8px; background: #eef3ff; color: #0046ff; font-size: .72rem; font-weight: 700; margin-bottom: 8px; }
.benefit-detail { margin: 0; font-size: .88rem; color: #364153; line-height: 1.5; }

/* 리뷰 폼 */
.review-form { background: #f7f8fb; border-radius: 14px; padding: 20px; margin-bottom: 24px; display: flex; flex-direction: column; gap: 14px; }
.rating-row { display: flex; align-items: center; gap: 12px; }
.rating-label { font-size: .88rem; color: #616b7d; font-weight: 600; }
.stars { display: flex; gap: 4px; }
.star-btn { background: none; border: none; font-size: 1.5rem; color: #d8deea; cursor: pointer; padding: 0; transition: color .1s, transform .1s; line-height: 1; }
.star-btn.on { color: #f5a623; }
.star-btn:hover { transform: scale(1.15); }
.review-form textarea {
  width: 100%; min-height: 88px; padding: 13px 14px;
  border: 1px solid #e7eaf0; border-radius: 10px;
  font-size: .92rem; color: #364153; background: white;
  resize: vertical; box-sizing: border-box; font-family: inherit;
  outline: none; transition: border-color .15s;
}
.review-form textarea:focus { border-color: #0046ff; }
.submit-btn {
  align-self: flex-end; padding: 11px 24px;
  background: #0046ff; color: white;
  border: none; border-radius: 10px;
  font-size: .9rem; font-weight: 700; cursor: pointer;
  transition: background .15s, transform .15s;
}
.submit-btn:hover { background: #0036cc; transform: translateY(-1px); }

/* 리뷰 목록 */
.review-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 16px; }
.review-item { padding: 18px; border: 1px solid #edf0f5; border-radius: 14px; }
.review-stars { display: flex; gap: 3px; }
.star { font-size: 1rem; color: #d8deea; }
.star.on { color: #f5a623; }
.review-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.review-author { font-size: .82rem; font-weight: 700; color: #364153; }
.review-date { font-size: .75rem; color: #98a2b3; margin-left: 2px; }
.del-review-btn {
  margin-left: auto; padding: 3px 10px; border: 1px solid #fca5a5; border-radius: 6px;
  background: #fff5f5; color: #dc2626; font-size: .75rem; cursor: pointer;
}
.review-content { margin: 0; font-size: .9rem; color: #364153; line-height: 1.6; }
.empty { text-align: center; padding: 36px 0; color: #98a2b3; font-size: .9rem; }
.mine { border-color: #c9d7ff !important; background: #f5f8ff !important; }
.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }
.toast { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); padding: 13px 24px; border-radius: 12px; background: #191f2b; color: white; font-size: .9rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,.18); white-space: nowrap; z-index: 9999; pointer-events: none; }
.toast-error { background: #c62828; }
.toast-enter-active { transition: opacity .2s ease, transform .2s ease; }
.toast-leave-active { transition: opacity .3s ease, transform .3s ease; }
.toast-enter-from { opacity: 0; transform: translate(-50%, 12px); }
.toast-leave-to { opacity: 0; transform: translate(-50%, 8px); }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .hero-card, .section { padding: 22px 20px; }
  .card-title { font-size: 1.4rem; }
  .benefits-grid { grid-template-columns: 1fr; }
}
</style>
