<template>
  <section class="board">
    <h2 class="board-title">종목 토론방</h2>

    <!-- 작성 폼 (로그인 시) -->
    <div v-if="isLoggedIn" class="write-box">
      <textarea v-model.trim="newContent" placeholder="의견을 남겨주세요..." rows="2" maxlength="300"></textarea>
      <button @click="submit" :disabled="!newContent">등록</button>
    </div>
    <div v-else class="login-prompt">
      <RouterLink to="/login">로그인</RouterLink>하고 토론에 참여해보세요.
    </div>

    <p v-if="loading" class="status-msg">불러오는 중...</p>
    <p v-if="error" class="status-msg error">{{ error }}</p>

    <!-- 게시글 목록 -->
    <div v-if="posts.length" class="post-list">
      <article v-for="post in posts" :key="post.id" class="post-item">
        <div class="post-header">
          <span class="post-author">{{ post.username || '익명' }}</span>
          <span class="post-date">{{ fmt(post.created_at) }}</span>
          <button v-if="post.user === myUserId" class="del-btn" @click="deletePost(post.id)">삭제</button>
        </div>
        <p class="post-content">{{ post.content }}</p>
        <div class="post-footer">
          <button class="like-btn" :class="{ liked: post.is_liked }" @click="togglePostLike(post)">
            ♥ {{ post.likes_count }}
          </button>
          <button class="reply-toggle" @click="toggleReply(post.id)">
            💬 댓글 {{ replyCount(post.id) }} {{ openReplies[post.id] ? '▲' : '▼' }}
          </button>
        </div>

        <!-- 댓글 영역 -->
        <div v-if="openReplies[post.id]" class="reply-area">
          <div v-if="comments[post.id]" class="comment-list">
            <div v-for="c in comments[post.id]" :key="c.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ c.username }}</span>
                <span class="comment-date">{{ fmt(c.created_at) }}</span>
                <button v-if="c.user === myUserId" class="del-btn" @click="deleteComment(c.id, post.id)">삭제</button>
              </div>
              <p class="comment-content">{{ c.content }}</p>
              <div class="comment-footer">
                <button class="like-btn sm" :class="{ liked: c.is_liked }" @click="toggleCommentLike(c, post.id)">
                  ♥ {{ c.likes_count }}
                </button>
                <button class="reply-write-btn" @click="setReplyTarget(post.id, c.id, c.username)">답글</button>
              </div>

              <!-- 대댓글 -->
              <div v-if="c.replies?.length" class="reply-list">
                <div v-for="r in c.replies" :key="r.id" class="reply-item">
                  <span class="reply-arrow">↳</span>
                  <div>
                    <div class="comment-header">
                      <span class="comment-author">{{ r.username }}</span>
                      <span class="comment-date">{{ fmt(r.created_at) }}</span>
                      <button v-if="r.user === myUserId" class="del-btn" @click="deleteComment(r.id, post.id)">삭제</button>
                    </div>
                    <p class="comment-content">{{ r.content }}</p>
                    <button class="like-btn sm" :class="{ liked: r.is_liked }" @click="toggleCommentLike(r, post.id)">
                      ♥ {{ r.likes_count }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 댓글/대댓글 작성 -->
          <div v-if="isLoggedIn" class="comment-write">
            <span v-if="replyTarget[post.id]" class="reply-target-label">
              @{{ replyTarget[post.id].username }} 에게 답글
              <button @click="clearReplyTarget(post.id)">✕</button>
            </span>
            <div class="comment-input-row">
              <input v-model.trim="commentInputs[post.id]"
                :placeholder="replyTarget[post.id] ? '대댓글 입력...' : '댓글 입력...'"
                @keyup.enter="submitComment(post.id)" maxlength="200" />
              <button @click="submitComment(post.id)" :disabled="!commentInputs[post.id]">등록</button>
            </div>
          </div>
        </div>
      </article>
    </div>
    <p v-else-if="!loading" class="empty">아직 게시글이 없습니다. 첫 번째로 의견을 남겨보세요!</p>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getErrorMessage } from '@/api'

