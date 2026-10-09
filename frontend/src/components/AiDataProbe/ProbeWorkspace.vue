<template>
  <div class="page-wrap ai-probe-workspace">
    <page-section title="AI智能问数">
      <template slot="extra">
        <div class="header-filters">
          <span class="filter-label">产品</span>
          <el-select
            v-model="productId"
            clearable
            filterable
            size="small"
            placeholder="选择产品"
            style="width:160px;"
            @change="onProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.id"
              :label="p.name"
              :value="String(p.id)"
            />
          </el-select>
          <span class="filter-label">项目</span>
          <el-select
            v-model="projectId"
            clearable
            filterable
            size="small"
            placeholder="选择项目"
            style="width:160px;"
            :disabled="!productId"
            @change="onProjectChange"
          >
            <el-option
              v-for="p in projectOptions"
              :key="p.id"
              :label="p.name"
              :value="String(p.id)"
            />
          </el-select>
          <el-tag v-if="currentConnectionMeta" size="mini" type="info" class="conn-meta-tag" :title="currentConnectionMeta">
            {{ currentConnectionMeta }}
          </el-tag>
          <el-button size="small" @click="$router.push('/ai-data-probe/connections')">连接管理</el-button>
        </div>
      </template>

      <div class="workspace">
        <aside class="side">
          <div class="side-block">
            <div class="side-title">业务库连接</div>
            <el-select
              v-model="connectionId"
              filterable
              clearable
              placeholder="选择连接"
              size="small"
              style="width:100%;"
              @change="onConnectionChange"
            >
              <el-option
                v-for="item in displayConnections"
                :key="item.id"
                :label="connectionLabel(item)"
                :value="String(item.id)"
              />
            </el-select>
            <div v-if="currentConnection" class="conn-bound">
              <div>产品：{{ currentConnection.productName || '-' }}</div>
              <div>项目：{{ currentConnection.projectName || '-' }}</div>
            </div>
          </div>
          <div class="side-block">
            <div class="side-title">
              <span>会话</span>
              <el-button type="text" size="mini" @click="newSession">新建</el-button>
            </div>
            <div v-loading="sessionLoading" class="session-list">
              <div
                v-for="item in sessions"
                :key="item.id"
                class="session-item"
                :class="{ active: String(item.id) === String(sessionId) }"
                @click="loadSession(item.id)"
              >
                <div class="session-row">
                  <div class="session-name" :title="item.title || item.sessionNo">{{ item.title || item.sessionNo }}</div>
                  <el-button
                    type="text"
                    size="mini"
                    icon="el-icon-edit"
                    class="session-rename-btn"
                    title="重命名"
                    @click.stop="renameSession(item)"
                  />
                </div>
                <div class="session-meta">{{ item.updatedTime || item.createdTime }}</div>
              </div>
              <div v-if="!sessions.length" class="empty-tip">暂无会话</div>
            </div>
          </div>
        </aside>

        <aside class="table-side">
          <div class="side-title">
            <span>数据表{{ tableTotal ? ' (' + tableTotal + ')' : '' }}</span>
            <el-button type="text" size="mini" :loading="tableLoading" :disabled="!connectionId" @click="loadTables">刷新</el-button>
          </div>
          <el-input
            v-model="tableKeyword"
            size="mini"
            clearable
            prefix-icon="el-icon-search"
            placeholder="过滤表名"
            :disabled="!connectionId"
            @input="onTableFilter"
          />
          <div v-loading="tableLoading" class="table-list">
            <div v-if="!connectionId" class="empty-tip">请先选择连接</div>
            <div v-else-if="tableError" class="empty-tip table-error">{{ tableError }}</div>
            <div v-else-if="!filteredTables.length" class="empty-tip">暂无表</div>
            <div
              v-for="item in filteredTables"
              :key="item.name"
              class="table-item"
              :class="{ active: item.name === activeTable }"
            >
              <div class="table-row" @click="toggleTable(item.name)">
                <i :class="item.name === activeTable ? 'el-icon-arrow-down' : 'el-icon-arrow-right'"></i>
                <span class="table-name" :title="item.name">{{ item.name }}</span>
                <el-button type="text" size="mini" class="use-btn" @click.stop="useTable(item.name)">用它查</el-button>
              </div>
              <div v-if="item.name === activeTable" class="column-list">
                <div v-if="columnLoading" class="empty-tip">加载字段…</div>
                <div v-else-if="!tableColumns.length" class="empty-tip">无字段</div>
                <div v-for="col in tableColumns" :key="col.name" class="column-item" :title="col.type">
                  <span class="col-name">{{ col.name }}</span>
                  <span class="col-type">{{ col.type }}</span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <main class="main">
          <div class="chat-panel" ref="chatPanel">
            <div v-if="!messages.length" class="empty-tip chat-empty">
              选择连接后可问库表数据，也可问项目 Git 里的代码逻辑/配置（如：选了 IP 后有多少种场景图）
            </div>
            <div v-for="(msg, idx) in messages" :key="msg.id || idx" class="msg" :class="msg.role">
              <div class="bubble">
                <template v-if="msg.role === 'user'">
                  <div class="user-q">{{ (msg.content && msg.content.question) || '' }}</div>
                </template>
                <template v-else>
                  <div v-if="msg.content && msg.content.streaming && !(msg.content.conclusion || msg.content.streamText)" class="stream-status">
                    {{ msg.content.streamStatus || '思考中…' }}
                    <span class="typing-cursor">▍</span>
                  </div>
                  <div
                    v-if="msg.content && (msg.content.conclusion || msg.content.streamText)"
                    class="conclusion"
                    :class="'st-' + ((msg.content && msg.content.status) || 'insufficient')"
                  >
                    {{ msg.content.conclusion || msg.content.streamText }}
                    <span v-if="msg.content.streaming" class="typing-cursor">▍</span>
                  </div>
                  <div v-if="msg.content && msg.content.highlights && msg.content.highlights.length" class="highlights">
                    <el-tag v-for="(h, i) in msg.content.highlights" :key="i" size="mini" style="margin:2px 4px 2px 0;">{{ h }}</el-tag>
                  </div>
                  <el-collapse v-if="msg.content && msg.content.sqls && msg.content.sqls.length && !msg.content.streaming">
                    <el-collapse-item title="查看 SQL / 证据">
                      <div v-for="(sql, si) in msg.content.sqls" :key="si" class="sql-block">
                        <pre>{{ sql }}</pre>
                      </div>
                      <el-table
                        v-if="msg.content.evidence && msg.content.evidence.length"
                        :data="msg.content.evidence"
                        border
                        size="mini"
                        style="width:100%; margin-top:8px;"
                        max-height="240"
                      >
                        <el-table-column
                          v-for="col in evidenceColumns(msg.content.evidence)"
                          :key="col"
                          :prop="col"
                          :label="col"
                          min-width="100"
                          show-overflow-tooltip
                        />
                      </el-table>
                      <div v-if="msg.content.schemaMeta && msg.content.schemaMeta.matchedTables" class="meta-line">
                        匹配表：{{ (msg.content.schemaMeta.matchedTables || []).join(', ') || '-' }}
                      </div>
                      <div v-if="msg.content.codeMeta && msg.content.codeMeta.codeFiles && msg.content.codeMeta.codeFiles.length" class="meta-line">
                        代码参考：{{ (msg.content.codeMeta.codeFiles || []).slice(0, 4).join('；') }}
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                  <div v-if="!msg.content.streaming && codeTip(msg.content)" class="code-tip">
                    {{ codeTip(msg.content) }}
                    <el-button
                      v-if="msg.content.codeMeta && msg.content.codeMeta.projectId"
                      type="text"
                      size="mini"
                      @click="goProjectCodeSettings(msg.content.codeMeta.projectId)"
                    >去配置</el-button>
                  </div>
                  <div
                    v-if="!msg.content.streaming && msg.content.codeMeta && msg.content.codeMeta.codeFiles && msg.content.codeMeta.codeFiles.length"
                    class="meta-line"
                  >
                    代码依据：{{ (msg.content.codeMeta.codeFiles || []).slice(0, 6).join('；') }}
                    <el-tag v-if="msg.content.mode === 'code'" size="mini" type="success" style="margin-left:6px;">代码问答</el-tag>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <div class="composer">
            <el-input
              v-model="question"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 12 }"
              placeholder="可问库表数据，也可问代码逻辑/配置；例：选了 IP 后有多少种场景图（Enter 发送，Alt+Enter 换行）"
              @keydown.native="onComposerKeydown"
            />
            <div class="composer-actions">
              <el-checkbox v-model="executeSql">立即执行 SQL</el-checkbox>
              <el-button size="small" @click="openRerun">改 SQL 再跑</el-button>
              <el-button v-if="asking" size="small" @click="stopAsk">停止</el-button>
              <el-button type="primary" size="small" :disabled="!connectionId || asking" @click="sendAsk">智能问数</el-button>
            </div>
          </div>
        </main>
      </div>
    </page-section>

    <el-dialog title="修订 SQL 后只读重跑" :visible.sync="rerunVisible" width="640px" :close-on-click-modal="false">
      <el-input v-model="rerunSql" type="textarea" :rows="8" placeholder="仅允许 SELECT" />
      <span slot="footer">
        <el-button size="small" @click="rerunVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="asking" @click="doRerun">执行</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  askAiDataProbeStream,
  getAiDataProbeConnections,
  getAiDataProbeSessionDetail,
  getAiDataProbeSessions,
  getAiDataProbeTableColumns,
  getAiDataProbeTables,
  renameAiDataProbeSession,
  rerunAiDataProbeSql
} from '@/api/aiDataProbeApi'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  readLastProductProjectCache,
  saveLastProductProjectCache
} from '@/utils/lastProductProjectCache'

