<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">카드 찾기</h1>
        <p class="page-sub">신용카드·체크카드를 비교하고 혜택에 맞는 카드를 골라보세요.</p>
      </div>

      <div class="tabs-row">
        <div class="tabs">
          <button
            v-for="t in types"
            :key="t.value"
            class="tab-btn"
            :class="{ active: type === t.value }"
            @click="type = t.value"
          >{{ t.label }}</button>
        </div>
        <div v-if="!isLoggedIn" class="login-cta">
          <span>💡 <strong>로그인</strong>하고 카드 AI 추천 받기</span>
          <div class="cta-btns">
            <RouterLink to="/login" class="cta-login">로그인</RouterLink>
            <RouterLink to="/signup" class="cta-signup">회원가입</RouterLink>
          </div>
        </div>
      </div>

      <div class="filter-bar">
        <input
          v-model.trim="keyword"
          class="search-input"
          placeholder="카드사 또는 카드명 검색"
        />
        <select v-model="sort" class="sort-select">
          <option value="fee_asc">연회비 낮은순</option>
          <option value="fee_desc">연회비 높은순</option>
          <option value="name_asc">카드명 가나다순</option>
        </select>
        <label class="free-fee-label">
          <input type="checkbox" v-model="onlyFree" />
          연회비 무료만
        </label>
      </div>
      <p class="result-count">{{ filtered.length }}개 카드</p>

      <p v-if="loading" class="status">카드를 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <div class="grid">
          <RouterLink
            v-for="card in filtered"
            :key="card.id"
            class="card-item"
            :to="`/cards/${card.id}`"
          >
            <div class="card-top">
              <div class="company-logo" :style="companyStyle(card.company)">
                {{ companyInitial(card.company) }}
              </div>
              <span class="type-badge" :class="card.card_type === '신용' ? 'credit' : 'check'">
                {{ card.card_type }}카드
              </span>
            </div>
            <p class="company-name">{{ card.company }}</p>
            <h3 class="card-name">{{ card.card_name }}</h3>
            <div v-if="card.annual_fee != null" class="fee-row">
              <span class="fee-label">연회비</span>
              <span class="fee-value" :class="{ free: card.annual_fee === 0 }">
                {{ card.annual_fee === 0 ? '없음' : Number(card.annual_fee).toLocaleString() + '원' }}
              </span>
            </div>
          </RouterLink>
        </div>
        <p v-if="!filtered.length" class="empty">조건에 맞는 카드가 없습니다.</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))

const cards = ref([])
const loading = ref(true)
const error = ref('')
const type = ref('all')
const keyword = ref('')
const sort = ref('fee_asc')
const onlyFree = ref(false)

const types = [
  { value: 'all', label: '전체' },
  { value: '신용', label: '신용카드' },
  { value: '체크', label: '체크카드' },
]

const filtered = computed(() => {
  let list = cards.value

  if (type.value !== 'all')
    list = list.filter(c => c.card_type === type.value)

  if (keyword.value)
    list = list.filter(c =>
      c.company.includes(keyword.value) || c.card_name.includes(keyword.value)
    )

  if (onlyFree.value)
    list = list.filter(c => c.annual_fee === 0 || c.annual_fee == null)

  if (sort.value === 'fee_asc')
    list = [...list].sort((a, b) => (a.annual_fee ?? 0) - (b.annual_fee ?? 0))
  else if (sort.value === 'fee_desc')
    list = [...list].sort((a, b) => (b.annual_fee ?? 0) - (a.annual_fee ?? 0))
  else if (sort.value === 'name_asc')
    list = [...list].sort((a, b) => a.card_name.localeCompare(b.card_name, 'ko'))

  return list
})

const CARD_BRANDS = {
  'KB국민':   { bg: '#F0A500', color: '#fff',    initial: 'KB' },
  '신한':     { bg: '#0046A0', color: '#fff',    initial: '신한' },
  '삼성':     { bg: '#1428A0', color: '#fff',    initial: '삼성' },
  '현대':     { bg: '#002C5F', color: '#fff',    initial: '현대' },
  '롯데':     { bg: '#E60028', color: '#fff',    initial: '롯데' },
  '하나':     { bg: '#009B77', color: '#fff',    initial: '하나' },
  '우리':     { bg: '#1B4B8E', color: '#fff',    initial: '우리' },
  'BC':       { bg: '#FF6B00', color: '#fff',    initial: 'BC' },
  '농협':     { bg: '#008C4A', color: '#fff',    initial: 'NH' },
  'NH':       { bg: '#008C4A', color: '#fff',    initial: 'NH' },
  '카카오':   { bg: '#FAE100', color: '#3C1E1E', initial: '카카오' },
  '케이':     { bg: '#6D34B0', color: '#fff',    initial: 'K' },
  '토스':     { bg: '#0064FF', color: '#fff',    initial: 'T' },
  '씨티':     { bg: '#003B70', color: '#fff',    initial: 'Citi' },
  '전북':     { bg: '#007934', color: '#fff',    initial: '전북' },
  '광주':     { bg: '#C8102E', color: '#fff',    initial: '광주' },
  '수협':     { bg: '#0068B7', color: '#fff',    initial: '수협' },
}

