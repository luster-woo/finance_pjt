<template>
  <div class="page-bg">
    <div class="container">
      <button class="back-btn" @click="router.back()">← 목록으로</button>

      <p v-if="loading" class="status">불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <!-- 종목 헤더 카드 -->
        <div class="hero-card">
          <div class="hero-top">
            <div class="stock-avatar" :style="avatarStyle(stock.stock_name)">
              {{ stock.stock_name?.slice(0, 1) }}
            </div>
            <div class="stock-meta">
              <span class="stock-code-label">{{ stock.stock_code }}</span>
              <h1 class="stock-title">{{ stock.stock_name }}</h1>
            </div>
            <button
              class="fav-btn"
              :class="{ active: isFav }"
              @click="toggleFavorite"
            >
              {{ isFav ? '★ 관심 등록됨' : '☆ 관심 종목' }}
            </button>
          </div>

          <!-- 최신 시세 -->
          <div v-if="latest" class="price-section">
            <div class="price-main">
              <span class="price-value">{{ formatPrice(latest.price) }}원</span>
              <span class="price-change" :class="changeClass">
                {{ changeSign }}{{ Math.abs(latest.change_rate ?? 0).toFixed(2) }}%
              </span>
            </div>
            <span class="price-label">현재가 (최신 기준)</span>
          </div>
          <div v-else class="price-empty">시세 정보가 없습니다.</div>

          <p v-if="stock.description" class="stock-desc">{{ stock.description }}</p>
        </div>

        <!-- 가격 차트 -->
        <section v-if="priceHistory.length" class="section chart-section">
          <div class="chart-top">
            <div>
              <h2 class="section-title" style="margin:0 0 2px">가격 차트</h2>
              <p class="chart-sub">단위: 원</p>
            </div>
            <div class="chart-meta" v-if="chartStat.min">
              <span>최저 <strong>{{ formatPrice(chartStat.min) }}</strong></span>
              <span>최고 <strong>{{ formatPrice(chartStat.max) }}</strong></span>
            </div>
          </div>

          <div class="period-tabs">
            <button v-for="p in periods" :key="p.v" class="period-btn"
              :class="{ active: chartPeriod === p.v && !customRange }" @click="applyPeriod(p.v)">
              {{ p.label }}
            </button>
            <span class="period-divider">|</span>
            <input type="date" class="date-input" v-model="dateFrom" :max="dateTo || undefined" @change="applyCustomRange" />
            <span class="date-sep">~</span>
            <input type="date" class="date-input" v-model="dateTo" :min="dateFrom || undefined" @change="applyCustomRange" />
            <button v-if="customRange" class="period-btn date-reset" @click="resetDateRange">초기화</button>
          </div>

          <div class="chart-wrap" @click="chartMaximized = true">
            <div class="chart-canvas-box" ref="chartBox">
              <canvas ref="chartCanvas"></canvas>
            </div>
            <div class="chart-dates" v-if="chartDateRange.start">
              <span>{{ chartDateRange.start }}</span>
              <span>{{ chartDateRange.end }}</span>
            </div>
            <span class="enlarge-hint">클릭하여 확대 ↗</span>
          </div>
        </section>

        <!-- 차트 최대화 모달 -->
        <Teleport to="body">
          <div v-if="chartMaximized" class="chart-modal-overlay" @click.self="chartMaximized = false">
            <div class="chart-modal">
              <div class="chart-modal-header">
                <div>
                  <strong>{{ stock.stock_name }}</strong> 가격 차트
                </div>
                <div class="period-tabs" style="margin:0">
                  <button v-for="p in periods" :key="p.v" class="period-btn"
                    :class="{ active: chartPeriod === p.v && !customRange }" @click="applyPeriod(p.v)">
                    {{ p.label }}
                  </button>
                </div>
                <button class="chart-close" @click="chartMaximized = false">✕</button>
              </div>
              <canvas ref="chartCanvasLarge"></canvas>
            </div>
          </div>
        </Teleport>

        <!-- 가격 이력 -->
        <section v-if="priceHistory.length" class="section">
          <h2 class="section-title">시세 이력</h2>
          <div class="price-table">
            <div class="table-header">
              <span>날짜</span>
              <span>종가</span>
              <span>등락률</span>
              <span>거래량</span>
            </div>
            <div
              v-for="p in visibleHistory"
              :key="p.id"
              class="table-row"
            >
              <span class="date-cell">{{ formatDate(p.recorded_at) }}</span>
              <span class="price-cell">{{ formatPrice(p.price) }}원</span>
              <span class="rate-cell" :class="rateClass(p.change_rate)">
                {{ p.change_rate != null ? (p.change_rate >= 0 ? '+' : '') + Number(p.change_rate).toFixed(2) + '%' : '-' }}
              </span>
              <span class="vol-cell">{{ p.volume ? Number(p.volume).toLocaleString() : '-' }}</span>
            </div>
          </div>
          <button v-if="historyHasMore" class="more-btn" @click="loadMoreHistory">
            10개 더보기 ({{ priceHistory.length - historyLimit }}개 남음) ↓
          </button>
          <button v-if="historyIsAll" class="more-btn collapse-btn" @click="collapseHistory">
            접기 ↑
          </button>
        </section>

        <!-- 종목 관련 뉴스 -->
        <section v-if="stockNews.length" class="section">
          <h2 class="section-title">관련 뉴스</h2>
          <div class="news-list">
            <a
              v-for="news in visibleNews"
              :key="news.url || news.title"
              :href="news.url || '#'"
              target="_blank"
              rel="noopener noreferrer"
              class="news-item"
            >
              <div class="news-body">
                <h4 class="news-title">{{ news.title }}</h4>
                <p v-if="news.summary" class="news-summary">{{ news.summary }}</p>
                <div class="news-meta">
                  <span class="news-publisher">{{ news.publisher }}</span>
                  <span v-if="news.published_at" class="news-dot">·</span>
                  <span v-if="news.published_at" class="news-date">{{ formatDate(news.published_at) }}</span>
                </div>
              </div>
              <span class="news-arrow">↗</span>
            </a>
          </div>
          <button v-if="stockNews.length > 5 && !showAllNews" class="more-btn" @click="showAllNews = true">
            뉴스 더보기 ({{ stockNews.length - 5 }}개) ↓
          </button>
        </section>

        <!-- 비로그인 커뮤니티 유도 -->
        <div v-if="!isLoggedInUser" class="signup-prompt">
          <span>💬 종목 토론에 참여하려면</span>
          <RouterLink to="/login">로그인</RouterLink>
          또는
          <RouterLink to="/signup" class="signup-link">회원가입</RouterLink>
          이 필요합니다.
        </div>

        <!-- 토론 게시판 -->
        <section class="section">
          <StockDiscussionBoard :stock-id="String(route.params.id)" />
        </section>
      </template>
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
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import StockDiscussionBoard from '@/components/community/StockDiscussionBoard.vue'
import { api, getErrorMessage } from '@/api'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const route = useRoute()
const router = useRouter()