const props = defineProps({ stockId: { type: String, required: true } })

const posts = ref([])
const loading = ref(false)
const error = ref('')
const newContent = ref('')
const comments = reactive({})
const commentInputs = reactive({})
const openReplies = reactive({})
const replyTarget = reactive({})
const myUserId = ref(null)

const isLoggedIn = computed(() => !!(localStorage.getItem('accessToken') || localStorage.getItem('token')))

const fmt = v => v ? new Date(v).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''

function replyCount(postId) {
  return comments[postId]?.length ?? 0
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/community/posts/')
    posts.value = data.filter(p => !p.stock || String(p.stock) === props.stockId)
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function loadMyId() {
  if (!isLoggedIn.value) return
  try {
    const { data } = await api.get('/mypage/')
    myUserId.value = data.id
  } catch { /* ignore */ }
}

async function submit() {
  try {
    await api.post('/community/posts/', {
      stock_id: Number(props.stockId),
      category: 'stock_discussion',
      title: '종목 토론',
      content: newContent.value,
    })
    newContent.value = ''
    await load()
  } catch (e) {
    error.value = getErrorMessage(e, '게시글 등록에 실패했습니다.')
  }
}

async function deletePost(id) {
  try {
    await api.delete(`/community/posts/${id}/`)
    await load()
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

async function togglePostLike(post) {
  if (!isLoggedIn.value) return
  try {
    const { data } = await api.post(`/community/posts/${post.id}/like/`)
    post.is_liked = data.is_liked
    post.likes_count = data.likes_count
  } catch { /* ignore */ }
}

async function toggleReply(postId) {
  openReplies[postId] = !openReplies[postId]
  if (openReplies[postId] && !comments[postId]) {
    await loadComments(postId)
  }
}

async function loadComments(postId) {
  try {
    const { data } = await api.get(`/community/posts/${postId}/comments/`)
    comments[postId] = data
  } catch { /* ignore */ }
}

async function submitComment(postId) {
  const content = commentInputs[postId]?.trim()
  if (!content) return
  const payload = { content, post: postId }
  if (replyTarget[postId]?.commentId) payload.parent = replyTarget[postId].commentId
  try {
    await api.post(`/community/posts/${postId}/comments/`, payload)
    commentInputs[postId] = ''
    clearReplyTarget(postId)
    await loadComments(postId)
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

async function deleteComment(commentId, postId) {
  try {
    await api.delete(`/community/comments/${commentId}/`)
    await loadComments(postId)
  } catch { /* ignore */ }
}

async function toggleCommentLike(comment, postId) {
  if (!isLoggedIn.value) return
  try {
    const { data } = await api.post(`/community/comments/${comment.id}/like/`)
    comment.is_liked = data.is_liked
    comment.likes_count = data.likes_count
  } catch { /* ignore */ }
}

function setReplyTarget(postId, commentId, username) {
  replyTarget[postId] = { commentId, username }
}
function clearReplyTarget(postId) {
  delete replyTarget[postId]
}

onMounted(async () => {
  await Promise.all([load(), loadMyId()])
})
</script>

<style scoped>
.board { margin-top: 8px; }
.board-title { font-size: 1.05rem; font-weight: 800; color: #191f2b; margin: 0 0 16px; }

.write-box { display: flex; gap: 8px; margin-bottom: 20px; align-items: stretch; }
.write-box textarea {
  flex: 1; padding: 12px 14px; border: 1px solid #e7eaf0; border-radius: 10px;
  font-size: .9rem; resize: none; font-family: inherit; height: 44px; box-sizing: border-box;
}
.write-box textarea:focus { outline: none; border-color: #0046ff; }
.write-box button {
  padding: 0 20px; border: none; border-radius: 10px; height: 44px;
  background: #0046ff; color: white; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.write-box button:disabled { background: #c4d0f5; cursor: not-allowed; }

.login-prompt {
  padding: 14px 16px; background: #f7f8fb; border-radius: 10px;
  font-size: .88rem; color: #616b7d; margin-bottom: 16px; text-align: center;
}
.login-prompt a { color: #0046ff; font-weight: 700; }

.post-list { display: flex; flex-direction: column; gap: 12px; }
.post-item {
  background: #fafbfc; border: 1px solid #edf0f5; border-radius: 14px; padding: 16px 18px;
}
.post-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.post-author { font-size: .82rem; font-weight: 700; color: #364153; }
.post-date { font-size: .75rem; color: #98a2b3; margin-left: auto; }
.post-content { margin: 0 0 12px; font-size: .9rem; color: #364153; line-height: 1.6; }
.post-footer { display: flex; align-items: center; gap: 10px; }

.like-btn {
  padding: 5px 12px; border-radius: 20px; border: 1px solid #e7eaf0;
  background: white; font-size: .8rem; cursor: pointer; color: #616b7d;
  transition: all .15s;
}
.like-btn.liked { background: #fff0f5; border-color: #fca5a5; color: #e53e3e; }
.like-btn.sm { padding: 3px 9px; font-size: .75rem; }
.reply-toggle {
  padding: 5px 12px; border-radius: 20px; border: 1px solid #e7eaf0;
  background: white; font-size: .8rem; cursor: pointer; color: #616b7d;
}

.del-btn {
  padding: 2px 8px; border: 1px solid #fca5a5; border-radius: 6px;
  background: #fff5f5; color: #dc2626; font-size: .72rem; cursor: pointer;
}

.reply-area { margin-top: 12px; border-top: 1px solid #f0f2f6; padding-top: 12px; }
.comment-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.comment-item { background: white; border: 1px solid #f0f2f6; border-radius: 10px; padding: 12px 14px; }
.comment-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.comment-author { font-size: .78rem; font-weight: 700; color: #364153; }
.comment-date { font-size: .72rem; color: #98a2b3; margin-left: auto; }
.comment-content { margin: 0 0 6px; font-size: .86rem; color: #364153; line-height: 1.5; }
.comment-footer { display: flex; align-items: center; gap: 8px; }
.reply-write-btn {
  font-size: .75rem; color: #0046ff; font-weight: 600; cursor: pointer;
  background: none; border: none; padding: 0;
}

.reply-list { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; padding-left: 12px; border-left: 2px solid #e7eaf0; }
.reply-item { display: flex; gap: 8px; }
.reply-arrow { color: #98a2b3; font-size: .85rem; flex: 0 0 auto; margin-top: 2px; }

.comment-write { }
.reply-target-label {
  display: inline-flex; align-items: center; gap: 6px; margin-bottom: 6px;
  font-size: .78rem; color: #0046ff; font-weight: 600;
  background: #eef3ff; padding: 4px 10px; border-radius: 8px;
}
.reply-target-label button { background: none; border: none; cursor: pointer; color: #98a2b3; font-size: .8rem; }
.comment-input-row { display: flex; gap: 8px; align-items: stretch; }
.comment-input-row input {
  flex: 1; padding: 0 12px; border: 1px solid #e7eaf0; border-radius: 8px;
  font-size: .88rem; height: 38px; box-sizing: border-box;
}
.comment-input-row input:focus { outline: none; border-color: #0046ff; }
.comment-input-row button {
  padding: 0 14px; border: none; border-radius: 8px; height: 38px;
  background: #0046ff; color: white; font-size: .82rem; font-weight: 700; cursor: pointer;
}
.comment-input-row button:disabled { background: #c4d0f5; cursor: not-allowed; }

.status-msg { color: #98a2b3; font-size: .9rem; text-align: center; padding: 20px 0; }
.error { color: #c62828; }
.empty { text-align: center; padding: 30px 0; color: #98a2b3; font-size: .88rem; }
</style>
