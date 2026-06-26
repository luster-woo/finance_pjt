<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">주식 종목</h1>
        <p class="page-sub">관심 종목을 찾아 시세와 토론을 확인해보세요.</p>
      </div>

      <div class="search-row">
        <div class="search-bar">
          <span class="search-icon">🔍</span>
          <input v-model="keyword" class="search-input" placeholder="종목명 또는 코드 검색..." />
          <button v-if="keyword" class="clear-btn" @click="keyword = ''">✕</button>
        </div>
        <div v-if="!isLoggedIn" class="login-cta">
          <span>💡 <strong>로그인</strong>하고 주식 AI 추천 받기</span>
          <div class="cta-btns">
            <RouterLink to="/login" class="cta-login">로그인</RouterLink>
            <RouterLink to="/signup" class="cta-signup">회원가입</RouterLink>
          </div>
        </div>
      </div>

      <p v-if="loading" class="status">종목을 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <template v-else>
        <p class="result-count">총 <strong>{{ filtered.length }}</strong>개 종목</p>

        <div class="stock-grid">
          <RouterLink
            v-for="stock in filtered"
            :key="stock.id"
            :to="`/stocks/${stock.id}`"
            class="stock-card"
          >
            <div class="card-header">
              <div class="stock-avatar" :style="avatarStyle(stock.stock_name)">
                {{ stock.stock_name?.slice(0, 1) }}
              </div>
              <div class="stock-code-wrap">
                <span class="stock-code">{{ stock.stock_code }}</span>
                <span class="market-badge">KOSPI</span>
              </div>
            </div>
            <h3 class="stock-name">{{ stock.stock_name }}</h3>
            <p class="stock-desc">{{ stock.description || '종목 설명이 없습니다.' }}</p>
            <div class="card-footer">
              <div v-if="stock.latest_price" class="price-wrap">
                <span class="price-val">{{ Number(stock.latest_price).toLocaleString() }}원</span>
                <span class="price-rate" :class="stock.latest_change_rate > 0 ? 'up' : stock.latest_change_rate < 0 ? 'down' : 'flat'">
                  {{ stock.latest_change_rate > 0 ? '▲' : stock.latest_change_rate < 0 ? '▼' : '' }}
                  {{ stock.latest_change_rate != null ? Math.abs(Number(stock.latest_change_rate)).toFixed(2) + '%' : '' }}
                </span>
              </div>
              <span class="detail-link">자세히 보기 →</span>
            </div>
          </RouterLink>
        </div>

        <p v-if="!filtered.length" class="empty">
          <span class="empty-icon">📭</span><br>
          검색 결과가 없습니다.
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))

const stocks = ref([])
const loading = ref(true)
const error = ref('')
const keyword = ref('')

const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return stocks.value
  return stocks.value.filter(
    s => s.stock_name?.toLowerCase().includes(q) || s.stock_code?.toLowerCase().includes(q)
  )
})

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

onMounted(async () => {
  try {
    stocks.value = (await api.get('/stocks/')).data
  } catch (e) {
    error.value = getErrorMessage(e, '주식 목록을 불러오지 못했습니다.')
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

.search-row { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.search-bar {
  flex: 1; display: flex; align-items: center; gap: 10px;
  background: white; border: 1.5px solid #e7eaf0;
  border-radius: 14px; padding: 12px 18px;
  box-shadow: 0 2px 10px rgba(28,39,65,.04);
  transition: border-color .15s;
}
.search-bar:focus-within { border-color: #0046ff; }
.search-icon { font-size: 1rem; color: #98a2b3; flex: 0 0 auto; }
.search-input {
  flex: 1; border: none; outline: none;
  font-size: .95rem; color: #191f2b; background: transparent;
}
.clear-btn {
  background: none; border: none; color: #98a2b3;
  font-size: .85rem; cursor: pointer; padding: 2px 6px; border-radius: 6px;
}
.clear-btn:hover { background: #f0f2f6; color: #364153; }

.result-count { margin: 0 0 16px; font-size: .88rem; color: #98a2b3; }
.result-count strong { color: #364153; }

.stock-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.stock-card {
  background: white; border: 1px solid #e7eaf0; border-radius: 18px;
  padding: 22px; text-decoration: none; color: inherit;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  transition: transform .2s, box-shadow .2s, border-color .2s;
  display: flex; flex-direction: column; gap: 8px;
}
.stock-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(28,39,65,.1);
  border-color: #c9d7ff;
}

.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }

.stock-avatar {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; font-weight: 800; flex: 0 0 auto;
}

.stock-code-wrap { display: flex; flex-direction: column; gap: 4px; }
.stock-code { font-size: .72rem; font-weight: 700; color: #0046ff; letter-spacing: .06em; }
.market-badge {
  display: inline-block; padding: 2px 8px;
  background: #eef3ff; color: #0046ff;
  border-radius: 6px; font-size: .65rem; font-weight: 700;
}

.stock-name { margin: 0; font-size: 1.05rem; font-weight: 800; color: #191f2b; line-height: 1.3; }
.stock-desc {
  margin: 0; font-size: .82rem; color: #98a2b3; line-height: 1.55;
  flex: 1;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.card-footer { padding-top: 12px; border-top: 1px solid #f0f2f6; margin-top: auto; display: flex; align-items: center; justify-content: space-between; }
.price-wrap { display: flex; align-items: baseline; gap: 6px; }
.price-val { font-size: .92rem; font-weight: 800; color: #191f2b; }
.price-rate { font-size: .78rem; font-weight: 700; }
.price-rate.up { color: #e53e3e; }
.price-rate.down { color: #0046ff; }
.price-rate.flat { color: #98a2b3; }
.detail-link { font-size: .82rem; font-weight: 700; color: #0046ff; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }
.empty { text-align: center; padding: 60px 0; color: #98a2b3; font-size: .9rem; line-height: 2; }
.empty-icon { font-size: 2rem; }

.login-cta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 7px 14px; background: linear-gradient(135deg, #eef3ff, #f0fbf7); border: 1px solid #c9d7ff; border-radius: 20px; font-size: .84rem; color: #364153; white-space: nowrap; }
.cta-btns { display: flex; gap: 6px; }
.cta-login { padding: 5px 12px; border: 1.5px solid #0046ff; border-radius: 8px; color: #0046ff; font-weight: 700; text-decoration: none; font-size: .82rem; }
.cta-signup { padding: 5px 12px; background: #0046ff; border-radius: 8px; color: white; font-weight: 700; text-decoration: none; font-size: .82rem; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .stock-grid { grid-template-columns: 1fr; }
}
</style>
