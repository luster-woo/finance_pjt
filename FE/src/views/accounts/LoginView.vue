<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>로그인</h1>
      <p>금융 서비스의 새로운 시작</p>
      <form class="auth-form" @submit.prevent="login">
        <input v-model.trim="username" type="text" placeholder="아이디" required />
        <input v-model="password" type="password" placeholder="비밀번호" required />
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? '로그인 중...' : '로그인' }}
        </button>
      </form>
      <div class="divider"><span>또는 소셜 계정으로 로그인</span></div>

      <div class="social-btns">
        <button class="social-btn kakao" @click="socialAlert('카카오')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="#3A1D1D">
            <path d="M12 3C6.477 3 2 6.477 2 10.857c0 2.784 1.647 5.226 4.134 6.72L5.11 21l4.663-2.476A11.07 11.07 0 0012 18.714c5.523 0 10-3.477 10-7.857C22 6.477 17.523 3 12 3z"/>
          </svg>
          카카오로 시작하기
        </button>
        <button class="social-btn google" @click="socialAlert('구글')">
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          구글로 시작하기
        </button>
        <button class="social-btn apple" @click="socialAlert('애플')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.7 9.05 7.4c1.39.07 2.35.67 3.15.72 1.19-.24 2.33-.93 3.62-.84 1.54.13 2.7.7 3.46 1.86-3.14 1.88-2.4 5.98.72 7.14-.62 1.47-1.37 2.92-2.95 4zm-3.22-17.9c.06 2-1.73 3.66-3.6 3.47-.27-1.83 1.58-3.66 3.6-3.47z"/>
          </svg>
          Apple로 시작하기
        </button>
      </div>

      <p class="auth-link">계정이 없으신가요? <RouterLink to="/signup">회원가입</RouterLink></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, getErrorMessage, saveAuth } from '@/api'

const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

function socialAlert(provider) {
  alert(`${provider} 로그인은 준비 중입니다.`)
}

async function login() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await api.post('/accounts/login/', {
      username: username.value,
      password: password.value,
    })
    saveAuth(data)
    await router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '아이디 또는 비밀번호를 확인해 주세요.')
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container { min-height: 80vh; display: flex; justify-content: center; align-items: flex-start; background: #f4f6fa; padding-top: 10vh; }
.auth-card { width: 100%; max-width: 400px; padding: 40px; background: white; border-radius: 24px; box-shadow: 0 10px 25px rgba(0,0,0,.05); text-align: center; }
.auth-form input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #e1e1e1; border-radius: 12px; box-sizing: border-box; }
.submit-btn { width: 100%; padding: 15px; margin-top: 15px; border: 0; border-radius: 12px; color: white; background: #0046ff; font-weight: bold; cursor: pointer; }
.submit-btn:disabled { opacity: .6; cursor: wait; }
.error { color: #d93025; text-align: left; font-size: .9rem; }
.auth-link { margin-top: 20px; color: #666; }
.auth-link a { color: #0046ff; font-weight: bold; text-decoration: none; }

.divider { display: flex; align-items: center; gap: 12px; margin: 20px 0 16px; }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e1e1e1; }
.divider span { font-size: .82rem; color: #999; white-space: nowrap; }

.social-btns { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.social-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 13px; border-radius: 12px;
  font-size: .92rem; font-weight: 600; cursor: pointer;
  border: 1.5px solid #e1e1e1; transition: all .15s;
}
.social-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.social-btn.kakao { background: #FEE500; border-color: #FEE500; color: #3A1D1D; }
.social-btn.kakao:hover { background: #f0d900; }
.social-btn.google { background: white; color: #374151; }
.social-btn.google:hover { border-color: #4285F4; }
.social-btn.apple { background: #000; border-color: #000; color: white; }
.social-btn.apple:hover { background: #1a1a1a; }
</style>