const stock = ref({})
const latest = ref(null)
const priceHistory = ref([])
const stockNews = ref([])
const loading = ref(true)
const error = ref('')
const isFav = ref(false)
const toast = ref({ show: false, msg: '', isError: false })
let toastTimer = null
const showAllNews = ref(false)
const historyLimit = ref(5)
const isLoggedInUser = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))
const visibleNews = computed(() => showAllNews.value ? stockNews.value : stockNews.value.slice(0, 5))
const visibleHistory = computed(() => priceHistory.value.slice(0, historyLimit.value))
const historyHasMore = computed(() => historyLimit.value < priceHistory.value.length)
const historyIsAll = computed(() => historyLimit.value >= priceHistory.value.length && priceHistory.value.length > 5)
function loadMoreHistory() { historyLimit.value = Math.min(historyLimit.value + 10, priceHistory.value.length) }
function collapseHistory() { historyLimit.value = 5 }
const chartCanvas = ref(null)
const chartCanvasLarge = ref(null)
const chartBox = ref(null)
const chartMaximized = ref(false)
const chartPeriod = ref('1m')
const dateFrom = ref('')
const dateTo = ref('')
const customRange = ref(false)
let chartInstance = null
let chartInstanceLarge = null

const periods = [
  { label: '1개월', v: '1m' },
  { label: '3개월', v: '3m' },
  { label: '6개월', v: '6m' },
  { label: '1년',   v: '1y' },
  { label: '전체',  v: 'all' },
]