export default {
  name: 'AiDataProbeWorkspace',
  components: { PageSection },
  data() {
    return {
      connections: [],
      connectionId: '',
      productId: '',
      projectId: '',
      productOptions: [],
      projectOptions: [],
      sessions: [],
      sessionId: '',
      messages: [],
      question: '',
      executeSql: true,
      asking: false,
      sessionLoading: false,
      rerunVisible: false,
      rerunSql: '',
      tables: [],
      tableTotal: 0,
      tableKeyword: '',
      tableLoading: false,
      tableError: '',
      activeTable: '',
      tableColumns: [],
      columnLoading: false,
      _tableFilterTimer: null,
      _streamHandle: null,
      _syncingFromConnection: false
    }
  },
  computed: {
    filteredTables() {
      const kw = (this.tableKeyword || '').trim().toLowerCase()
      if (!kw) return this.tables
      return (this.tables || []).filter(t => (t.name || '').toLowerCase().indexOf(kw) >= 0)
    },
    displayConnections() {
      let list = this.connections || []
      if (this.productId) {
        list = list.filter(c => String(c.productId || '') === String(this.productId))
      }
      if (this.projectId) {
        list = list.filter(c => String(c.projectId || '') === String(this.projectId))
      }
      return list
    },
    currentConnection() {
      if (!this.connectionId) return null
      return (this.connections || []).find(c => String(c.id) === String(this.connectionId)) || null
    },
    currentConnectionMeta() {
      const c = this.currentConnection
      if (!c) return ''
      const parts = []
      if (c.productName) parts.push(c.productName)
      if (c.projectName) parts.push(c.projectName)
      return parts.join(' / ')
    }
  },
  created() {
    const qid = this.$route.query.connectionId
    if (qid) this.connectionId = String(qid)
    const cache = readLastProductProjectCache() || {}
    if (cache.productId) this.productId = String(cache.productId)
    if (cache.projectId) this.projectId = String(cache.projectId)
    this.loadProducts()
      .then(() => {
        if (this.productId) return this.loadProjects()
      })
      .then(() => this.loadConnections())
      .then(() => {
        this.ensureConnectionInFilter()
        if (this.connectionId) {
          this.syncProductProjectFromConnection()
          this.refreshSessions()
          this.loadTables()
        }
      })
  },
  beforeDestroy() {
    if (this._tableFilterTimer) clearTimeout(this._tableFilterTimer)
    this.stopAsk()
  },
  methods: {
    connectionLabel(item) {
      if (!item) return ''
      const base = (item.name || '') + ' (' + (item.env || '-') + ')'
      if (item.projectName) return base + ' · ' + item.projectName
      return base
    },
    loadProducts() {
      return getProductList({ pageNo: 1, pageSize: 200, status: 1 })
        .then(res => {
          const data = (res && res.data) || {}
          this.productOptions = data.list || data.items || data.records || []
        })
        .catch(() => { this.productOptions = [] })
    },
    loadProjects() {
      if (!this.productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 200, productId: this.productId })
        .then(res => {
          const data = (res && res.data) || {}
          this.projectOptions = data.list || data.items || data.records || []
        })
        .catch(() => { this.projectOptions = [] })
    },
    onProductChange() {
      if (this._syncingFromConnection) return
      this.projectId = ''
      this.projectOptions = []
      this.loadProjects().then(() => {
        this.ensureConnectionInFilter(true)
      })
    },
    onProjectChange() {
      if (this._syncingFromConnection) return
      if (this.productId && this.projectId) {
        saveLastProductProjectCache(this.productId, this.projectId)
      }
      this.ensureConnectionInFilter(true)
    },
    ensureConnectionInFilter(resetIfMissing) {
      const list = this.displayConnections
      const stillValid = list.some(c => String(c.id) === String(this.connectionId))
      if (stillValid) return
      if (!resetIfMissing && this.connectionId) return
      const next = list[0]
      const nextId = next ? String(next.id) : ''
      if (String(this.connectionId) === nextId) return
      this.connectionId = nextId
      this.onConnectionChange()
    },
    syncProductProjectFromConnection() {
      const c = this.currentConnection
      if (!c) return
      this._syncingFromConnection = true
      const nextProduct = c.productId != null && c.productId !== '' ? String(c.productId) : ''
      const nextProject = c.projectId != null && c.projectId !== '' ? String(c.projectId) : ''
      const productChanged = nextProduct && nextProduct !== String(this.productId || '')
      this.productId = nextProduct || this.productId
      const after = () => {
        this.projectId = nextProject || (productChanged ? '' : this.projectId)
        if (this.productId && this.projectId) {
          saveLastProductProjectCache(this.productId, this.projectId)
        }
        this.$nextTick(() => { this._syncingFromConnection = false })
      }
      if (productChanged || (this.productId && !this.projectOptions.length)) {
        this.loadProjects().then(after)
      } else {
        after()
      }
    },
    loadConnections() {
      return getAiDataProbeConnections({ pageNo: 1, pageSize: 100, enabled: 1 })
        .then(res => {
          const data = (res && res.data) || {}
          this.connections = data.list || []
          if (!this.connectionId && this.displayConnections.length) {
            this.connectionId = String(this.displayConnections[0].id)
          } else if (!this.connectionId && this.connections.length) {
            this.connectionId = String(this.connections[0].id)
          }
        })
        .catch(() => { this.connections = [] })
    },
    onConnectionChange() {
      this.sessionId = ''
      this.messages = []
      this.activeTable = ''
      this.tableColumns = []
      this.tableKeyword = ''
      this.syncProductProjectFromConnection()
      this.refreshSessions()
      this.loadTables()
    },
    loadTables() {
      if (!this.connectionId) {
        this.tables = []
        this.tableTotal = 0
        this.tableError = ''
        return
      }
      this.tableLoading = true
      this.tableError = ''
      getAiDataProbeTables({ connectionId: this.connectionId })
        .then(res => {
          const data = (res && res.data) || {}
          this.tables = data.list || []
          this.tableTotal = data.total || this.tables.length
        })
        .catch(err => {
          this.tables = []
          this.tableTotal = 0
          this.tableError = (err && err.message) || '拉取表列表失败'
        })
        .finally(() => { this.tableLoading = false })
    },
    onTableFilter() {
      // 前端本地过滤即可；保留钩子便于后续改为服务端检索
    },
    toggleTable(name) {
      if (this.activeTable === name) {
        this.activeTable = ''
        this.tableColumns = []
        return
      }
      this.activeTable = name
      this.tableColumns = []
      this.columnLoading = true
      getAiDataProbeTableColumns({ connectionId: this.connectionId, tableName: name })
        .then(res => {
          const data = (res && res.data) || {}
          this.tableColumns = data.columns || []
        })
        .catch(() => { this.tableColumns = [] })
        .finally(() => { this.columnLoading = false })
    },
    useTable(name) {
      if (!name) return
      const tip = `查一下表 ${name} 的数据条数和最近几条样例`
      this.question = tip
    },
    refreshSessions() {
      if (!this.connectionId) {
        this.sessions = []
        return
      }
      this.sessionLoading = true
      getAiDataProbeSessions({ connectionId: this.connectionId, pageNo: 1, pageSize: 50 })
        .then(res => {
          const data = (res && res.data) || {}
          this.sessions = data.list || []
        })
        .catch(() => { this.sessions = [] })
        .finally(() => { this.sessionLoading = false })
    },
    newSession() {
      this.sessionId = ''
      this.messages = []
      this.question = ''
    },
    loadSession(id) {
      this.sessionId = String(id)
      getAiDataProbeSessionDetail({ sessionId: id }).then(res => {
        const data = (res && res.data) || {}
        this.messages = data.messages || []
        if (data.connectionId) this.connectionId = String(data.connectionId)
        this.$nextTick(this.scrollBottom)
      })
    },
    renameSession(item) {
      if (!item || !item.id) return
      this.$prompt('请输入新的会话名称', '重命名会话', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: item.title || item.sessionNo || '',
        inputPattern: /\S+/,
        inputErrorMessage: '名称不能为空',
        closeOnClickModal: false
      }).then(({ value }) => {
        const title = (value || '').trim()
        if (!title) return
        return renameAiDataProbeSession({ sessionId: item.id, title }).then(res => {
          const data = (res && res.data) || {}
          // 以用户提交的名称为准，避免接口因缓存回传旧 title
          const nextTitle = title || data.title || item.title
          const idx = (this.sessions || []).findIndex(s => String(s.id) === String(item.id))
          if (idx >= 0) {
            this.$set(this.sessions, idx, Object.assign({}, this.sessions[idx], {
              title: nextTitle,
              updatedTime: data.updatedTime || this.sessions[idx].updatedTime
            }))
          } else {
            this.refreshSessions()
          }
          this.$message.success('已重命名')
        })
      }).catch(() => {})
    },
    onComposerKeydown(e) {
      if (e.key !== 'Enter' && e.keyCode !== 13) return
      if (e.altKey) return
      e.preventDefault()
      if (this.asking) return
      this.sendAsk()
    },
    stopAsk() {
      if (this._streamHandle && this._streamHandle.abort) {
        this._streamHandle.abort()
      }
      this._streamHandle = null
      this.asking = false
      const last = this.messages[this.messages.length - 1]
      if (last && last.role === 'assistant' && last.content && last.content.streaming) {
        this.$set(last, 'content', Object.assign({}, last.content, {
          streaming: false,
          streamStatus: '',
          conclusion: last.content.conclusion || last.content.streamText || '已停止生成',
          status: last.content.status || 'insufficient'
        }))
      }
    },
    patchAssistant(idx, patch) {
      const msg = this.messages[idx]
      if (!msg || !msg.content) return
      this.$set(this.messages, idx, {
        ...msg,
        content: Object.assign({}, msg.content, patch)
      })
      this.$nextTick(this.scrollBottom)
    },
    sendAsk() {
      const q = (this.question || '').trim()
      if (!q) {
        this.$message.warning('请输入问题')
        return
      }
      if (q.length > 20000) {
        this.$message.warning('内容过长（最多 20000 字），请精简后再试')
        return
      }
      if (!this.connectionId) {
        this.$message.warning('请先选择连接')
        return
      }
      if (this.asking) return

      this.question = ''
      this.messages = this.messages.concat([
        { role: 'user', content: { question: q } },
        {
          role: 'assistant',
          content: {
            streaming: true,
            streamStatus: '已发送，正在思考…',
            streamText: '',
            conclusion: '',
            status: 'insufficient',
            sqls: [],
            evidence: [],
            highlights: []
          }
        }
      ])
      const assistantIdx = this.messages.length - 1
      this.$nextTick(this.scrollBottom)

      this.asking = true
      const payload = {
        question: q,
        connectionId: this.connectionId,
        execute: this.executeSql
      }
      if (this.sessionId) payload.sessionId = this.sessionId

      this._streamHandle = askAiDataProbeStream(
        payload,
        (evt) => {
          if (!evt || !evt.type) return
          if (evt.type === 'session') {
            if (evt.sessionId) this.sessionId = String(evt.sessionId)
            return
          }
          if (evt.type === 'status') {
            this.patchAssistant(assistantIdx, { streamStatus: evt.message || '处理中…' })
            return
          }
          if (evt.type === 'sqls') {
            const isCode = String(evt.reason || '').indexOf('code_only') >= 0
            this.patchAssistant(assistantIdx, {
              sqls: evt.sqls || [],
              planReason: evt.reason || '',
              mode: isCode ? 'code' : ((this.messages[assistantIdx] && this.messages[assistantIdx].content && this.messages[assistantIdx].content.mode) || 'sql'),
              streamStatus: isCode ? '正在结合项目 Git 代码分析…' : (evt.reason || 'SQL 已就绪，继续执行…')
            })
            return
          }
          if (evt.type === 'exec') {
            const cur = (this.messages[assistantIdx] && this.messages[assistantIdx].content) || {}
            const execResults = (cur.execResults || []).slice()
            if (evt.item) execResults.push(evt.item)
            const evidence = []
            execResults.forEach(item => {
              (item.rows || []).forEach(r => evidence.push(r))
            })
            this.patchAssistant(assistantIdx, {
              execResults,
              evidence: evidence.slice(0, 20),
              sqls: execResults.map(x => x.sql).filter(Boolean)
            })
            return
          }
          if (evt.type === 'delta') {
            const cur = (this.messages[assistantIdx] && this.messages[assistantIdx].content) || {}
            const streamText = (cur.streamText || '') + (evt.text || '')
            this.patchAssistant(assistantIdx, {
              streamText,
              conclusion: streamText,
              streamStatus: ''
            })
            return
          }
          if (evt.type === 'done') {
            const result = evt.result || {}
            this.sessionId = String(result.sessionId || this.sessionId || '')
            this.patchAssistant(assistantIdx, Object.assign({}, result, {
              streaming: false,
              streamStatus: '',
              streamText: ''
            }))
            this.refreshSessions()
            return
          }
          if (evt.type === 'error') {
            this.patchAssistant(assistantIdx, {
              streaming: false,
              streamStatus: '',
              conclusion: evt.message || '智能问数失败',
              status: 'insufficient'
            })
          }
        },
        (err) => {
          this.patchAssistant(assistantIdx, {
            streaming: false,
            streamStatus: '',
            conclusion: (err && err.message) || '请求失败',
            status: 'insufficient'
          })
          this.asking = false
          this._streamHandle = null
        },
        () => {
          this.asking = false
          this._streamHandle = null
          const last = this.messages[assistantIdx]
          if (last && last.content && last.content.streaming) {
            this.patchAssistant(assistantIdx, { streaming: false, streamStatus: '' })
          }
        }
      )
    },
    openRerun() {
      const last = [...this.messages].reverse().find(m => m.role === 'assistant')
      const sqls = (last && last.content && last.content.sqls) || []
      this.rerunSql = sqls[0] || 'SELECT 1 LIMIT 1'
      this.rerunVisible = true
    },
    doRerun() {
      if (!this.rerunSql.trim()) {
        this.$message.warning('SQL 不能为空')
        return
      }
      this.asking = true
      rerunAiDataProbeSql({
        sessionId: this.sessionId || undefined,
        connectionId: this.connectionId,
        sql: this.rerunSql,
        question: this.question || '按修订 SQL 对号'
      }).then(res => {
        const data = (res && res.data) || {}
        this.sessionId = String(data.sessionId || this.sessionId || '')
        this.rerunVisible = false
        this.refreshSessions()
        if (this.sessionId) this.loadSession(this.sessionId)
      }).finally(() => { this.asking = false })
    },
    evidenceColumns(rows) {
      if (!rows || !rows.length) return []
      return Object.keys(rows[0]).slice(0, 12)
    },
    codeTip(content) {
      if (!content || !content.codeMeta) return ''
      const meta = content.codeMeta
      if (meta.missingRepoTip) return meta.missingRepoTip
      if (meta.codeError && /未配置 Git|缺少 projectId|未绑定项目/.test(meta.codeError)) {
        return meta.codeError.indexOf('建议') >= 0
          ? meta.codeError
          : '想要更准确查询，建议在项目里面配置 Git 代码仓库哦'
      }
      return ''
    },
    goProjectCodeSettings(projectId) {
      if (!projectId) return
      this.$router.push({
        path: '/test-platform/project/setting',
        query: { projectId: String(projectId), tab: 'codePrd' }
      })
    },
    scrollBottom() {
      const el = this.$refs.chatPanel
      if (el) el.scrollTop = el.scrollHeight
    }
  }
}
</script>

