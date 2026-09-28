<template>
  <div class="qa-assistant">
    <button
      v-show="!visible"
      class="qa-fab"
      type="button"
      title="质量助手"
      @click="open"
    >
      <i class="el-icon-chat-dot-round"></i>
      <span>质量助手</span>
    </button>

    <el-drawer
      :visible.sync="visible"
      direction="rtl"
      size="420px"
      :with-header="false"
      custom-class="qa-drawer"
      :append-to-body="true"
    >
      <div class="qa-panel">
        <div class="qa-header">
          <div>
            <div class="qa-title">质量助手</div>
            <div class="qa-sub">覆盖效能平台全模块 · 质量事实可核验</div>
          </div>
          <div class="qa-header-actions">
            <el-button type="text" size="mini" @click="clearChat">清空</el-button>
            <el-button type="text" size="mini" icon="el-icon-close" @click="visible = false" />
          </div>
        </div>

        <div class="qa-context">
          <el-select
            v-model="productId"
            clearable
            filterable
            placeholder="产品"
            size="mini"
            style="width: 48%"
            @change="onProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
          <el-select
            v-model="projectId"
            clearable
            filterable
            placeholder="项目"
            size="mini"
            style="width: 48%"
            :disabled="!productId"
            @change="onProjectChange"
          >
            <el-option
              v-for="p in projectOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </div>

        <div ref="msgList" class="qa-messages">
          <div v-if="!messages.length" class="qa-empty">
            {{ restoring ? '正在恢复历史对话…' : '试着问一句，例如「今天哪些 breaking？」' }}
          </div>
          <div
            v-for="(m, idx) in messages"
            :key="idx"
            class="qa-msg"
            :class="'qa-msg--' + m.role"
          >
            <div class="qa-bubble">
              <div class="qa-text" v-html="formatText(m.content)"></div>
              <div v-if="m.answer && m.answer.citations && m.answer.citations.length" class="qa-citations">
                <div class="qa-citations-head">
                  <span class="qa-citations-label">依据 {{ m.answer.citations.length }} 条</span>
                  <button
                    v-if="m.answer.citations.length > citationPreview"
                    type="button"
                    class="qa-citations-toggle"
                    @click.stop="toggleCitations(idx)"
                  >
                    {{ isCitationExpanded(idx) ? '收起' : '展开全部' }}
                    <i :class="isCitationExpanded(idx) ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
                  </button>
                </div>
                <div
                  v-for="(c, ci) in visibleCitations(m, idx)"
                  :key="ci"
                  class="qa-citation"
                  @click="goRoute(c.route)"
                >
                  <div class="qa-citation-title">{{ c.title }}</div>
                  <div
                    v-for="(h, hi) in (c.highlights || []).slice(0, 3)"
                    :key="hi"
                    class="qa-citation-h"
                  >{{ h }}</div>
                </div>
              </div>
              <div v-if="m.answer && m.answer.actions && m.answer.actions.length" class="qa-actions">
                <el-button
                  v-for="(a, ai) in m.answer.actions"
                  :key="ai"
                  size="mini"
                  :type="a.type === 'run_contract_suite' ? 'warning' : 'primary'"
                  plain
                  @click="onAction(a)"
                >{{ a.label }}</el-button>
              </div>
              <div v-if="m.answer && m.answer.suggestions && m.answer.suggestions.length" class="qa-suggestions">
                <el-tag
                  v-for="(s, si) in m.answer.suggestions"
                  :key="si"
                  size="mini"
                  effect="plain"
                  class="qa-chip"
                  @click="ask(s)"
                >{{ s }}</el-tag>
              </div>
            </div>
          </div>
          <div v-if="loading" class="qa-msg qa-msg--assistant">
            <div class="qa-bubble qa-loading">正在查询质量事实…</div>
          </div>
        </div>

        <div class="qa-examples">
          <el-tag
            v-for="(ex, i) in examples"
            :key="i"
            size="mini"
            class="qa-chip"
            effect="plain"
            @click="ask(ex.text || ex)"
          >{{ ex.text || ex }}</el-tag>
        </div>

        <div class="qa-input">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            placeholder="用自然语言问质量现状…"
            @keydown.native.ctrl.enter="send"
          />
          <el-button type="primary" size="small" :loading="loading" @click="send">发送</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import {
  getQualityAssistantExamples,
  qualityAssistantChat,
  getQualityAssistantSession,
  getLatestQualityAssistantSession,
  clearQualityAssistantSession,
  executeQualityAssistantAction
} from '@/api/qualityAssistantApi'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  readLastProductProjectCache,
  saveLastProductProjectCache
} from '@/utils/lastProductProjectCache'

