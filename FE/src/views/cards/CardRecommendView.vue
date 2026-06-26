<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <span class="eyebrow">AI CARD MATCH</span>
        <h1 class="page-title">소비 습관 맞춤 카드 추천</h1>
        <p class="page-sub">자주 쓰는 소비 항목을 선택하면 AI가 최적의 카드를 추천해드립니다.</p>
      </div>

      <div class="form-card">
        <div class="form-label">주요 소비 항목 선택 <span class="hint">(복수 선택 가능)</span></div>
        <div class="habit-grid">
          <button
            v-for="h in habitOptions"
            :key="h.value"
            class="habit-btn"
            :class="{ active: selected.includes(h.value) }"
            @click="toggle(h.value)"
          >
            <span class="habit-emoji">{{ h.emoji }}</span>
            <span class="habit-label">{{ h.label }}</span>
          </button>
        </div>

        <!-- 채점 기준 안내 -->
        <div class="algo-info">
          <span class="algo-title">AI 채점 기준</span>
          <div class="algo-bars">
            <div class="algo-row"><div class="algo-bar" style="width:40%;background:#0046ff"></div><span>소비 카테고리 혜택 매칭 40%</span></div>
            <div class="algo-row"><div class="algo-bar" style="width:30%;background:#00a984"></div><span>혜택 수 및 질 30%</span></div>
            <div class="algo-row"><div class="algo-bar" style="width:20%;background:#f5a623"></div><span>연회비 효율성 20%</span></div>
            <div class="algo-row"><div class="algo-bar" style="width:10%;background:#7b4dce"></div><span>전월 실적 허들 10%</span></div>
          </div>
        </div>

        <button class="submit-btn" :disabled="!selected.length || loading" @click="recommend">
          <span v-if="loading">AI 분석 중...</span>
          <span v-else>추천 받기 → ({{ selected.length }}개 선택됨)</span>
        </button>
      </div>

      <!-- 결과 -->
      <p v-if="error" class="status error">{{ error }}</p>

      <div v-if="results.length" class="results-section">
        <h2 class="results-title">추천 카드 TOP {{ results.length }}</h2>

        <div class="result-list">
          <RouterLink
            v-for="(item, idx) in results"
            :key="item.card_id"
            :to="`/cards/${item.card_id}`"
            class="result-card"
          >
            <div class="rank-badge" :class="['rank-' + (idx+1)]">{{ idx + 1 }}</div>

            <div class="card-info">
              <div class="card-top">
                <div class="company-logo" :style="logoStyle(item.company)">{{ logoInitial(item.company) }}</div>
                <div>
                  <p class="company-name">{{ item.company }} · {{ item.card_type }}카드</p>
                  <h3 class="card-name">{{ item.card_name }}</h3>
                </div>
              </div>

              <!-- AI 근거 -->
              <div class="ai-reason-box">
                <span class="ai-badge">AI</span>
                <p class="ai-reason">{{ item.reason }}</p>
              </div>

              <!-- 매칭 혜택 태그 -->
              <div class="benefit-tags">
                <span
                  v-for="b in item.matched_benefits"
                  :key="b.category"
                  class="benefit-tag"
                >{{ b.category }}</span>
              </div>
            </div>

            <!-- 카드 정보 + 점수 -->
            <div class="score-info">
              <div class="fee-info">
                <span class="fee-label">연회비</span>
                <span class="fee-value">{{ item.annual_fee ? item.annual_fee.toLocaleString() + '원' : '없음' }}</span>
              </div>
              <div class="score-ring" :style="ringStyle(item.score)">
                <span class="score-num">{{ Math.round(item.score) }}</span>
                <span class="score-unit">점</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api, getErrorMessage } from '@/api'

const selected = ref([])
const results = ref([])
const loading = ref(false)
const error = ref('')

