<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <span class="eyebrow">SAVINGS PLANNER</span>
        <h1 class="page-title">목표 저축 플래너</h1>
        <p class="page-sub">목표 금액과 기간을 입력하면 AI가 최적의 저축 전략을 계산해드립니다.</p>
      </div>

      <!-- 입력 카드 -->
      <div class="form-card">
        <div class="form-grid">
          <!-- 목표 금액 -->
          <div class="field">
            <label class="field-label">🎯 목표 금액</label>
            <div class="input-wrap">
              <input v-model.number="form.goal" type="number" class="field-input" placeholder="예: 30000000" min="1" step="100000" />
              <span class="unit">원</span>
            </div>
            <p class="hint">{{ formatAmt(form.goal) }}</p>
            <div class="chips">
              <button v-for="p in goalPresets" :key="p.v" class="chip" :class="{ active: form.goal === p.v }" @click="form.goal = p.v">{{ p.label }}</button>
            </div>
          </div>

          <!-- 월 저축액 -->
          <div class="field">
            <label class="field-label">💰 월 저축 가능 금액</label>
            <div class="input-wrap">
              <input v-model.number="form.monthly" type="number" class="field-input" placeholder="예: 500000" min="1" step="10000" />
              <span class="unit">원</span>
            </div>
            <p class="hint">{{ formatAmt(form.monthly) }}</p>
            <div class="chips">
              <button v-for="p in monthlyPresets" :key="p.v" class="chip" :class="{ active: form.monthly === p.v }" @click="form.monthly = p.v">{{ p.label }}</button>
            </div>
          </div>

          <!-- 목표 기간 -->
          <div class="field">
            <label class="field-label">📅 목표 기간</label>
            <div class="period-grid">
              <button v-for="m in periodOptions" :key="m" class="period-btn" :class="{ active: form.months === m }" @click="form.months = m">
                <span class="period-num">{{ m }}</span>
                <span class="period-unit">개월</span>
              </button>
            </div>
          </div>
        </div>

        <button class="calc-btn" :disabled="!canCalc || loading" @click="calculate">
          <span v-if="loading">계산 중...</span>
          <span v-else>📊 저축 계획 계산하기</span>
        </button>
      </div>

      <!-- 결과 -->
      <template v-if="result">
        <!-- 달성 여부 배너 -->
        <div class="result-banner" :class="result.achievable ? 'ok' : 'fail'">
          <div class="banner-icon">{{ result.achievable ? '✅' : '⚠️' }}</div>
          <div class="banner-text">
            <strong v-if="result.achievable">목표 달성 가능!</strong>
            <strong v-else>목표 달성이 어렵습니다</strong>
            <p v-if="result.achievable">
              {{ form.months }}개월 후 예상 수령액 <em>{{ formatAmt(result.maturity_amount) }}</em>으로
              목표 <em>{{ formatAmt(result.goal_amount) }}</em>을 달성할 수 있어요.
            </p>
            <p v-else>
              현재 계획으로는 <em>{{ formatAmt(result.shortfall) }}</em> 부족합니다.
              <template v-if="result.required_monthly">월 <em>{{ formatAmt(result.required_monthly) }}</em>이면 달성 가능해요.</template>
              <template v-else-if="result.months_needed"> <em>{{ result.months_needed }}개월</em> 후 달성 가능해요.</template>
            </p>
          </div>
        </div>

        <!-- 요약 수치 -->
        <div class="summary-grid">
          <div class="summary-card">
            <span class="summary-label">총 납입 원금</span>
            <span class="summary-value">{{ formatAmt(result.total_principal) }}</span>
          </div>
          <div class="summary-card highlight">
            <span class="summary-label">예상 이자 수익</span>
            <span class="summary-value green">+ {{ formatAmt(result.total_interest) }}</span>
          </div>
          <div class="summary-card highlight2">
            <span class="summary-label">만기 수령 예상액</span>
            <span class="summary-value blue">{{ formatAmt(result.maturity_amount) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">적용 최고 금리</span>
            <span class="summary-value">{{ result.best_rate }}%</span>
          </div>
        </div>

        <!-- 월별 누적 그래프 -->
        <div class="chart-card">
          <h2 class="chart-title">월별 누적 저축 예측</h2>
          <div class="chart-wrap">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>

        <!-- 추천 상품 -->
        <div class="products-section" v-if="result.recommended_products.length">
          <h2 class="section-title">추천 저축 상품</h2>
          <div class="product-list">
            <RouterLink
              v-for="(p, idx) in result.recommended_products"
              :key="p.product_id"
              :to="`/products/${p.product_id}`"
              class="product-card"
            >
              <span class="rank-badge" :class="`r${idx+1}`">{{ idx + 1 }}위</span>
              <div class="product-info">
                <span class="bank-name">{{ p.bank_name }}</span>
                <strong class="product-name">{{ p.product_name }}</strong>
                <span class="product-type">{{ p.product_type === 'deposit' ? '예금' : '적금' }} · {{ p.term }}개월</span>
              </div>
              <div class="product-rate">
                <span class="rate-val">{{ p.rate }}%</span>
                <span class="rate-label">최고금리</span>
                <span class="interest-val">+ {{ formatAmt(p.estimated_interest) }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </template>

      <p v-if="error" class="status error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend } from 'chart.js'
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend)

const form = ref({ goal: null, monthly: null, months: 12 })
const result = ref(null)
const loading = ref(false)
const error = ref('')
const chartCanvas = ref(null)
let chartInstance = null

const goalPresets = [
  { label: '500만', v: 5000000 }, { label: '1000만', v: 10000000 },
  { label: '3000만', v: 30000000 }, { label: '5000만', v: 50000000 }, { label: '1억', v: 100000000 },
]
const monthlyPresets = [
  { label: '10만', v: 100000 }, { label: '30만', v: 300000 },
  { label: '50만', v: 500000 }, { label: '100만', v: 1000000 },
]
const periodOptions = [1, 3, 6, 12, 24, 36]

const canCalc = computed(() => form.value.goal > 0 && form.value.monthly > 0 && form.value.months > 0)

function formatAmt(v) {
  if (!v) return ''
  if (v >= 100000000) return `${(v / 100000000).toFixed(v % 100000000 ? 1 : 0)}억원`
  if (v >= 10000) return `${Math.round(v / 10000).toLocaleString()}만원`
  return `${Number(v).toLocaleString()}원`
}

async function calculate() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await api.post('/planner/', {
      goal_amount: form.value.goal,
      monthly_savings: form.value.monthly,
      months: form.value.months,
    })
    result.value = data
    await nextTick()
    drawChart(data)
  } catch (e) {
    error.value = getErrorMessage(e, '계산 중 오류가 발생했습니다.')
  } finally {
    loading.value = false
  }
}