function matchBrand(company) {
  for (const key of Object.keys(CARD_BRANDS)) {
    if (company.includes(key)) return CARD_BRANDS[key]
  }
  return { bg: '#e7eaf0', color: '#616b7d', initial: company.slice(0, 2) }
}

function companyStyle(company) {
  const b = matchBrand(company)
  return { background: b.bg, color: b.color }
}
function companyInitial(company) {
  return matchBrand(company).initial
}

onMounted(async () => {
  try {
    cards.value = (await api.get('/cards/')).data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 1040px; margin: 0 auto; }

.page-header { margin-bottom: 28px; }
.page-title { margin: 0 0 8px; font-size: 1.75rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.page-sub { margin: 0; color: #98a2b3; font-size: .92rem; }

.tabs-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.tabs { display: flex; gap: 8px; }
.tab-btn {
  padding: 10px 22px; border: 1px solid #e7eaf0; border-radius: 20px;
  background: white; color: #616b7d; font-size: .9rem; font-weight: 600;
  cursor: pointer; transition: all .18s;
}
.tab-btn:hover { border-color: #0046ff; color: #0046ff; }
.tab-btn.active { background: #0046ff; border-color: #0046ff; color: white; }

.filter-bar {
  display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; align-items: center;
}
.search-input {
  flex: 1; min-width: 180px; padding: 10px 14px;
  border: 1px solid #e7eaf0; border-radius: 10px;
  font-size: .9rem; outline: none; background: white;
}
.search-input:focus { border-color: #0046ff; }
.sort-select {
  padding: 10px 14px; border: 1px solid #e7eaf0; border-radius: 10px;
  font-size: .9rem; background: white; cursor: pointer; outline: none;
}
.sort-select:focus { border-color: #0046ff; }
.free-fee-label {
  display: flex; align-items: center; gap: 6px;
  font-size: .88rem; font-weight: 600; color: #364153; cursor: pointer;
  white-space: nowrap;
}
.free-fee-label input { cursor: pointer; accent-color: #0046ff; width: 16px; height: 16px; }

.result-count { margin: 0 0 16px; font-size: .82rem; color: #98a2b3; font-weight: 600; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
}

.card-item {
  background: white; border: 1px solid #e7eaf0; border-radius: 18px;
  padding: 22px; text-decoration: none; color: inherit;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  transition: transform .2s, box-shadow .2s, border-color .2s;
  display: flex; flex-direction: column; gap: 4px;
}
.card-item:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(28,39,65,.1); border-color: #d0d8f0; }

.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }

.company-logo {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 800; letter-spacing: -.01em;
  flex: 0 0 auto;
}

.type-badge { padding: 4px 10px; border-radius: 8px; font-size: .72rem; font-weight: 700; }
.type-badge.credit { background: #eef3ff; color: #0046ff; }
.type-badge.check  { background: #f0faf6; color: #00a984; }

.company-name { margin: 0; font-size: .75rem; color: #98a2b3; font-weight: 600; }
.card-name { margin: 4px 0 10px; font-size: .98rem; font-weight: 800; color: #191f2b; line-height: 1.4; }

.fee-row { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 12px; border-top: 1px solid #f0f2f6; }
.fee-label { font-size: .72rem; color: #98a2b3; font-weight: 600; }
.fee-value { font-size: .92rem; font-weight: 800; color: #364153; }
.fee-value.free { color: #00a984; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }
.empty { text-align: center; padding: 60px 0; color: #98a2b3; font-size: .9rem; }

.login-cta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 7px 14px; background: linear-gradient(135deg, #eef3ff, #f0fbf7); border: 1px solid #c9d7ff; border-radius: 20px; font-size: .84rem; color: #364153; white-space: nowrap; }
.cta-btns { display: flex; gap: 6px; }
.cta-login { padding: 5px 12px; border: 1.5px solid #0046ff; border-radius: 8px; color: #0046ff; font-weight: 700; text-decoration: none; font-size: .82rem; }
.cta-signup { padding: 5px 12px; background: #0046ff; border-radius: 8px; color: white; font-weight: 700; text-decoration: none; font-size: .82rem; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .filter-bar { flex-direction: column; align-items: stretch; }
}
</style>
