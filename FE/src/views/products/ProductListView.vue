<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">금융상품 찾기</h1>
        <p class="page-sub">예금·적금 상품을 비교하고 나에게 맞는 상품을 찾아보세요.</p>
      </div>

      <div class="tabs-row">
        <div class="tabs">
          <button
            v-for="item in types"
            :key="item.value"
            class="tab-btn"
            :class="{ active: type === item.value }"
            @click="type = item.value"
          >{{ item.label }}</button>
        </div>
        <div v-if="!isLoggedIn" class="login-cta">
          <span>💡 <strong>로그인</strong>하고 AI 맞춤 추천 받기</span>
          <div class="cta-btns">
            <RouterLink to="/login" class="cta-login">로그인</RouterLink>
            <RouterLink to="/signup" class="cta-signup">회원가입</RouterLink>
          </div>
        </div>
      </div>

      <div class="filter-bar">
        <input v-model.trim="keyword" class="search-input" placeholder="은행명 또는 상품명 검색" />
        <select v-model="sort" class="sort-select">
          <option value="rate_desc">최고금리 높은순</option>
          <option value="rate_asc">최고금리 낮은순</option>
          <option value="name_asc">상품명 가나다순</option>
        </select>
      </div>
      <div class="filter-bar filter-bar-2">
        <div class="filter-group">
          <label class="filter-label">가입기간</label>
          <select v-model="period" class="sort-select">
            <option value="">전체</option>
            <option value="1">1개월</option>
            <option value="3">3개월</option>
            <option value="6">6개월</option>
            <option value="12">12개월</option>
            <option value="24">24개월</option>
            <option value="36">36개월</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">최저금리</label>
          <select v-model="minRate" class="sort-select">
            <option value="">제한 없음</option>
            <option value="2">2% 이상</option>
            <option value="3">3% 이상</option>
            <option value="4">4% 이상</option>
            <option value="5">5% 이상</option>
          </select>
        </div>
      </div>
      <p class="result-count">{{ filteredProducts.length }}개 상품</p>

      <p v-if="loading" class="status">상품을 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <div class="grid">
          <RouterLink
            v-for="p in filteredProducts"
            :key="p.id"
            class="card"
            :to="`/products/${p.id}`"
          >
            <div class="card-top">
              <div class="bank-logo" :style="bankStyle(p.bank_name)">
                {{ bankInitial(p.bank_name) }}
              </div>
              <span class="type-badge" :class="p.product_type">
                {{ p.product_type === 'deposit' ? '예금' : '적금' }}
              </span>
            </div>
            <p class="bank-name">{{ p.bank_name }}</p>
            <h3 class="product-name">{{ p.product_name }}</h3>
            <div v-if="bestRate(p)" class="rate-row">
              <span class="rate-label">최고금리</span>
              <span class="rate-value">{{ bestRate(p) }}%</span>
            </div>
          </RouterLink>
        </div>
        <p v-if="!filteredProducts.length" class="empty">조건에 맞는 상품이 없습니다.</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))

const products = ref([])
const loading = ref(false)
const error = ref('')
const type = ref('all')
const keyword = ref('')
const sort = ref('rate_desc')
const period = ref('')
const minRate = ref('')

const types = [
  { value: 'all',     label: '전체' },
  { value: 'deposit', label: '예금' },
  { value: 'saving',  label: '적금' },
]

function bestRate(p) {
  if (!p.options?.length) return null
  const rates = p.options.map(o => parseFloat(o.max_interest_rate || o.interest_rate)).filter(r => !isNaN(r))
  return rates.length ? Math.max(...rates).toFixed(2) : null
}

function bestRateNum(p) {
  return parseFloat(bestRate(p)) || 0
}

const filteredProducts = computed(() => {
  let list = products.value

  if (type.value !== 'all')
    list = list.filter(p => p.product_type === type.value)

  if (keyword.value)
    list = list.filter(p =>
      p.bank_name.includes(keyword.value) || p.product_name.includes(keyword.value)
    )

  if (period.value)
    list = list.filter(p => p.options?.some(o => String(o.save_trm) === period.value))

  if (minRate.value) {
    const min = parseFloat(minRate.value)
    list = list.filter(p => bestRateNum(p) >= min)
  }

  if (sort.value === 'rate_desc') list = [...list].sort((a, b) => bestRateNum(b) - bestRateNum(a))
  else if (sort.value === 'rate_asc') list = [...list].sort((a, b) => bestRateNum(a) - bestRateNum(b))
  else if (sort.value === 'name_asc') list = [...list].sort((a, b) => a.product_name.localeCompare(b.product_name, 'ko'))

  return list
})

