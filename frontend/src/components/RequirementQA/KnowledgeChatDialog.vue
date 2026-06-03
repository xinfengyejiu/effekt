<template>
  <section class="knowledge-chat">
    <header class="chat-header">
      <div>
        <div class="chat-title">{{ projectName || '项目知识问答' }}</div>
        <div class="chat-subtitle">{{ projectId ? '基于当前项目全部已解析资料回答' : '选择产品和项目后开始问答' }}</div>
      </div>
      <el-dropdown v-if="projectId" trigger="click" @command="handleSessionCommand">
        <el-button size="mini" icon="el-icon-time">历史会话</el-button>
        <el-dropdown-menu slot="dropdown" class="session-menu">
          <el-dropdown-item command="new"><i class="el-icon-plus" /> 新建会话</el-dropdown-item>
          <el-dropdown-item v-for="item in sessions" :key="item.id" :command="String(item.id)" divided>{{ item.title || '未命名会话' }}</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </header>

    <div ref="messageArea" class="message-area">
      <div v-if="!projectId" class="chat-empty">
        <i class="el-icon-chat-dot-round" />
        <div>请选择一个项目知识库</div>
        <p>上传并解析需求资料后，可以围绕整个项目持续提问。</p>
      </div>
      <div v-else-if="!messages.length" class="chat-empty">
        <i class="el-icon-chat-dot-round" />
        <div>开始项目知识问答</div>
        <p>回答将综合当前项目知识库中的全部资料。</p>
        <div class="suggestions">
          <button v-for="item in suggestions" :key="item" type="button" @click="query = item">{{ item }}</button>
        </div>
      </div>
      <div v-for="(message, index) in messages" :key="index" :class="['message-row', message.role]">
        <div class="message-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
        <div class="message-body">
          <div class="message-content">{{ message.content }}</div>
          <div v-if="message.role === 'assistant' && message.content" class="message-actions">
            <button type="button" :disabled="message.mindmapLoading" @click="generateMindMap(message, index)">
              <i class="el-icon-share" /> {{ message.mindmapLoading ? '生成中...' : (message.mindmap ? '重新生成脑图' : '生成脑图') }}
            </button>
          </div>
          <div v-if="message.mindmap" class="mindmap-wrap">
            <div class="mindmap-title">
              <span>回答脑图</span>
              <button type="button" @click="toggleMindMap(message, index)">
                {{ message.mindmapVisible === false ? '展开' : '收起' }}
              </button>
            </div>
            <div v-show="message.mindmapVisible !== false" :ref="'mindmap-' + index" class="mindmap-canvas" />
          </div>
          <div v-if="message.evidence && message.evidence.length" class="evidence-wrap">
            <button type="button" class="evidence-toggle" @click="toggleEvidence(index)">
              <i class="el-icon-document" /> {{ message.evidence.length }} 条知识库依据
              <i :class="message.showEvidence ? 'el-icon-arrow-up' : 'el-icon-arrow-down'" />
            </button>
            <div v-if="message.showEvidence" class="evidence-list">
              <div v-for="(item, evidenceIndex) in message.evidence" :key="item.chunkId || evidenceIndex" class="evidence-item">
                <div class="evidence-title">[{{ evidenceIndex + 1 }}] {{ item.title || '文档片段' }}</div>
                <div class="evidence-meta">文档 {{ item.documentId }} · 分片 {{ item.chunkNo }} · 匹配分 {{ item.score }}</div>
                <div class="evidence-snippet">{{ item.snippet }}</div>
              </div>
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
        <el-input
          v-model="query"
          type="textarea"
          :rows="3"
          resize="none"
          :disabled="!projectId || loading"
          placeholder="基于当前项目知识库提问，Ctrl + Enter 发送"
          @keydown.native.ctrl.enter.prevent="submit" />
        <div class="composer-footer">
          <el-radio-group v-model="mode" size="mini">
            <el-radio-button label="hybrid">大模型问答</el-radio-button>
            <el-radio-button label="local">本地检索</el-radio-button>
          </el-radio-group>
          <el-button type="primary" size="small" icon="el-icon-position" :disabled="!projectId || !query.trim()" :loading="loading" @click="submit">发送</el-button>
        </div>
      </div>
    </footer>
  </section>
