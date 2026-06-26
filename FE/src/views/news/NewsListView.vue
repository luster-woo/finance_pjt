<template>
  <div class="page-bg">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">금융 뉴스</h1>
        <p class="page-sub">최신 금융·경제 뉴스를 확인하세요.</p>
      </div>

      <p v-if="loading" class="status">뉴스를 불러오는 중...</p>
      <p v-else-if="error" class="status error">{{ error }}</p>
      <div v-else class="news-list">
        <RouterLink
          v-for="item in news"
          :key="item.id"
          :to="`/news/${item.id}`"
          class="news-card"
        >
          <div class="news-body">
            <h3 class="news-title">{{ item.title }}</h3>
            <p class="news-summary">{{ item.summary }}</p>
            <div class="news-meta">
              <span class="news-publisher">{{ item.publisher }}</span>
              <span class="news-dot">·</span>
              <span class="news-date">{{ formatDate(item.published_at) }}</span>
            </div>
          </div>
          <span class="news-arrow">›</span>
        </RouterLink>
        <p v-if="!news.length" class="status">등록된 뉴스가 없습니다.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, getErrorMessage } from '@/api'

const news = ref([])
const loading = ref(true)
const error = ref('')

const formatDate = v => v ? new Date(v).toLocaleDateString('ko-KR') : '-'

onMounted(async () => {
  try {
    news.value = (await api.get('/news/')).data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-bg { min-height: 100vh; background: #f7f8fb; padding: 40px 20px 80px; }
.container { max-width: 860px; margin: 0 auto; }

.page-header { margin-bottom: 28px; }
.page-title { margin: 0 0 8px; font-size: 1.75rem; font-weight: 800; color: #191f2b; letter-spacing: -.03em; }
.page-sub { margin: 0; color: #98a2b3; font-size: .92rem; }

.news-list {
  display: flex; flex-direction: column; gap: 0;
  background: white; border: 1px solid #e7eaf0;
  border-radius: 20px; overflow: hidden;
  box-shadow: 0 4px 16px rgba(28,39,65,.045);
}
.news-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 24px; border-bottom: 1px solid #f0f2f6;
  text-decoration: none; color: inherit;
  transition: background .14s;
}
.news-card:last-child { border-bottom: none; }
.news-card:hover { background: #fafbff; }
.news-body { flex: 1; min-width: 0; }
.news-title { margin: 0 0 6px; font-size: .98rem; font-weight: 700; color: #191f2b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.news-summary { margin: 0 0 8px; font-size: .85rem; color: #697386; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.news-meta { display: flex; align-items: center; gap: 6px; font-size: .75rem; color: #98a2b3; }
.news-publisher { font-weight: 600; }
.news-dot { color: #d1d5db; }
.news-arrow { color: #c4c9d4; font-size: 1.4rem; flex: 0 0 auto; }

.status { text-align: center; padding: 60px 0; color: #98a2b3; }
.error { color: #d14343; }

@media (max-width: 480px) {
  .page-bg { padding: 24px 14px 60px; }
  .news-card { padding: 16px 18px; }
}
</style>
