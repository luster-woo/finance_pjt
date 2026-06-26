<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>회원가입</h1>
      <p>새로운 금융 경험을 시작해보세요</p>

      <form class="auth-form" @submit.prevent="signup">
        <div class="input-group">
          <input v-model="username" type="text" placeholder="아이디" />
          <p
            class="helper-text"
            :style="{ color: isUsernameValid ? 'var(--accent)' : username.length > 0 ? '#ff4757' : '#888' }"
          >
            <template v-if="username.length === 0">영문/숫자 혼합 6~12자</template>
            <template v-else-if="!isUsernameValid">❌ 영문과 숫자를 반드시 포함하세요 (6~12자)</template>
            <template v-else>✅ 올바른 아이디입니다.</template>
          </p>
        </div>

        <div class="input-group">
          <input v-model="password" type="password" placeholder="비밀번호" />
          <p
            class="helper-text"
            :style="{ color: isPasswordValid ? 'var(--accent)' : password.length > 0 ? '#ff4757' : '#888' }"
          >
            <template v-if="password.length === 0">
              영문/숫자/특수문자 조합 8자 이상
              <span class="allowed-characters">(허용문자: !@#$%^&amp;*()_+-=[]{}|;':&quot;,./?)</span>
            </template>
            <template v-else-if="!isPasswordValid">❌ 조합 조건이 맞지 않습니다.</template>
            <template v-else>✅ 안전한 비밀번호입니다.</template>
          </p>
        </div>

        <div class="input-group">
          <input v-model="passwordConfirm" type="password" placeholder="비밀번호 확인" />
          <p class="helper-text" :style="{ color: isPasswordMatch ? 'var(--accent)' : '#ff4757' }">
            <template v-if="passwordConfirm.length > 0">
              {{ isPasswordMatch ? '✅ 비밀번호가 일치합니다.' : '❌ 비밀번호가 일치하지 않습니다.' }}
            </template>
          </p>
        </div>

        <div class="input-group">
          <input v-model="email" type="text" placeholder="이메일" />
          <p
            class="helper-text"
            :style="{ color: isEmailValid ? 'var(--accent)' : email.length > 0 ? '#ff4757' : '#888' }"
          >
            <template v-if="email.length > 0 && !isEmailValid">❌ 올바른 이메일 형식이 아닙니다.</template>
          </p>
        </div>

        <p v-if="errorMessage" class="server-error">{{ errorMessage }}</p>

        <button
          type="submit"
          class="submit-btn"
          :disabled="!isFormValid || isLoading"
          :class="{ 'disabled-btn': !isFormValid || isLoading }"
        >
          {{ isLoading ? '가입 중...' : '가입하기' }}
        </button>
      </form>

      <div class="divider"><span>또는 소셜 계정으로 가입</span></div>

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

      <p class="auth-link">
        이미 계정이 있으신가요? <RouterLink to="/login">로그인</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getErrorMessage, saveAuth } from '@/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const passwordConfirm = ref('')
const email = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

function socialAlert(provider) {
  alert(`${provider} 로그인은 준비 중입니다.`)
}

const isUsernameValid = computed(() => {
  const regex = /^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{6,12}$/
  return regex.test(username.value)
})

const isPasswordValid = computed(() => {
  const regex = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?])[a-zA-Z\d!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]{8,}$/
  return regex.test(password.value)
})

const isPasswordMatch = computed(
  () => password.value === passwordConfirm.value && passwordConfirm.value.length > 0,
)

const isEmailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value))

const isFormValid = computed(
  () =>
    isUsernameValid.value &&
    isPasswordValid.value &&
    isPasswordMatch.value &&
    isEmailValid.value,
)

async function signup() {
  if (!isFormValid.value) return

  isLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await api.post('/accounts/signup/', {
      username: username.value,
      password: password.value,
      email: email.value,
    })
    saveAuth(data)
    await router.push('/')
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '회원가입에 실패했습니다.')
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 10vh;
  background-color: var(--bg);
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  text-align: center;
}

h1 { font-size: 1.8rem; color: var(--primary); margin-bottom: 10px; }
.input-group { margin-bottom: 15px; text-align: left; }

.auth-form input {
  width: 100%;
  padding: 15px;
  border: 1px solid #e1e1e1;
  border-radius: 12px;
  box-sizing: border-box;
}

.helper-text { font-size: 0.75rem; color: #888; margin-top: 5px; margin-left: 5px; }
.allowed-characters { display: block; font-size: 0.7rem; color: #aaa; }
.server-error { color: #ff4757; font-size: 0.85rem; text-align: left; }
.auth-link { margin-top: 20px; font-size: 0.9rem; color: #666; }
.auth-link a { color: var(--primary); font-weight: bold; text-decoration: none; }

.submit-btn {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 12px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 15px;
  background-color: #0046ff !important;
  color: #ffffff !important;
}

.submit-btn:disabled {
  background-color: #cbd5e0 !important;
  color: #ffffff !important;
  cursor: not-allowed;
  opacity: 1 !important;
}

.submit-btn:not(:disabled):hover { background-color: #0036cc !important; }

.divider { display: flex; align-items: center; gap: 12px; margin: 20px 0 16px; }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e1e1e1; }
.divider span { font-size: .82rem; color: #999; white-space: nowrap; }

.social-btns { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.social-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 13px; border-radius: 12px;
  font-size: .92rem; font-weight: 600; cursor: pointer;
  border: 1.5px solid #e1e1e1; transition: all .15s; background: white;
}
.social-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.social-btn.kakao { background: #FEE500; border-color: #FEE500; color: #3A1D1D; }
.social-btn.kakao:hover { background: #f0d900; }
.social-btn.google { background: white; color: #374151; }
.social-btn.google:hover { border-color: #4285F4; }
.social-btn.apple { background: #000; border-color: #000; color: white; }
.social-btn.apple:hover { background: #1a1a1a; }
</style>