function applyPeriod(v) {
  customRange.value = false
  dateFrom.value = ''
  dateTo.value = ''
  chartPeriod.value = v
}

function applyCustomRange() {
  if (dateFrom.value || dateTo.value) {
    customRange.value = true
    redrawCharts()
  }
}

function resetDateRange() {
  customRange.value = false
  dateFrom.value = ''
  dateTo.value = ''
  redrawCharts()
}

function filterByPeriod(prices, period) {
  if (customRange.value) {
    return prices.filter(p => {
      const d = new Date(p.recorded_at)
      if (dateFrom.value && d < new Date(dateFrom.value)) return false
      if (dateTo.value && d > new Date(dateTo.value + 'T23:59:59')) return false
      return true
    })
  }
  if (!prices.length || period === 'all') return prices
  const now = new Date()
  const cut = new Date(now)
  if (period === '1m') cut.setMonth(now.getMonth() - 1)
  else if (period === '3m') cut.setMonth(now.getMonth() - 3)
  else if (period === '6m') cut.setMonth(now.getMonth() - 6)
  else if (period === '1y') cut.setFullYear(now.getFullYear() - 1)
  return prices.filter(p => new Date(p.recorded_at) >= cut)
}

const chartStat = computed(() => {
  const filtered = filterByPeriod(
    [...priceHistory.value].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at)),
    chartPeriod.value
  )
  if (!filtered.length) return { min: null, max: null }
  const vals = filtered.map(p => Number(p.price))
  return { min: Math.min(...vals), max: Math.max(...vals) }
})

const chartDateRange = computed(() => {
  const filtered = filterByPeriod(
    [...priceHistory.value].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at)),
    chartPeriod.value
  )
  if (filtered.length < 2) return { start: '', end: '' }
  const fmt = d => new Date(d).toLocaleDateString('ko-KR', { year: 'numeric', month: 'numeric', day: 'numeric' })
  return { start: fmt(filtered[0].recorded_at), end: fmt(filtered[filtered.length - 1].recorded_at) }
})

function buildChart(canvas, prices, existing) {
  if (!canvas) return existing
  if (existing) { existing.destroy() }
  const isLarge = canvas === chartCanvasLarge.value
  // 레이아웃이 완료된 후의 실제 너비 사용, 없으면 고정값
  const section = canvas.closest('.section') || canvas.parentElement
  const w = section?.offsetWidth ? section.offsetWidth - 64 : (isLarge ? 820 : 760)
  const h = isLarge ? 360 : 180
  canvas.width  = Math.max(w, 300)
  canvas.height = h
  const sorted = filterByPeriod(
    [...prices].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at)),
    chartPeriod.value
  )
  if (!sorted.length) return null
  const labels = sorted.map(p => new Date(p.recorded_at).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' }))
  const data = sorted.map(p => Number(p.price))
  const isUp = data[data.length - 1] >= data[0]
  const color = isUp ? '#e53e3e' : '#0046ff'
  return new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data,
        borderColor: color,
        backgroundColor: isUp ? 'rgba(229,62,62,.06)' : 'rgba(0,70,255,.06)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: false,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${Number(ctx.raw).toLocaleString()}원` } }
      },
      scales: {
        x: { ticks: { maxTicksLimit: 7, font: { size: 11 }, color: '#98a2b3' }, grid: { display: false }, border: { display: false } },
        y: { ticks: { font: { size: 11 }, color: '#98a2b3', callback: v => Number(v).toLocaleString() }, grid: { color: '#f0f2f6' }, border: { display: false } }
      }
    }
  })
}

