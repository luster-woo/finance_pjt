<template>
  <div class="page-bg">
    <div class="container">
      <button class="back-btn" @click="router.back()">← 목록으로</button>

      <p v-if="loading" class="status">불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <article v-else class="article-card">
        <div class="article-meta">
          <span class="publisher-badge">{{ article.publisher || '출처 미상' }}</span>
          <span class="meta-dot">·</span>
          <span class="meta-date">{{ formatDate(article.published_at) }}</span>
        </div>
        <h1 class="article-title">{{ article.title }}</h1>
        <p class="article-summary">{{ article.summary || '요약 내용이 없습니다.' }}</p>
        <a
          v-if="article.url"
          :href="article.url"
          target="_blank"
          rel="noopener noreferrer"
          class="read-original-btn"
        >
          원문 기사 보기 ↗
        </a>
      </article>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const route = useRoute()
const router = useRouter()
const article = ref({})
const loading = ref(true)
const error = ref('')

const formatDate = v => v ? new Date(v).toLocaleString('ko-KR') : '-'

onMounted(async () => {
  try {
    article.value = (await api.get(`/news/${route.params.id}/`)).data
  } catch (e) {
    error.value = getErrorMessage(e, '뉴스를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 720px; margin: 0 auto; }

.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 16px; margin-bottom: 28px;
  background: white; border: 1px solid #e7eaf0; border-radius: 10px;
  color: #616b7d; font-size: .9rem; font-weight: 600; cursor: pointer;
  transition: box-shadow .15s;
}
.back-btn:hover { box-shadow: 0 3px 10px rgba(0,0,0,.07); }

.article-card {
  background: white; border: 1px solid #e7eaf0;
  border-radius: 22px; padding: 36px 40px;
  box-shadow: 0 5px 18px rgba(28,39,65,.045);
}

.article-meta {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 16px; flex-wrap: wrap;
}
.publisher-badge {
  padding: 4px 12px; border-radius: 20px;
  background: #eef3ff; color: #0046ff;
  font-size: .78rem; font-weight: 700;
}
.meta-dot { color: #c4c9d4; }
.meta-date { font-size: .82rem; color: #98a2b3; }

.article-title {
  margin: 0 0 20px;
  font-size: 1.55rem; font-weight: 800; color: #191f2b;
  line-height: 1.4; letter-spacing: -.03em;
}

.article-summary {
  margin: 0 0 32px;
  font-size: .97rem; color: #364153;
  line-height: 1.85; white-space: pre-line;
  border-left: 3px solid #eef3ff; padding-left: 18px;
}

.read-original-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 13px 24px; border-radius: 12px;
  background: #0046ff; color: white;
  font-size: .92rem; font-weight: 700; text-decoration: none;
  box-shadow: 0 6px 16px rgba(0,70,255,.2);
  transition: background .15s, transform .15s;
}
.read-original-btn:hover { background: #0036cc; transform: translateY(-1px); }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .article-card { padding: 24px 20px; }
  .article-title { font-size: 1.3rem; }
}
</style>