const SESSION_CACHE_KEY = 'effekt_qa_assistant_session'

export default {
  name: 'QualityAssistant',
  data () {
    return {
      visible: false,
      loading: false,
      restoring: false,
      input: '',
      sessionId: null,
      messages: [],
      examples: [
        { text: '今天哪些 breaking？' },
        { text: '当前项目有多少未关闭 Bug？' },
        { text: '该跑哪包回归？' },
        { text: '打开精准测试' },
        { text: '平台都能做什么？' }
      ],
      productId: '',
      projectId: '',
      productOptions: [],
      projectOptions: [],
      citationPreview: 2,
      citationExpanded: {}
    }
  },
  mounted () {
    this.restoreSessionQuietly()
  },
  methods: {
    isCitationExpanded (idx) {
      return !!this.citationExpanded[idx]
    },
    visibleCitations (m, idx) {
      const list = (m.answer && m.answer.citations) || []
      if (this.isCitationExpanded(idx) || list.length <= this.citationPreview) return list
      return list.slice(0, this.citationPreview)
    },
    toggleCitations (idx) {
      this.$set(this.citationExpanded, idx, !this.citationExpanded[idx])
    },
    readSessionCache () {
      try {
        const raw = localStorage.getItem(SESSION_CACHE_KEY)
        if (!raw) return null
        const o = JSON.parse(raw)
        if (!o || !o.sessionId) return null
        return o
      } catch (e) {
        return null
      }
    },
    writeSessionCache (sessionId, productId, projectId) {
      if (!sessionId) return
      try {
        localStorage.setItem(SESSION_CACHE_KEY, JSON.stringify({
          sessionId,
          productId: productId || this.productId || '',
          projectId: projectId || this.projectId || ''
        }))
      } catch (e) {}
    },
    clearSessionCache () {
      try { localStorage.removeItem(SESSION_CACHE_KEY) } catch (e) {}
    },
    mapServerMessages (rows) {
      return (rows || []).map(m => {
        const answer = m.answer || m.answer_payload || null
        return {
          role: m.role,
          content: m.content || (answer && answer.answer_text) || '',
          answer: answer && typeof answer === 'object' ? answer : null
        }
      }).filter(m => m.role === 'user' || m.role === 'assistant')
    },
    restoreSessionQuietly () {
      const cache = this.readSessionCache()
      this.restoring = true
      const applyDetail = (data) => {
        const session = (data && data.session) || null
        if (!session || !session.id) {
          this.sessionId = null
          this.messages = []
          return
        }
        this.sessionId = session.id
        if (session.product_id) this.productId = session.product_id
        if (session.project_id) this.projectId = session.project_id
        this.messages = this.mapServerMessages(data.messages)
        this.writeSessionCache(this.sessionId, this.productId, this.projectId)
      }
      const fetchById = (sessionId) => getQualityAssistantSession(sessionId).then(res => {
        applyDetail((res && res.data) || res || {})
      })
      const fetchLatest = () => getLatestQualityAssistantSession().then(res => {
        applyDetail((res && res.data) || res || {})
      })
      const task = cache && cache.sessionId
        ? fetchById(cache.sessionId).catch(() => fetchLatest())
        : fetchLatest()
      return task.catch(() => {
        this.sessionId = null
        this.messages = []
        this.clearSessionCache()
      }).finally(() => {
        this.restoring = false
      })
    },
    open () {
      this.visible = true
      this.ensureContext()
      this.loadExamples()
      const after = () => this.$nextTick(this.scrollBottom)
      if (!this.messages.length && this.readSessionCache()) {
        this.restoreSessionQuietly().then(after)
      } else {
        after()
      }
    },
    resolveErrorMessage (err) {
      if (!err) return '助手暂不可用，请到契约/巡检菜单查看'
      if (typeof err === 'string') return err
      const res = err.response && err.response.data
      const detail = res && res.detail
      return (detail && detail.message) ||
        (res && res.message) ||
        err.message ||
        '助手暂不可用，请到契约/巡检菜单查看'
    },
    ensureContext () {
      const cache = readLastProductProjectCache() || {}
      const sessionCache = this.readSessionCache() || {}
      const preferProduct = this.productId || sessionCache.productId || cache.productId
      const preferProject = this.projectId || sessionCache.projectId || cache.projectId
      this.loadProducts().then(() => {
        if (preferProduct) {
          this.productId = preferProduct
          return this.loadProjects().then(() => {
            if (preferProject) this.projectId = preferProject
          })
        }
      })
    },
    loadExamples () {
      getQualityAssistantExamples().then(res => {
        const items = (res && res.data && res.data.items) || (res && res.items) || []
        if (items.length) this.examples = items
      }).catch(() => {})
    },
    loadProducts () {
      return getProductList({ pageNo: 1, pageSize: 200, status: 1 }).then(res => {
        const data = (res && res.data) || res || {}
        this.productOptions = data.list || data.items || data.records || []
      }).catch(() => {
        this.productOptions = []
      })
    },
    loadProjects () {
      if (!this.productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 200, productId: this.productId }).then(res => {
        const data = (res && res.data) || res || {}
        this.projectOptions = data.list || data.items || data.records || []
      }).catch(() => {
        this.projectOptions = []
      })
    },
    onProductChange () {
      this.projectId = ''
      this.loadProjects()
    },
    onProjectChange () {
      if (this.productId && this.projectId) {
        saveLastProductProjectCache(this.productId, this.projectId)
      }
    },
    ask (text) {
      this.input = text
      this.send()
    },
    send () {
      const message = (this.input || '').trim()
      if (!message || this.loading) return
      if (!this.projectId) {
        this.$message.warning('请先选择产品与项目')
        return
      }
      this.messages.push({ role: 'user', content: message })
      this.input = ''
      this.loading = true
      this.scrollBottom()
      qualityAssistantChat({
        session_id: this.sessionId,
        product_id: this.productId,
        project_id: this.projectId,
        message,
        context: { time_range: 'last_24h' }
      }).then(res => {
        const data = (res && res.data) || res || {}
        this.sessionId = data.session_id || this.sessionId
        this.writeSessionCache(this.sessionId, this.productId, this.projectId)
        const answer = data.answer || {}
        this.messages.push({
          role: 'assistant',
          content: answer.answer_text || data.message || '无返回',
          answer
        })
      }).catch(err => {
        this.messages.push({ role: 'assistant', content: this.resolveErrorMessage(err) })
      }).finally(() => {
        this.loading = false
        this.scrollBottom()
      })
    },
    clearChat () {
      const done = () => {
        this.messages = []
        this.sessionId = null
        this.citationExpanded = {}
        this.clearSessionCache()
      }
      if (!this.sessionId) {
        done()
        return
      }
      clearQualityAssistantSession(this.sessionId).then(done).catch(done)
    },
    onAction (action) {
      if (!action) return
      if (action.type === 'navigate' && action.route) {
        this.goRoute(action.route)
        return
      }
      if (action.type === 'run_contract_suite') {
        const suiteId = (action.payload && action.payload.suite_id) || action.suite_id
        this.$confirm('确认触发契约套件执行？', '二次确认', { type: 'warning' })
          .then(() => {
            this.loading = true
            return executeQualityAssistantAction({
              type: 'run_contract_suite',
              session_id: this.sessionId,
              payload: { suite_id: suiteId }
            })
          })
          .then(res => {
            const data = (res && res.data) || res || {}
            const answer = data.answer || {
              answer_text: '已触发执行',
              actions: [],
              citations: []
            }
            this.messages.push({
              role: 'assistant',
              content: answer.answer_text,
              answer
            })
            this.scrollBottom()
          })
          .catch(() => {})
          .finally(() => { this.loading = false })
      }
    },
    goRoute (route) {
      if (!route) return
      if (route.indexOf('?') >= 0) {
        const [path, qs] = route.split('?')
        const query = {}
        qs.split('&').forEach(pair => {
          const [k, v] = pair.split('=')
          if (k) query[k] = decodeURIComponent(v || '')
        })
        this.$router.push({ path, query })
      } else {
        this.$router.push(route)
      }
    },
    formatText (text) {
      return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br/>')
    },
    scrollBottom () {
      const el = this.$refs.msgList
      if (el) el.scrollTop = el.scrollHeight
    }
  }
}
</script>

