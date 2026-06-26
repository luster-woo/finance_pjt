<template>
  <div class="page-bg">
    <div class="container">
      <p v-if="loading" class="status">마이페이지를 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <!-- 프로필 헤더 -->
        <div class="profile-card">
          <div class="profile-main">
            <div class="avatar-wrap">
              <img v-if="profile.profile_image" :src="profile.profile_image" alt="프로필 사진" class="avatar" />
              <div v-else class="avatar avatar-placeholder">
                {{ (profile.nickname || profile.username || '?')[0].toUpperCase() }}
              </div>
            </div>
            <div class="profile-info">
              <div class="profile-name-row">
                <h1 class="profile-name">{{ profile.nickname || profile.username }}</h1>
                <span v-if="profile.financial_type" class="type-badge">{{ profile.financial_type }}</span>
              </div>
              <p class="profile-email">{{ profile.email }}</p>
              <p v-if="profile.bio" class="profile-bio">{{ profile.bio }}</p>
            </div>
          </div>

          <div class="profile-actions">
            <RouterLink to="/mypage/edit" class="edit-btn">내 정보 수정</RouterLink>
            <RouterLink to="/test/result" class="test-result-btn" v-if="profile.financial_type">
              📊 금융성향 결과 보기
            </RouterLink>
            <RouterLink to="/test" class="test-result-btn test-new-btn" v-else>
              📊 금융성향 검사하기
            </RouterLink>
          </div>

          <div class="stats-row">
            <div class="stat">
              <span class="stat-num">{{ profile.subscriptions_count ?? 0 }}</span>
              <span class="stat-label">가입상품</span>
            </div>
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-num">{{ profile.favorites_count ?? 0 }}</span>
              <span class="stat-label">관심상품</span>
            </div>
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-num">{{ profile.stock_favorites_count ?? 0 }}</span>
              <span class="stat-label">관심종목</span>
            </div>
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-num">{{ (profile.product_reviews_count ?? 0) + (profile.card_reviews_count ?? 0) }}</span>
              <span class="stat-label">작성 리뷰</span>
            </div>
          </div>
        </div>

        <!-- 탭 네비게이션 -->
        <nav class="tab-nav">
          <button
            v-for="item in tabs"
            :key="item.value"
            class="tab-btn"
            :class="{ active: tab === item.value }"
            @click="changeTab(item.value)"
          >{{ item.label }}</button>
        </nav>

        <!-- 탭 콘텐츠 -->
        <div class="tab-stage">
          <Transition :name="tabTransition">
            <section :key="tab" class="tab-panel">

              <!-- 금융상품 탭 -->
              <template v-if="tab === 'products'">
                <div v-for="sec in productSections" :key="sec.title" class="section-wrap">
                  <div class="section-header">
                    <h2 class="section-title">{{ sec.title }}</h2>
                    <span class="section-count">{{ sec.items.length }}개</span>
                  </div>
                  <div v-if="sec.items.length" class="product-list">
                    <div
                      v-for="item in sec.items"
                      :key="item.id"
                      class="product-row"
                    >
                      <RouterLink :to="`/products/${item.id}`" class="product-row-link">
                        <div class="product-row-info">
                          <span class="product-row-bank">{{ item.bank_name }}</span>
                          <strong class="product-row-name">{{ item.product_name }}</strong>
                        </div>
                        <span class="product-row-date">{{ formatDate(item[sec.dateKey]) }}</span>
                      </RouterLink>
                      <button class="del-btn" @click.stop="sec.onDelete(item.id)" title="삭제">✕</button>
                    </div>
                  </div>
                  <p v-else class="empty">{{ sec.empty }}</p>
                </div>
              </template>

              <!-- 가입 상품 금리 차트 -->
              <div v-if="tab === 'products' && subscriptions.length" class="rate-chart-card">
                <div class="section-header">
                  <h2 class="section-title">가입 상품 금리 비교</h2>
                  <span class="section-count">기준금리 / 최고금리 (%)</span>
                </div>
                <div class="rate-chart-wrap">
                  <canvas ref="rateChartCanvas" style="width:100%;"></canvas>
                </div>
              </div>

              <!-- 주식 탭 -->
              <template v-else-if="tab === 'stocks'">
                <div class="section-header">
                  <h2 class="section-title">관심 종목</h2>
                  <span class="section-count">{{ stocks.length }}개</span>
                </div>
                <div v-if="stocks.length" class="stock-grid">
                  <div v-for="s in stocks" :key="s.id" class="stock-card-wrap">
                    <RouterLink :to="`/stocks/${s.id}`" class="stock-card">
                      <span class="stock-code">{{ s.stock_code }}</span>
                      <strong class="stock-name">{{ s.stock_name }}</strong>
                      <span class="stock-date">{{ formatDate(s.created_at) }}</span>
                    </RouterLink>
                    <button class="del-btn del-btn-stock" @click="deleteStock(s.id)" title="삭제">✕</button>
                  </div>
                </div>
                <p v-else class="empty">관심 종목이 없습니다.</p>
              </template>

              <!-- 커뮤니티 탭 -->
              <template v-else-if="tab === 'community'">
                <div class="section-wrap">
                  <div class="section-header">
                    <h2 class="section-title">내가 쓴 게시글</h2>
                    <span class="section-count">{{ community.posts.length }}개</span>
                  </div>
                  <div v-if="community.posts.length" class="review-list">
                    <RouterLink
                      v-for="p in community.posts"
                      :key="p.id"
                      :to="p.stock ? `/stocks/${p.stock}` : '#'"
                      class="review-card"
                    >
                      <p class="review-content">{{ p.content }}</p>
                      <span class="review-date">♥ {{ p.likes_count }} · {{ formatDate(p.created_at) }}</span>
                    </RouterLink>
                  </div>
                  <p v-else class="empty">작성한 게시글이 없습니다.</p>
                </div>
                <div class="section-wrap">
                  <div class="section-header">
                    <h2 class="section-title">내가 쓴 댓글</h2>
                    <span class="section-count">{{ community.comments.length }}개</span>
                  </div>
                  <div v-if="community.comments.length" class="review-list">
                    <div v-for="c in community.comments" :key="c.id" class="review-card">
                      <p class="review-content">{{ c.content }}</p>
                      <span class="review-date">♥ {{ c.likes_count }} · {{ formatDate(c.created_at) }}</span>
                    </div>
                  </div>
                  <p v-else class="empty">작성한 댓글이 없습니다.</p>
                </div>
              </template>

              <!-- 리뷰 탭 -->
              <template v-else>
                <div class="section-wrap">
                  <div class="section-header">
                    <h2 class="section-title">상품 리뷰</h2>
                    <span class="section-count">{{ reviews.product_reviews?.length ?? 0 }}개</span>
                  </div>
                  <div v-if="reviews.product_reviews?.length" class="review-list">
                    <RouterLink
                      v-for="r in reviews.product_reviews"
                      :key="r.id"
                      :to="`/products/${r.product_id}`"
                      class="review-card"
                    >
                      <div class="review-stars">
                        <span v-for="n in 5" :key="n" class="star" :class="{ on: n <= r.rating }">★</span>
                      </div>
                      <p class="review-content">{{ r.content }}</p>
                      <span class="review-date">{{ formatDate(r.created_at) }}</span>
                    </RouterLink>
                  </div>
                  <p v-else class="empty">작성한 상품 리뷰가 없습니다.</p>
                </div>

                <div class="section-wrap">
                  <div class="section-header">
                    <h2 class="section-title">카드 리뷰</h2>
                    <span class="section-count">{{ reviews.card_reviews?.length ?? 0 }}개</span>
                  </div>
                  <div v-if="reviews.card_reviews?.length" class="review-list">
                    <RouterLink
                      v-for="r in reviews.card_reviews"
                      :key="r.id"
                      :to="`/cards/${r.card_id}`"
                      class="review-card"
                    >
                      <div class="review-stars">
                        <span v-for="n in 5" :key="n" class="star" :class="{ on: n <= r.rating }">★</span>
                      </div>
                      <p class="review-content">{{ r.content }}</p>
                      <span class="review-date">{{ formatDate(r.created_at) }}</span>
                    </RouterLink>
                  </div>
                  <p v-else class="empty">작성한 카드 리뷰가 없습니다.</p>
                </div>
              </template>

            </section>
          </Transition>
        </div>
      </template>
    </div>

    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="{ 'toast-error': toast.isError }">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const profile = ref({})