function drawChart(data) {
  if (!chartCanvas.value) return
  if (chartInstance) { chartInstance.destroy(); chartInstance = null }

  const labels = data.monthly_data.map(d => `${d.month}개월`)
  const principals = data.monthly_data.map(d => d.principal)
  const totals = data.monthly_data.map(d => d.total)
  const goalLine = data.monthly_data.map(() => data.goal_amount)

  const w = chartCanvas.value.parentElement?.clientWidth || 700
  chartCanvas.value.width = Math.max(w - 40, 300)
  chartCanvas.value.height = 260

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '만기 예상액',
          data: totals,
          borderColor: '#0046ff',
          backgroundColor: 'rgba(0,70,255,0.08)',
          fill: true,
          tension: 0.3,
          borderWidth: 2.5,
          pointRadius: 3,
        },
        {
          label: '납입 원금',
          data: principals,
          borderColor: '#00a984',
          backgroundColor: 'rgba(0,169,132,0.06)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          borderDash: [4, 3],
          pointRadius: 0,
        },
        {
          label: '목표 금액',
          data: goalLine,
          borderColor: '#e53e3e',
          borderWidth: 1.5,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: false,
      animation: false,
      plugins: {
        legend: { position: 'top', labels: { font: { size: 12 } } },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString()}원`,
          },
        },
      },
      scales: {
        x: { ticks: { font: { size: 11 }, color: '#98a2b3' }, grid: { display: false } },
        y: {
          ticks: { font: { size: 11 }, color: '#98a2b3', callback: v => `${Math.round(v / 10000).toLocaleString()}만` },
          grid: { color: '#f0f2f6' },
        },
      },
    },
  })
}
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

.page-header { text-align: center; margin-bottom: 32px; }
.eyebrow { font-size: .72rem; font-weight: 800; color: #0046ff; letter-spacing: .12em; display: block; margin-bottom: 8px; }
.page-title { margin: 0 0 8px; font-size: 2rem; font-weight: 800; color: #191f2b; letter-spacing: -.04em; }
.page-sub { margin: 0; color: #616b7d; font-size: .95rem; }

.form-card { background: white; border: 1px solid #e7eaf0; border-radius: 24px; padding: 32px; margin-bottom: 24px; box-shadow: 0 4px 18px rgba(28,39,65,.05); }
.form-grid { display: flex; flex-direction: column; gap: 28px; margin-bottom: 28px; }
.field-label { display: block; font-size: .85rem; font-weight: 700; color: #364153; margin-bottom: 10px; }
.input-wrap { display: flex; align-items: center; gap: 8px; }
.field-input { flex: 1; padding: 12px 14px; border: 1.5px solid #e7eaf0; border-radius: 10px; font-size: .95rem; color: #191f2b; outline: none; transition: border-color .15s; }
.field-input:focus { border-color: #0046ff; }
.unit { font-size: .88rem; font-weight: 600; color: #616b7d; }
.hint { margin: 6px 0 10px; font-size: .82rem; color: #0046ff; font-weight: 700; min-height: 18px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { padding: 5px 12px; border-radius: 20px; border: 1px solid #e7eaf0; background: white; color: #616b7d; font-size: .78rem; font-weight: 600; cursor: pointer; transition: all .15s; }
.chip:hover, .chip.active { background: #0046ff; border-color: #0046ff; color: white; }

.period-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
.period-btn { padding: 10px 4px; border: 1.5px solid #e7eaf0; border-radius: 12px; background: white; cursor: pointer; transition: all .15s; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.period-btn:hover, .period-btn.active { border-color: #0046ff; background: #0046ff; color: white; }
.period-num { font-size: 1.1rem; font-weight: 800; }
.period-unit { font-size: .65rem; font-weight: 600; }

.calc-btn { width: 100%; padding: 16px; background: #0046ff; color: white; border: none; border-radius: 14px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background .15s, transform .15s; }
.calc-btn:hover:not(:disabled) { background: #0036cc; transform: translateY(-2px); }
.calc-btn:disabled { background: #a0bbf2; cursor: not-allowed; transform: none; }

/* 결과 배너 */
.result-banner { display: flex; align-items: flex-start; gap: 16px; padding: 20px 24px; border-radius: 16px; margin-bottom: 20px; }
.result-banner.ok { background: #f0fdf4; border: 1.5px solid #86efac; }
.result-banner.fail { background: #fff7ed; border: 1.5px solid #fcd34d; }
.banner-icon { font-size: 1.8rem; flex: 0 0 auto; }
.banner-text strong { display: block; font-size: 1.05rem; color: #191f2b; margin-bottom: 6px; }
.banner-text p { margin: 0; font-size: .9rem; color: #616b7d; line-height: 1.6; }
.banner-text em { font-style: normal; font-weight: 700; color: #0046ff; }

/* 요약 카드 */
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.summary-card { background: white; border: 1px solid #e7eaf0; border-radius: 14px; padding: 16px; text-align: center; }
.summary-card.highlight { border-color: #86efac; background: #f0fdf4; }
.summary-card.highlight2 { border-color: #c9d7ff; background: #eef3ff; }
.summary-label { display: block; font-size: .72rem; color: #98a2b3; font-weight: 600; margin-bottom: 6px; }
.summary-value { font-size: .95rem; font-weight: 800; color: #191f2b; }
.summary-value.green { color: #16a34a; }
.summary-value.blue { color: #0046ff; }

/* 차트 */
.chart-card { background: white; border: 1px solid #e7eaf0; border-radius: 20px; padding: 24px; margin-bottom: 24px; box-shadow: 0 3px 12px rgba(28,39,65,.04); }
.chart-title { margin: 0 0 16px; font-size: 1rem; font-weight: 800; color: #191f2b; }
.chart-wrap { width: 100%; overflow-x: auto; }

/* 추천 상품 */
.products-section { margin-bottom: 32px; }
.section-title { margin: 0 0 14px; font-size: 1.1rem; font-weight: 800; color: #191f2b; }
.product-list { display: flex; flex-direction: column; gap: 10px; }
.product-card { display: flex; align-items: center; gap: 16px; padding: 18px 20px; background: white; border: 1px solid #e7eaf0; border-radius: 16px; text-decoration: none; transition: transform .18s, box-shadow .18s; }
.product-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(28,39,65,.08); border-color: #c9d7ff; }
.rank-badge { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: .82rem; font-weight: 800; flex: 0 0 auto; }
.r1 { background: linear-gradient(135deg,#f5d020,#f5a623); color: white; }
.r2 { background: linear-gradient(135deg,#d4d4d4,#a8a8a8); color: white; }
.r3 { background: linear-gradient(135deg,#d49a6a,#c07a3b); color: white; }
.product-info { flex: 1; min-width: 0; }
.bank-name { font-size: .72rem; color: #98a2b3; font-weight: 600; display: block; }
.product-name { display: block; font-size: .95rem; font-weight: 700; color: #191f2b; margin: 2px 0; }
.product-type { font-size: .75rem; color: #616b7d; }
.product-rate { text-align: right; flex: 0 0 auto; }
.rate-val { display: block; font-size: 1.3rem; font-weight: 800; color: #0046ff; }
.rate-label { font-size: .7rem; color: #98a2b3; display: block; }
.interest-val { font-size: .78rem; font-weight: 700; color: #16a34a; }

.status { text-align: center; padding: 40px 0; color: #98a2b3; }
.error { color: #d14343; }

@media(max-width: 600px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
  .period-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