function redrawCharts() {
  requestAnimationFrame(() => {
    if (chartCanvas.value && priceHistory.value.length) {
      chartInstance = buildChart(chartCanvas.value, priceHistory.value, chartInstance)
    }
    if (chartMaximized.value && chartCanvasLarge.value && priceHistory.value.length) {
      chartInstanceLarge = buildChart(chartCanvasLarge.value, priceHistory.value, chartInstanceLarge)
    }
  })
}

watch(chartPeriod, redrawCharts)
watch(chartMaximized, async (val) => {
  if (val) {
    await nextTick()
    chartInstanceLarge = buildChart(chartCanvasLarge.value, priceHistory.value, chartInstanceLarge)
  } else {
    if (chartInstanceLarge) { chartInstanceLarge.destroy(); chartInstanceLarge = null }
  }
})

function showToast(msg, isError = false) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, msg, isError }
  toastTimer = setTimeout(() => { toast.value.show = false }, 2500)
}

const changeClass = computed(() => {
  const r = latest.value?.change_rate ?? 0
  return r > 0 ? 'up' : r < 0 ? 'down' : 'flat'
})
const changeSign = computed(() => {
  const r = latest.value?.change_rate ?? 0
  return r > 0 ? '▲ +' : r < 0 ? '▼ ' : ''
})

function rateClass(rate) {
  if (rate == null) return ''
  return rate > 0 ? 'up' : rate < 0 ? 'down' : 'flat'
}