<style scoped>
.qa-fab {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 3000;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 14px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: linear-gradient(135deg, #0ea5e9, #0369a1);
  color: #f8fafc;
  box-shadow: 0 10px 30px rgba(3, 105, 161, 0.35);
}
.qa-fab:hover { filter: brightness(1.06); }
.qa-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0b1220;
  color: #e2e8f0;
}
.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 16px 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}
.qa-title { font-size: 16px; font-weight: 600; }
.qa-sub { margin-top: 4px; font-size: 12px; color: #94a3b8; }
.qa-context {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 16px;
}
.qa-messages { flex: 1; overflow: auto; padding: 8px 16px 12px; }
.qa-empty { color: #64748b; font-size: 13px; padding: 24px 8px; text-align: center; }
.qa-msg { margin-bottom: 12px; display: flex; }
.qa-msg--user { justify-content: flex-end; }
.qa-msg--assistant { justify-content: flex-start; }
.qa-bubble {
  max-width: 92%;
  padding: 10px 12px;
  border-radius: 12px;
  background: #1e293b;
  border: 1px solid rgba(148, 163, 184, 0.18);
  font-size: 13px;
  line-height: 1.55;
  white-space: normal;
}
.qa-msg--user .qa-bubble {
  background: #0c4a6e;
  border-color: rgba(56, 189, 248, 0.35);
}
.qa-citations { margin-top: 8px; display: grid; gap: 6px; }
.qa-citations-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.qa-citations-label {
  font-size: 11px;
  color: #94a3b8;
}
.qa-citations-toggle {
  border: none;
  background: transparent;
  color: #38bdf8;
  cursor: pointer;
  font-size: 11px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.qa-citations-toggle:hover { opacity: 0.85; }
.qa-citation {
  padding: 8px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(56, 189, 248, 0.25);
  cursor: pointer;
}
.qa-citation:hover { border-color: #38bdf8; }
.qa-citation-title { font-weight: 600; font-size: 12px; }
.qa-citation-h { margin-top: 2px; color: #94a3b8; font-size: 11px; }
.qa-actions { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.qa-suggestions,
.qa-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 8px;
}
.qa-suggestions { margin-top: 8px; padding: 0; }
.qa-chip { cursor: pointer; }
.qa-input {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 12px 16px 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  align-items: end;
}
.qa-loading { color: #94a3b8; }
</style>

<style>
.qa-drawer {
  background: #0b1220 !important;
}
.qa-drawer .el-drawer__body {
  padding: 0;
  height: 100%;
}

body.theme-light .qa-fab {
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22);
}
body.theme-light .qa-drawer {
  background: #ffffff !important;
  border-left: 1px solid #dbe5f3;
}
body.theme-light .qa-panel {
  background: #ffffff;
  color: #1f2937;
}
body.theme-light .qa-header,
body.theme-light .qa-input {
  border-color: #e2e8f0;
}
body.theme-light .qa-sub,
body.theme-light .qa-empty,
body.theme-light .qa-loading,
body.theme-light .qa-citation-h {
  color: #64748b;
}
body.theme-light .qa-bubble {
  background: #f8fbff;
  border-color: #dbe5f3;
  color: #1f2937;
}
body.theme-light .qa-msg--user .qa-bubble {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #0f172a;
}
body.theme-light .qa-citations-label {
  color: #64748b;
}
body.theme-light .qa-citations-toggle {
  color: #2563eb;
}
body.theme-light .qa-citation {
  background: #ffffff;
  border-color: #bfdbfe;
}
body.theme-light .qa-citation:hover {
  border-color: #3b82f6;
}
body.theme-light .qa-drawer .el-button--text {
  color: #2563eb;
}
</style>