</template>

<script>
import echarts from 'echarts'
import { chatKnowledge, getKnowledgeMessages, getKnowledgeSessions, searchKnowledge } from '@/api/knowledgeApi'

export default {
  name: 'KnowledgeChatDialog',
  props: {
    productId: [String, Number],
    projectId: [String, Number],
    projectName: String
  },
  data() {
    return {
      query: '',
      mode: 'hybrid',
      loading: false,
      sessionId: null,
      sessions: [],
      messages: [],
      suggestions: ['梳理当前项目的核心需求', '有哪些关键业务流程？', '总结需要重点关注的风险点']
    }
  },
  watch: {
    projectId: {
      immediate: true,
      handler(value, oldValue) {
        if (value === oldValue && oldValue !== undefined) return
        this.sessionId = null
        this.messages = []
        this.query = ''
        if (value) this.loadSessions()
        else this.sessions = []
      }
    }
  },
  methods: {
    submit() {
      const question = this.query.trim()
      if (!this.projectId || !question || this.loading) return
      this.messages.push({ role: 'user', content: question })
      this.query = ''
      this.loading = true
      this.scrollToBottom()
      const payload = { productId: this.productId, projectId: this.projectId, query: question, topK: 5 }
      const request = this.mode === 'local'
        ? searchKnowledge(payload)
        : chatKnowledge(Object.assign({}, payload, { mode: 'hybrid', sessionId: this.sessionId }))
      request.then(res => {
        const data = res.data || {}
        if (this.mode === 'local') {
          const evidence = Array.isArray(data) ? data : []
          this.messages.push({ role: 'assistant', content: evidence.length ? `本地检索命中 ${evidence.length} 条知识库依据。` : '当前项目知识库未找到充分依据。', evidence, showEvidence: true, mindmap: null, mindmapVisible: true })
        } else {
          this.sessionId = data.sessionId || this.sessionId
          this.messages.push({ role: 'assistant', content: data.answer || '暂未生成回答。', evidence: data.evidence || [], showEvidence: false, mindmap: null, mindmapVisible: true })
          this.loadSessions()
        }
      }).finally(() => {
        this.loading = false
        this.scrollToBottom()
      })
    },
    loadSessions() {
      getKnowledgeSessions({ productId: this.productId, projectId: this.projectId, pageNo: 1, pageSize: 20 }).then(res => {
        this.sessions = (res.data && res.data.list) || []
      }).catch(() => {
        this.sessions = []
      })
    },
    handleSessionCommand(command) {
      if (command === 'new') {
        this.sessionId = null
        this.messages = []
        return
      }
      this.sessionId = Number(command)
      getKnowledgeMessages({ sessionId: this.sessionId }).then(res => {
        this.messages = ((res.data || [])).map(item => ({
          role: item.role,
          content: item.content,
          evidence: item.evidence || [],
          showEvidence: false,
          mindmap: null,
          mindmapVisible: true
        }))
        this.scrollToBottom()
      })
    },
    toggleEvidence(index) {
      this.$set(this.messages[index], 'showEvidence', !this.messages[index].showEvidence)
    },
    toggleMindMap(message, index) {
      const visible = message.mindmapVisible === false
      this.$set(message, 'mindmapVisible', visible)
      if (visible && message.mindmap) this.renderMindMap(index, message.mindmap)
    },
    generateMindMap(message, index) {
      if (!message || !message.content || message.mindmapLoading) return
      this.$set(message, 'mindmapLoading', true)
      this.$nextTick(() => {
        const directAnswer = this.extractDirectAnswerSection(message.content)
        const data = this.buildMindMapData(directAnswer, message.content)
        this.$set(message, 'mindmap', data)
        this.$set(message, 'mindmapVisible', true)
        this.$set(message, 'mindmapLoading', false)
        this.renderMindMap(index, data)
        this.scrollToBottom()
      })
    },
    extractDirectAnswerSection(content) {
      const text = (content || '').replace(/\r/g, '').trim()
      if (!text) return ''
      const directMatch = text.match(/(?:^|\n)\s*(?:#{1,6}\s*)?(?:\d+[、.．]\s*)?直接答案\s*[:：]?\s*\n([\s\S]*?)(?=\n\s*(?:#{1,6}\s*)?(?:\d+[、.．]\s*)?(?:依据引用|测试关注点|风险点|信息不足项|信息不足)\s*[:：]?\s*(?:\n|$)|$)/)
      if (directMatch && directMatch[1].trim()) return directMatch[1].trim()
      const numberedMatch = text.match(/(?:^|\n)\s*1[、.．]\s*直接答案\s*[:：]?\s*\n([\s\S]*?)(?=\n\s*2[、.．]\s*(?:依据引用|依据)|$)/)
      if (numberedMatch && numberedMatch[1].trim()) return numberedMatch[1].trim()
      return text
    },
    buildMindMapData(content, fullContent = '') {
      const text = (content || '').replace(/\r/g, '')
      const rawLines = text.split('\n').map(item => item.replace(/\s+$/, '')).filter(item => item.trim())
      let businessName = this.extractBusinessName(rawLines, fullContent)
      const lines = rawLines.filter(item => !/^\s*(?:业务名称|业务|模块名称|功能名称)\s*[:：]/.test(item))
      const root = { name: businessName || '业务脑图', children: [] }
      const stack = [{ level: 0, node: root }]
      const fallback = []
      lines.forEach(rawLine => {
        let level = 1
        let line = rawLine.replace(/^\s+/, '')
        let name = line
        const indentMatched = rawLine.match(/^(\s*)[-*•]\s*(.+)$/)
        if (indentMatched) {
          level = Math.floor(indentMatched[1].length / 2) + 1
          line = '- ' + indentMatched[2]
          name = indentMatched[2]
        }
        let matched = line.match(/^(#{1,6})\s+(.+)$/)
        if (matched) {
          level = matched[1].length
          name = matched[2]
        } else {
          matched = line.match(/^(\d+(?:\.\d+)*|[一二三四五六七八九十]+)[、.．]\s*(.+)$/)
          if (matched) {
            level = matched[1].indexOf('.') > -1 ? matched[1].split('.').length : 1
            name = matched[2]
          } else {
            matched = line.match(/^[-*•]\s*(.+)$/)
            if (matched) {
              level = indentMatched ? level : 1
              name = matched[1]
            } else {
              fallback.push(line)
              return
            }
          }
        }
        name = this.normalizeMindMapName(name)
        if (!name) return
        while (stack.length && stack[stack.length - 1].level >= level) stack.pop()
        const parent = stack[stack.length - 1] ? stack[stack.length - 1].node : root
        if (!parent.children) this.$set(parent, 'children', [])
        const node = { name, children: [] }
        parent.children.push(node)
        stack.push({ level, node })
      })
      if (!root.children.length) {
        const sentences = fallback.join('。').split(/[。；;！!？?]/).map(item => item.trim()).filter(Boolean)
        sentences.slice(0, 10).forEach((item, idx) => {
          root.children.push({ name: this.normalizeMindMapName((idx + 1) + '. ' + item), children: [] })
        })
      }
      if (!root.children.length) root.children.push({ name: '暂无可结构化内容', children: [] })
      return this.decorateMindMapData(root)
    },
    extractBusinessName(lines, fullContent = '') {
      const sourceLines = lines || []
      const namedLine = sourceLines.find(item => /^\s*(?:业务名称|业务|模块名称|功能名称)\s*[:：]/.test(item))
      if (namedLine) {
        const name = namedLine.replace(/^\s*(?:业务名称|业务|模块名称|功能名称)\s*[:：]\s*/, '')
        return this.normalizeMindMapName(name, 18)
      }
      const heading = (fullContent || '').match(/(?:^|\n)\s*#{1,6}\s*(?!直接答案|依据引用|测试关注点|风险点|信息不足)([^\n]{2,30})/)
      if (heading) return this.normalizeMindMapName(heading[1], 18)
      const firstBullet = sourceLines.find(item => /^\s*[-*•]\s*(.+)/.test(item))
      if (firstBullet) return this.normalizeMindMapName(firstBullet.replace(/^\s*[-*•]\s*/, '').split(/[：:，,。；;]/)[0], 18)
      return '业务脑图'
    },
    decorateMindMapData(node, depth = 0, branchIndex = 0) {
      const palette = ['#28c76f', '#2f8cff', '#ef4bb5', '#20b8aa']
      const color = depth === 0 ? '#16a56f' : palette[branchIndex % palette.length]
      node.itemStyle = depth === 0
        ? { color: '#ffffff', borderColor: '#15a36b', borderWidth: 2, shadowBlur: 0 }
        : { color, borderColor: '#ffffff', borderWidth: 1 }
      node.lineStyle = { color, width: depth === 0 ? 2 : 1.6, curveness: 0.55 }
      node.label = depth === 0
        ? { color: '#111827', fontSize: 16, fontWeight: 700, backgroundColor: '#ffffff', borderColor: '#16a56f', borderWidth: 2, borderRadius: 6, padding: [10, 12], lineHeight: 22, formatter: params => this.wrapMindMapLabel(params.name, 8) }
        : { color: '#111827', fontSize: depth === 1 ? 13 : 12, fontWeight: depth === 1 ? 700 : 400, lineHeight: 18, formatter: params => this.wrapMindMapLabel(params.name, depth === 1 ? 16 : 20) }
      ;(node.children || []).forEach((child, index) => this.decorateMindMapData(child, depth + 1, depth === 0 ? index : branchIndex))
      return node
    },
    normalizeMindMapName(text, maxLength = 42) {
      return (text || '').replace(/[*_`>#]/g, '').replace(/\s+/g, ' ').trim().slice(0, maxLength)
    },
    wrapMindMapLabel(text, size = 16) {
      const value = String(text || '')
      if (value.length <= size) return value
      const lines = []
      for (let index = 0; index < value.length; index += size) lines.push(value.slice(index, index + size))
      return lines.slice(0, 3).join('\n')
    },
    renderMindMap(index, data) {
      this.$nextTick(() => {
        const ref = this.$refs['mindmap-' + index]
        const el = Array.isArray(ref) ? ref[0] : ref
        if (!el) return
        const chart = echarts.init(el)
        chart.setOption({
          backgroundColor: 'transparent',
          tooltip: { trigger: 'item', triggerOn: 'mousemove' },
          series: [{
            type: 'tree',
            data: [data],
            left: 180,
            right: 260,
            top: 70,
            bottom: 70,
            orient: 'LR',
            symbol: 'circle',
            symbolSize: 6,
            expandAndCollapse: true,
            initialTreeDepth: 5,
            roam: true,
            edgeShape: 'curve',
            label: { position: 'right', verticalAlign: 'middle', align: 'left', color: '#111827', fontSize: 12 },
            leaves: { label: { position: 'right', verticalAlign: 'middle', align: 'left', color: '#111827', fontSize: 12 } },
            lineStyle: { width: 1.6, curveness: 0.55 },
            animationDuration: 450,
            animationDurationUpdate: 650
          }]
        })
        setTimeout(() => chart.resize(), 50)
      })
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const area = this.$refs.messageArea
        if (area) area.scrollTop = area.scrollHeight
      })
    }
  }
}
</script>

<style scoped>
.knowledge-chat { min-width: 0; min-height: 0; display: flex; flex-direction: column; background: #fbfcfd; }
.chat-header { height: 64px; box-sizing: border-box; padding: 13px 18px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8edf3; background: #fff; }
.chat-title { color: #202b3a; font-size: 15px; font-weight: 700; }
.chat-subtitle { margin-top: 4px; color: #98a2b0; font-size: 12px; }
.message-area { flex: 1; min-height: 0; padding: 22px 7%; overflow: auto; scroll-behavior: smooth; }
.chat-empty { max-width: 520px; margin: 14vh auto 0; color: #657184; text-align: center; }
.chat-empty > i { color: #57aa9c; font-size: 38px; }
.chat-empty div { margin-top: 14px; color: #354255; font-size: 17px; font-weight: 700; }
.chat-empty p { margin: 8px 0 0; color: #97a1af; font-size: 13px; }
.suggestions { margin-top: 24px !important; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.suggestions button { padding: 8px 11px; border: 1px solid #e4e9ef; border-radius: 16px; background: #fff; color: #748093; cursor: pointer; font-size: 12px; transition: border-color .18s ease, color .18s ease; }
.suggestions button:hover { border-color: #7dbeb3; color: #218b79; }
.message-row { margin: 0 auto 22px; display: flex; gap: 11px; max-width: 920px; }
.message-row.user { flex-direction: row-reverse; }
.message-avatar { width: 30px; height: 30px; flex: 0 0 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #dff0ed; color: #258b7b; font-size: 11px; font-weight: 700; }
.user .message-avatar { background: #e8eef7; color: #526987; }
.message-body { max-width: min(96%, 1120px); }
.message-content { padding: 10px 13px; border: 1px solid #e7ebf0; border-radius: 4px 13px 13px; background: #fff; color: #3e4a5b; font-size: 14px; line-height: 1.75; white-space: pre-wrap; word-break: break-word; }
.user .message-content { border-color: #dce9e7; border-radius: 13px 4px 13px 13px; background: #edf7f5; }
.message-actions { margin-top: 8px; display: flex; justify-content: flex-end; }
.message-actions button { padding: 7px 12px; border: 0; border-radius: 6px; background: #24272c; color: #fff; cursor: pointer; font-size: 12px; transition: opacity .18s ease, transform .18s ease; }
.message-actions button:hover { opacity: .88; transform: translateY(-1px); }
.message-actions button:disabled { cursor: not-allowed; opacity: .6; transform: none; }
.mindmap-wrap { margin-top: 12px; padding: 12px; border: 1px solid #e3e9f1; border-radius: 8px; background: #fff; overflow-x: auto; }
.mindmap-title { margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; color: #1f2d3d; font-size: 13px; font-weight: 700; }
.mindmap-title button { padding: 0; border: 0; background: transparent; color: #168f72; cursor: pointer; font-size: 12px; }
.mindmap-canvas { width: 1500px; min-width: 1500px; height: 560px; border-radius: 6px; background-color: #fff; background-image: radial-gradient(#d9dee7 1px, transparent 1px); background-size: 16px 16px; overflow: hidden; }
.evidence-wrap { margin-top: 7px; }
.evidence-toggle { padding: 0; border: 0; background: transparent; color: #5f9d93; cursor: pointer; font-size: 12px; }
.evidence-list { margin-top: 8px; padding-left: 9px; border-left: 2px solid #d8ebe8; }
.evidence-item { margin: 7px 0; color: #667386; font-size: 12px; line-height: 1.6; }
.evidence-title { color: #3f4e60; font-weight: 700; }
.evidence-meta { color: #a1aab7; font-size: 11px; }
.evidence-snippet { margin-top: 2px; }
.composer-wrap { padding: 12px 6% 17px; border-top: 1px solid #e9edf2; background: rgba(255,255,255,.92); }
.composer { max-width: 960px; margin: 0 auto; padding: 9px 11px; border: 1px solid #dce3ea; border-radius: 11px; background: #fff; box-shadow: 0 5px 18px rgba(41, 53, 72, .05); transition: border-color .18s ease, box-shadow .18s ease; }
.composer:focus-within { border-color: #84bfb5; box-shadow: 0 7px 20px rgba(46, 132, 117, .09); }
.composer /deep/ .el-textarea__inner { padding: 3px 2px; border: 0; font-family: inherit; box-shadow: none; }
.composer-footer { margin-top: 7px; display: flex; align-items: center; justify-content: space-between; }
.typing { padding: 13px; display: flex; gap: 4px; border: 1px solid #e7ebf0; border-radius: 4px 13px 13px; background: #fff; }
.typing span { width: 5px; height: 5px; border-radius: 50%; background: #79b6ac; animation: blink 1s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay: .16s; }
.typing span:nth-child(3) { animation-delay: .32s; }
@keyframes blink { 0%, 70%, 100% { opacity: .3; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-3px); } }
</style>
