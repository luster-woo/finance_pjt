import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    // 🏠 메인 홈
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    
    // 👤 회원 관리 (Accounts)
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/accounts/LoginView.vue')
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/accounts/SignupView.vue')
    },

    // 🏦 금융 상품 (Products)
    {
      path: '/products',
      name: 'products',
      component: () => import('../views/products/ProductListView.vue')
    },
    {
      path: '/products/recommend',
      name: 'product-recommend',
      component: () => import('../views/products/ProductRecommendView.vue')
    },
    {
      path: '/products/:id',
      name: 'product-detail',
      component: () => import('../views/products/ProductDetailView.vue')
    },

    // 🗂️ 마이페이지 (MyPage)
    {
      path: '/mypage',
      name: 'mypage',
      component: () => import('../views/mypage/MyPageView.vue')
    },
    
    // 👤 내 정보 수정
    {
      path: '/mypage/edit',
      name: 'profile-edit',
      component: () => import('../views/accounts/ProfileEditView.vue')
    },

    // 📈 주식 (Stocks) & 종목 토론방
    {
      path: '/stocks',
      name: 'stocks',
      component: () => import('../views/stocks/StockListView.vue')
    },
    {
      path: '/stocks/recommend',
      name: 'stock-recommend',
      component: () => import('../views/stocks/StockRecommendView.vue')
    },
    {
      path: '/stocks/:id',
      name: 'stock-detail',
      component: () => import('../views/stocks/StockDetailView.vue')
    },

    // 🏢 주변 은행 찾기 (Bank Map)
    {
      path: '/banks',
      name: 'banks',
      component: () => import('../views/banks/BankMapView.vue')
    },

    // 📝 금융 성향 테스트
    {
      path: '/test',
      name: 'financial-test',
      component: () => import('../views/tests/FinancialTestView.vue')
    },

    // 🎁 AI 추천 결과 페이지
    {
      path: '/test/result',
      name: 'test-result',
      component: () => import('../views/tests/RecommendationView.vue')
    },

    // 💳 카드 (Cards)
    {
      path: '/cards',
      name: 'cards',
      component: () => import('../views/cards/CardListView.vue')
    },
    {
      path: '/cards/recommend',
      name: 'card-recommend',
      component: () => import('../views/cards/CardRecommendView.vue')
    },
    {
      path: '/cards/:id',
      name: 'card-detail',
      component: () => import('../views/cards/CardDetailView.vue')
    },

    // 📊 목표 저축 플래너
    {
      path: '/planner',
      name: 'planner',
      component: () => import('../views/planner/PlannerView.vue')
    },

    // 🥇 원자재 (금·은)
    {
      path: '/commodities',
      name: 'commodities',
      component: () => import('../views/stocks/CommodityView.vue')
    },

    // 📰 금융 뉴스 및 원자재
    {
      path: '/news',
      name: 'news',
      component: () => import('../views/news/NewsListView.vue')
    },
    {
      path: '/news/:id',
      name: 'news-detail',
      component: () => import('../views/news/NewsDetailView.vue')
    },
  ]
})

const protectedRoutes = new Set(['mypage', 'profile-edit', 'financial-test', 'test-result', 'stock-recommend', 'card-recommend', 'product-recommend', 'planner'])

router.beforeEach((to) => {
  const loggedIn = !!(localStorage.getItem('accessToken') || localStorage.getItem('token'))
  if (protectedRoutes.has(to.name) && !loggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if ((to.name === 'login' || to.name === 'signup') && loggedIn) return { name: 'home' }
})

export default router
