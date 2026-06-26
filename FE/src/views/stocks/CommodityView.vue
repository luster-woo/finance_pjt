<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">원자재 시세</h1>
        <p class="page-sub">금·은 시세를 차트로 확인하세요.</p>
      </div>

      <p v-if="loading" class="status">시세를 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <!-- 금 -->
        <div class="commodity-card">
          <div class="card-header">
            <div class="comm-icon gold-icon">Au</div>
            <div>
              <h2 class="comm-name">금 (Gold)</h2>
              <p class="comm-sub">GC=F · USD/oz</p>
            </div>
            <div class="latest-price" v-if="data.Gold?.latest_price">
              <span class="price-num">${{ Number(data.Gold.latest_price).toLocaleString() }}</span>
              <span class="price-date">{{ data.Gold.latest_date }}</span>
            </div>
          </div>

          <div class="period-tabs">
            <button v-for="p in periods" :key="p.value" class="period-btn"
              :class="{ active: goldPeriod === p.value && !goldCustom }" @click="applyGoldPeriod(p.value)">
              {{ p.label }}
            </button>
            <span class="period-divider">|</span>
            <input type="date" class="date-input" v-model="goldDateFrom" @change="applyGoldCustom" />
            <span class="date-sep">~</span>
            <input type="date" class="date-input" v-model="goldDateTo" @change="applyGoldCustom" />
            <button v-if="goldCustom" class="period-btn date-reset" @click="resetGoldRange">초기화</button>
          </div>

          <div class="chart-wrap" @click="openModal('Gold')">
            <canvas ref="goldCanvas" height="140"></canvas>
            <span class="enlarge-hint">클릭하여 확대 ↗</span>
          </div>
        </div>

        <!-- 은 -->
        <div class="commodity-card">
          <div class="card-header">
            <div class="comm-icon silver-icon">Ag</div>
            <div>
              <h2 class="comm-name">은 (Silver)</h2>
              <p class="comm-sub">SI=F · USD/oz</p>
            </div>
            <div class="latest-price" v-if="data.Silver?.latest_price">
              <span class="price-num">${{ Number(data.Silver.latest_price).toLocaleString() }}</span>
              <span class="price-date">{{ data.Silver.latest_date }}</span>
            </div>
          </div>

          <div class="period-tabs">
            <button v-for="p in periods" :key="p.value" class="period-btn"
              :class="{ active: silverPeriod === p.value && !silverCustom }" @click="applySilverPeriod(p.value)">
              {{ p.label }}
            </button>
            <span class="period-divider">|</span>
            <input type="date" class="date-input" v-model="silverDateFrom" @change="applySilverCustom" />
            <span class="date-sep">~</span>
            <input type="date" class="date-input" v-model="silverDateTo" @change="applySilverCustom" />
            <button v-if="silverCustom" class="period-btn date-reset" @click="resetSilverRange">초기화</button>
          </div>

          <div class="chart-wrap" @click="openModal('Silver')">
            <canvas ref="silverCanvas" height="140"></canvas>
            <span class="enlarge-hint">클릭하여 확대 ↗</span>
          </div>
        </div>
      </template>
    </div>

    <!-- 모달 -->
    <Teleport to="body">
      <div v-if="modal.show" class="modal-overlay" @click.self="modal.show = false">
        <div class="modal-box">
          <div class="modal-header">
            <h3>{{ modal.type === 'Gold' ? '금 (Gold)' : '은 (Silver)' }} 시세</h3>
            <button class="modal-close" @click="modal.show = false">✕</button>
          </div>
          <div class="modal-period-tabs">
            <button v-for="p in periods" :key="p.value" class="period-btn"
              :class="{ active: modal.period === p.value }"
              @click="modal.period = p.value; drawModal()">
              {{ p.label }}
            </button>
          </div>
          <canvas ref="modalCanvas" height="300"></canvas>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { api, getErrorMessage } from '@/api'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const data = ref({})
const loading = ref(true)
const error = ref('')
const goldCanvas = ref(null)
const silverCanvas = ref(null)
const modalCanvas = ref(null)
const goldPeriod = ref('6m')
const silverPeriod = ref('6m')
const goldDateFrom = ref('')
const goldDateTo = ref('')
const goldCustom = ref(false)
const silverDateFrom = ref('')
const silverDateTo = ref('')
const silverCustom = ref(false)
const modal = ref({ show: false, type: 'Gold', period: '6m' })

const periods = [
  { label: '1개월', value: '1m' },
  { label: '3개월', value: '3m' },
  { label: '6개월', value: '6m' },
  { label: '1년',   value: '1y' },
  { label: '전체',  value: 'all' },
]

let goldChart = null
let silverChart = null
let modalChart = null

function applyGoldPeriod(v) { goldCustom.value = false; goldDateFrom.value = ''; goldDateTo.value = ''; goldPeriod.value = v }
function applyGoldCustom() { if (goldDateFrom.value || goldDateTo.value) { goldCustom.value = true; nextTick(drawGold) } }
function resetGoldRange() { goldCustom.value = false; goldDateFrom.value = ''; goldDateTo.value = ''; nextTick(drawGold) }

function applySilverPeriod(v) { silverCustom.value = false; silverDateFrom.value = ''; silverDateTo.value = ''; silverPeriod.value = v }
function applySilverCustom() { if (silverDateFrom.value || silverDateTo.value) { silverCustom.value = true; nextTick(drawSilver) } }
function resetSilverRange() { silverCustom.value = false; silverDateFrom.value = ''; silverDateTo.value = ''; nextTick(drawSilver) }

