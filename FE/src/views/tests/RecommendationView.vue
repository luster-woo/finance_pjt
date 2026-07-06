<template>
  <div class="page-bg">
    <div class="container">
      <p v-if="loading" class="status">AI 추천 결과를 분석하는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <!-- 결과 헤더 -->
        <div class="result-header">
          <div class="result-badge">금융성향 분석 결과</div>
          <h1 class="result-type">{{ result.result_type }}</h1>
          <p class="result-desc">{{ result.description }}</p>

          <!-- MBTI 스타일 4축 바 -->
          <div class="axes-card" v-if="result.axes">
            <div class="axis-row" v-for="ax in axesList" :key="ax.key">
              <span class="axis-letter" :class="result.axes[ax.key] < 50 ? 'letter-active' : 'letter-dim'">{{ ax.loL }}</span>
              <span class="axis-label lo">{{ ax.lo }}</span>
              <div class="axis-track">
                <div class="axis-fill" :class="ax.key" :style="{ width: result.axes[ax.key] + '%' }"></div>
                <div class="axis-marker" :style="{ left: result.axes[ax.key] + '%' }"></div>
              </div>
              <span class="axis-label hi">{{ ax.hi }}</span>
              <span class="axis-letter" :class="result.axes[ax.key] >= 50 ? 'letter-active' : 'letter-dim'">{{ ax.hiL }}</span>
              <span class="axis-pct" :class="result.axes[ax.key] >= 50 ? 'hi-color' : 'lo-color'">
                {{ dominantPct(result.axes[ax.key]) }}%
              </span>
            </div>
            <p class="axis-code">유형 코드: <strong>{{ result.axes.code }}</strong></p>
          </div>
        </div>

        <p v-if="recLoading" class="rec-loading">🤖 AI가 맞춤 상품을 분석하는 중입니다...</p>
        <p v-if="recError" class="rec-error">{{ recError }}</p>

        <!-- 추천 금융상품 -->
        <section v-if="!recLoading" class="rec-section">
          <div class="section-header">
            <span class="section-eyebrow product-color">PRODUCT</span>
            <h2 class="section-title">추천 금융상품</h2>
          </div>
          <div class="rec-grid">
            <RouterLink
              v-for="(item, idx) in products"
              :key="item.id"
              :to="item.product_id ? `/products/${item.product_id}` : '#'"
              class="rec-card product-card"
            >
              <span class="rank-badge">{{ idx + 1 }}위</span>
              <div class="rec-card-header">
                <span class="rec-institution">{{ item.bank_name }}</span>
                <span class="rec-score product-score">{{ item.score }}점</span>
              </div>
              <h3 class="rec-name">{{ item.product_name }}</h3>
              <p class="rec-reason">{{ item.reason }}</p>
            </RouterLink>
            <div v-if="!products.length" class="empty-card">
              <span>추천할 금융상품 데이터가 없습니다.</span>
            </div>
          </div>
        </section>

        <!-- 추천 카드 -->
        <section v-if="!recLoading" class="rec-section">
          <div class="section-header">
            <span class="section-eyebrow card-color">CARD</span>
            <h2 class="section-title">추천 카드</h2>
          </div>
          <div class="rec-grid">
            <RouterLink
              v-for="(item, idx) in cards"
              :key="item.id"
              :to="`/cards/${item.id}`"
              class="rec-card card-item"
            >
              <span class="rank-badge card-rank">{{ idx + 1 }}위</span>
              <div class="rec-card-header">
                <span class="rec-institution">{{ item.company }} · {{ item.card_type }}카드</span>
                <span class="rec-score card-score">{{ item.score }}점</span>
              </div>
              <h3 class="rec-name">{{ item.card_name }}</h3>
              <p class="rec-reason">{{ item.reason }}</p>
            </RouterLink>
            <div v-if="!cards.length" class="empty-card">
              <span>추천할 카드 데이터가 없습니다.</span>
            </div>
          </div>
        </section>

        <!-- 추천 주식 -->
        <section v-if="!recLoading" class="rec-section">
          <div class="section-header">
            <span class="section-eyebrow stock-color">STOCK</span>
            <h2 class="section-title">추천 주식</h2>
          </div>
          <div class="rec-grid">
            <RouterLink
              v-for="(item, idx) in stocks"
              :key="item.id"
              :to="item.stock_id ? `/stocks/${item.stock_id}` : '#'"
              class="rec-card stock-item"
            >
              <span class="rank-badge stock-rank">{{ idx + 1 }}위</span>
              <div class="rec-card-header">
                <span class="rec-institution">{{ item.stock_code }}</span>
                <span class="rec-score stock-score">{{ item.score }}점</span>
              </div>
              <h3 class="rec-name">{{ item.stock_name }}</h3>
              <p class="rec-reason">{{ item.reason }}</p>
            </RouterLink>
            <div v-if="!stocks.length" class="empty-card">
              <span>추천할 주식 데이터가 없습니다.</span>
            </div>
          </div>
        </section>

        <!-- 비슷한 사용자 통계 -->
        <section v-if="!recLoading && stats" class="stats-section">
          <h2 class="stats-title">📊 비슷한 사용자들의 선택</h2>
          <div class="stats-grid">

            <!-- 같은 성향 인기 카드 -->
            <div class="stats-card" v-if="stats.similar_type_cards?.length">
              <p class="stats-subtitle">{{ stats.my_type }} 사람들이 많이 쓰는 카드</p>
              <div v-for="item in stats.similar_type_cards" :key="item.card_id" class="stat-bar-row">
                <span class="stat-label">{{ item.card_name }}</span>
                <div class="stat-bar-wrap">
                  <div class="stat-bar card-bar" :style="{ width: item.pct + '%' }"></div>
                </div>
                <span class="stat-pct">{{ item.pct }}%</span>
              </div>
            </div>

            <!-- 비슷한 나이/금액대 인기 금융상품 -->
            <div class="stats-card" v-if="stats.similar_age_products?.length">
              <p class="stats-subtitle">비슷한 나이·금액대가 많이 가입한 상품</p>
              <div v-for="item in stats.similar_age_products" :key="item.product_id" class="stat-bar-row">
                <span class="stat-label">{{ item.bank_name }} {{ item.product_type === 'deposit' ? '예금' : '적금' }}</span>
                <div class="stat-bar-wrap">
                  <div class="stat-bar product-bar" :style="{ width: item.pct + '%' }"></div>
                </div>
                <span class="stat-pct">{{ item.pct }}%</span>
              </div>
            </div>

            <!-- 같은 성향 인기 주식 -->
            <div class="stats-card" v-if="stats.similar_type_stocks?.length">
              <p class="stats-subtitle">{{ stats.my_type }} 사람들이 많이 담은 주식</p>
              <div v-for="item in stats.similar_type_stocks" :key="item.stock_id" class="stat-bar-row">
                <span class="stat-label">{{ item.stock_name }}</span>
                <div class="stat-bar-wrap">
                  <div class="stat-bar stock-bar" :style="{ width: item.pct + '%' }"></div>
                </div>
                <span class="stat-pct">{{ item.pct }}%</span>
              </div>
            </div>

          </div>
        </section>

        <div v-if="!recLoading" class="actions">
          <RouterLink to="/test" class="action-btn secondary">다시 검사하기</RouterLink>
          <RouterLink to="/mypage" class="action-btn primary">마이페이지</RouterLink>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, getErrorMessage } from '@/api'