const habitOptions = [
  { value: '식비', emoji: '🍽️', label: '식비/외식' },
  { value: '교통', emoji: '🚌', label: '교통' },
  { value: '온라인쇼핑', emoji: '🛍️', label: '온라인쇼핑' },
  { value: '주유', emoji: '⛽', label: '주유' },
  { value: '통신비', emoji: '📱', label: '통신비' },
  { value: '의료', emoji: '🏥', label: '의료/병원' },
  { value: '해외', emoji: '✈️', label: '해외여행' },
  { value: '편의점', emoji: '🏪', label: '편의점' },
  { value: '카페', emoji: '☕', label: '카페/음료' },
  { value: '문화', emoji: '🎬', label: '영화/문화' },
  { value: '마트', emoji: '🛒', label: '마트/슈퍼' },
  { value: '구독', emoji: '📺', label: 'OTT/구독' },
]

function toggle(v) {
  const i = selected.value.indexOf(v)
  if (i >= 0) selected.value.splice(i, 1)
  else selected.value.push(v)
}

const BRANDS = {
  'KB국민': { bg: '#F0A500', color: '#fff', initial: 'KB' },
  '신한': { bg: '#0046A0', color: '#fff', initial: '신한' },
  '삼성': { bg: '#1428A0', color: '#fff', initial: '삼성' },
  '현대': { bg: '#002C5F', color: '#fff', initial: '현대' },
  '롯데': { bg: '#E60028', color: '#fff', initial: '롯데' },
  '하나': { bg: '#009B77', color: '#fff', initial: '하나' },
  '우리': { bg: '#1B4B8E', color: '#fff', initial: '우리' },
  'NH': { bg: '#008C4A', color: '#fff', initial: 'NH' },
  '농협': { bg: '#008C4A', color: '#fff', initial: 'NH' },
  '카카오': { bg: '#FAE100', color: '#3C1E1E', initial: '카카오' },
  '토스': { bg: '#0064FF', color: '#fff', initial: 'T' },
}
function matchBrand(company) {
  for (const [k, v] of Object.entries(BRANDS)) {
    if (company.includes(k)) return v
  }
  return { bg: '#e7eaf0', color: '#616b7d', initial: company.slice(0, 2) }
}
function logoStyle(company) {
  const b = matchBrand(company)
  return { background: b.bg, color: b.color }
}
function logoInitial(company) {
  return matchBrand(company).initial
}

function ringStyle(score) {
  const c = score >= 80 ? '#0046ff' : score >= 60 ? '#00a984' : '#f5a623'
  return { background: `conic-gradient(${c} ${score * 3.6}deg, #edf0f5 0deg)` }
}

