<template>
  <nav>
    <div class="nav-header">
      <RouterLink to="/" class="brand" @click="closeMenu">
        <span class="brand-logo">💹</span>FinFit
      </RouterLink>
      
      <button class="hamburger" @click="toggleMenu" :class="{ 'is-active': isMenuOpen }">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>

    <div class="nav-collapse" :class="{ 'is-open': isMenuOpen }">
      <div class="links">
        <RouterLink to="/products" @click="closeMenu">금융상품</RouterLink>
        <RouterLink to="/cards" @click="closeMenu">카드</RouterLink>
        <RouterLink to="/stocks" @click="closeMenu">주식</RouterLink>
        <RouterLink to="/commodities" @click="closeMenu">금·은 시세</RouterLink>
        <RouterLink to="/banks" @click="closeMenu">주변 은행</RouterLink>
        <RouterLink to="/news" @click="closeMenu">뉴스</RouterLink>
        <RouterLink to="/planner" @click="closeMenu" class="planner-link">📊 저축 플래너</RouterLink>
      </div>
      
      <div class="account">
        <template v-if="loggedIn">
          <RouterLink to="/products/recommend" @click="closeMenu">금융상품 AI추천</RouterLink>
          <RouterLink to="/cards/recommend" @click="closeMenu">카드 AI추천</RouterLink>
          <RouterLink to="/stocks/recommend" @click="closeMenu">주식 AI추천</RouterLink>
          <RouterLink to="/test" @click="closeMenu">금융성향 검사</RouterLink>
          <RouterLink to="/mypage" @click="closeMenu">마이페이지</RouterLink>
          <button @click="handleLogout">로그아웃</button>
        </template>
        <template v-else>
          <RouterLink to="/login" @click="closeMenu">로그인</RouterLink>
          <RouterLink to="/signup" class="signup" @click="closeMenu">회원가입</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { api, clearAuth } from '@/api';

const router = useRouter();
const loggedIn = ref(false);

// 모바일 메뉴 열림/닫힘 상태 관리
const isMenuOpen = ref(false);

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

const closeMenu = () => {
  isMenuOpen.value = false;
};

const sync = () => {
  loggedIn.value = !!(localStorage.getItem('accessToken') || localStorage.getItem('token'));
};

async function handleLogout() {
  try {
    await api.post('/accounts/logout/');
  } catch { 
    /* 로컬 토큰은 항상 정리합니다. */ 
  }
  clearAuth();
  closeMenu(); // 로그아웃 시 메뉴 닫기
  await router.push('/');
}

onMounted(() => {
  sync();
  window.addEventListener('auth-changed', sync);
  window.addEventListener('storage', sync);
});

onBeforeUnmount(() => {
  window.removeEventListener('auth-changed', sync);
  window.removeEventListener('storage', sync);
});
</script>

<style scoped>
nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 5%;
  border-bottom: 1px solid #eee;
  background: white;
  position: sticky;
  top: 0;
  z-index: 1000; /* 메뉴가 항상 위에 오도록 z-index를 넉넉하게 */
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: auto;
}

.brand { font-size: 1.4rem; font-weight: 800; color: #0046ff; display: flex; align-items: center; gap: 6px; }
.brand-logo { font-size: 1.3rem; }
a { text-decoration: none; color: #333; }

/* 데스크탑 기본 레이아웃 */
.nav-collapse { display: flex; flex: 1; justify-content: space-between; align-items: center; }
.links { display: flex; gap: 22px; margin-left: 28px; }
.account { display: flex; gap: 14px; align-items: center; }

.signup { padding: 8px 14px; background: #0046ff; color: white; border-radius: 8px; }
.planner-link { color: #0046ff !important; font-weight: 700 !important; }
button { border: 1px solid #ddd; background: white; padding: 8px 12px; border-radius: 8px; cursor: pointer;}

/* 데스크탑에서는 햄버거 버튼 숨김 */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.hamburger span {
  width: 100%;
  height: 2px;
  background-color: #333;
  transition: all 0.3s ease-in-out;
}

/* 850px 이하 모바일/태블릿 화면 (반응형) */
@media(max-width: 850px) {
  nav { flex-direction: column; padding: 0; }
  
  .nav-header { width: 100%; padding: 15px 5%; box-sizing: border-box; }
  
  .hamburger { display: flex; } /* 햄버거 표시 */
  
  /* 메뉴 닫혔을 때 (기본값) */
  .nav-collapse {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-in-out, padding 0.3s ease;
    background: white;
  }
  
  /* 햄버거 눌러서 메뉴 열렸을 때 */
  .nav-collapse.is-open {
    max-height: 500px; /* 내용물이 들어갈 충분한 높이 */
    padding: 20px 5%;
    border-top: 1px solid #f5f5f5;
    box-sizing: border-box;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  }

  .links, .account {
    flex-direction: column;
    width: 100%;
    margin-left: 0;
    gap: 15px;
  }

  .links { padding-bottom: 15px; border-bottom: 1px solid #f5f5f5; }
  .account { padding-top: 15px; }
  
  /* 햄버거 버튼 애니메이션 (X 모양으로 변형) */
  .hamburger.is-active span:nth-child(1) { transform: translateY(8px) rotate(45deg); }
  .hamburger.is-active span:nth-child(2) { opacity: 0; }
  .hamburger.is-active span:nth-child(3) { transform: translateY(-8px) rotate(-45deg); }
}
/* 메뉴 링크와 버튼 글씨 굵게 변경 */
.nav-collapse a,
.nav-collapse button {
  font-weight: 600; /* 600은 Semi-bold 느낌입니다. 더 굵게 원하시면 'bold'나 '700'을 입력하세요. */
}
</style>