const result = ref({})
const products = ref([])
const cards = ref([])
const stocks = ref([])
const stats = ref(null)
const loading = ref(true)
const recLoading = ref(false)
const error = ref('')
const recError = ref('')

const axesList = [
  { key: 'risk',     lo: '안전형', hi: '공격형', loL: 'S', hiL: 'A' },
  { key: 'rational', lo: '감정형', hi: '이성형', loL: 'E', hiL: 'R' },
  { key: 'longterm', lo: '단기형', hi: '장기형', loL: 'T', hiL: 'L' },
  { key: 'active',   lo: '수동형', hi: '능동형', loL: 'P', hiL: 'N' },
]

function dominantPct(val) {
  return val >= 50 ? val : 100 - val
}

onMounted(async () => {
  // 1단계: 테스트 결과만 먼저 빠르게 표시
  try {
    result.value = (await api.get('/tests/result/')).data
  } catch (e) {
    error.value = getErrorMessage(e, '결과를 불러오지 못했습니다.')
    loading.value = false
    return
  }
  loading.value = false

  // 2단계: 추천 결과는 별도 로딩 (AI 호출 시간이 걸려도 결과 화면은 이미 보임)
  recLoading.value = true
  try {
    const byScore = arr => [...arr].sort((a, b) => b.score - a.score).slice(0, 3)
    const [productRes, cardRes, stockRes] = await Promise.all([
      api.get('/tests/recommendations/products/'),
      api.get('/tests/recommendations/cards/'),
      api.get('/tests/recommendations/stocks/'),
    ])
    products.value = byScore(productRes.data)
    cards.value = byScore(cardRes.data)
    stocks.value = byScore(stockRes.data)
  } catch (e) {
    recError.value = getErrorMessage(e, '추천 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.')
  } finally {
    recLoading.value = false
  }

  // 비슷한 사용자 통계 (별도 로딩)
  api.get('/tests/stats/similar-users/').then(r => { stats.value = r.data }).catch(() => {})
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 1200px; margin: 0 auto; }

/* 결과 헤더 */
.result-header {
  text-align: center;
  padding: 44px 40px 36px;
  background: linear-gradient(135deg, #edf3ff 0%, #f0fbf7 100%);
  border: 1px solid #e4edff;
  border-radius: 28px;
  margin-bottom: 36px;
  box-shadow: 0 6px 24px rgba(0,70,255,.07);
}
.result-badge {
  display: inline-block; padding: 5px 14px; margin-bottom: 14px;
  background: rgba(0,70,255,.1); color: #0046ff;
  border-radius: 20px; font-size: .8rem; font-weight: 800; letter-spacing: .06em;
}
.result-type { margin: 0 0 14px; font-size: 2.2rem; font-weight: 800; color: #191f2b; letter-spacing: -.04em; }
.result-desc { margin: 0 0 28px; color: #606a7a; font-size: .98rem; line-height: 1.7; max-width: 560px; margin-left: auto; margin-right: auto; }

/* MBTI 스타일 축 */
.axes-card {
  background: white; border: 1px solid #e7eaf0; border-radius: 20px;
  padding: 24px 28px; max-width: 560px; margin: 0 auto;
  box-shadow: 0 3px 14px rgba(28,39,65,.05);
  text-align: left;
}
.axis-row {
  display: grid;
  grid-template-columns: 22px 68px 1fr 68px 22px 56px;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.axis-row:last-of-type { margin-bottom: 0; }
.axis-letter {
  font-size: .85rem; font-weight: 900; text-align: center; letter-spacing: -.01em;
}
.axis-letter.letter-active { color: #191f2b; }
.axis-letter.letter-dim { color: #d0d5dd; }
.axis-label {
  font-size: .8rem; font-weight: 700; color: #98a2b3; white-space: nowrap;
}
.axis-label.lo { text-align: right; }
.axis-label.hi { text-align: left; }

.axis-track {
  position: relative; height: 10px;
  background: #edf0f5; border-radius: 5px; overflow: visible;
}
.axis-fill {
  height: 100%; border-radius: 5px;
  transition: width .6s ease;
}
.axis-fill.risk     { background: #93b4f8; }
.axis-fill.rational { background: #f9c784; }
.axis-fill.longterm { background: #7dd8c0; }
.axis-fill.active   { background: #c4a8e8; }

.axis-marker {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  width: 16px; height: 16px; border-radius: 50%;
  background: white; border: 2.5px solid #364153;
  box-shadow: 0 2px 6px rgba(0,0,0,.15);
  transition: left .6s ease;
}

.axis-pct { font-size: .82rem; font-weight: 800; white-space: nowrap; }
.hi-color { color: #0046ff; }
.lo-color { color: #e53e3e; }

.axis-code {
  margin: 16px 0 0; padding-top: 14px; border-top: 1px solid #f0f2f6;
  text-align: center; font-size: .82rem; color: #98a2b3;
}
.axis-code strong { color: #191f2b; font-size: .9rem; letter-spacing: .1em; }

/* 섹션 */
.rec-section { margin-bottom: 36px; }
.section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.section-eyebrow {
  font-size: .72rem; font-weight: 800; letter-spacing: .12em;
  padding: 4px 10px; border-radius: 8px;
}
.product-color { background: #eef3ff; color: #0046ff; }
.card-color { background: #f0faf6; color: #00a984; }
.stock-color { background: #f5f0ff; color: #7b4dce; }
.section-title { margin: 0; font-size: 1.2rem; font-weight: 800; color: #191f2b; }

.rec-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; align-items: stretch; }

.rec-card {
  position: relative; display: flex; flex-direction: column; padding: 20px 18px;
  background: white; border: 1px solid #e7eaf0;
  border-radius: 16px; text-decoration: none; color: inherit;
  box-shadow: 0 3px 14px rgba(28,39,65,.045);
  transition: transform .18s, box-shadow .18s, border-color .18s;
  overflow: hidden;
}
.rec-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(28,39,65,.1); }
.product-card:hover { border-color: #c9d7ff; }
.card-item:hover { border-color: #b8eedd; }
.stock-item:hover { border-color: #d4c4f5; }

.rank-badge {
  position: absolute; top: 14px; right: 14px;
  padding: 3px 9px; border-radius: 8px;
  font-size: .7rem; font-weight: 800;
  background: #eef3ff; color: #0046ff;
}
.card-rank { background: #f0faf6; color: #00a984; }
.stock-rank { background: #f5f0ff; color: #7b4dce; }

.rec-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; padding-right: 36px; }
.rec-institution { font-size: .78rem; color: #98a2b3; font-weight: 600; }
.rec-score { font-size: .78rem; font-weight: 700; }
.product-score { color: #0046ff; }
.card-score { color: #00a984; }
.stock-score { color: #7b4dce; }

.rec-name { margin: 0 0 8px; font-size: 1rem; font-weight: 800; color: #191f2b; line-height: 1.35; }
.rec-reason { margin: 0; font-size: .84rem; color: #697386; line-height: 1.5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.empty-card {
  grid-column: 1 / -1; padding: 40px; text-align: center;
  background: #fafbfc; border: 1px dashed #e7eaf0; border-radius: 16px;
  color: #98a2b3; font-size: .9rem;
}

.actions { display: flex; gap: 12px; justify-content: center; margin-top: 44px; }
.action-btn {
  padding: 13px 28px; border-radius: 12px;
  font-size: .95rem; font-weight: 700; text-decoration: none;
  transition: transform .15s, box-shadow .15s;
}
.action-btn:hover { transform: translateY(-2px); }
.action-btn.primary { background: #0046ff; color: white; box-shadow: 0 6px 18px rgba(0,70,255,.2); }
.action-btn.secondary { background: #f0f2f7; color: #364153; }

.rec-loading { text-align: center; padding: 40px; color: #0046ff; font-size: .95rem; font-weight: 600; }
.rec-error { text-align: center; padding: 16px 20px; margin-bottom: 24px; background: #fff5f5; border: 1px solid #fed7d7; border-radius: 12px; color: #c62828; font-size: .9rem; }
/* 비슷한 사용자 통계 */
.stats-section { margin-bottom: 36px; }
.stats-title { margin: 0 0 16px; font-size: 1.15rem; font-weight: 800; color: #191f2b; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.stats-card {
  background: white; border: 1px solid #e7eaf0; border-radius: 18px; padding: 20px;
  box-shadow: 0 3px 12px rgba(28,39,65,.045);
}
.stats-subtitle { margin: 0 0 14px; font-size: .8rem; font-weight: 700; color: #98a2b3; }
.stat-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.stat-label { font-size: .78rem; color: #364153; font-weight: 600; flex: 0 0 90px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat-bar-wrap { flex: 1; height: 8px; background: #f0f2f6; border-radius: 4px; overflow: hidden; }
.stat-bar { height: 100%; border-radius: 4px; transition: width .6s ease; }
.card-bar    { background: #00a984; }
.product-bar { background: #0046ff; }
.stock-bar   { background: #7b4dce; }
.stat-pct { font-size: .78rem; font-weight: 800; color: #616b7d; flex: 0 0 32px; text-align: right; }

.status { text-align: center; padding: 80px 20px; color: #98a2b3; }
.error { color: #c62828; }

@media (max-width: 820px) {
  .rec-grid { grid-template-columns: 1fr; }
  .result-header { padding: 36px 24px; }
  .result-type { font-size: 1.7rem; }
  .axis-row { grid-template-columns: 60px 1fr 60px 70px; }
}
</style>