const AVATAR_COLORS = [
  { bg: '#eef3ff', color: '#0046ff' },
  { bg: '#f0faf6', color: '#00a984' },
  { bg: '#fff8eb', color: '#c68400' },
  { bg: '#fdf0f8', color: '#c0339e' },
  { bg: '#f0f4ff', color: '#4c6ef5' },
]
function avatarStyle(name) {
  const idx = (name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length
  return { background: AVATAR_COLORS[idx].bg, color: AVATAR_COLORS[idx].color }
}

const formatPrice = v => v != null ? Number(v).toLocaleString() : '-'
const formatDate = v => v ? new Date(v).toLocaleDateString('ko-KR') : '-'

async function toggleFavorite() {
  try {
    const { data } = await api.post(`/stocks/${route.params.id}/favorite/`)
    isFav.value = data.is_favorite
    showToast(isFav.value ? '관심 종목에 추가했습니다.' : '관심 종목에서 제거했습니다.')
  } catch (e) {
    showToast(getErrorMessage(e, '로그인이 필요합니다.'), true)
  }
}

onMounted(async () => {
  try {
    const isLoggedIn = !!(localStorage.getItem('accessToken') || localStorage.getItem('token'))
    const [a, b, c, d, e] = await Promise.all([
      api.get(`/stocks/${route.params.id}/`),
      api.get(`/stocks/${route.params.id}/latest-price/`).catch(() => ({ data: null })),
      api.get(`/stocks/${route.params.id}/prices/`).catch(() => ({ data: [] })),
      api.get(`/stocks/${route.params.id}/news/`).catch(() => ({ data: [] })),
      isLoggedIn
        ? api.get(`/stocks/${route.params.id}/favorite/`).catch(() => ({ data: null }))
        : Promise.resolve({ data: null }),
    ])
    stock.value = a.data
    latest.value = b.data
    priceHistory.value = c.data
    stockNews.value = d.data
    if (e.data) isFav.value = e.data.is_favorite
    await nextTick()
    // requestAnimationFrame으로 레이아웃 완료 후 차트 생성
    requestAnimationFrame(() => {
      chartInstance = buildChart(chartCanvas.value, priceHistory.value, chartInstance)
    })
  } catch (e) {
    error.value = getErrorMessage(e, '종목 정보를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

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

.hero-top {
  display: flex; align-items: center; gap: 16px; margin-bottom: 24px;
}

.stock-avatar {
  width: 56px; height: 56px; border-radius: 16px; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; font-weight: 800;
}

.stock-meta { flex: 1; min-width: 0; }
.stock-code-label {
  display: inline-block; margin-bottom: 6px;
  padding: 3px 10px; border-radius: 8px;
  background: #eef3ff; color: #0046ff;
  font-size: .72rem; font-weight: 700; letter-spacing: .06em;
}
.stock-title { margin: 0; font-size: 1.75rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }

.fav-btn {
  flex: 0 0 auto;
  padding: 10px 18px; border-radius: 12px;
  font-size: .88rem; font-weight: 700; cursor: pointer;
  border: 1.5px solid #e7eaf0; background: white; color: #616b7d;
  transition: all .18s;
  white-space: nowrap;
}
.fav-btn:hover { border-color: #f5a623; color: #f5a623; }
.fav-btn.active { background: #fff8eb; border-color: #f5a623; color: #d48800; }

/* 시세 */
.price-section { margin-bottom: 20px; }
.price-main { display: flex; align-items: baseline; gap: 12px; margin-bottom: 4px; }
.price-value { font-size: 2.2rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.price-change { font-size: 1.1rem; font-weight: 700; }
.price-change.up { color: #e53e3e; }
.price-change.down { color: #0046ff; }
.price-change.flat { color: #98a2b3; }
.price-label { font-size: .78rem; color: #98a2b3; }
.price-empty { padding: 16px 0; color: #98a2b3; font-size: .9rem; }

.stock-desc { margin: 16px 0 0; font-size: .92rem; color: #616b7d; line-height: 1.7; }

/* 차트 */
.chart-section { }
.chart-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; }
.chart-sub { margin: 0; font-size: .78rem; color: #98a2b3; }
.chart-meta { display: flex; gap: 16px; font-size: .8rem; color: #616b7d; }
.chart-meta strong { color: #191f2b; }

.period-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.period-btn {
  padding: 5px 13px; border-radius: 20px; border: 1px solid #e7eaf0;
  background: white; color: #616b7d; font-size: .8rem; font-weight: 600; cursor: pointer; transition: all .15s;
}
.period-btn:hover { border-color: #0046ff; color: #0046ff; }
.period-btn.active { background: #0046ff; border-color: #0046ff; color: white; }
.period-divider { color: #d0d5dd; font-size: .9rem; margin: 0 2px; }
.date-input {
  padding: 4px 8px; border: 1px solid #e7eaf0; border-radius: 8px;
  font-size: .78rem; color: #364153; background: white; cursor: pointer;
  outline: none; transition: border-color .15s;
}
.date-input:focus { border-color: #0046ff; }
.date-sep { font-size: .8rem; color: #98a2b3; }
.date-reset { background: #fef0f0; border-color: #fca5a5; color: #dc2626; }
.date-reset:hover { background: #fee2e2; border-color: #ef4444; color: #b91c1c; }

.chart-wrap { position: relative; cursor: pointer; }
.chart-canvas-box { width: 100%; overflow: hidden; }
.chart-canvas-box canvas { display: block; max-width: 100%; }
.chart-dates { display: flex; justify-content: space-between; font-size: .72rem; color: #98a2b3; margin-top: 6px; padding: 0 4px; }
.enlarge-hint {
  position: absolute; top: 6px; right: 6px; pointer-events: none;
  font-size: .72rem; color: #98a2b3; background: rgba(255,255,255,.85);
  padding: 3px 8px; border-radius: 6px;
}

.chart-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 20px;
}
.chart-modal {
  background: white; border-radius: 20px; padding: 28px;
  width: 100%; max-width: 900px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.chart-modal-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;
}
.chart-modal-header strong { font-size: 1rem; }
.chart-close {
  margin-left: auto; padding: 7px 14px; border-radius: 8px; border: 1px solid #e7eaf0;
  background: white; font-size: .85rem; font-weight: 700; cursor: pointer; color: #616b7d;
}
.chart-close:hover { background: #f0f2f6; }

/* 섹션 공통 */
.section {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 22px; padding: 28px 32px;
  margin-bottom: 20px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
}
.section-title { margin: 0 0 20px; font-size: 1.05rem; font-weight: 800; color: #191f2b; }

/* 가격 테이블 */
.price-table { border: 1px solid #edf0f5; border-radius: 14px; overflow: hidden; }
.table-header, .table-row {
  display: grid;
  grid-template-columns: 1.4fr 1.2fr 1fr 1fr;
  padding: 12px 18px;
}
.table-header {
  background: #f7f8fb;
  font-size: .75rem; font-weight: 700; color: #98a2b3;
  border-bottom: 1px solid #edf0f5;
}
.table-row {
  font-size: .88rem; border-bottom: 1px solid #f0f2f6;
  transition: background .12s;
}
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: #fafbff; }
.date-cell { color: #616b7d; }
.price-cell { font-weight: 700; color: #191f2b; }
.rate-cell { font-weight: 700; }
.rate-cell.up { color: #e53e3e; }
.rate-cell.down { color: #0046ff; }
.rate-cell.flat { color: #98a2b3; }
.vol-cell { color: #98a2b3; }

/* 토스트 */
.toast {
  position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%);
  padding: 13px 24px; border-radius: 12px;
  background: #191f2b; color: white;
  font-size: .9rem; font-weight: 600;
  box-shadow: 0 8px 24px rgba(0,0,0,.18);
  white-space: nowrap; z-index: 9999; pointer-events: none;
}
.toast-error { background: #c62828; }
.toast-enter-active { transition: opacity .2s ease, transform .2s ease; }
.toast-leave-active { transition: opacity .3s ease, transform .3s ease; }
.toast-enter-from { opacity: 0; transform: translate(-50%, 12px); }
.toast-leave-to { opacity: 0; transform: translate(-50%, 8px); }

/* 뉴스 */
.news-list { display: flex; flex-direction: column; }
.news-item {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 16px 0; border-bottom: 1px solid #f0f2f6;
  text-decoration: none; color: inherit;
  transition: background .12s;
}
.news-item:last-child { border-bottom: none; }
.news-item:hover { background: #fafbff; margin: 0 -8px; padding: 16px 8px; border-radius: 10px; }
.news-body { flex: 1; min-width: 0; }
.news-title {
  margin: 0 0 5px; font-size: .92rem; font-weight: 700; color: #191f2b;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.news-summary {
  margin: 0 0 6px; font-size: .8rem; color: #697386; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.news-meta { display: flex; align-items: center; gap: 5px; font-size: .72rem; color: #98a2b3; }
.news-publisher { font-weight: 600; }
.news-dot { color: #c4c9d4; }
.news-arrow { color: #c4c9d4; font-size: 1rem; flex: 0 0 auto; margin-top: 2px; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

.more-btn {
  display: block; width: 100%; margin-top: 12px;
  padding: 10px; border: 1px dashed #d0d8f0; border-radius: 10px;
  background: #f7f8fb; color: #0046ff; font-size: .85rem; font-weight: 700;
  cursor: pointer; transition: background .15s;
}
.more-btn:hover { background: #eef3ff; }
.collapse-btn { color: #98a2b3; border-color: #e7eaf0; }
.collapse-btn:hover { background: #f0f2f6; color: #616b7d; }

.signup-prompt {
  background: #eef3ff; border: 1px solid #c9d7ff; border-radius: 14px;
  padding: 14px 20px; margin-bottom: 20px;
  font-size: .9rem; color: #364153; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.signup-prompt a { color: #0046ff; font-weight: 700; }
.signup-link { background: #0046ff; color: white !important; padding: 4px 12px; border-radius: 8px; }

@media (max-width: 600px) {
  .page-bg { padding: 24px 14px 60px; }
  .hero-card, .section { padding: 22px 18px; }
  .hero-top { flex-wrap: wrap; }
  .stock-title { font-size: 1.4rem; }
  .price-value { font-size: 1.7rem; }
  .table-header, .table-row { grid-template-columns: 1.2fr 1fr .8fr .9fr; font-size: .78rem; padding: 10px 12px; }
  .fav-btn { width: 100%; text-align: center; }
}
</style>
