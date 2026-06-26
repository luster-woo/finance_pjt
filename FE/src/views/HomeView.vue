<template>
  <main class="home-page">
    <section class="hero-wrap">
      <div class="hero">
        <div class="hero-copy">
          <span class="hero-badge">나를 위한 금융 탐색</span>
          <h1>복잡한 금융,<br><em>나답게</em> 시작하세요</h1>
          <p>예·적금부터 카드와 주식까지 비교하고<br>내 성향에 맞는 금융 선택을 찾아보세요.</p>
          <div class="hero-actions">
            <RouterLink to="/products" class="primary-action">금융상품 둘러보기 <span>→</span></RouterLink>
            <RouterLink to="/test" class="secondary-action">1분 금융성향 검사</RouterLink>
          </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
          <div class="visual-glow"></div>
          <div class="visual-card main-card">
            <span class="mini-label">💹 FINFIT</span>
            <strong>한눈에 찾는<br>나의 금융생활</strong>
            <div class="mini-chart">
              <i></i><i></i><i></i><i></i><i></i>
            </div>
          </div>
          <div class="visual-card rate-card">
            <span class="card-icon">↗</span>
            <div><small>맞춤 상품</small><b>간편 비교</b></div>
          </div>
          <div class="visual-card test-card">
            <span class="card-icon mint">✓</span>
            <div><small>금융 성향</small><b>1분 진단</b></div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI 주간 브리핑 (로그인 사용자, features 위) -->
    <section class="briefing-section" v-if="isLoggedIn && briefing">
      <div class="briefing-inner">
        <div class="briefing-header">
          <div class="briefing-title-group">
            <span class="briefing-badge">🗞️ AI 주간 브리핑</span>
            <span class="briefing-week">{{ formatWeek(briefing.week_start) }}</span>
          </div>
          <span class="briefing-type" v-if="briefing.financial_type && briefing.financial_type !== '일반'">{{ briefing.financial_type }}</span>
        </div>
        <div class="briefing-body">
          <div class="briefing-economy">
            <div class="eco-item" v-for="item in briefing.economy_summary" :key="item.title">
              <span class="eco-label">{{ item.title }}</span>
              <span class="eco-desc">{{ item.desc }}</span>
            </div>
          </div>
          <div class="briefing-actions">
            <p class="actions-title">🎯 이번 주 추천 행동</p>
            <ul>
              <li v-for="(action, i) in briefing.actions" :key="i">{{ action }}</li>
            </ul>
          </div>
          <div class="briefing-tip" v-if="briefing.tip">
            <span class="tip-label">💡 이번 주 TIP</span>
            <p>{{ briefing.tip }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 기능 소개 섹션 -->
    <section class="features-section">
      <div class="features-inner">
        <h2 class="features-title">한 곳에서 완성하는 나의 금융 생활</h2>
        <div class="features-grid">
          <RouterLink to="/products" class="feature-card">
            <span class="feature-icon">🏦</span>
            <h3>금융상품 비교</h3>
            <p>예금·적금 금리를 한눈에 비교하고 금리 높은순 정렬·은행 검색으로 최적 상품을 찾아보세요.</p>
          </RouterLink>
          <RouterLink to="/cards" class="feature-card">
            <span class="feature-icon">💳</span>
            <h3>카드 AI 추천</h3>
            <p>식비·교통·쇼핑 등 소비 습관을 선택하면 AI가 혜택 매칭률을 채점해 최적 카드를 추천해드립니다.</p>
          </RouterLink>
          <RouterLink to="/stocks" class="feature-card">
            <span class="feature-icon">📈</span>
            <h3>주식 시세 & 추천</h3>
            <p>KOSPI·KOSDAQ 주요 70여 개 종목의 실시간 시세 차트를 확인하고, 내 성향 맞춤 종목을 추천받으세요.</p>
          </RouterLink>
          <RouterLink to="/test" class="feature-card">
            <span class="feature-icon">🧠</span>
            <h3>금융 성향 진단</h3>
            <p>위험 수용도·투자 기간·심리 반응 10가지 지표로 내 투자 성향을 정밀 분석하고 맞춤 전략을 받으세요.</p>
          </RouterLink>
          <RouterLink to="/banks" class="feature-card">
            <span class="feature-icon">🗺️</span>
            <h3>주변 은행 찾기</h3>
            <p>현재 위치 기반으로 주변 은행 지점을 지도에서 찾고, 운영시간과 전화번호를 바로 확인하세요.</p>
          </RouterLink>
          <RouterLink to="/news" class="feature-card">
            <span class="feature-icon">📰</span>
            <h3>금융 뉴스 & 커뮤니티</h3>
            <p>실시간 금융·경제 뉴스와 종목별 토론방에서 투자 인사이트를 얻고 의견을 나눠보세요.</p>
          </RouterLink>
        </div>
      </div>
    </section>

    <section class="dashboard">
      <article class="dashboard-card">
        <div class="section-header">
          <div class="title-group">
            <span class="title-icon news-icon">N</span>
            <div>
            <span class="eyebrow">MARKET NEWS</span>
            <h2>최신 금융 뉴스</h2>
            </div>
          </div>
          <RouterLink to="/news" class="more-link">전체보기 →</RouterLink>
        </div>

        <p v-if="isLoading" class="status">뉴스를 불러오는 중...</p>
        <p v-else-if="newsError" class="status error">{{ newsError }}</p>
        <ul v-else class="content-list">
          <li v-for="article in latestNews" :key="article.id">
            <RouterLink :to="`/news/${article.id}`" class="list-link">
              <div class="list-copy">
                <strong>{{ article.title }}</strong>
                <p>{{ article.summary || '기사 요약이 없습니다.' }}</p>
                <small>{{ article.publisher || '출처 미상' }} · {{ formatDate(article.published_at) }}</small>
              </div>
              <span class="arrow">›</span>
            </RouterLink>
          </li>
          <li v-if="latestNews.length === 0" class="empty">등록된 뉴스가 없습니다.</li>
        </ul>
      </article>

      <article class="dashboard-card">
        <div class="section-header">
          <div class="title-group">
            <span class="title-icon community-icon">C</span>
            <div>
            <span class="eyebrow community-label">COMMUNITY</span>
            <h2>커뮤니티 인기글</h2>
            </div>
          </div>
          <RouterLink to="/stocks" class="more-link">종목 보러가기 →</RouterLink>
        </div>

        <p v-if="isLoading" class="status">인기글을 불러오는 중...</p>
        <p v-else-if="communityError" class="status error">{{ communityError }}</p>
        <ol v-else class="ranking-list">
          <li v-for="(post, index) in popularPosts" :key="post.id">
            <RouterLink v-if="post.stock" :to="`/stocks/${post.stock}`" class="list-link">
              <span class="rank">{{ index + 1 }}</span>
              <div class="list-copy">
                <strong>{{ post.title }}</strong>
                <p>{{ post.content }}</p>
                <small>좋아요 {{ post.likes_count }}</small>
              </div>
              <span class="arrow">›</span>
            </RouterLink>
            <div v-else class="list-link">
              <span class="rank">{{ index + 1 }}</span>
              <div class="list-copy">
                <strong>{{ post.title }}</strong>
                <p>{{ post.content }}</p>
                <small>좋아요 {{ post.likes_count }}</small>
              </div>
            </div>
          </li>
          <li v-if="popularPosts.length === 0" class="empty">아직 등록된 커뮤니티 글이 없습니다.</li>
        </ol>
      </article>
    </section>
    <!-- 브리핑 제거됨 (features 위로 이동) -->
    <section class="briefing-section-removed" v-if="false">
      <div class="briefing-inner">
        <div class="briefing-header">
          <div class="briefing-title-group">
            <span class="briefing-badge">🗞️ AI 주간 브리핑</span>
            <span class="briefing-week">{{ formatWeek(briefing.week_start) }}</span>
          </div>
          <span class="briefing-type" v-if="briefing.financial_type && briefing.financial_type !== '일반'">{{ briefing.financial_type }}</span>
        </div>
        <div class="briefing-body">
          <div class="briefing-economy">
            <div class="eco-item" v-for="item in briefing.economy_summary" :key="item.title">
              <span class="eco-label">{{ item.title }}</span>
              <span class="eco-desc">{{ item.desc }}</span>
            </div>
          </div>
          <div class="briefing-actions">
            <p class="actions-title">🎯 이번 주 추천 행동</p>
            <ul>
              <li v-for="(action, i) in briefing.actions" :key="i">{{ action }}</li>
            </ul>
          </div>
          <div class="briefing-tip" v-if="briefing.tip">
            <span class="tip-label">💡 이번 주 TIP</span>
            <p>{{ briefing.tip }}</p>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const latestNews = ref([])
const popularPosts = ref([])
const briefing = ref(null)
const isLoading = ref(true)
const newsError = ref('')
const communityError = ref('')
const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))