<style scoped>
/* 占满主内容区高度，禁止整页滚动；滚动仅发生在对话区 */
.ai-probe-workspace {
  height: calc(100vh - 104px);
  max-height: calc(100vh - 104px);
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ai-probe-workspace >>> .page-section.el-card {
  flex: 1;
  min-height: 0;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ai-probe-workspace >>> .page-section > .el-card__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: 12px;
  padding-bottom: 12px;
}
.ai-probe-workspace >>> .section-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.header-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.filter-label {
  color: #606266;
  font-size: 13px;
}
.conn-meta-tag {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conn-bound {
  margin-top: 8px;
  padding: 6px 8px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
}
.workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
  overflow: hidden;
}
.side {
  width: 240px;
  flex-shrink: 0;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.table-side {
  width: 260px;
  flex-shrink: 0;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.side-block { margin-bottom: 14px; flex-shrink: 0; }
.side-block:last-child {
  flex: 1;
  min-height: 0;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}
.side-title { display: flex; justify-content: space-between; align-items: center; font-weight: 600; margin-bottom: 8px; font-size: 13px; flex-shrink: 0; }
.session-list { flex: 1; min-height: 0; overflow: auto; }
.session-item { padding: 8px; border-radius: 4px; cursor: pointer; margin-bottom: 4px; background: #fff; border: 1px solid transparent; }
.session-item:hover, .session-item.active { border-color: #409EFF; background: #ecf5ff; }
.session-row { display: flex; align-items: center; gap: 4px; }
.session-name { flex: 1; min-width: 0; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-rename-btn { padding: 0 2px; flex-shrink: 0; color: #909399; }
.session-item:hover .session-rename-btn { color: #409EFF; }
.session-meta { font-size: 12px; color: #909399; margin-top: 2px; }
.table-list { flex: 1; overflow: auto; margin-top: 8px; min-height: 0; }
.table-item { margin-bottom: 4px; background: #fff; border: 1px solid transparent; border-radius: 4px; }
.table-item.active { border-color: #409EFF; background: #ecf5ff; }
.table-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 12px;
}
.table-row:hover { background: #f0f7ff; }
.table-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #303133; }
.use-btn { padding: 0 2px; flex-shrink: 0; }
.column-list { padding: 0 8px 8px 22px; }
.column-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  line-height: 1.6;
  color: #606266;
}
.col-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-type { color: #909399; flex-shrink: 0; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-error { color: #F56C6C; }
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: #fff;
}
.chat-panel {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 12px;
  background: #fff;
  -webkit-overflow-scrolling: touch;
}
.msg { display: flex; margin-bottom: 12px; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }
.bubble { max-width: 88%; padding: 10px 12px; border-radius: 8px; background: #f5f7fa; font-size: 13px; line-height: 1.5; }
.msg.user .bubble { background: #ecf5ff; color: #303133; }
.user-q { white-space: pre-wrap; word-break: break-word; }
.conclusion { font-weight: 600; margin-bottom: 6px; white-space: pre-wrap; word-break: break-word; }
.stream-status { color: #909399; font-size: 13px; margin-bottom: 4px; }
.stream-status.subtle { font-weight: normal; }
.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #409EFF;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
.st-matched { color: #67C23A; }
.st-mismatch { color: #E6A23C; }
.st-not_found { color: #909399; }
.st-insufficient { color: #F56C6C; }
.sql-block pre { margin: 0 0 8px; white-space: pre-wrap; word-break: break-all; background: #1e1e1e; color: #dcdcdc; padding: 8px; border-radius: 4px; font-size: 12px; }
.meta-line { margin-top: 8px; color: #909399; font-size: 12px; }
.code-tip { margin-top: 8px; color: #909399; font-size: 12px; line-height: 1.5; }
.composer {
  flex-shrink: 0;
  border-top: 1px solid #ebeef5;
  padding: 10px;
  background: #fafafa;
}
.composer-actions { margin-top: 8px; display: flex; justify-content: flex-end; align-items: center; gap: 12px; }
.empty-tip { color: #909399; font-size: 13px; text-align: center; padding: 16px 8px; }
.chat-empty { margin-top: 80px; }
</style>
