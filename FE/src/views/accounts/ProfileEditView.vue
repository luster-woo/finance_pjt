<template>
  <main class="wrap">
    <form class="card" @submit.prevent="save">

      <div class="card-header">
        <h1>내 정보 수정</h1>
        <p>프로필을 최신 상태로 업데이트해 주세요.</p>
      </div>

      <!-- 아이디 확인 (읽기 전용) -->
      <div class="id-display" v-if="myUsername">
        <span class="id-label">내 아이디</span>
        <span class="id-value">{{ myUsername }}</span>
      </div>

      <div class="form-group">
        <label>
          <span class="label-text">닉네임</span>
          <input v-model.trim="form.nickname" placeholder="사용하실 닉네임을 입력하세요" />
        </label>

        <label>
          <span class="label-text">이메일 (필수)</span>
          <input v-model.trim="form.email" type="email" required placeholder="example@email.com" />
        </label>

        <label>
          <span class="label-text">생년월일</span>
          <input v-model="form.birth_date" type="date" />
        </label>

        <label>
          <span class="label-text">프로필 이미지 파일</span>
          <input type="file" accept="image/*" @change="handleFileChange" class="file-input" />
          <span v-if="form.profile_image" class="file-hint">이미지가 등록되어 있습니다.</span>
        </label>

        <label>
          <span class="label-text">간단 소개</span>
          <textarea v-model.trim="form.bio" placeholder="나를 표현할 수 있는 짧은 소개글을 적어주세요."></textarea>
        </label>

        <label>
          <span class="label-text">거주 주소 <small style="color:#98a2b3">(인근 은행 기반 상품 추천에 사용)</small></span>
          <input v-model.trim="form.address" placeholder="예: 서울 강남구 역삼동" />
        </label>
      </div>

      <p v-if="error" class="error-msg">⚠️ {{ error }}</p>

      <div class="button-group">
        <button type="button" class="btn-cancel" @click="router.back()">취소</button>
        <button type="submit" class="btn-save" :disabled="loading">
          {{ loading ? '저장 중...' : '저장하기' }}
        </button>
      </div>

    </form>

    <!-- 비밀번호 변경 카드 -->
    <div class="card pw-card">
      <div class="card-header">
        <h2>비밀번호 변경</h2>
        <p>보안을 위해 주기적으로 변경해주세요.</p>
      </div>
      <div class="form-group">
        <label>
          <span class="label-text">현재 비밀번호</span>
          <input v-model="pw.current" type="password" placeholder="현재 비밀번호" />
        </label>
        <label>
          <span class="label-text">새 비밀번호</span>
          <input v-model="pw.next" type="password" placeholder="새 비밀번호 (8자 이상)" />
        </label>
        <label>
          <span class="label-text">새 비밀번호 확인</span>
          <input v-model="pw.confirm" type="password" placeholder="새 비밀번호 다시 입력" />
        </label>
      </div>
      <p v-if="pwError" class="error-msg">⚠️ {{ pwError }}</p>
      <p v-if="pwSuccess" class="success-msg">✅ {{ pwSuccess }}</p>
      <div class="button-group">
        <button class="btn-save" :disabled="pwLoading" @click="changePassword">
          {{ pwLoading ? '변경 중...' : '비밀번호 변경' }}
        </button>
      </div>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { api, getErrorMessage } from '@/api';

const router = useRouter();

const form = ref({
  nickname: '',
  email: '',
  birth_date: null,
  profile_image: null,
  bio: '',
  address: '',
})
const myUsername = ref('')
const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')

// 비밀번호 변경
const pw = ref({ current: '', next: '', confirm: '' })
const pwLoading = ref(false)
const pwError = ref('')
const pwSuccess = ref('')

async function changePassword() {
  pwError.value = ''
  pwSuccess.value = ''
  if (!pw.value.current || !pw.value.next || !pw.value.confirm) {
    pwError.value = '모든 항목을 입력해주세요.'; return
  }
  if (pw.value.next !== pw.value.confirm) {
    pwError.value = '새 비밀번호가 일치하지 않습니다.'; return
  }
  if (pw.value.next.length < 8) {
    pwError.value = '새 비밀번호는 8자 이상이어야 합니다.'; return
  }
  pwLoading.value = true
  try {
    const { data } = await api.post('/mypage/password/', {
      current_password: pw.value.current,
      new_password: pw.value.next,
    })
    pwSuccess.value = data.message + ' 3초 후 로그인 페이지로 이동합니다.'
    pw.value = { current: '', next: '', confirm: '' }
    setTimeout(() => router.push('/login'), 3000)
  } catch (e) {
    pwError.value = getErrorMessage(e, '비밀번호 변경에 실패했습니다.')
  } finally {
    pwLoading.value = false
  }
}

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) selectedFile.value = file
}

