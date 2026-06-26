<template>
  <footer class="site-footer">
    <div class="footer-inner">

      <!-- 데이터 출처 고지 -->
      <div class="footer-info">
        <div class="footer-info-row">
          <span class="footer-logo">💹 FinFit</span>
          <span class="footer-sep">|</span>
          <span>금융 데이터: 금융감독원 금융상품통합비교공시 (FINLIFE API)</span>
          <span class="footer-sep">|</span>
          <span>주식·원자재 시세: Yahoo Finance (yfinance)</span>
          <span class="footer-sep">|</span>
          <span>지도: 카카오맵 API</span>
        </div>
        <div class="footer-disclaimer">
          ⚠️ 본 서비스의 AI 추천 결과는 참고용이며, 실제 금융 상품 가입 및 투자 결정은 본인 판단에 따릅니다.
          금융상품 가입 전 반드시 상품 설명서를 확인하세요.
        </div>
      </div>

      <div class="footer-divider"></div>

      <!-- 하단: 빠른 접근 서비스 -->
      <div class="footer-bottom">
        <div class="footer-quick">
          <RouterLink to="/test" class="quick-chip">📊 금융성향 검사</RouterLink>
          <RouterLink to="/products/recommend" class="quick-chip">🏦 금융상품 AI 추천</RouterLink>
          <RouterLink to="/cards/recommend" class="quick-chip">💳 카드 AI 추천</RouterLink>
          <RouterLink to="/stocks/recommend" class="quick-chip">📈 주식 AI 추천</RouterLink>
          <RouterLink to="/banks" class="quick-chip">🗺️ 주변 은행 찾기</RouterLink>
        </div>
        <p class="footer-copy">© 2026 FinFit. All Rights Reserved.</p>
      </div>

    </div>
  </footer>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.site-footer {
  background: #1a2133;
  color: #8a94a8;
  padding: 40px 0 28px;
  margin-top: 60px;
  font-size: .84rem;
}

.footer-inner {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
}

.footer-divider {
  height: 1px;
  background: #2a3448;
  margin: 0 0 24px;
}

/* 중단 정보 */
.footer-info { margin-bottom: 24px; }

.footer-info-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
  color: #6b7690;
  font-size: .8rem;
  line-height: 1.6;
}

.footer-logo {
  font-weight: 800;
  color: #c4cad8;
  font-size: .9rem;
}

.footer-sep { color: #2a3448; }

.footer-disclaimer {
  color: #5a6278;
  font-size: .76rem;
  line-height: 1.6;
  padding: 10px 14px;
  background: #1e2840;
  border-left: 3px solid #2a3448;
  border-radius: 0 8px 8px 0;
}

/* 하단 */
.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.footer-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-chip {
  padding: 5px 12px;
  border: 1px solid #2a3448;
  border-radius: 20px;
  color: #8a94a8;
  text-decoration: none;
  font-size: .78rem;
  transition: all .15s;
  background: transparent;
}
.quick-chip:hover {
  border-color: #4a5568;
  color: #c4cad8;
  background: #222d42;
}

.footer-copy {
  margin: 0;
  color: #4a5568;
  font-size: .76rem;
  white-space: nowrap;
}

@media (max-width: 820px) {
  .footer-nav { grid-template-columns: repeat(2, 1fr); }
  .footer-info-row { flex-direction: column; align-items: flex-start; gap: 4px; }
  .footer-sep { display: none; }
}

@media (max-width: 480px) {
  .footer-nav { grid-template-columns: 1fr 1fr; gap: 20px; }
  .footer-bottom { flex-direction: column; align-items: flex-start; }
}
</style>