const subscriptions = ref([])
const favorites = ref([])
const recent = ref([])
const stocks = ref([])
const reviews = ref({ product_reviews: [], card_reviews: [] })
const community = ref({ posts: [], comments: [] })
const loading = ref(true)
const error = ref('')
const tab = ref('products')
const toast = ref({ show: false, msg: '', isError: false })
let toastTimer = null
function showToast(msg, isError = false) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, msg, isError }
  toastTimer = setTimeout(() => { toast.value.show = false }, 2500)
}
const tabDirection = ref('forward')
const rateChartCanvas = ref(null)
let rateChartInstance = null

const tabs = [
  { value: 'products',  label: '금융상품' },
  { value: 'stocks',    label: '주식' },
  { value: 'reviews',   label: '리뷰' },
  { value: 'community', label: '커뮤니티' },
]

const tabTransition = computed(() =>
  tabDirection.value === 'backward' ? 'tab-backward' : 'tab-forward'
)

const productSections = computed(() => [
  { title: '가입 상품',    items: subscriptions.value, dateKey: 'subscribed_at', empty: '가입한 상품이 없습니다.', onDelete: deleteSubscription },
  { title: '관심 상품',    items: favorites.value,     dateKey: 'created_at',    empty: '관심 상품이 없습니다.',  onDelete: deleteFavorite },
  { title: '최근 본 상품', items: recent.value,        dateKey: 'viewed_at',     empty: '최근 본 상품이 없습니다.', onDelete: deleteRecent },
])

