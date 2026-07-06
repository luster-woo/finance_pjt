import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { saveAuth, clearAuth } from '@/api/index.js'

/**
 * 인증 상태 스토어 (JWT accessToken 기반)
 *
 * localStorage와 동기화:
 *  - saveAuth(data)  : access/refresh 저장 + 스토어 상태 갱신
 *  - logoutStore()   : 토큰 삭제 + 스토어 상태 초기화
 *
 * 컴포넌트에서 사용 예시:
 *   const auth = useAuthStore()
 *   if (auth.isLoggedIn) { ... }
 */
export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!accessToken.value)

  function setAuth(data) {
    saveAuth(data)
    accessToken.value = data.access
    if (data.user) user.value = data.user
  }

  function logoutStore() {
    clearAuth()
    accessToken.value = ''
    user.value = null
  }

  // api interceptor가 토큰을 갱신하거나 만료 시 auth-changed 이벤트를 발생시킴
  window.addEventListener('auth-changed', () => {
    const stored = localStorage.getItem('accessToken') || ''
    accessToken.value = stored
    if (!stored) user.value = null
  })

  return { accessToken, user, isLoggedIn, setAuth, logoutStore }
})
