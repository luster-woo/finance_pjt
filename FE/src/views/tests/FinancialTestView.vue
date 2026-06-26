<template>
  <div class="test-container">
    <div class="test-wrapper">
      
      <Transition :name="questionTransition" mode="out-in">
      <div v-if="currentStep === 0" :key="'intro'" class="intro-section">
        <h1>📊 나의 금융 페르소나 찾기</h1>
        <p>위험 수용도·투자 기간·심리 반응 등 10가지<br>핵심 지표로 당신의 금융 성향을 정밀 진단합니다.</p>
        <button class="primary-btn" @click="startTest">테스트 시작하기</button>
      </div>

      <div v-else-if="currentStep <= questions.length" :key="currentStep" class="question-section">
        
        <div class="progress-container">
          <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <span class="step-indicator">Question {{ currentStep }} / {{ questions.length }}</span>
        
        <h2 class="question-text">{{ currentQuestion.text }}</h2>
        <p class="question-desc">{{ currentQuestion.desc }}</p>
        
        <div class="options-group">
          <button 
            v-for="scale in scaleOptions" 
            :key="scale.value"
            class="option-btn"
            :class="{ selected: answers[`q${currentStep}`] === scale.value }"
            @click="selectOption(scale.value)"
          >
            {{ scale.text }}
          </button>
        </div>

        <div class="nav-buttons">
          <button @click="prevStep" class="nav-btn prev-btn" :style="{ visibility: currentStep > 1 ? 'visible' : 'hidden' }">
            이전
          </button>
          
          <button v-if="currentStep < questions.length" 
                  @click="nextStep" 
                  class="nav-btn next-btn"
                  :disabled="!answers[`q${currentStep}`]">
            다음
          </button>
                  
          <button v-if="currentStep === questions.length"
                  @click="submitTest"
                  class="nav-btn submit-btn"
                  :disabled="!answers[`q${currentStep}`] || isLoading">
            {{ isLoading ? 'AI 분석 중...' : '결과 보기' }}
          </button>
        </div>
        <p v-if="submitError" class="submit-error">{{ submitError }}</p>
      </div>
      </Transition>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const router = useRouter()

const currentStep = ref(0)
const isLoading = ref(false)
const transitionDirection = ref('next')
const submitError = ref('')

// 백엔드로 보낼 답변 객체 (예: { q1: 5, q2: 2, q3: 4, q4: 1, q5: 3 })
const answers = ref({})

// 5점 척도 옵션 (고정)
const scaleOptions = [
  { text: "매우 그렇다", value: 5 },
  { text: "그런 편이다", value: 4 },
  { text: "보통이다", value: 3 },
  { text: "아닌 편이다", value: 2 },
  { text: "전혀 아니다", value: 1 }
]

// 금융 성향 핵심 질문 10개 (고품질 엄선)
const questions = [
  {
    id: "q1",
    text: "나는 원금의 30% 이상 손실이 발생하더라도, 더 높은 수익을 위해 감수할 수 있다.",
    desc: "[위험 수용도] 손실 허용 범위를 측정합니다. 투자 성향의 가장 핵심 지표입니다."
  },
  {
    id: "q2",
    text: "수익률이 낮더라도 원금이 보장되는 상품(예금·적금)이 그 어떤 투자보다 우선순위다.",
    desc: "[안전 선호도] 원금 보장에 대한 선호 강도를 측정합니다. (역방향 문항)"
  },
  {
    id: "q3",
    text: "나는 단기 수익보다 5년 이상을 바라보는 장기 투자 전략을 선호한다.",
    desc: "[투자 기간] 시간적 관점(Time Horizon)의 투자 성향을 파악합니다."
  },
  {
    id: "q4",
    text: "투자 결정 전에 재무제표, 업종 동향, 금리 환경 등을 직접 분석하는 편이다.",
    desc: "[정보 분석력] 데이터 기반 의사결정 능력과 투자 주도성을 측정합니다."
  },
  {
    id: "q5",
    text: "보유 자산이 20% 이상 하락한 상황에서도 추가 매수(물타기)를 적극 고려할 수 있다.",
    desc: "[하락 대응력] 위기 상황에서의 대처 능력과 심리적 안정성을 측정합니다."
  },
  {
    id: "q6",
    text: "주변의 투자 성공 사례를 듣고 충분한 검토 없이 충동적으로 매수한 경험이 있다.",
    desc: "[군중 심리] 충동 투자 경향을 측정합니다. (역방향 문항)"
  },
  {
    id: "q7",
    text: "주식, 채권, ETF, 예금 등 여러 자산에 분산 투자해 리스크를 관리하는 것이 중요하다고 생각한다.",
    desc: "[분산 투자] 포트폴리오 다각화에 대한 인식과 실행 의지를 측정합니다."
  },
  {
    id: "q8",
    text: "ETF, 채권, 파생상품, 리츠(REITs) 등 다양한 금융상품의 구조와 특성을 이해하고 있다.",
    desc: "[금융 이해도] 투자 지식 수준과 자기주도 투자 역량을 측정합니다."
  },
  {
    id: "q9",
    text: "시장이 급등할 때 나만 뒤처지는 것 같아 충분한 분석 없이 매수 버튼을 누른 적이 있다.",
    desc: "[FOMO 충동성] 기회 손실 불안으로 인한 충동 매수 성향을 측정합니다. (역방향 문항)"
  },
  {
    id: "q10",
    text: "나는 연 10% 이상의 높은 수익률을 목표로 하며, 이를 위해 적극적으로 투자 공부를 한다.",
    desc: "[수익 목표] 기대 수익률 수준과 투자 학습 의지를 종합 측정합니다."
  }
]