function changeTab(value) {
  const cur = tabs.findIndex(t => t.value === tab.value)
  const next = tabs.findIndex(t => t.value === value)
  tabDirection.value = next < cur ? 'backward' : 'forward'
  tab.value = value
}

function buildRateChart() {
  if (!rateChartCanvas.value || !subscriptions.value.length) return
  const items = subscriptions.value.filter(s => s.interest_rate != null || s.max_interest_rate != null)
  if (!items.length) return
  if (rateChartInstance) { rateChartInstance.destroy(); rateChartInstance = null }
  const labels = items.map(s => s.product_name.length > 10 ? s.product_name.slice(0, 10) + '…' : s.product_name)
  const baseRates = items.map(s => s.interest_rate ?? 0)
  const maxRates = items.map(s => s.max_interest_rate ?? 0)
  const canvas = rateChartCanvas.value
  const w = canvas.parentElement?.clientWidth || 700
  canvas.width = Math.max(w - 40, 300)
  canvas.height = Math.max(items.length * 50 + 60, 200)
  rateChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: '기본금리', data: baseRates, backgroundColor: 'rgba(0,70,255,0.55)', borderRadius: 5 },
        { label: '최고금리', data: maxRates, backgroundColor: 'rgba(0,169,132,0.55)', borderRadius: 5 },
      ],
    },
    options: {
      responsive: false,
      indexAxis: 'y',
      plugins: {
        legend: { position: 'top', labels: { font: { size: 12 } } },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}%` } },
      },
      scales: {
        x: { ticks: { callback: v => v + '%', font: { size: 11 } }, grid: { color: '#f0f2f6' } },
        y: { ticks: { font: { size: 11 }, color: '#364153' }, grid: { display: false } },
      },
    },
  })
}

// canvas가 실제로 DOM에 마운트될 때 차트 빌드 (v-if 중첩으로 nextTick 한 번으론 부족)
watch(rateChartCanvas, (canvas) => {
  if (canvas) buildRateChart()
})

// 탭 전환 시에도 재빌드
watch(tab, async (newTab) => {
  if (newTab === 'products') {
    await nextTick()
    if (rateChartCanvas.value) buildRateChart()
  }
})

const formatDate = v => v ? new Date(v).toLocaleDateString('ko-KR') : '-'

async function deleteFavorite(id) {
  try {
    await api.post(`/products/${id}/favorite/`)
    favorites.value = favorites.value.filter(i => i.id !== id)
    profile.value.favorites_count = Math.max(0, (profile.value.favorites_count ?? 0) - 1)
    showToast('관심 상품에서 제거했습니다.')
  } catch { showToast('삭제에 실패했습니다.', true) }
}
async function deleteSubscription(id) {
  try {
    await api.post(`/products/${id}/subscribe/`)
    subscriptions.value = subscriptions.value.filter(i => i.id !== id)
    profile.value.subscriptions_count = Math.max(0, (profile.value.subscriptions_count ?? 0) - 1)
    showToast('가입 상품에서 제거했습니다.')
  } catch { showToast('삭제에 실패했습니다.', true) }
}
async function deleteRecent(id) {
  try {
    await api.delete(`/products/${id}/recent/`)
    recent.value = recent.value.filter(i => i.id !== id)
    showToast('최근 본 상품에서 제거했습니다.')
  } catch { showToast('삭제에 실패했습니다.', true) }
}
async function deleteStock(id) {
  try {
    await api.post(`/stocks/${id}/favorite/`)
    stocks.value = stocks.value.filter(s => s.id !== id)
    profile.value.stock_favorites_count = Math.max(0, (profile.value.stock_favorites_count ?? 0) - 1)
    showToast('관심 종목에서 제거했습니다.')
  } catch { showToast('삭제에 실패했습니다.', true) }
}

onMounted(async () => {
  try {
    const [a, b, c, d, e, f, g] = await Promise.all([
      api.get('/mypage/'),
      api.get('/mypage/products/subscriptions/'),
      api.get('/mypage/products/favorites/'),
      api.get('/mypage/products/recent/'),
      api.get('/mypage/stocks/favorites/'),
      api.get('/mypage/reviews/'),
      api.get('/mypage/community/'),
    ])
    profile.value       = a.data
    subscriptions.value = b.data
    favorites.value     = c.data
    recent.value        = d.data
    stocks.value        = e.data
    reviews.value       = f.data
    community.value     = g.data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

/* 프로필 카드 */
.profile-card {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 24px; padding: 32px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
  margin-bottom: 24px; position: relative;
}
.profile-main { display: flex; align-items: center; gap: 22px; margin-bottom: 28px; }

.avatar-wrap { flex: 0 0 auto; }
.avatar {
  width: 80px; height: 80px; border-radius: 50%;
  object-fit: cover; border: 3px solid #eef3ff;
}
.avatar-placeholder {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, #0046ff, #0036cc);
  color: white; font-size: 2rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}

.profile-info { flex: 1; min-width: 0; }
.profile-name-row { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 6px; }
.profile-name { margin: 0; font-size: 1.45rem; font-weight: 800; color: #191f2b; letter-spacing: -.025em; }
.type-badge { padding: 4px 12px; border-radius: 20px; background: #eef3ff; color: #0046ff; font-size: .75rem; font-weight: 700; white-space: nowrap; }
.profile-email { margin: 0 0 4px; font-size: .88rem; color: #98a2b3; }
.profile-bio { margin: 0; font-size: .88rem; color: #616b7d; line-height: 1.5; }

.profile-actions {
  position: absolute; top: 28px; right: 28px;
  display: flex; flex-direction: column; gap: 8px; align-items: flex-end;
}
.edit-btn {
  padding: 8px 16px; border: 1px solid #e7eaf0; border-radius: 10px;
  background: white; color: #616b7d; font-size: .82rem; font-weight: 700;
  text-decoration: none; transition: box-shadow .15s;
}
.edit-btn:hover { box-shadow: 0 3px 10px rgba(0,0,0,.07); }
.test-result-btn {
  padding: 8px 16px; border: 1px solid #c9d7ff; border-radius: 10px;
  background: #eef3ff; color: #0046ff; font-size: .82rem; font-weight: 700;
  text-decoration: none; white-space: nowrap; transition: box-shadow .15s;
}
.test-result-btn:hover { box-shadow: 0 3px 10px rgba(0,70,255,.15); }
.test-new-btn { background: #f0faf6; border-color: #b8eedd; color: #00a984; }

/* 통계 행 */
.stats-row {
  display: flex; align-items: center;
  background: #f7f8fb; border-radius: 14px; overflow: hidden;
  border: 1px solid #edf0f5;
}
.stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 16px 12px; }
.stat-num { font-size: 1.35rem; font-weight: 800; color: #191f2b; }
.stat-label { font-size: .72rem; color: #98a2b3; font-weight: 600; letter-spacing: .03em; }
.stat-div { width: 1px; height: 36px; background: #e7eaf0; flex: 0 0 auto; }

/* 탭 네비게이션 */
.tab-nav { display: flex; gap: 8px; margin-bottom: 20px; }
.tab-btn {
  padding: 10px 22px; border: 1px solid #e7eaf0; border-radius: 20px;
  background: white; color: #616b7d; font-size: .9rem; font-weight: 600;
  cursor: pointer; transition: all .18s ease;
}
.tab-btn:hover { border-color: #0046ff; color: #0046ff; }
.tab-btn.active { background: #0046ff; border-color: #0046ff; color: white; }

/* 탭 스테이지 */
.tab-stage { min-height: 360px; position: relative; overflow: hidden; }
.tab-panel { width: 100%; }

/* 금리 차트 */
.rate-chart-card {
  background: white; border: 1px solid #e7eaf0; border-radius: 16px;
  padding: 20px 22px; margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(28,39,65,.03);
}
.rate-chart-wrap { width: 100%; overflow-x: auto; }

/* 섹션 공통 */
.section-wrap { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.section-title { margin: 0; font-size: 1rem; font-weight: 800; color: #191f2b; }
.section-count { padding: 2px 10px; border-radius: 20px; background: #eef3ff; color: #0046ff; font-size: .75rem; font-weight: 700; }

/* 금융상품 목록 */
.product-list { background: white; border: 1px solid #e7eaf0; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 10px rgba(28,39,65,.03); }
.product-row {
  display: flex; align-items: center;
  border-bottom: 1px solid #f0f2f6;
  transition: background .14s;
}
.product-row:last-child { border-bottom: none; }
.product-row:hover { background: #fafbff; }
.product-row-link {
  flex: 1; display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; text-decoration: none; color: inherit; min-width: 0;
}
.product-row-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.product-row-bank { font-size: .75rem; color: #98a2b3; font-weight: 600; }
.product-row-name { font-size: .95rem; font-weight: 700; color: #191f2b; }
.product-row-date { font-size: .78rem; color: #c4c9d4; white-space: nowrap; margin-left: 12px; flex: 0 0 auto; }

/* 삭제 버튼 */
.del-btn {
  flex: 0 0 auto; width: 32px; height: 32px; margin-right: 12px;
  border: none; border-radius: 8px; background: transparent;
  color: #c4c9d4; font-size: .8rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background .15s, color .15s;
}
.del-btn:hover { background: #fff0f0; color: #e53e3e; }

/* 주식 그리드 */
.stock-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
.stock-card-wrap { position: relative; }
.stock-card {
  padding: 18px; background: white; border: 1px solid #e7eaf0;
  border-radius: 16px; text-decoration: none; color: inherit;
  display: flex; flex-direction: column; gap: 6px;
  box-shadow: 0 2px 10px rgba(28,39,65,.03);
  transition: border-color .15s, box-shadow .15s, transform .15s;
}
.stock-card:hover { border-color: #c9d7ff; box-shadow: 0 5px 16px rgba(0,70,255,.09); transform: translateY(-2px); }
.stock-code { font-size: .72rem; color: #0046ff; font-weight: 700; letter-spacing: .05em; }
.stock-name { font-size: .95rem; font-weight: 800; color: #191f2b; }
.stock-date { font-size: .75rem; color: #c4c9d4; margin-top: 4px; }
.del-btn-stock {
  position: absolute; top: 8px; right: 8px;
  width: 24px; height: 24px; margin: 0;
  font-size: .7rem; border-radius: 6px;
  opacity: 0; transition: opacity .15s, background .15s, color .15s;
}
.stock-card-wrap:hover .del-btn-stock { opacity: 1; }

/* 리뷰 */
.review-list { display: flex; flex-direction: column; gap: 10px; }
.review-card {
  padding: 18px 20px; background: white; border: 1px solid #e7eaf0;
  border-radius: 16px; text-decoration: none; color: inherit;
  box-shadow: 0 2px 10px rgba(28,39,65,.03);
  transition: border-color .15s, box-shadow .15s;
  display: block;
}
.review-card:hover { border-color: #c9d7ff; box-shadow: 0 4px 14px rgba(0,70,255,.07); }
.review-stars { display: flex; gap: 2px; margin-bottom: 8px; }
.star { font-size: .95rem; color: #d8deea; }
.star.on { color: #f5a623; }
.review-content { margin: 0 0 8px; font-size: .88rem; color: #364153; line-height: 1.55; }
.review-date { font-size: .75rem; color: #c4c9d4; }

.empty { color: #98a2b3; font-size: .88rem; padding: 28px 0; text-align: center; }
.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

/* 탭 트랜지션 */
.tab-forward-enter-active, .tab-forward-leave-active,
.tab-backward-enter-active, .tab-backward-leave-active { transition: opacity 210ms ease, transform 210ms ease; }
.tab-forward-leave-active, .tab-backward-leave-active { position: absolute; inset: 0; }
.tab-forward-enter-from { opacity: 0; transform: translateX(14px); }
.tab-forward-leave-to { opacity: 0; transform: translateX(-14px); }
.tab-backward-enter-from { opacity: 0; transform: translateX(-14px); }
.tab-backward-leave-to { opacity: 0; transform: translateX(14px); }

@media (prefers-reduced-motion: reduce) {
  .tab-forward-enter-active, .tab-forward-leave-active,
  .tab-backward-enter-active, .tab-backward-leave-active { transition: none; }
  .tab-forward-enter-from, .tab-forward-leave-to,
  .tab-backward-enter-from, .tab-backward-leave-to { transform: none; }
}
@media (max-width: 600px) {
  .page-bg { padding: 20px 14px 60px; }
  .profile-card { padding: 22px 18px; }
  .edit-btn { position: static; margin-bottom: 20px; display: inline-block; }
  .profile-main { gap: 16px; }
  .avatar, .avatar-placeholder { width: 64px; height: 64px; font-size: 1.5rem; }
  .stats-row { flex-wrap: wrap; }
  .stock-grid { grid-template-columns: 1fr 1fr; }
}

.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%);
  background: #191f2b; color: white; padding: 12px 24px; border-radius: 12px;
  font-size: .9rem; font-weight: 600; z-index: 9999;
  box-shadow: 0 6px 20px rgba(0,0,0,.18); white-space: nowrap;
}
.toast-error { background: #d14343; }
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }
</style>
