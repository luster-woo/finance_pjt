<template>
  <div class="page-bg">
    <div class="container">

      <!-- 성향 미검사 시 -->
      <div v-if="!loading && noTest" class="no-test-card">
        <div class="no-test-icon">📊</div>
        <h2>금융성향 테스트가 필요해요</h2>
        <p>내 투자 성향을 분석해야 맞춤 주식을 추천해드릴 수 있어요.</p>
        <RouterLink to="/test" class="go-test-btn">1분 성향 테스트 하러가기 →</RouterLink>
      </div>

      <template v-else-if="!loading && testInfo">
        <!-- 성향 요약 배너 -->
        <div class="personality-banner">
          <div class="banner-left">
            <span class="banner-eyebrow">AI STOCK MATCH</span>
            <h1 class="banner-title">{{ testInfo.result_type }} 맞춤 주식</h1>
            <p class="banner-sub">내 금융 성향 기반으로 AI가 선별한 종목입니다.</p>

            <!-- 미니 MBTI 바 -->
            <div class="mini-axes" v-if="testInfo.axes">
              <div class="mini-axis" v-for="ax in miniAxes" :key="ax.key">
                <span class="mini-letter" :class="testInfo.axes[ax.key] < 50 ? 'ml-active' : 'ml-dim'">{{ ax.loL }}</span>
                <span class="mini-lo">{{ ax.lo }}</span>
                <div class="mini-track">
                  <div class="mini-fill" :class="ax.key" :style="{ width: testInfo.axes[ax.key] + '%' }"></div>
                  <div class="mini-dot" :style="{ left: testInfo.axes[ax.key] + '%' }"></div>
                </div>
                <span class="mini-hi">{{ ax.hi }}</span>
                <span class="mini-letter" :class="testInfo.axes[ax.key] >= 50 ? 'ml-active' : 'ml-dim'">{{ ax.hiL }}</span>
                <span class="mini-val" :class="testInfo.axes[ax.key] >= 50 ? 'c-hi' : 'c-lo'">
                  {{ testInfo.axes[ax.key] >= 50 ? ax.hi : ax.lo }} {{ testInfo.axes[ax.key] >= 50 ? testInfo.axes[ax.key] : 100 - testInfo.axes[ax.key] }}%
                </span>
              </div>
            </div>
          </div>
          <div class="type-code-badge" v-if="testInfo.axes">
            <span class="code-label">유형 코드</span>
            <strong class="code-value">{{ testInfo.axes.code }}</strong>
          </div>
        </div>

        <!-- AI 채점 기준 -->
        <div class="algo-card">
          <span class="algo-title">AI 채점 기준</span>
          <div class="algo-bars">
            <div class="algo-row"><div class="algo-bar" style="width:45%;background:#0046ff"></div><span>성향 적합도 45%</span></div>
            <div class="algo-row"><div class="algo-bar" style="width:30%;background:#00a984"></div><span>섹터 분산 30%</span></div>
            <div class="algo-row"><div class="algo-bar" style="width:25%;background:#f5a623"></div><span>시가총액 안정성 25%</span></div>
          </div>
          <p class="algo-desc">{{ personalityGuide }}</p>
        </div>

        <!-- 추천 종목 -->
        <p v-if="recLoading" class="status">AI가 종목을 분석하는 중...</p>
        <p v-else-if="recError" class="status error">{{ recError }}</p>

        <div v-else-if="recommendations.length" class="rec-list">
          <div
            v-for="(item, idx) in recommendations"
            :key="item.stock_id"
            class="rec-card"
            @click="$router.push(`/stocks/${item.stock_id}`)"
          >
            <!-- 순위 -->
            <div class="rank" :class="['r' + (idx+1)]">{{ idx + 1 }}</div>

            <!-- 종목 아바타 -->
            <div class="avatar" :style="avatarStyle(item.stock_name)">
              {{ item.stock_name?.slice(0, 1) }}
            </div>

            <!-- 종목 정보 -->
            <div class="stock-info">
              <div class="stock-header">
                <span class="stock-code">{{ item.stock_code }}</span>
                <span class="sector-tag">{{ sectorTag(item.stock_code) }}</span>
              </div>
              <h3 class="stock-name">{{ item.stock_name }}</h3>
              <p class="stock-desc">{{ item.description }}</p>

              <!-- AI 근거 -->
              <div class="ai-reason-box">
                <span class="ai-badge">AI</span>
                <p class="ai-reason">{{ item.reason }}</p>
              </div>
            </div>

            <!-- 가격 + 점수 -->
            <div class="price-score">
              <div v-if="item.latest_price" class="price-block">
                <span class="price-val">{{ item.latest_price.toLocaleString() }}원</span>
                <span
                  class="price-change"
                  :class="item.change_rate > 0 ? 'up' : item.change_rate < 0 ? 'down' : ''"
                >
                  {{ item.change_rate > 0 ? '▲' : item.change_rate < 0 ? '▼' : '' }}
                  {{ item.change_rate != null ? Math.abs(item.change_rate).toFixed(2) + '%' : '-' }}
                </span>
              </div>
              <div class="score-donut" :style="donutStyle(item.score)">
                <span class="donut-num">{{ Math.round(item.score) }}</span>
                <span class="donut-label">점</span>
              </div>
            </div>
          </div>
        </div>


        <div class="actions">
          <RouterLink to="/stocks" class="action-btn secondary">전체 종목 보기</RouterLink>
          <RouterLink to="/test" class="action-btn primary">테스트 다시하기</RouterLink>
        </div>
      </template>

      <p v-else-if="loading" class="status">불러오는 중...</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, getErrorMessage } from '@/api'