const formatDate = (value) => (value ? new Date(value).toLocaleDateString('ko-KR') : '-')
const formatWeek = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 주`
}

onMounted(async () => {
  // 브리핑 비동기 로드 (실패해도 홈 정상 표시)
  api.get('/news/briefing/').then(r => { if (r.data) briefing.value = r.data }).catch(() => {})

  const [newsResult, communityResult] = await Promise.allSettled([
    api.get('/news/'),
    api.get('/community/posts/'),
  ])

  if (newsResult.status === 'fulfilled') {
    latestNews.value = newsResult.value.data.slice(0, 4)  // 뉴스 4개
  } else {
    newsError.value = getErrorMessage(newsResult.reason, '뉴스를 불러오지 못했습니다.')
  }

  if (communityResult.status === 'fulfilled') {
    popularPosts.value = [...communityResult.value.data]
      .sort((a, b) => b.likes_count - a.likes_count)
      .slice(0, 4)  // 커뮤니티 4개 (뉴스와 동일)
  } else {
    communityError.value = getErrorMessage(
      communityResult.reason,
      '커뮤니티 인기글을 불러오지 못했습니다.',
    )
  }

  isLoading.value = false
})
</script>

<style scoped>
.home-page { min-height: 100vh; background: #f7f8fb; color: #191f2b; }
.hero-wrap { padding: 38px 0 28px; background: #fff; }
.hero {
  width: min(1180px, calc(100% - 40px));
  box-sizing: border-box;
  min-height: 480px;
  margin: 0 auto;
  padding: 62px 72px;
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  align-items: center;
  overflow: hidden;
  position: relative;
  border-radius: 32px;
  background: linear-gradient(125deg, #eef3ff 0%, #f5f8ff 50%, #ecfbf7 100%);
}
.hero::before { content: ''; position: absolute; width: 360px; height: 360px; left: -180px; bottom: -250px; border-radius: 50%; background: rgba(0,70,255,.08); }
.hero-copy { position: relative; z-index: 2; }
.hero-badge { display: inline-flex; padding: 7px 12px; margin-bottom: 18px; border-radius: 20px; background: rgba(0,70,255,.08); color: #0046ff; font-size: .8rem; font-weight: 800; }
.hero h1 { margin: 0; font-size: clamp(2.45rem, 4.5vw, 4.15rem); line-height: 1.13; letter-spacing: -.055em; }
.hero h1 em { color: #0046ff; font-style: normal; }
.hero p { margin: 23px 0 0; color: #616b7d; font-size: 1.05rem; line-height: 1.75; }
.hero-actions { display: flex; align-items: center; gap: 11px; margin-top: 32px; }
.hero-actions a { padding: 14px 20px; border-radius: 12px; text-decoration: none; font-size: .94rem; font-weight: 750; transition: transform .18s ease, box-shadow .18s ease; }
.hero-actions a:hover { transform: translateY(-2px); }
.primary-action { background: #0046ff; color: #fff; box-shadow: 0 9px 22px rgba(0,70,255,.2); }
.primary-action span { margin-left: 9px; }
.secondary-action { border: 1px solid #d8deea; background: rgba(255,255,255,.72); color: #364153; }

.hero-visual { height: 330px; position: relative; }
.visual-glow { position: absolute; width: 270px; height: 270px; top: 25px; left: 50%; transform: translateX(-50%); border-radius: 50%; background: linear-gradient(145deg, rgba(0,70,255,.14), rgba(0,214,168,.2)); filter: blur(2px); }
.visual-card { position: absolute; background: rgba(255,255,255,.92); border: 1px solid rgba(255,255,255,.9); box-shadow: 0 20px 45px rgba(29,52,102,.14); backdrop-filter: blur(12px); }
.main-card { width: 225px; height: 260px; top: 34px; left: 50%; transform: translateX(-50%) rotate(3deg); padding: 27px; border-radius: 25px; background: linear-gradient(155deg, #0757ff, #003fd5); color: white; }
.mini-label { font-size: .65rem; letter-spacing: .16em; opacity: .72; }
.main-card strong { display: block; margin-top: 42px; font-size: 1.35rem; line-height: 1.45; }
.mini-chart { height: 60px; margin-top: 28px; display: flex; align-items: flex-end; gap: 8px; }
.mini-chart i { width: 15px; border-radius: 5px 5px 2px 2px; background: rgba(255,255,255,.82); }
.mini-chart i:nth-child(1) { height: 24%; }.mini-chart i:nth-child(2) { height: 48%; }.mini-chart i:nth-child(3) { height: 38%; }.mini-chart i:nth-child(4) { height: 72%; }.mini-chart i:nth-child(5) { height: 95%; background: #64e6c7; }
.rate-card, .test-card { display: flex; align-items: center; gap: 11px; padding: 13px 15px; border-radius: 15px; z-index: 2; }
.rate-card { left: 1%; top: 65px; }.test-card { right: -2%; bottom: 45px; }
.rate-card small, .test-card small { display: block; color: #8a94a6; font-size: .7rem; margin-bottom: 3px; }
.rate-card b, .test-card b { font-size: .88rem; }
.card-icon { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 10px; background: #e8efff; color: #0046ff; font-weight: 900; }
.card-icon.mint { background: #e4f9f3; color: #00a984; }

/* 기능 소개 */
.features-section { background: white; padding: 60px 0; border-top: 1px solid #f0f2f6; }
.features-inner { width: min(1180px, calc(100% - 40px)); margin: 0 auto; }
.features-title { text-align: center; font-size: 1.55rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; margin: 0 0 36px; }
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature-card {
  padding: 26px 22px; border: 1px solid #e7eaf0; border-radius: 18px; background: #fafbfc;
  transition: box-shadow .18s, border-color .18s, transform .18s;
  text-decoration: none; color: inherit; display: block;
}
.feature-card:hover { box-shadow: 0 8px 22px rgba(28,39,65,.08); border-color: #d0d8f0; transform: translateY(-3px); }
.feature-icon { font-size: 2rem; display: block; margin-bottom: 12px; }
.feature-card h3 { margin: 0 0 8px; font-size: 1rem; font-weight: 800; color: #191f2b; }
.feature-card p { margin: 0; font-size: .86rem; color: #697386; line-height: 1.65; }

/* AI 주간 브리핑 — features 위 */
.briefing-section { background: #f7f8fb; padding: 32px 0; }
.briefing-inner {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
  box-sizing: border-box;
  background: linear-gradient(135deg, #1a2133 0%, #1e2d4a 100%);
  border-radius: 22px; padding: 28px 32px;
  box-shadow: 0 8px 32px rgba(0,70,255,.12);
}
.briefing-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }
.briefing-title-group { display: flex; align-items: center; gap: 12px; }
.briefing-badge { font-size: .88rem; font-weight: 800; color: #7dd8c0; }
.briefing-week { font-size: .8rem; color: #5a6278; }
.briefing-type { padding: 4px 12px; background: rgba(0,70,255,.25); color: #93b4f8; border-radius: 20px; font-size: .78rem; font-weight: 700; }
.briefing-body { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.briefing-economy { display: flex; flex-direction: column; gap: 8px; }
.eco-item { display: flex; flex-direction: column; gap: 2px; }
.eco-label { font-size: .7rem; font-weight: 800; color: #7dd8c0; letter-spacing: .06em; }
.eco-desc { font-size: .84rem; color: #c4cad8; line-height: 1.5; }
.briefing-actions p.actions-title { margin: 0 0 8px; font-size: .78rem; font-weight: 800; color: #f9c784; }
.briefing-actions ul { margin: 0; padding-left: 16px; display: flex; flex-direction: column; gap: 6px; }
.briefing-actions li { font-size: .84rem; color: #c4cad8; line-height: 1.5; }
.briefing-tip { background: rgba(255,255,255,.05); border-left: 3px solid #f9c784; padding: 12px 14px; border-radius: 0 10px 10px 0; }
.tip-label { display: block; font-size: .72rem; font-weight: 800; color: #f9c784; margin-bottom: 6px; }
.briefing-tip p { margin: 0; font-size: .84rem; color: #c4cad8; line-height: 1.6; }
.briefing-footer { border-top: 1px solid rgba(255,255,255,.08); padding-top: 12px; }
.briefing-login-hint { font-size: .82rem; color: #5a6278; }
.briefing-login-hint a { color: #93b4f8; font-weight: 700; }

.dashboard {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
  box-sizing: border-box;
  padding: 34px 0 80px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22px;
  position: relative;
}

.dashboard-card { background: white; border: 1px solid #e7eaf0; border-radius: 18px; padding: 25px; box-shadow: 0 5px 18px rgba(28,39,65,.045); min-width: 0; }
.section-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding-bottom: 18px; border-bottom: 1px solid #edf0f5; }
.title-group { display: flex; align-items: center; gap: 12px; }
.title-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; font-size: .85rem; font-weight: 900; }
.news-icon { background: #eaf0ff; color: #0046ff; }.community-icon { background: #e7faf5; color: #00a984; }
.section-header h2 { margin: 3px 0 0; font-size: 1.28rem; letter-spacing: -.025em; }
.eyebrow { color: #0046ff; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.1em; }
.community-label { color: #00a984; }
.more-link { color: #667085; font-size: 0.86rem; text-decoration: none; white-space: nowrap; }

.content-list, .ranking-list { list-style: none; margin: 0; padding: 0; }
.list-link { min-height: 70px; display: flex; align-items: center; gap: 14px; padding: 14px 3px; border-bottom: 1px solid #f0f2f6; color: #252b36; text-decoration: none; transition: background .16s ease, padding .16s ease; }
.list-link:hover { padding-left: 8px; background: #fafbfc; }
.list-copy { min-width: 0; flex: 1; }
.list-copy strong, .list-copy p { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list-copy p { color: #697386; font-size: 0.88rem; margin: 6px 0; }
.list-copy small { color: #98a2b3; }
.arrow { color: #98a2b3; font-size: 1.5rem; }
.rank { width: 30px; height: 30px; display: grid; place-items: center; flex: 0 0 auto; border-radius: 9px; background: #e9fbf5; color: #008f70; font-weight: 800; }
.ranking-list li:first-child .rank { background: #00a984; color: white; }
.status, .empty { padding: 36px 4px; color: #7b8495; text-align: center; }
.error { color: #d14343; }

@media (max-width: 820px) {
  .hero-wrap { padding: 22px 0; }
  .hero { grid-template-columns: 1fr; padding: 48px 36px 30px; text-align: center; }
  .hero p br { display: none; }
  .hero-actions { justify-content: center; }
  .hero-visual { height: 270px; margin-top: 20px; transform: scale(.88); }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .briefing-body { grid-template-columns: 1fr; }
  .briefing-inner { padding: 20px; }
  .dashboard { grid-template-columns: 1fr; }
}
@media (max-width: 540px) {
  .features-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .briefing-inner { width: min(1180px, calc(100% - 24px)); }
  .hero-wrap { padding: 12px 0; }
  .hero { width: min(1180px, calc(100% - 24px)); }
  .hero { padding: 40px 22px 22px; border-radius: 22px; }
  .hero h1 { font-size: 2.4rem; }
  .hero-visual { margin-left: -20px; margin-right: -20px; }
  .dashboard { width: min(100% - 24px, 1180px); padding-top: 24px; }
  .dashboard-card { padding: 20px; border-radius: 18px; }
  .hero-actions { flex-direction: column; }
  .hero-actions a { width: 100%; box-sizing: border-box; }
  .section-header { align-items: center; }
}
</style>
