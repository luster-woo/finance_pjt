<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <span class="page-eyebrow">AI PRODUCT MATCH</span>
        <h1 class="page-title">맞춤 금융상품 추천</h1>
        <p class="page-sub">투자 금액과 기간을 입력하면 AI가 최적의 상품을 추천해드립니다.</p>
      </div>

      <!-- 입력 폼 -->
      <div class="form-card">
        <div class="form-row">
          <!-- 목돈 입력 -->
          <div class="form-group">
            <label class="form-label">투자 금액</label>
            <div class="amount-input-wrap">
              <input
                v-model.number="amount"
                type="number"
                class="form-input"
                placeholder="예: 10000000"
                min="1"
                step="100000"
              />
              <span class="input-unit">원</span>
            </div>
            <p class="form-hint">{{ formatAmount(amount) }}</p>
            <!-- 빠른 선택 -->
            <div class="quick-chips">
              <button v-for="preset in amountPresets" :key="preset.value"
                class="chip" :class="{ active: amount === preset.value }"
                @click="amount = preset.value">{{ preset.label }}</button>
            </div>
          </div>

          <!-- 기간 선택 -->
          <div class="form-group">
            <label class="form-label">투자 기간</label>
            <div class="period-grid">
              <button
                v-for="m in periodOptions"
                :key="m.value"
                class="period-btn"
                :class="{ active: months === m.value }"
                @click="months = m.value"
              >
                <span class="period-num">{{ m.value }}</span>
                <span class="period-unit">개월</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 예상 요약 -->
        <div v-if="amount && months" class="summary-bar">
          <div class="summary-item">
            <span class="summary-label">투자 금액</span>
            <span class="summary-value">{{ formatAmount(amount) }}</span>
          </div>
          <span class="summary-sep">→</span>
          <div class="summary-item">
            <span class="summary-label">{{ months }}개월 후</span>
            <span class="summary-value highlight">만기 수령 예상</span>
          </div>
        </div>

        <!-- AI 채점 기준 안내 -->
        <div class="algo-info">
          <span class="algo-title">AI 채점 기준</span>
          <div class="algo-items">
            <div class="algo-item"><span class="algo-bar" style="width:40%"></span><span>금리 경쟁력 40%</span></div>
            <div class="algo-item"><span class="algo-bar" style="width:30%;background:#00a984"></span><span>수익 절대액 30%</span></div>
            <div class="algo-item"><span class="algo-bar" style="width:15%;background:#f5a623"></span><span>상품 유형 적합성 15%</span></div>
            <div class="algo-item"><span class="algo-bar" style="width:15%;background:#7b4dce"></span><span>은행 신뢰도 15%</span></div>
          </div>
        </div>

        <button
          class="submit-btn"
          :disabled="!amount || !months || loading"
          @click="recommend"
        >
          <span v-if="loading" class="btn-loading">AI 분석 중...</span>
          <span v-else>AI 추천 받기 →</span>
        </button>
      </div>

      <!-- 결과 -->
      <template v-if="results.length || error">
        <p v-if="error" class="status error">{{ error }}</p>

        <div v-if="results.length" class="results-section">
          <div class="results-header">
            <h2 class="results-title">추천 결과</h2>
            <span class="results-sub">{{ months }}개월 · {{ formatAmount(amount) }} 기준</span>
          </div>

          <div class="result-list">
            <RouterLink
              v-for="(item, idx) in results"
              :key="item.product_id"
              :to="`/products/${item.product_id}`"
              class="result-card"
            >
              <!-- 순위 -->
              <div class="rank-col">
                <span class="rank-num" :class="{ gold: idx === 0, silver: idx === 1, bronze: idx === 2 }">
                  {{ idx + 1 }}
                </span>
              </div>

              <!-- 상품 정보 -->
              <div class="product-col">
                <div class="product-top">
                  <span class="bank-name">{{ item.bank_name }}</span>
                  <span class="type-badge" :class="item.product_type">
                    {{ item.product_type === 'deposit' ? '예금' : '적금' }}
                  </span>
                </div>
                <h3 class="product-name">{{ item.product_name }}</h3>
                <!-- AI 점수 근거 -->
                <div class="ai-reason-wrap">
                  <span class="ai-icon">AI</span>
                  <p class="ai-reason">{{ item.reason }}</p>
                </div>
                <!-- 점수 기준 태그 -->
                <div class="score-tags">
                  <span class="score-tag rate">금리 {{ item.best_rate }}%</span>
                  <span class="score-tag mat">만기 +{{ formatAmount(item.interest) }}</span>
                  <span class="score-tag type">{{ item.product_type === 'deposit' ? '예금' : '적금' }}</span>
                </div>
              </div>

              <!-- 수익 정보 -->
              <div class="profit-col">
                <div class="rate-box">
                  <span class="rate-label">최고금리</span>
                  <span class="rate-value">{{ item.best_rate }}%</span>
                </div>
                <div class="maturity-box">
                  <span class="maturity-label">만기 예상</span>
                  <span class="maturity-value">{{ formatAmount(item.maturity_amount) }}</span>
                  <span class="interest-diff">+{{ formatAmount(item.interest) }}</span>
                </div>
              </div>

              <!-- AI 점수 -->
              <div class="score-col">
                <div class="score-ring" :style="scoreStyle(item.score)">
                  <span class="score-num">{{ Math.round(item.score) }}</span>
                  <span class="score-label">점</span>
                </div>
              </div>
            </RouterLink>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api, getErrorMessage } from '@/api'