const loading = ref(true)
const noTest = ref(false)
const similarStocks = ref([])
const testInfo = ref(null)
const recommendations = ref([])
const recLoading = ref(false)
const recError = ref('')

const PERSONALITY_GUIDES = {
  '안정형 투자자':     '원금 안정성 중심 — 금융주, 배당주, 대형 지주사를 우선 선별했습니다.',
  '안정추구형 투자자': '안정성 위주 — 제조·소재 대형주와 금융주를 균형 있게 선별했습니다.',
  '위험중립형 투자자': '균형 포트폴리오 — 성장성과 안정성을 고루 갖춘 종목을 선별했습니다.',
  '적극투자형 투자자': '성장 중심 — IT·반도체·이차전지 등 고성장 섹터 종목을 선별했습니다.',
  '공격투자형 투자자': '고성장 추구 — 반도체·바이오·엔터 등 높은 변동성 종목을 선별했습니다.',
}
const personalityGuide = computed(() =>
  PERSONALITY_GUIDES[testInfo.value?.result_type] ?? ''
)

const SECTOR_MAP = {
  '005930': '반도체', '000660': '반도체', '058470': '반도체', '042700': '반도체', '000990': '반도체',
  '035420': 'IT', '035720': 'IT', '293490': 'IT', '259960': 'IT',
  '005380': '자동차', '000270': '자동차', '012330': '자동차', '018880': '자동차', '241560': '기계',
  '051910': '소재', '006400': '소재', '003670': '소재', '096770': '에너지',
  '247540': '소재', '086520': '소재',
  '068270': '바이오', '207940': '바이오', '196170': '바이오', '145020': '바이오', '091990': '바이오',
  '005490': '철강', '004020': '철강', '010130': '소재', '011170': '화학',
  '105560': '금융', '055550': '금융', '086790': '금융', '032830': '금융', '000810': '금융', '001450': '금융',
  '017670': '통신', '030200': '통신', '032640': '통신',
  '010950': '에너지', '015760': '에너지',
  '352820': '엔터', '041510': '엔터', '035760': '엔터',
  '090430': '소비재', '097950': '소비재', '139480': '유통', '011200': '해운', '003490': '항공',
  '028260': '지주', '066570': '전자', '034730': '지주', '003550': '지주',
}
function sectorTag(code) { return SECTOR_MAP[code] ?? '기타' }

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

const miniAxes = [
  { key: 'risk',     lo: '안전', hi: '공격', loL: 'S', hiL: 'A' },
  { key: 'rational', lo: '감정', hi: '이성', loL: 'E', hiL: 'R' },
  { key: 'longterm', lo: '단기', hi: '장기', loL: 'T', hiL: 'L' },
  { key: 'active',   lo: '수동', hi: '능동', loL: 'P', hiL: 'N' },
]

function donutStyle(score) {
  const c = score >= 80 ? '#0046ff' : score >= 60 ? '#00a984' : '#f5a623'
  return { background: `conic-gradient(${c} ${score * 3.6}deg, #edf0f5 0deg)` }
}

