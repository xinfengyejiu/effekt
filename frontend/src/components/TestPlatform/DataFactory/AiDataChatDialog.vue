<template>
  <el-dialog
    :visible.sync="visibleProxy"
    title="对话造数"
    width="920px"
    top="4vh"
    custom-class="ai-data-chat-dialog"
    :close-on-click-modal="false"
    @open="onOpen"
    @close="onClose">
    <section class="ai-data-chat">
      <header class="chat-header">
        <div>
          <div class="chat-title">统一造数对话</div>
          <div class="chat-context">
            <span>{{ productName || '未选产品' }}</span>
            <span class="sep">/</span>
            <span>{{ projectName || '未选项目' }}</span>
            <template v-if="env">
              <span class="sep">·</span>
              <span>环境 {{ env }}</span>
            </template>
          </div>
          <div class="chat-subtitle">自然语言 / SQL / 粘贴截图 · 使用当前项目环境库连接 · 确认前不写库</div>
        </div>
        <div class="header-actions">
          <el-dropdown trigger="click" @command="handleSessionCommand">
            <el-button size="mini" icon="el-icon-time">历史对话</el-button>
            <el-dropdown-menu slot="dropdown" class="session-menu">
              <el-dropdown-item command="new"><i class="el-icon-plus" /> 新对话</el-dropdown-item>
              <el-dropdown-item
                v-for="item in sessions"
                :key="item.id"
                :command="String(item.id)"
                divided>
                {{ item.title || '未命名对话' }}
              </el-dropdown-item>
              <el-dropdown-item v-if="!sessions.length" disabled divided>暂无历史</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
          <el-button size="mini" icon="el-icon-refresh" @click="resetChat">新对话</el-button>
        </div>
      </header>

      <div ref="messageArea" class="message-area">
        <div v-if="!messages.length" class="chat-empty">
          <i class="el-icon-chat-dot-round" />
          <div>开始对话造数</div>
          <p>当前针对「{{ productName || '-' }} / {{ projectName || '-' }}」造数；截图可直接粘贴识别。</p>
          <div class="suggestions">
            <button v-for="item in suggestions" :key="item" type="button" @click="useSuggestion(item)">{{ item }}</button>
          </div>
        </div>
        <div v-for="(message, index) in messages" :key="index" :class="['message-row', message.role]">
          <div class="message-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
          <div class="message-body">
            <div v-if="message.imageUrl" class="message-image">
              <img :src="message.imageUrl" alt="截图">
            </div>
            <div class="message-content">{{ message.content }}</div>
            <div v-if="message.draft" class="draft-card">
              <div class="draft-title">{{ message.draft.name || '场景草稿' }}</div>
              <div class="draft-desc">{{ message.draft.description }}</div>
              <div v-if="matchedTablesText(message.draft)" class="draft-tables">
                自动选表：{{ matchedTablesText(message.draft) }}
              </div>
              <div v-if="codeFilesText(message.draft)" class="draft-code">
                代码上下文：{{ codeFilesText(message.draft) }}
              </div>
              <div v-if="schemaErrorText(message.draft)" class="draft-schema-err">
                {{ schemaErrorText(message.draft) }}
              </div>
              <div v-if="codeErrorText(message.draft)" class="draft-schema-err">
                {{ codeErrorText(message.draft) }}
              </div>
              <el-table :data="stepRows(message.draft)" size="mini" border style="width: 100%; margin-top: 8px;">
                <el-table-column prop="type" label="类型" width="80" />
                <el-table-column prop="name" label="步骤" width="120" />
                <el-table-column prop="summary" label="摘要" min-width="220" show-overflow-tooltip />
              </el-table>
              <div class="draft-actions">
                <el-button type="primary" size="mini" @click="adoptDraft(message.draft)">采用并审阅</el-button>
                <el-button size="mini" :loading="executing" @click="confirmExecute(message.draft)">确认执行</el-button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="message-row assistant">
          <div class="message-avatar">AI</div>
          <div class="message-body"><div class="typing"><span /><span /><span /></div></div>
        </div>
      </div>

      <footer class="composer-wrap">
        <div class="composer">
          <div v-if="pendingImage" class="pending-image">
            <img :src="pendingImage.url" alt="待识别">
            <el-button type="text" icon="el-icon-close" @click="clearPendingImage">移除</el-button>
          </div>
          <el-input
            v-model="query"
            type="textarea"
            :rows="3"
            resize="none"
            :disabled="loading"
            :placeholder="composerPlaceholder"
            @keydown.native.ctrl.enter.prevent="submit"
            @paste.native="onPaste" />
          <div class="composer-footer">
            <div class="composer-left">
              <el-radio-group v-model="mode" size="mini">
                <el-radio-button label="nl">自然语言</el-radio-button>
                <el-radio-button label="sql">SQL</el-radio-button>
              </el-radio-group>
              <el-select
                v-model="env"
                size="mini"
                filterable
                clearable
                placeholder="选择环境"
                style="width: 140px;"
                :loading="envLoading"
                :disabled="!projectId">
                <el-option
                  v-for="item in runnableEnvs"
                  :key="item.name"
                  :label="item.label"
                  :value="item.name"
                  :disabled="!item.hasDb" />
              </el-select>
              <el-button
                v-if="projectId"
                type="text"
                size="mini"
                @click="goProjectEnvSettings">环境库连接</el-button>
              <el-button
                v-if="projectId"
                type="text"
                size="mini"
                @click="goProjectCodeSettings">代码仓库</el-button>
            </div>
            <el-button
              type="primary"
              size="small"
              icon="el-icon-position"
              :disabled="!canSend"
              :loading="loading"
              @click="submit">发送</el-button>
          </div>
        </div>
      </footer>
    </section>
  </el-dialog>