onMounted(async () => {
  try {
    const response = await api.get('/accounts/profile/')
    form.value = { ...form.value, ...response.data }
    myUsername.value = response.data.username || ''
  } catch (e) {
    error.value = getErrorMessage(e)
  }
});

async function save() {
  loading.value = true;
  error.value = '';
  
  try {
    // 파일을 서버로 보낼 때는 FormData 객체를 사용해야 합니다.
    const formData = new FormData();
    formData.append('nickname', form.value.nickname || '');
    formData.append('email', form.value.email || '');
    if (form.value.birth_date) formData.append('birth_date', form.value.birth_date);
    formData.append('bio', form.value.bio || '');
    formData.append('address', form.value.address || '');

    // 새로 선택한 파일이 있을 때만 폼데이터에 추가
    if (selectedFile.value) {
      formData.append('profile_image', selectedFile.value);
    }

    // 파일 전송 시에는 Content-Type을 multipart/form-data로 명시해야 합니다.
    await api.put('/accounts/profile/', formData);
    
    await router.push('/mypage');
  } catch (e) {
    error.value = getErrorMessage(e, '정보 수정에 실패했습니다.');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* 기존 스타일은 그대로 유지하고 파일 인풋 디자인만 약간 수정 */
.wrap { min-height: 90vh; display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 50px 20px; background-color: #f4f6fa; }
.card { width: 100%; max-width: 500px; background: white; border-radius: 24px; padding: 40px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05); }
.pw-card h2 { font-size: 1.3rem; font-weight: 800; color: #191f2b; margin: 0 0 6px; }

/* 아이디 표시 */
.id-display { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #f7f8fb; border-radius: 12px; border: 1px solid #e7eaf0; margin-bottom: 20px; }
.id-label { font-size: .78rem; font-weight: 700; color: #98a2b3; }
.id-value { font-size: 1rem; font-weight: 800; color: #191f2b; }

.success-msg { color: #16a34a; font-size: .9rem; margin-top: 12px; padding: 10px; background: #f0fdf4; border-radius: 8px; text-align: center; }
.card-header { text-align: center; margin-bottom: 30px; }
.card-header h1 { font-size: 1.6rem; color: #111; margin-bottom: 8px; font-weight: 800; }
.card-header p { font-size: 0.95rem; color: #666; }
.form-group { display: flex; flex-direction: column; gap: 20px; }
label { display: flex; flex-direction: column; gap: 8px; }
.label-text { font-size: 0.9rem; font-weight: 600; color: #333; margin-left: 4px; }
input, textarea { width: 100%; padding: 14px 16px; border: 1px solid #e1e8f0; border-radius: 12px; font-size: 0.95rem; background-color: #fafbfc; transition: all 0.2s ease; box-sizing: border-box; }
textarea { min-height: 100px; resize: vertical; font-family: inherit; }
input:focus, textarea:focus { outline: none; border-color: #0046ff; background-color: white; box-shadow: 0 0 0 3px rgba(0, 70, 255, 0.1); }
input::placeholder, textarea::placeholder { color: #adb5bd; }

/* 파일 입력창 특화 스타일 */
.file-input { background-color: white; cursor: pointer; padding: 10px; }
.file-input::file-selector-button { padding: 8px 16px; border-radius: 8px; border: 1px solid #ddd; background-color: #f8f9fa; cursor: pointer; margin-right: 10px; font-weight: 600; transition: 0.2s; }
.file-input::file-selector-button:hover { background-color: #e9ecef; }
.file-hint { font-size: 0.8rem; color: #0046ff; margin-left: 4px; margin-top: -4px; }

.error-msg { color: #e74c3c; font-size: 0.9rem; margin-top: 15px; padding: 10px; background-color: #fdf0ed; border-radius: 8px; text-align: center; }
.button-group { display: flex; gap: 12px; margin-top: 30px; }
button { flex: 1; padding: 16px; font-size: 1rem; font-weight: bold; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; border: none; }
.btn-cancel { background-color: #f1f3f5; color: #495057; }
.btn-cancel:hover { background-color: #e9ecef; }
.btn-save { background-color: #0046ff; color: white; }
.btn-save:hover:not(:disabled) { background-color: #0036cc; transform: translateY(-1px); }
.btn-save:disabled { background-color: #a0bbf2; cursor: not-allowed; }
</style>