const amount = ref(null)
const months = ref(null)
const results = ref([])
const loading = ref(false)
const error = ref('')

const amountPresets = [
  { label: '100만원', value: 1000000 },
  { label: '500만원', value: 5000000 },
  { label: '1,000만원', value: 10000000 },
  { label: '3,000만원', value: 30000000 },
]

const periodOptions = [
  { value: 1 }, { value: 3 }, { value: 6 },
  { value: 12 }, { value: 24 }, { value: 36 },
]

function formatAmount(v) {
  if (!v) return ''
  if (v >= 100000000) return `${(v / 100000000).toFixed(v % 100000000 ? 1 : 0)}억원`
  if (v >= 10000) return `${(v / 10000).toFixed(v % 10000 ? 1 : 0)}만원`
  return `${Number(v).toLocaleString()}원`
}

function scoreStyle(score) {
  const pct = Math.round(score)
  const color = score >= 80 ? '#0046ff' : score >= 60 ? '#00a984' : '#f5a623'
  return {
    background: `conic-gradient(${color} ${pct * 3.6}deg, #edf0f5 0deg)`,
  }
}

async function recommend() {
  if (!amount.value || !months.value) return
  loading.value = true
  error.value = ''
  results.value = []
  try {
    const { data } = await api.post('/tests/recommendations/by-criteria/', {
      amount: amount.value,
      months: months.value,
    })
    results.value = data
    if (!data.length) error.value = '해당 조건에 맞는 상품이 없습니다.'
  } catch (e) {
    error.value = getErrorMessage(e, 'AI 추천 중 오류가 발생했습니다.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

.page-header { margin-bottom: 28px; }
.page-eyebrow { font-size: .72rem; font-weight: 800; color: #0046ff; letter-spacing: .14em; }
.page-title { margin: 8px 0 6px; font-size: 1.9rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.page-sub { margin: 0; color: #98a2b3; font-size: .93rem; }

/* 입력 폼 */
.form-card {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 24px; padding: 32px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
  margin-bottom: 28px;
}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-bottom: 24px; }
.form-group { display: flex; flex-direction: column; gap: 10px; }
.form-label { font-size: .88rem; font-weight: 800; color: #364153; }

.amount-input-wrap { display: flex; align-items: center; border: 1.5px solid #e7eaf0; border-radius: 12px; overflow: hidden; transition: border-color .15s; }
.amount-input-wrap:focus-within { border-color: #0046ff; }
.form-input {
  flex: 1; padding: 13px 16px; border: none; outline: none;
  font-size: 1rem; color: #191f2b; background: transparent;
}
.input-unit { padding: 0 14px 0 0; font-size: .88rem; color: #98a2b3; font-weight: 600; }
.form-hint { margin: 0; font-size: .82rem; color: #0046ff; font-weight: 700; min-height: 18px; }

.quick-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  padding: 6px 12px; border: 1px solid #e7eaf0; border-radius: 20px;
  background: white; color: #616b7d; font-size: .78rem; font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.chip:hover { border-color: #0046ff; color: #0046ff; }
.chip.active { background: #0046ff; border-color: #0046ff; color: white; }

.period-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.period-btn {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 12px 8px; border: 1.5px solid #e7eaf0; border-radius: 12px;
  background: white; cursor: pointer; transition: all .15s;
}
.period-btn:hover { border-color: #0046ff; }
.period-btn.active { background: #0046ff; border-color: #0046ff; color: white; }
.period-num { font-size: 1.1rem; font-weight: 800; }
.period-unit { font-size: .65rem; font-weight: 600; opacity: .8; }

.summary-bar {
  display: flex; align-items: center; gap: 16px;
  background: #f0f4ff; border-radius: 14px; padding: 16px 20px;
  margin-bottom: 20px;
}
.summary-item { display: flex; flex-direction: column; gap: 2px; }
.summary-label { font-size: .72rem; color: #98a2b3; font-weight: 600; }
.summary-value { font-size: .95rem; font-weight: 800; color: #191f2b; }
.summary-value.highlight { color: #0046ff; }
.summary-sep { font-size: 1.2rem; color: #c4c9d4; }

/* 알고리즘 안내 */
.algo-info { background: #f7f8fb; border-radius: 14px; padding: 16px 18px; margin-bottom: 16px; }
.algo-title { font-size: .78rem; font-weight: 800; color: #364153; display: block; margin-bottom: 10px; }
.algo-items { display: flex; flex-direction: column; gap: 6px; }
.algo-item { display: flex; align-items: center; gap: 10px; font-size: .75rem; color: #616b7d; }
.algo-bar { display: inline-block; height: 6px; border-radius: 3px; background: #0046ff; flex: 0 0 auto; }

.submit-btn {
  width: 100%; padding: 16px;
  background: #0046ff; color: white;
  border: none; border-radius: 14px;
  font-size: 1rem; font-weight: 800; cursor: pointer;
  box-shadow: 0 8px 20px rgba(0,70,255,.22);
  transition: background .15s, transform .15s;
}
.submit-btn:hover:not(:disabled) { background: #0036cc; transform: translateY(-1px); }
.submit-btn:disabled { background: #c4c9d4; box-shadow: none; cursor: not-allowed; }
.btn-loading { display: inline-flex; align-items: center; gap: 8px; }

/* 결과 */
.results-section { margin-top: 8px; }
.results-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px; }
.results-title { margin: 0; font-size: 1.2rem; font-weight: 800; color: #191f2b; }
.results-sub { font-size: .82rem; color: #98a2b3; }

.result-list { display: flex; flex-direction: column; gap: 12px; }
.result-card {
  display: grid; grid-template-columns: 48px 1fr auto 80px;
  align-items: center; gap: 20px;
  background: white; border: 1px solid #e7eaf0;
  border-radius: 18px; padding: 22px 24px;
  text-decoration: none; color: inherit;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.result-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(28,39,65,.1); border-color: #c9d7ff; }

.rank-col { display: flex; justify-content: center; }
.rank-num {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; font-size: 1rem; font-weight: 800;
  background: #f0f2f7; color: #616b7d;
}
.rank-num.gold { background: linear-gradient(135deg, #f5d020, #f5a623); color: white; }
.rank-num.silver { background: linear-gradient(135deg, #d4d4d4, #a8a8a8); color: white; }
.rank-num.bronze { background: linear-gradient(135deg, #d49a6a, #c07a3b); color: white; }

.product-col { min-width: 0; }
.product-top { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.bank-name { font-size: .75rem; color: #98a2b3; font-weight: 600; }
.type-badge { padding: 2px 8px; border-radius: 6px; font-size: .68rem; font-weight: 700; }
.type-badge.deposit { background: #eef3ff; color: #0046ff; }
.type-badge.saving { background: #f0faf6; color: #00a984; }
.product-name { margin: 0 0 8px; font-size: .95rem; font-weight: 800; color: #191f2b; }
.ai-reason-wrap { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 8px; }
.ai-icon {
  flex: 0 0 auto; padding: 2px 6px; border-radius: 6px;
  background: linear-gradient(135deg, #0046ff, #0077ff);
  color: white; font-size: .62rem; font-weight: 800; letter-spacing: .04em;
  margin-top: 1px;
}
.ai-reason { margin: 0; font-size: .8rem; color: #364153; line-height: 1.55; }
.score-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.score-tag {
  padding: 3px 8px; border-radius: 6px;
  font-size: .7rem; font-weight: 700;
}
.score-tag.rate { background: #eef3ff; color: #0046ff; }
.score-tag.mat { background: #f0faf6; color: #00a984; }
.score-tag.type { background: #f5f0ff; color: #7b4dce; }

.profit-col { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; min-width: 120px; }
.rate-box, .maturity-box { display: flex; flex-direction: column; align-items: flex-end; }
.rate-label, .maturity-label { font-size: .68rem; color: #98a2b3; font-weight: 600; }
.rate-value { font-size: 1.15rem; font-weight: 800; color: #0046ff; }
.maturity-value { font-size: .88rem; font-weight: 800; color: #191f2b; }
.interest-diff { font-size: .72rem; color: #00a984; font-weight: 700; }

.score-col { display: flex; justify-content: flex-end; }
.score-ring {
  width: 60px; height: 60px; border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: conic-gradient(#0046ff 270deg, #edf0f5 0deg);
  box-shadow: inset 0 0 0 8px white;
}
.score-num { font-size: 1rem; font-weight: 800; color: #191f2b; line-height: 1; }
.score-label { font-size: .6rem; color: #98a2b3; font-weight: 600; }

.status { text-align: center; padding: 40px; color: #98a2b3; }
.error { color: #d14343; }

@media (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
  .result-card { grid-template-columns: 40px 1fr; }
  .profit-col, .score-col { display: none; }
  .page-bg { padding: 24px 14px 60px; }
  .form-card { padding: 22px 18px; }
}
</style>