</template>

<script>
import {
  aiGenerateBuilder,
  aiRefineBuilder,
  createBuilder,
  executeBuilder,
  ocrGenerateBuilder,
  sqlDraftBuilder
} from '@/api/dataFactoryApi'
import { getProjectEnvironments } from '@/api/projectApi'

const HISTORY_PREFIX = 'effekt_ai_data_chat_'
const HISTORY_LIMIT = 20
const BLOCKED_ENVS = ['prod', 'production', 'prd', 'online']

function hasEnvDb(variables) {
  const vars = variables && typeof variables === 'object' ? variables : {}
  const db = vars.dbConnection || vars.db_connection || vars.database || null
  if (!db || typeof db !== 'object') return false
  return !!(db.host && (db.database || db.database_name || db.databaseName) && (db.user || db.username) && db.port)
}

export default {
  name: 'AiDataChatDialog',
  props: {
    visible: Boolean,
    projectId: [String, Number],
    productId: [String, Number],
    productName: { type: String, default: '' },
    projectName: { type: String, default: '' }
  },
  data() {
    return {
      query: '',
      mode: 'nl',
      loading: false,
      executing: false,
      env: '',
      envLoading: false,
      projectEnvs: [],
      sessionId: null,
      sessions: [],
      messages: [],
      currentDraft: null,
      pendingImage: null,
      suggestions: [
        '造一条演示订单并返回 id',
        '按手机号造一条用户数据',
        'SELECT 1 AS id'
      ]
    }
  },
  computed: {
    visibleProxy: {
      get() { return this.visible },
      set(v) { this.$emit('update:visible', v) }
    },
    composerPlaceholder() {
      if (this.mode === 'sql') return '粘贴 SQL，Ctrl+Enter 发送（确认前不写库）'
      return '用自然语言描述造数需求，或直接粘贴截图；Ctrl+Enter 发送'
    },
    canSend() {
      return !!(this.query.trim() || this.pendingImage)
    },
    storageKey() {
      return HISTORY_PREFIX + String(this.projectId || '0')
    },
    runnableEnvs() {
      return (this.projectEnvs || []).map(item => {
        const name = item.name || ''
        const blocked = BLOCKED_ENVS.includes(String(name).toLowerCase())
        const configured = hasEnvDb(item.variables)
        return {
          name,
          hasDb: configured && !blocked,
          label: blocked
            ? `${name}（生产禁止）`
            : (configured ? name : `${name}（未配库）`)
        }
      }).filter(item => item.name)
    }
  },
  watch: {
    projectId() {
      this.loadSessions()
      this.loadProjectEnvs()
      this.resetChat(false)
    },
    visible(val) {
      if (val) this.loadProjectEnvs()
    }
  },
  methods: {
    onOpen() {
      this.loadSessions()
      this.loadProjectEnvs()
      if (!this.messages.length) this.resetChat(false)
    },
    onClose() {
      this.persistCurrentSession()
      this.$emit('update:visible', false)
    },
    loadProjectEnvs() {
      if (!this.projectId) {
        this.projectEnvs = []
        this.env = ''
        return
      }
      this.envLoading = true
      getProjectEnvironments(this.projectId, { pageNo: 1, pageSize: 100 }).then(res => {
        const data = (res && res.data) || res || {}
        const list = data.items || data.list || data.data || data || []
        this.projectEnvs = Array.isArray(list) ? list : []
        const available = this.runnableEnvs.filter(item => item.hasDb).map(item => item.name)
        if (!available.includes(this.env)) {
          this.env = available[0] || ''
        }
      }).catch(() => {
        this.projectEnvs = []
        this.env = ''
      }).finally(() => {
        this.envLoading = false
      })
    },
    goProjectEnvSettings() {
      if (!this.projectId) return
      this.visibleProxy = false
      this.$router.push({
        path: '/test-platform/project/setting',
        query: {
          projectId: this.projectId,
          productId: this.productId,
          tab: 'environments'
        }
      })
    },
    goProjectCodeSettings() {
      if (!this.projectId) return
      this.visibleProxy = false
      this.$router.push({
        path: '/test-platform/project/setting',
        query: {
          projectId: this.projectId,
          productId: this.productId,
          tab: 'codePrd'
        }
      })
    },
    ensureEnvReady() {
      if (!this.projectId) {
        this.$message.warning('请先选择产品与项目')
        return false
      }
      if (!this.env) {
        this.$message.warning('请先选择环境；若无可选环境，请先在项目设置中配置环境与数据库连接')
        return false
      }
      const selected = this.runnableEnvs.find(item => item.name === this.env)
      if (!selected || !selected.hasDb) {
        this.$message.warning(`环境「${this.env}」未配置可用数据库连接，请先在项目设置中配置`)
        return false
      }
      return true
    },
    loadSessions() {
      try {
        const raw = localStorage.getItem(this.storageKey)
        const list = raw ? JSON.parse(raw) : []
        this.sessions = Array.isArray(list) ? list : []
      } catch (e) {
        this.sessions = []
      }
    },
    persistCurrentSession() {
      if (!this.projectId || !this.messages.length) return
      const title = this.buildSessionTitle()
      const record = {
        id: this.sessionId || Date.now(),
        title,
        updatedAt: new Date().toISOString(),
        mode: this.mode,
        currentDraft: this.currentDraft,
        messages: this.messages.map(m => ({
          role: m.role,
          content: m.content,
          imageUrl: m.imageUrl || '',
          draft: m.draft || null
        }))
      }
      this.sessionId = record.id
      const others = (this.sessions || []).filter(s => String(s.id) !== String(record.id))
      const next = [record].concat(others).slice(0, HISTORY_LIMIT)
      this.sessions = next
      try {
        localStorage.setItem(this.storageKey, JSON.stringify(next))
      } catch (e) { /* quota */ }
    },
    buildSessionTitle() {
      const firstUser = (this.messages || []).find(m => m.role === 'user')
      const text = (firstUser && firstUser.content) || '未命名对话'
      return String(text).replace(/\s+/g, ' ').slice(0, 28) || '未命名对话'
    },
    handleSessionCommand(command) {
      if (command === 'new') {
        this.persistCurrentSession()
        this.resetChat(true)
        return
      }
      this.persistCurrentSession()
      const item = (this.sessions || []).find(s => String(s.id) === String(command))
      if (!item) return
      this.sessionId = item.id
      this.mode = item.mode || 'nl'
      this.currentDraft = item.currentDraft || null
      this.messages = (item.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        imageUrl: m.imageUrl || '',
        draft: m.draft || null
      }))
      this.query = ''
      this.clearPendingImage()
      this.scrollToBottom()
    },
    resetChat(persistBefore) {
      if (persistBefore) this.persistCurrentSession()
      this.sessionId = null
      this.messages = []
      this.currentDraft = null
      this.query = ''
      this.clearPendingImage()
      this.loading = false
    },
    useSuggestion(text) {
      this.query = text
      if (/^\s*(select|insert|update|delete|with)\b/i.test(text)) this.mode = 'sql'
      else this.mode = 'nl'
    },
    stepRows(draft) {
      const steps = (((draft || {}).definition || {}).steps) || []
      return steps.map(step => ({
        type: step.type,
        name: step.name,
        summary: this.stepSummary(step)
      }))
    },
    matchedTablesText(draft) {
      const tables = ((draft || {}).meta || {}).matchedTables || []
      return Array.isArray(tables) && tables.length ? tables.join('、') : ''
    },
    codeFilesText(draft) {
      const files = ((draft || {}).meta || {}).codeFiles || []
      if (!Array.isArray(files) || !files.length) return ''
      const short = files.slice(0, 4).map(f => String(f).split('/').pop())
      const more = files.length > 4 ? ` 等${files.length}个文件` : ''
      return short.join('、') + more
    },
    schemaErrorText(draft) {
      return (((draft || {}).meta || {}).schemaError || '').trim()
    },
    codeErrorText(draft) {
      return (((draft || {}).meta || {}).codeError || '').trim()
    },
    stepSummary(step) {
      if (!step) return ''
      if (step.type === 'sql') {
        return [step.env, (step.sql || '').slice(0, 100)].filter(Boolean).join(' | ')
      }
      if (step.type === 'set_var') return 'vars: ' + Object.keys(step.vars || {}).join(',')
      if (step.type === 'assert') return step.expr || ''
      return JSON.stringify(step).slice(0, 80)
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.messageArea
        if (el) el.scrollTop = el.scrollHeight
      })
    },
    clearPendingImage() {
      if (this.pendingImage && this.pendingImage.url && String(this.pendingImage.url).indexOf('blob:') === 0) {
        URL.revokeObjectURL(this.pendingImage.url)
      }
      this.pendingImage = null
    },
    fileToDataUrl(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    },
    setPendingImage(file) {
      this.clearPendingImage()
      this.pendingImage = {
        file,
        url: URL.createObjectURL(file)
      }
    },
    onPaste(e) {
      const items = (e.clipboardData && e.clipboardData.items) || []
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type && item.type.indexOf('image') === 0) {
          const file = item.getAsFile()
          if (file) {
            e.preventDefault()
            this.setPendingImage(file)
            return
          }
        }
      }
    },
    submit() {
      if (!this.ensureEnvReady()) return
      if (this.loading) return
      if (this.pendingImage) {
        this.submitOcr()
        return
      }
      const text = (this.query || '').trim()
      if (!text) return
      if (this.mode === 'sql' || /^\s*(select|insert|update|delete|with)\b/i.test(text)) {
        this.submitSql(text)
      } else {
        this.submitNl(text)
      }
    },
    buildContextPayload(extra) {
      return Object.assign({
        projectId: this.projectId,
        productId: this.productId,
        productName: this.productName || '',
        projectName: this.projectName || '',
        env: this.env
      }, extra || {})
    },
    submitNl(text) {
      this.messages.push({ role: 'user', content: text })
      this.query = ''
      this.loading = true
      this.scrollToBottom()
      const req = this.currentDraft
        ? aiRefineBuilder(this.buildContextPayload({
          draft: this.currentDraft,
          instruction: text
        }))
        : aiGenerateBuilder(this.buildContextPayload({
          prompt: text
        }))
      req.then(res => {
        const draft = (res && res.data) || res || {}
        if (!draft || (!draft.definition && !draft.name)) {
          this.messages.push({ role: 'assistant', content: '生成结果为空，请稍后重试。' })
          return
        }
        const tip = this.currentDraft
          ? '已按你的指令改了一版草稿。'
          : '已生成造数草稿，请审阅后采用或执行。'
        this.pushDraftMessage(draft, tip)
      }).catch(err => {
        let msg = (err && err.message) ? String(err.message) : '生成失败，请稍后重试。'
        if (/timeout/i.test(msg)) {
          msg = '生成超时：AI 或探表耗时过长。可先用 SQL 模式，或检查环境库/代码仓库后重试。'
        }
        this.messages.push({ role: 'assistant', content: msg })
      }).finally(() => {
        this.loading = false
        this.persistCurrentSession()
        this.scrollToBottom()
      })
    },
    submitSql(sql) {
      this.messages.push({ role: 'user', content: sql })
      this.query = ''
      this.loading = true
      this.scrollToBottom()
      sqlDraftBuilder(this.buildContextPayload({ sql })).then(res => {
        const draft = (res && res.data) || res || {}
        this.pushDraftMessage(draft, '已将 SQL 收成场景草稿（确认前不写库）。')
      }).catch(() => {
        this.messages.push({ role: 'assistant', content: 'SQL 草稿生成失败，请检查语句或环境。' })
      }).finally(() => {
        this.loading = false
        this.persistCurrentSession()
        this.scrollToBottom()
      })
    },
    submitOcr() {
      const file = this.pendingImage && this.pendingImage.file
      if (!file) return
      const caption = (this.query || '').trim() || '请根据截图生成造数场景'
      this.loading = true
      this.fileToDataUrl(file).then(dataUrl => {
        this.messages.push({ role: 'user', content: caption, imageUrl: dataUrl })
        this.query = ''
        this.clearPendingImage()
        this.scrollToBottom()
        const fd = new FormData()
        fd.append('file', file)
        fd.append('projectId', this.projectId)
        fd.append('productId', this.productId || '')
        fd.append('productName', this.productName || '')
        fd.append('projectName', this.projectName || '')
        fd.append('env', this.env)
        fd.append('prompt', caption)
        return ocrGenerateBuilder(fd)
      }).then(res => {
        const draft = (res && res.data) || res || {}
        const tip = (draft.meta && draft.meta.aiError)
          ? ('截图识别降级：' + draft.meta.aiError)
          : '已根据截图生成草稿，请审阅。'
        this.pushDraftMessage(draft, tip)
      }).catch(() => {
        this.messages.push({ role: 'assistant', content: '截图识别失败，请改用自然语言或 SQL。' })
      }).finally(() => {
        this.loading = false
        this.persistCurrentSession()
        this.scrollToBottom()
      })
    },
    pushDraftMessage(draft, tip) {
      this.currentDraft = draft
      const tables = ((draft || {}).meta || {}).matchedTables || []
      const files = ((draft || {}).meta || {}).codeFiles || []
      let content = tip
      if (Array.isArray(tables) && tables.length) {
        content = content + '\n已根据环境库自动匹配表：' + tables.join('、')
      } else if (((draft || {}).meta || {}).schemaError) {
        content = content + '\n（未能自动探表：' + draft.meta.schemaError + '）'
      }
      if (Array.isArray(files) && files.length) {
        content = content + '\n已结合代码仓库上下文：' + files.slice(0, 4).map(f => String(f).split('/').pop()).join('、')
        if (files.length > 4) content += ` 等${files.length}个文件`
      } else if (((draft || {}).meta || {}).codeError) {
        content = content + '\n（未能加载代码：' + draft.meta.codeError + '）'
      }
      this.messages.push({
        role: 'assistant',
        content,
        draft
      })
    },
    adoptDraft(draft) {
      this.persistCurrentSession()
      try {
        sessionStorage.setItem('dataFactoryAiDraft', JSON.stringify(draft || {}))
      } catch (e) { /* ignore */ }
      this.visibleProxy = false
      this.$emit('adopt', draft)
      this.$router.push({
        path: '/data-tools/factory/editor',
        query: {
          projectId: this.projectId,
          productId: this.productId,
          fromAi: 1
        }
      })
    },
    confirmExecute(draft) {
      if (!draft || !this.projectId) return
      if (!this.ensureEnvReady()) return
      const stamped = this.stampDraftEnv(draft)
      this.$confirm(
        `确认在环境「${this.env}」执行？将按草稿 steps 写入该环境配置的目标库（生产环境已禁止）。`,
        '确认执行',
        { type: 'warning' }
      ).then(() => {
        this.executing = true
        return createBuilder(this.projectId, {
          name: stamped.name || '对话造数临时场景',
          description: stamped.description || '',
          builderType: 1,
          source: stamped.meta && stamped.meta.generatedBy === 'sql' ? 'manual' : 'ai',
          tags: stamped.tags || ['对话'],
          definition: stamped.definition,
          inputSchema: stamped.inputSchema || {}
        })
      }).then(res => {
        const id = ((res && res.data) || res || {}).id
        if (!id) throw new Error('创建场景失败')
        return executeBuilder(this.projectId, id, { params: stamped.params || {} })
      }).then(res => {
        const data = (res && res.data) || res || {}
        this.$message.success('执行完成，任务ID：' + (data.taskId || '-'))
        this.persistCurrentSession()
        this.$emit('executed', data)
      }).catch(() => {}).finally(() => {
        this.executing = false
      })
    },
    stampDraftEnv(draft) {
      const next = JSON.parse(JSON.stringify(draft || {}))
      const steps = (((next.definition || {}).steps) || [])
      steps.forEach(step => {
        if (step && String(step.type || '').toLowerCase() === 'sql') {
          step.env = this.env
        }
      })
      if (!next.meta) next.meta = {}
      next.meta.env = this.env
      next.meta.projectId = this.projectId
      return next
    }
  }
}
</script>