async function recommend() {
  loading.value = true
  error.value = ''
  results.value = []
  try {
    const { data } = await api.post('/tests/recommendations/cards/by-habits/', { habits: selected.value })
    results.value = data
    if (!data.length) error.value = '추천 결과가 없습니다.'
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
.eyebrow { font-size: .72rem; font-weight: 800; color: #00a984; letter-spacing: .14em; }
.page-title { margin: 8px 0 6px; font-size: 1.9rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.page-sub { margin: 0; color: #98a2b3; font-size: .93rem; }

.form-card {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 24px; padding: 32px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
  margin-bottom: 28px;
}
.form-label { font-size: .88rem; font-weight: 800; color: #364153; margin-bottom: 14px; }
.hint { font-size: .78rem; color: #98a2b3; font-weight: 400; margin-left: 6px; }

.habit-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 24px; }
.habit-btn {
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  padding: 14px 8px; border: 1.5px solid #e7eaf0; border-radius: 14px;
  background: white; cursor: pointer; transition: all .15s;
}
.habit-btn:hover { border-color: #00a984; }
.habit-btn.active { background: #f0faf6; border-color: #00a984; }
.habit-emoji { font-size: 1.5rem; }
.habit-label { font-size: .75rem; font-weight: 700; color: #364153; }
.habit-btn.active .habit-label { color: #00a984; }

.algo-info { background: #f7f8fb; border-radius: 14px; padding: 16px 18px; margin-bottom: 20px; }
.algo-title { font-size: .78rem; font-weight: 800; color: #364153; display: block; margin-bottom: 10px; }
.algo-bars { display: flex; flex-direction: column; gap: 7px; }
.algo-row { display: flex; align-items: center; gap: 10px; font-size: .74rem; color: #616b7d; }
.algo-bar { height: 6px; border-radius: 3px; flex: 0 0 auto; }

.submit-btn {
  width: 100%; padding: 16px; background: #00a984; color: white;
  border: none; border-radius: 14px; font-size: 1rem; font-weight: 800; cursor: pointer;
  box-shadow: 0 8px 20px rgba(0,169,132,.22); transition: background .15s, transform .15s;
}
.submit-btn:hover:not(:disabled) { background: #008a6b; transform: translateY(-1px); }
.submit-btn:disabled { background: #c4c9d4; box-shadow: none; cursor: not-allowed; }

.results-section { margin-top: 8px; }
.results-title { margin: 0 0 16px; font-size: 1.2rem; font-weight: 800; color: #191f2b; }
.result-list { display: flex; flex-direction: column; gap: 12px; }

.result-card {
  display: grid; grid-template-columns: 40px 1fr auto;
  align-items: flex-start; gap: 18px;
  background: white; border: 1px solid #e7eaf0;
  border-radius: 20px; padding: 22px 24px;
  text-decoration: none; color: inherit;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.result-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(28,39,65,.1); border-color: #b8eedd; }

.rank-badge {
  width: 36px; height: 36px; border-radius: 50%; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: .95rem; font-weight: 800;
  background: #f0f2f7; color: #616b7d;
}
.rank-1 { background: linear-gradient(135deg,#f5d020,#f5a623); color:white; }
.rank-2 { background: linear-gradient(135deg,#d4d4d4,#a8a8a8); color:white; }
.rank-3 { background: linear-gradient(135deg,#d49a6a,#c07a3b); color:white; }

.card-top { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.company-logo {
  width: 40px; height: 40px; border-radius: 12px; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: .7rem; font-weight: 800;
}
.company-name { margin: 0 0 3px; font-size: .75rem; color: #98a2b3; font-weight: 600; }
.card-name { margin: 0; font-size: 1rem; font-weight: 800; color: #191f2b; }

.ai-reason-box { display: flex; gap: 6px; align-items: flex-start; margin-bottom: 10px; }
.ai-badge {
  flex: 0 0 auto; padding: 2px 6px; border-radius: 6px;
  background: linear-gradient(135deg,#00a984,#0046ff); color:white;
  font-size: .62rem; font-weight: 800; margin-top: 1px;
}
.ai-reason { margin:0; font-size:.8rem; color:#364153; line-height:1.55; }

.benefit-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.benefit-tag { padding: 3px 9px; border-radius: 6px; font-size: .7rem; font-weight: 700; background: #f0faf6; color: #00a984; }

.score-info { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; min-width: 80px; }
.fee-info { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.fee-label { font-size: .68rem; color: #98a2b3; font-weight: 600; }
.fee-value { font-size: .85rem; font-weight: 800; color: #191f2b; }
.score-ring {
  width: 58px; height: 58px; border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: inset 0 0 0 8px white;
}
.score-num { font-size: .95rem; font-weight: 800; color: #191f2b; line-height: 1; }
.score-unit { font-size: .6rem; color: #98a2b3; }

.status { text-align: center; padding: 40px; color: #98a2b3; }
.error { color: #d14343; }

@media(max-width:600px) {
  .habit-grid { grid-template-columns: repeat(3,1fr); }
  .result-card { grid-template-columns: 36px 1fr; }
  .score-info { display: none; }
  .page-bg { padding: 24px 14px 60px; }
}
</style>