onMounted(async () => {
  try {
    const [pageRes, resultRes] = await Promise.all([
      api.get('/tests/recommendations/stocks/page/'),
      api.get('/tests/result/').catch(() => ({ data: null })),
    ])
    testInfo.value = { ...pageRes.data.test, axes: resultRes.data?.axes }
    recommendations.value = pageRes.data.recommendations
    // 비슷한 성향 통계
    api.get('/tests/stats/similar-users/').then(r => {
      similarStocks.value = r.data?.similar_type_stocks || []
    }).catch(() => {})
  } catch (e) {
    if (e.response?.status === 404) {
      noTest.value = true
    } else {
      recError.value = getErrorMessage(e, '추천 결과를 불러오지 못했습니다.')
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

/* 미검사 */
.no-test-card {
  text-align: center; background: white; border: 1px solid #e7eaf0;
  border-radius: 24px; padding: 60px 32px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
}
.no-test-icon { font-size: 3rem; margin-bottom: 16px; }
.no-test-card h2 { margin: 0 0 10px; font-size: 1.4rem; color: #191f2b; }
.no-test-card p { margin: 0 0 28px; color: #98a2b3; }
.go-test-btn {
  display: inline-block; padding: 14px 28px; border-radius: 14px;
  background: #0046ff; color: white; font-weight: 800; text-decoration: none;
  box-shadow: 0 8px 20px rgba(0,70,255,.2);
}

/* 성향 배너 */
.personality-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(135deg, #edf3ff 0%, #f0fbf7 100%);
  border: 1px solid #e4edff; border-radius: 24px;
  padding: 32px 36px; margin-bottom: 20px;
  box-shadow: 0 6px 24px rgba(0,70,255,.07);
}
.banner-left { flex: 1; min-width: 0; }
.banner-eyebrow { font-size: .72rem; font-weight: 800; color: #0046ff; letter-spacing: .12em; display: block; margin-bottom: 8px; }
.banner-title { margin: 0 0 6px; font-size: 1.8rem; font-weight: 800; color: #191f2b; letter-spacing: -.035em; }
.banner-sub { margin: 0 0 16px; font-size: .9rem; color: #616b7d; }

/* 미니 MBTI 바 */
.mini-axes { display: flex; flex-direction: column; gap: 7px; }
.mini-axis { display: grid; grid-template-columns: 16px 36px 1fr 36px 16px 80px; align-items: center; gap: 6px; }
.mini-letter { font-size: .78rem; font-weight: 900; text-align: center; }
.ml-active { color: #191f2b; }
.ml-dim { color: #d0d5dd; }
.mini-lo, .mini-hi { font-size: .72rem; font-weight: 700; color: #98a2b3; }
.mini-lo { text-align: right; }
.mini-track { position: relative; height: 8px; background: #edf0f5; border-radius: 4px; }
.mini-fill { height: 100%; border-radius: 4px; transition: width .5s ease; }
.mini-fill.risk     { background: #93b4f8; }
.mini-fill.rational { background: #f9c784; }
.mini-fill.longterm { background: #7dd8c0; }
.mini-fill.active   { background: #c4a8e8; }
.mini-dot {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  width: 13px; height: 13px; border-radius: 50%;
  background: white; border: 2px solid #364153;
  box-shadow: 0 1px 4px rgba(0,0,0,.15); transition: left .5s ease;
}
.mini-val { font-size: .75rem; font-weight: 800; white-space: nowrap; }
.c-hi { color: #0046ff; }
.c-lo { color: #e53e3e; }

/* 유형 코드 뱃지 */
.type-code-badge {
  flex: 0 0 auto; margin-left: 28px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  background: white; border: 1px solid #e7eaf0; border-radius: 16px;
  padding: 18px 22px; box-shadow: 0 3px 12px rgba(0,70,255,.07);
}
.code-label { font-size: .72rem; color: #98a2b3; font-weight: 700; letter-spacing: .06em; }
.code-value { font-size: 1.6rem; font-weight: 900; color: #0046ff; letter-spacing: .12em; }

/* 채점 기준 */
.algo-card { background: #f7f8fb; border-radius: 14px; padding: 16px 18px; margin-bottom: 20px; }
.algo-title { font-size: .78rem; font-weight: 800; color: #364153; display: block; margin-bottom: 10px; }
.algo-bars { display: flex; flex-direction: column; gap: 7px; margin-bottom: 10px; }
.algo-row { display: flex; align-items: center; gap: 10px; font-size: .74rem; color: #616b7d; }
.algo-bar { height: 6px; border-radius: 3px; flex: 0 0 auto; }
.algo-desc { margin: 8px 0 0; font-size: .78rem; color: #616b7d; line-height: 1.6; border-left: 3px solid #e0e7ff; padding-left: 10px; }

/* 유사 성향 통계 */
.stats-block { background: white; border: 1px solid #e7eaf0; border-radius: 20px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 3px 12px rgba(28,39,65,.04); }
.stats-block-title { margin: 0 0 14px; font-size: .9rem; font-weight: 800; color: #191f2b; }
.stat-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.stat-name { font-size: .82rem; font-weight: 600; color: #364153; flex: 0 0 90px; text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat-name:hover { color: #0046ff; }
.stat-track { flex: 1; height: 8px; background: #f0f2f6; border-radius: 4px; overflow: hidden; }
.stat-fill { height: 100%; background: #7b4dce; border-radius: 4px; transition: width .6s ease; }
.stat-pct { font-size: .78rem; font-weight: 800; color: #616b7d; flex: 0 0 32px; text-align: right; }

.criteria-detail { margin: 14px 0; border-top: 1px solid #f0f2f6; padding-top: 14px; display: flex; flex-direction: column; gap: 12px; }
.criterion { display: flex; gap: 10px; }
.crit-dot { width: 10px; height: 10px; border-radius: 50%; flex: 0 0 auto; margin-top: 5px; }
.criterion strong { display: block; font-size: .85rem; color: #191f2b; margin-bottom: 3px; }
.criterion p { margin: 0; font-size: .8rem; color: #697386; line-height: 1.55; }
.crit-note { margin: 4px 0 0; font-size: .75rem; color: #98a2b3; padding-left: 20px; }

/* 추천 카드 */
.rec-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 28px; }
.rec-card {
  display: grid; grid-template-columns: 36px 52px 1fr auto;
  align-items: flex-start; gap: 16px;
  background: white; border: 1px solid #e7eaf0;
  border-radius: 20px; padding: 20px 22px;
  box-shadow: 0 3px 12px rgba(28,39,65,.04);
  cursor: pointer;
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.rec-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(28,39,65,.1); border-color: #c9d7ff; }

.rank {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .95rem; font-weight: 800;
  background: #f0f2f7; color: #616b7d; flex: 0 0 auto;
}
.r1 { background: linear-gradient(135deg,#f5d020,#f5a623); color:white; }
.r2 { background: linear-gradient(135deg,#d4d4d4,#a8a8a8); color:white; }
.r3 { background: linear-gradient(135deg,#d49a6a,#c07a3b); color:white; }

.avatar {
  width: 52px; height: 52px; border-radius: 16px; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; font-weight: 800;
}

.stock-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.stock-code { font-size: .7rem; font-weight: 700; color: #0046ff; letter-spacing: .05em; }
.sector-tag { padding: 2px 8px; border-radius: 6px; background: #eef3ff; color: #0046ff; font-size: .65rem; font-weight: 700; }
.stock-name { margin: 0 0 4px; font-size: 1.05rem; font-weight: 800; color: #191f2b; }
.stock-desc { margin: 0 0 10px; font-size: .78rem; color: #98a2b3; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }

.ai-reason-box { display: flex; gap: 6px; align-items: flex-start; }
.ai-badge { flex: 0 0 auto; padding: 2px 6px; border-radius: 6px; background: linear-gradient(135deg,#0046ff,#0077ff); color:white; font-size: .62rem; font-weight: 800; margin-top: 1px; }
.ai-reason { margin:0; font-size:.78rem; color:#364153; line-height:1.5; }

.price-score { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; min-width: 90px; }
.price-block { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.price-val { font-size: .88rem; font-weight: 800; color: #191f2b; }
.price-change { font-size: .72rem; font-weight: 700; }
.price-change.up { color: #e53e3e; }
.price-change.down { color: #0046ff; }
.score-donut {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: inset 0 0 0 8px white;
}
.donut-num { font-size: .9rem; font-weight: 800; color: #191f2b; line-height: 1; }
.donut-label { font-size: .58rem; color: #98a2b3; }

.actions { display: flex; gap: 12px; justify-content: center; margin-top: 32px; }
.action-btn { padding: 13px 26px; border-radius: 12px; font-size: .9rem; font-weight: 700; text-decoration: none; transition: transform .15s; }
.action-btn:hover { transform: translateY(-2px); }
.action-btn.primary { background: #0046ff; color: white; box-shadow: 0 6px 18px rgba(0,70,255,.2); }
.action-btn.secondary { background: #f0f2f7; color: #364153; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

@media(max-width:600px) {
  .rec-card { grid-template-columns: 36px 1fr; }
  .avatar, .price-score { display: none; }
  .personality-banner { flex-direction: column; gap: 20px; text-align: center; }
  .page-bg { padding: 24px 14px 60px; }
}
</style>