<style>
.ai-data-chat-dialog .el-dialog__body {
  padding: 0;
}
</style>

<style scoped>
.ai-data-chat {
  height: 74vh;
  min-height: 520px;
  display: flex;
  flex-direction: column;
  background: #fbfcfd;
}
.chat-header {
  min-height: 64px;
  box-sizing: border-box;
  padding: 13px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8edf3;
  background: #fff;
}
.header-actions { display: flex; gap: 8px; align-items: center; }
.chat-title { color: #202b3a; font-size: 15px; font-weight: 700; }
.chat-context {
  margin-top: 4px;
  color: #2f6f66;
  font-size: 12px;
  font-weight: 600;
}
.chat-context .sep { margin: 0 4px; color: #9aa7b5; font-weight: 400; }
.chat-subtitle { margin-top: 2px; color: #98a2b0; font-size: 12px; }
.message-area { flex: 1; min-height: 0; padding: 18px 5%; overflow: auto; }
.chat-empty { max-width: 520px; margin: 10vh auto 0; color: #657184; text-align: center; }
.chat-empty > i { color: #57aa9c; font-size: 38px; }
.chat-empty div { margin-top: 14px; color: #354255; font-size: 17px; font-weight: 700; }
.chat-empty p { margin: 8px 0 0; color: #97a1af; font-size: 13px; }
.suggestions { margin-top: 24px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.suggestions button {
  padding: 8px 11px; border: 1px solid #e4e9ef; border-radius: 16px;
  background: #fff; color: #748093; cursor: pointer; font-size: 12px;
}
.suggestions button:hover { border-color: #7dbeb3; color: #218b79; }
.message-row { margin: 0 auto 18px; display: flex; gap: 11px; max-width: 860px; }
.message-row.user { flex-direction: row-reverse; }
.message-avatar {
  width: 30px; height: 30px; flex: 0 0 30px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; background: #dff0ed; color: #258b7b; font-size: 11px; font-weight: 700;
}
.user .message-avatar { background: #e8eef7; color: #526987; }
.message-body { max-width: min(96%, 760px); }
.message-content {
  padding: 10px 13px; border: 1px solid #e7ebf0; border-radius: 4px 13px 13px;
  background: #fff; color: #3e4a5b; font-size: 14px; line-height: 1.75; white-space: pre-wrap; word-break: break-word;
}
.user .message-content { border-color: #dce9e7; border-radius: 13px 4px 13px 13px; background: #edf7f5; }
.message-image { margin-bottom: 8px; }
.message-image img, .pending-image img {
  max-width: 220px; max-height: 140px; border-radius: 8px; border: 1px solid #e5eaf0;
}
.draft-card {
  margin-top: 8px; padding: 10px 12px; border: 1px solid #dce9e7; border-radius: 8px; background: #fff;
}
.draft-title { font-weight: 700; color: #1f2d3d; font-size: 13px; }
.draft-desc { margin-top: 4px; color: #667386; font-size: 12px; line-height: 1.5; }
.draft-tables {
  margin-top: 6px;
  color: #218b79;
  font-size: 12px;
  font-weight: 600;
}
.draft-code {
  margin-top: 4px;
  color: #3b6ea5;
  font-size: 12px;
  font-weight: 600;
}
.draft-schema-err {
  margin-top: 4px;
  color: #c45656;
  font-size: 12px;
}
.draft-actions { margin-top: 10px; text-align: right; }
.composer-wrap { border-top: 1px solid #e8edf3; background: #fff; padding: 12px 16px 14px; }
.composer { border: 1px solid #e4e9ef; border-radius: 10px; padding: 10px; background: #fff; }
.pending-image { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.composer-footer { margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.composer-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.typing { display: flex; gap: 5px; padding: 12px 14px; }
.typing span {
  width: 6px; height: 6px; border-radius: 50%; background: #9bb0a9;
  animation: blink 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes blink {
  0%, 80%, 100% { opacity: .35; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-2px); }
}
</style>