const BANK_BRANDS = {
  // ── 시중은행 ────────────────────────────────
  'KB국민':    { bg: '#F0A500', color: '#fff',    initial: 'KB'   },   // KB 골드
  '국민':      { bg: '#F0A500', color: '#fff',    initial: 'KB'   },   // 국민은행
  '신한':      { bg: '#0046FF', color: '#fff',    initial: '신한' },   // 신한 블루
  '우리':      { bg: '#006EB8', color: '#fff',    initial: '우리' },   // 우리 블루
  '하나':      { bg: '#009A44', color: '#fff',    initial: '하나' },   // 하나 그린
  'NH농협':    { bg: '#007A3D', color: '#fff',    initial: 'NH'   },   // NH 초록
  '농협':      { bg: '#007A3D', color: '#fff',    initial: 'NH'   },
  'IBK기업':   { bg: '#0069B4', color: '#fff',    initial: 'IBK'  },   // IBK 블루
  'SC제일':    { bg: '#00848A', color: '#fff',    initial: 'SC'   },
  '한국스탠다드차타드': { bg: '#00848A', color: '#fff', initial: 'SC' },
  '한국씨티':  { bg: '#003B8E', color: '#fff',    initial: 'Citi' },
  '씨티':      { bg: '#003B8E', color: '#fff',    initial: 'Citi' },
  // ── 인터넷·모바일은행 ────────────────────────
  '카카오뱅크':{ bg: '#FEE500', color: '#391B1B', initial: '카카오' },
  '케이뱅크':  { bg: '#00C4C4', color: '#fff',    initial: 'K'    },
  '토스뱅크':  { bg: '#0064FF', color: '#fff',    initial: 'T'    },
  // ── 지방은행 (실제 브랜드 색상) ──────────────
  'BNK부산':   { bg: '#CC0000', color: '#fff',    initial: 'BNK'  },
  '부산':      { bg: '#CC0000', color: '#fff',    initial: '부산' },   // BNK 부산 빨간색
  '경남':      { bg: '#CC0000', color: '#fff',    initial: '경남' },   // BNK 경남 빨간색
  'DGB대구':   { bg: '#E87722', color: '#fff',    initial: 'DGB'  },
  '대구':      { bg: '#E87722', color: '#fff',    initial: '대구' },   // DGB 오렌지
  'JB광주':    { bg: '#0055A5', color: '#fff',    initial: 'JB'   },
  '광주':      { bg: '#0055A5', color: '#fff',    initial: '광주' },   // 광주은행 파란색
  '전북':      { bg: '#0055A5', color: '#fff',    initial: '전북' },   // 전북은행 파란색
  '제주':      { bg: '#FF6400', color: '#fff',    initial: '제주' },   // 제주은행 주황색
  // ── 특수·기타은행 ────────────────────────────
  'KDB산업':   { bg: '#004A8C', color: '#fff',    initial: 'KDB'  },
  '산업':      { bg: '#004A8C', color: '#fff',    initial: '산업' },
  '수협':      { bg: '#1565C0', color: '#fff',    initial: '수협' },
  '새마을':    { bg: '#E53935', color: '#fff',    initial: 'MG'   },
  '신협':      { bg: '#1976D2', color: '#fff',    initial: '신협' },
  '저축':      { bg: '#546E7A', color: '#fff',    initial: '저축' },
}

function matchBrand(bankName) {
  for (const key of Object.keys(BANK_BRANDS)) {
    if (bankName.includes(key)) return BANK_BRANDS[key]
  }
  return { bg: '#e7eaf0', color: '#616b7d', initial: bankName.slice(0, 2) }
}

function bankStyle(name) {
  const b = matchBrand(name)
  return { background: b.bg, color: b.color }
}
function bankInitial(name) {
  return matchBrand(name).initial
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    products.value = (await api.get('/products/')).data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
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
  display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;
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

/* 비로그인 유도 — 탭과 같은 줄 오른쪽 */
.login-cta {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 7px 14px;
  background: linear-gradient(135deg, #eef3ff, #f0fbf7);
  border: 1px solid #c9d7ff; border-radius: 20px;
  font-size: .84rem; color: #364153; white-space: nowrap;
}
.cta-btns { display: flex; gap: 6px; }
.cta-login {
  padding: 5px 12px; border: 1.5px solid #0046ff; border-radius: 8px;
  color: #0046ff; font-weight: 700; text-decoration: none; font-size: .82rem;
}
.cta-signup {
  padding: 5px 12px; background: #0046ff; border-radius: 8px;
  color: white; font-weight: 700; text-decoration: none; font-size: .82rem;
}

.filter-bar-2 { margin-top: -4px; }
.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-label { font-size: .82rem; font-weight: 600; color: #616b7d; white-space: nowrap; }
.result-count { margin: 0 0 16px; font-size: .82rem; color: #98a2b3; font-weight: 600; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
}

.card {
  background: white; border: 1px solid #e7eaf0; border-radius: 18px;
  padding: 22px; text-decoration: none; color: inherit;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  transition: transform .2s, box-shadow .2s, border-color .2s;
  display: flex; flex-direction: column; gap: 4px;
}
.card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(28,39,65,.1); border-color: #d0d8f0; }

.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }

.bank-logo {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 800; letter-spacing: -.01em;
  flex: 0 0 auto;
}

.type-badge { padding: 4px 10px; border-radius: 8px; font-size: .72rem; font-weight: 700; }
.type-badge.deposit { background: #eef3ff; color: #0046ff; }
.type-badge.saving  { background: #f0faf6; color: #00a984; }

.bank-name { margin: 0; font-size: .75rem; color: #98a2b3; font-weight: 600; }
.product-name { margin: 4px 0 10px; font-size: .98rem; font-weight: 800; color: #191f2b; line-height: 1.4; }

.rate-row { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 12px; border-top: 1px solid #f0f2f6; }
.rate-label { font-size: .72rem; color: #98a2b3; font-weight: 600; }
.rate-value { font-size: 1.05rem; font-weight: 800; color: #0046ff; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }
.empty { text-align: center; padding: 60px 0; color: #98a2b3; font-size: .9rem; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .filter-bar { flex-direction: column; }
}
</style>