// 현재 질문과 진행률 계산
const currentQuestion = computed(() => questions[currentStep.value - 1])
const progressPercentage = computed(() => (currentStep.value / questions.length) * 100)
const questionTransition = computed(() =>
  transitionDirection.value === 'previous' ? 'question-back' : 'question-next',
)

// 이벤트 핸들러
const startTest = () => { transitionDirection.value = 'next'; currentStep.value = 1 }
const prevStep = () => { transitionDirection.value = 'previous'; currentStep.value-- }
const nextStep = () => { transitionDirection.value = 'next'; currentStep.value++ }

// 옵션 선택 (자동으로 다음 단계로 넘어가게 할 수도 있지만, 신중한 선택을 위해 버튼 유지)
const selectOption = (value) => {
  answers.value[`q${currentStep.value}`] = value
}

// 백엔드로 데이터 전송
const submitTest = async () => {
  if (Object.keys(answers.value).length < questions.length) {
    submitError.value = '모든 질문에 답변해주세요.'
    return
  }

  isLoading.value = true

  try {

    // 딕셔너리를 리스트로 변환
    // { q1: 5, q2: 2, q3: 4, ... } → [5, 2, 4, ...]
    const answersArray = Object.keys(answers.value)
      .sort((a, b) => {
        const numA = parseInt(a.slice(1))
        const numB = parseInt(b.slice(1))
        return numA - numB
      })
      .map(key => answers.value[key])

    // 데이터 전송 형태: { answers: [5, 2, 4, 4, 5, ...] }
    const response = await api.post('/tests/', { answers: answersArray })

    
    router.push('/test/result')

  } catch (error) {
    if (error.response?.status === 401) {
      submitError.value = '로그인이 필요합니다.'
      router.push('/login')
    } else {
      submitError.value = getErrorMessage(error, '결과 분석 중 오류가 발생했습니다.')
    }

  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.test-container { display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; background-color: #f4f6fa; padding-top: 5vh; }
.test-wrapper { width: 100%; max-width: 500px; padding: 40px; background: white; border-radius: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }

.intro-section { text-align: center; padding: 40px 0; }
.intro-section h1 { color: #0046ff; margin-bottom: 15px; font-size: 1.8rem; }
.intro-section p { color: #666; margin-bottom: 30px; line-height: 1.6; }

/* Progress Bar */
.progress-container { width: 100%; height: 8px; background-color: #e1e8f0; border-radius: 4px; margin-bottom: 15px; overflow: hidden; }
.progress-bar { height: 100%; background-color: #0046ff; transition: width 0.4s ease; }
.step-indicator { display: block; font-size: 0.85rem; color: #888; margin-bottom: 25px; font-weight: bold; text-align: right; }

/* Question */
.question-text { font-size: 1.3rem; margin-bottom: 10px; line-height: 1.5; color: #2d3436; font-weight: 800; }
.question-desc { font-size: 0.9rem; color: #888; margin-bottom: 30px; }

/* Options */
.options-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 30px; }
.option-btn { width: 100%; padding: 16px; text-align: center; background: white; border: 1px solid #e1e8f0; border-radius: 12px; font-size: 1rem; color: #2d3436; cursor: pointer; transition: all 0.2s ease; font-weight: 500; }
.option-btn:hover { border-color: #0046ff; background-color: #f0f4ff; }
.option-btn.selected { background-color: #0046ff; color: white; border-color: #0046ff; font-weight: bold; box-shadow: 0 4px 10px rgba(0, 70, 255, 0.2); }

/* Buttons */
.nav-buttons { display: flex; justify-content: space-between; align-items: center; }
.nav-btn { padding: 12px 24px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 1rem; transition: background-color 0.2s; }
.prev-btn { background-color: #f0f0f0; color: #666; }
.prev-btn:hover { background-color: #e4e4e4; }

.next-btn, .primary-btn, .submit-btn { background-color: #0046ff; color: white; }
.next-btn:hover, .primary-btn:hover, .submit-btn:hover { background-color: #0036cc; }
.nav-btn:disabled { background-color: #cbd5e0; color: white; cursor: not-allowed; }
.primary-btn { width: 100%; padding: 15px; font-size: 1.1rem; border-radius: 12px; }
.submit-error { margin: 12px 0 0; padding: 10px 14px; background: #fff0f0; border-radius: 10px; color: #c62828; font-size: .88rem; text-align: center; }

.question-next-enter-active,
.question-next-leave-active,
.question-back-enter-active,
.question-back-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.question-next-enter-from { opacity: 0; transform: translateX(16px); }
.question-next-leave-to { opacity: 0; transform: translateX(-12px); }
.question-back-enter-from { opacity: 0; transform: translateX(-16px); }
.question-back-leave-to { opacity: 0; transform: translateX(12px); }

@media (prefers-reduced-motion: reduce) {
  .question-next-enter-active, .question-next-leave-active,
  .question-back-enter-active, .question-back-leave-active { transition: none; }
  .question-next-enter-from, .question-next-leave-to,
  .question-back-enter-from, .question-back-leave-to { transform: none; }
}
</style>
