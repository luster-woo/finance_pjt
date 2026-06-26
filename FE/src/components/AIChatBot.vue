<template>
  <div class="chatbot-wrap">
    <!-- 플로팅 버튼 -->
    <button class="chat-fab" @click="toggle" :class="{ open: isOpen }" title="AI 금융 상담">
      <span v-if="!isOpen">💬</span>
      <span v-else>✕</span>
    </button>

    <!-- 챗 패널 -->
    <Transition name="chat-slide">
      <div v-if="isOpen" class="chat-panel">
        <!-- 헤더 -->
        <div class="chat-header">
          <div class="chat-header-left">
            <div class="bot-avatar">🤖</div>
            <div>
              <strong>FinFit AI 상담사</strong>
              <span class="online-dot"></span>
            </div>
          </div>
          <button class="chat-close" @click="isOpen = false">✕</button>
        </div>

        <!-- 메시지 목록 -->
        <div class="chat-messages" ref="messagesEl">
          <!-- 웰컴 메시지 -->
          <div class="msg bot">
            <div class="msg-bubble">
              안녕하세요! 💰 FinFit AI 금융 상담사입니다.<br>
              예금·적금, 주식·ETF, 카드 혜택, 세금·절세 등 무엇이든 물어보세요!
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="msg-bubble">{{ m.content }}</div>
          </div>

          <!-- 로딩 -->
          <div v-if="loading" class="msg bot">
            <div class="msg-bubble loading">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <!-- 빠른 질문 (메시지 없을 때) -->
        <div v-if="!messages.length" class="quick-questions">
          <button v-for="q in quickQuestions" :key="q" class="quick-btn" @click="sendQuick(q)">{{ q }}</button>
        </div>

        <!-- 입력창 -->
        <div class="chat-input-wrap">
          <input
            v-model.trim="input"
            class="chat-input"
            placeholder="금융 관련 질문을 입력하세요..."
            @keydown.enter.prevent="send"
            :disabled="loading"
            ref="inputEl"
          />
          <button class="send-btn" @click="send" :disabled="!input || loading">
            ↑
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { api } from '@/api'

const isOpen = ref(false)
const input = ref('')
const messages = ref([])
const loading = ref(false)
const messagesEl = ref(null)
const inputEl = ref(null)

const quickQuestions = [
  'ISA 계좌가 뭔가요?',
  '연금저축과 IRP 차이는?',
  '적금이자 계산 방법은?',
  '신용점수 올리는 방법은?',
]

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => inputEl.value?.focus())
  }
}

async function send() {
  if (!input.value || loading.value) return
  const userMsg = input.value
  input.value = ''
  messages.value.push({ role: 'user', content: userMsg })
  loading.value = true
  await scrollToBottom()

  try {
    const history = messages.value.slice(-12).map(m => ({ role: m.role, content: m.content }))
    const { data } = await api.post('/chat/', { message: userMsg, history })
    messages.value.push({ role: 'bot', content: data.reply })
  } catch {
    messages.value.push({ role: 'bot', content: '죄송합니다. 잠시 후 다시 시도해 주세요.' })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function sendQuick(q) {
  input.value = q
  send()
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}
</script>

<style scoped>
.chatbot-wrap {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 9000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

/* FAB 버튼 */
.chat-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0046ff, #0077ff);
  color: white;
  font-size: 1.4rem;
  border: none;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0,70,255,.35);
  transition: transform .2s, box-shadow .2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.chat-fab:hover { transform: scale(1.08); box-shadow: 0 8px 28px rgba(0,70,255,.45); }
.chat-fab.open { background: #364153; box-shadow: 0 4px 16px rgba(0,0,0,.2); }

/* 챗 패널 */
.chat-panel {
  width: 340px;
  height: 480px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(28,39,65,.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e7eaf0;
}

/* 헤더 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, #0046ff, #0077ff);
  color: white;
}
.chat-header-left { display: flex; align-items: center; gap: 10px; }
.bot-avatar { font-size: 1.4rem; }
.chat-header strong { display: block; font-size: .9rem; font-weight: 700; }
.online-dot {
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: #4ade80; margin-left: 4px; vertical-align: middle;
}
.chat-close { background: none; border: none; color: rgba(255,255,255,.8); font-size: 1rem; cursor: pointer; padding: 4px; }
.chat-close:hover { color: white; }

/* 메시지 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: #d0d5dd transparent;
}
.msg { display: flex; }
.msg.user { justify-content: flex-end; }
.msg.bot { justify-content: flex-start; }

.msg-bubble {
  max-width: 82%;
  padding: 10px 13px;
  border-radius: 16px;
  font-size: .85rem;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg.user .msg-bubble { background: #0046ff; color: white; border-bottom-right-radius: 4px; }
.msg.bot .msg-bubble { background: #f0f2f7; color: #191f2b; border-bottom-left-radius: 4px; }

/* 로딩 닷 */
.msg-bubble.loading { display: flex; align-items: center; gap: 5px; padding: 12px 16px; }
.msg-bubble.loading span {
  width: 7px; height: 7px; border-radius: 50%; background: #98a2b3;
  animation: dot-bounce 1.2s infinite;
}
.msg-bubble.loading span:nth-child(2) { animation-delay: .2s; }
.msg-bubble.loading span:nth-child(3) { animation-delay: .4s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: .5; }
  40% { transform: scale(1.1); opacity: 1; }
}

/* 빠른 질문 */
.quick-questions { padding: 4px 12px 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.quick-btn {
  padding: 5px 10px; border-radius: 12px; border: 1px solid #e7eaf0;
  background: #f7f8fb; color: #364153; font-size: .75rem; font-weight: 600;
  cursor: pointer; transition: all .15s;
}
.quick-btn:hover { border-color: #0046ff; color: #0046ff; background: #eef3ff; }

/* 입력창 */
.chat-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid #f0f2f6;
}
.chat-input {
  flex: 1;
  padding: 9px 12px;
  border: 1.5px solid #e7eaf0;
  border-radius: 20px;
  font-size: .85rem;
  outline: none;
  transition: border-color .15s;
}
.chat-input:focus { border-color: #0046ff; }
.send-btn {
  width: 34px; height: 34px; border-radius: 50%;
  background: #0046ff; color: white; border: none;
  font-size: 1rem; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background .15s;
  flex: 0 0 auto;
}
.send-btn:hover:not(:disabled) { background: #0036cc; }
.send-btn:disabled { background: #a0bbf2; cursor: not-allowed; }

/* 슬라이드 트랜지션 */
.chat-slide-enter-active { transition: all .25s ease; }
.chat-slide-leave-active { transition: all .2s ease; }
.chat-slide-enter-from { opacity: 0; transform: translateY(16px) scale(0.95); }
.chat-slide-leave-to { opacity: 0; transform: translateY(12px) scale(0.97); }

@media(max-width: 400px) {
  .chat-panel { width: calc(100vw - 40px); }
  .chatbot-wrap { right: 16px; bottom: 16px; }
}
</style>