function filterHistory(history, period, dateFrom, dateTo, isCustom) {
  if (!history?.length) return history
  if (isCustom) {
    return history.filter(h => {
      const d = new Date(h.date)
      if (dateFrom && d < new Date(dateFrom)) return false
      if (dateTo && d > new Date(dateTo + 'T23:59:59')) return false
      return true
    })
  }
  if (period === 'all') return history
  const now = new Date()
  const cutoff = new Date(now)
  if (period === '1m') cutoff.setMonth(now.getMonth() - 1)
  else if (period === '3m') cutoff.setMonth(now.getMonth() - 3)
  else if (period === '6m') cutoff.setMonth(now.getMonth() - 6)
  else if (period === '1y') cutoff.setFullYear(now.getFullYear() - 1)
  return history.filter(h => new Date(h.date) >= cutoff)
}

function buildChart(canvas, history, color, existingChart) {
  if (!canvas || !history?.length) return existingChart
  if (existingChart) existingChart.destroy()
  // 레이아웃 완료 후 캔버스 크기 설정
  const w = canvas.parentElement?.clientWidth || 800
  canvas.width = Math.max(w, 300)
  canvas.height = 140
  const labels = history.map(h => h.date.slice(5))
  const values = history.map(h => Number(h.price))
  return new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: color,
        backgroundColor: color.replace(')', ', 0.08)').replace('rgb', 'rgba'),
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `$${Number(ctx.raw).toLocaleString()}` } } },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 11 } }, grid: { display: false } },
        y: { ticks: { font: { size: 11 }, callback: v => `$${Number(v).toLocaleString()}` }, grid: { color: '#f0f2f6' } }
      }
    }
  })
}

function drawGold() {
  requestAnimationFrame(() => {
    const h = filterHistory(data.value.Gold?.history, goldPeriod.value, goldDateFrom.value, goldDateTo.value, goldCustom.value)
    goldChart = buildChart(goldCanvas.value, h, 'rgb(212,148,0)', goldChart)
  })
}
function drawSilver() {
  requestAnimationFrame(() => {
    const h = filterHistory(data.value.Silver?.history, silverPeriod.value, silverDateFrom.value, silverDateTo.value, silverCustom.value)
    silverChart = buildChart(silverCanvas.value, h, 'rgb(120,130,150)', silverChart)
  })
}
function drawModal() {
  nextTick(() => {
    const h = filterHistory(data.value[modal.value.type]?.history, modal.value.period, '', '', false)
    const color = modal.value.type === 'Gold' ? 'rgb(212,148,0)' : 'rgb(120,130,150)'
    modalChart = buildChart(modalCanvas.value, h, color, modalChart)
  })
}

function openModal(type) {
  modal.value = { show: true, type, period: '6m' }
  nextTick(() => drawModal())
}

watch(goldPeriod, () => nextTick(drawGold))
watch(silverPeriod, () => nextTick(drawSilver))

onMounted(async () => {
  try {
    data.value = (await api.get('/commodities/summary/')).data
    await nextTick()
    drawGold()
    drawSilver()
  } catch (e) {
    error.value = getErrorMessage(e, '시세를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }
.page-header { margin-bottom: 28px; }
.page-title { margin: 0 0 8px; font-size: 1.75rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.page-sub { margin: 0; color: #98a2b3; font-size: .92rem; }

.commodity-card {
  background: white; border: 1px solid #e7eaf0; border-radius: 22px;
  padding: 28px 32px; margin-bottom: 20px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
}

.card-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.comm-icon {
  width: 52px; height: 52px; border-radius: 16px; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; font-weight: 900; letter-spacing: -.02em;
}
.gold-icon { background: #fff8e6; color: #c68400; border: 1.5px solid #f5dfa0; }
.silver-icon { background: #f0f2f5; color: #6b7280; border: 1.5px solid #d1d5db; }
.comm-name { margin: 0 0 3px; font-size: 1.15rem; font-weight: 800; color: #191f2b; }
.comm-sub { margin: 0; font-size: .78rem; color: #98a2b3; }
.latest-price { margin-left: auto; text-align: right; }
.price-num { display: block; font-size: 1.4rem; font-weight: 800; color: #191f2b; }
.price-date { font-size: .75rem; color: #98a2b3; }

.period-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.period-btn {
  padding: 6px 14px; border-radius: 20px; border: 1px solid #e7eaf0;
  background: white; color: #616b7d; font-size: .82rem; font-weight: 600; cursor: pointer;
  transition: all .15s;
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
.date-reset { background: #fef0f0 !important; border-color: #fca5a5 !important; color: #dc2626 !important; padding: 4px 10px !important; }

.chart-wrap { position: relative; cursor: pointer; width: 100%; overflow: hidden; }
.chart-wrap canvas { display: block; max-width: 100%; }
.enlarge-hint {
  position: absolute; top: 8px; right: 8px;
  font-size: .72rem; color: #98a2b3; background: rgba(255,255,255,.85);
  padding: 3px 8px; border-radius: 6px; pointer-events: none;
}

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal-box {
  background: white; border-radius: 20px; padding: 28px;
  width: 100%; max-width: 900px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 1.2rem; font-weight: 800; }
.modal-close {
  padding: 8px 14px; border-radius: 8px; border: 1px solid #e7eaf0;
  background: white; font-size: .85rem; font-weight: 700; cursor: pointer; color: #616b7d;
}
.modal-close:hover { background: #f0f2f6; }
.modal-period-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

@media (max-width: 600px) {
  .commodity-card { padding: 22px 18px; }
  .card-header { flex-wrap: wrap; }
  .latest-price { margin-left: 0; }
}
</style>
