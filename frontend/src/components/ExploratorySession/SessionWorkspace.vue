<template>
  <div class="page-wrap explore-workspace-page" @paste="onPaste">
    <page-section :title="pageTitle">
      <template slot="extra">
        <el-button size="small" icon="el-icon-back" @click="goList">返回列表</el-button>
        <el-button
          v-if="session.status === 'draft'"
          size="small"
          type="primary"
          icon="el-icon-video-play"
          :loading="lifecycleLoading"
          @click="doStart"
        >开始探索</el-button>
        <el-button
          v-if="session.status === 'active'"
          size="small"
          type="warning"
          icon="el-icon-switch-button"
          :loading="lifecycleLoading"
          @click="openEndDialog"
        >结束 Session</el-button>
        <el-button
          v-if="session.status === 'ended'"
          size="small"
          icon="el-icon-folder-checked"
          :loading="lifecycleLoading"
          @click="doArchive"
        >归档</el-button>
      </template>

      <div v-loading="loading" class="workspace-layout">
        <div class="charter-panel">
          <div class="panel-title">章程与范围</div>
          <el-form label-width="80px" size="small">
            <el-form-item label="编号">{{ session.sessionNo || '-' }}</el-form-item>
            <el-form-item label="状态">
              <el-tag size="mini" :type="statusTag(session.status)">{{ statusLabel(session.status) }}</el-tag>
            </el-form-item>
            <el-form-item label="产品">{{ session.productName || '-' }}</el-form-item>
            <el-form-item label="项目">{{ session.projectName || '-' }}</el-form-item>
            <el-form-item label="环境">
              <el-input
                v-if="canEditMeta"
                v-model.trim="editForm.environment"
                maxlength="64"
                @blur="saveMeta"
              />
              <span v-else>{{ session.environment || '-' }}</span>
            </el-form-item>
            <el-form-item label="章程">
              <el-input
                v-if="canEditMeta"
                v-model="editForm.charter"
                type="textarea"
                :rows="4"
                @blur="saveMeta"
              />
              <div v-else class="text-block">{{ session.charter || '（未填写）' }}</div>
            </el-form-item>
            <el-form-item label="不测">
              <el-input
                v-if="canEditMeta"
                v-model="editForm.outOfScope"
                type="textarea"
                :rows="2"
                @blur="saveMeta"
              />
              <div v-else class="text-block">{{ session.outOfScope || '（未填写）' }}</div>
            </el-form-item>
            <el-form-item v-if="session.summary" label="摘要">
              <div class="text-block summary-block">{{ session.summary }}</div>
            </el-form-item>
          </el-form>
        </div>

        <div class="timeline-panel">
          <div class="panel-title-row">
            <div class="panel-title">时间线</div>
            <div class="timeline-actions">
              <el-button
                size="mini"
                type="primary"
                :disabled="!selectedIds.length || !canConvert"
                @click="openBugDialog"
              >转 Bug</el-button>
              <el-button
                size="mini"
                :disabled="!selectedIds.length || !canConvert"
                @click="openCaseDialog"
              >转用例</el-button>
            </div>
          </div>

          <div v-if="canWrite" class="quick-add">
            <el-radio-group v-model="quickType" size="mini">
              <el-radio-button label="note">备注</el-radio-button>
              <el-radio-button label="step">步骤</el-radio-button>
              <el-radio-button label="finding">发现</el-radio-button>
              <el-radio-button label="blocker">阻塞</el-radio-button>
            </el-radio-group>
            <el-input
              v-model="quickContent"
              type="textarea"
              :rows="2"
              placeholder="记录探索过程；Ctrl+Enter 提交；可粘贴截图"
              @keydown.ctrl.enter.native="submitQuickAdd"
            />
            <div class="quick-add-footer">
              <el-upload
                action=""
                :show-file-list="false"
                :http-request="uploadScreenshot"
                accept="image/*"
              >
                <el-button size="mini" icon="el-icon-picture-outline" :loading="uploadLoading">上传截图</el-button>
              </el-upload>
              <el-button size="mini" type="primary" :loading="addLoading" @click="submitQuickAdd">添加</el-button>
            </div>
          </div>
          <el-alert
            v-else
            :title="readonlyHint"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom:12px;"
          />

          <div v-if="!entries.length" class="empty-tip">暂无时间线条目</div>
          <div
            v-for="entry in entries"
            :key="entry.id"
            class="entry-card"
            :class="{ selected: selectedIds.indexOf(entry.id) >= 0 }"
          >
            <div class="entry-head">
              <el-checkbox
                :value="selectedIds.indexOf(entry.id) >= 0"
                @change="toggleSelect(entry.id, $event)"
              />
              <el-tag size="mini" :type="entryTag(entry.entryType)">{{ entryLabel(entry.entryType) }}</el-tag>
              <span class="entry-time">{{ entry.createdTime }}</span>
              <div class="entry-ops" v-if="canWrite">
                <el-button type="text" size="mini" @click="openEditEntry(entry)">编辑</el-button>
                <el-button type="text" size="mini" @click="removeEntry(entry)">删除</el-button>
              </div>
            </div>
            <div class="entry-body">{{ entry.content || '（无文字）' }}</div>
            <div v-if="entry.entryType === 'screenshot' && screenshotUrl(entry)" class="entry-shot">
              <a :href="screenshotUrl(entry)" target="_blank" rel="noopener">
                <img :src="screenshotUrl(entry)" alt="screenshot" />
              </a>
            </div>
            <div v-if="entry.linkedBugId || entry.linkedCaseId" class="entry-links">
              <el-link
                v-if="entry.linkedBugId"
                type="danger"
                :underline="false"
                @click="goBug(entry.linkedBugId)"
              >Bug #{{ entry.linkedBugId }}</el-link>
              <el-link
                v-if="entry.linkedCaseId"
                type="primary"
                :underline="false"
                @click="goCase(entry.linkedCaseId)"
              >用例 #{{ entry.linkedCaseId }}</el-link>
            </div>
          </div>
        </div>
      </div>
    </page-section>

    <el-dialog title="结束 Session" :visible.sync="endVisible" width="560px" :close-on-click-modal="false">
      <el-form label-width="100px" size="small">
        <el-form-item label="摘要">
          <el-input v-model="endForm.summary" type="textarea" :rows="5" placeholder="可留空，系统将按时间线生成模板摘要" />
        </el-form-item>
        <el-form-item label="AI 摘要">
          <el-switch v-model="endForm.useAiSummary" />
          <span class="hint">开启后优先尝试 AI，失败则回退模板</span>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="endVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="lifecycleLoading" @click="doEnd">确认结束</el-button>
      </div>
    </el-dialog>

    <el-dialog title="转为 Bug" :visible.sync="bugVisible" width="560px" :close-on-click-modal="false">
      <el-form ref="bugForm" :model="bugForm" :rules="bugRules" label-width="90px" size="small">
        <el-form-item label="标题" prop="title">
          <el-input v-model.trim="bugForm.title" maxlength="200" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="bugForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="选中条目">
          <div class="hint">已选 {{ selectedIds.length }} 条，将映射为复现步骤/附件</div>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="bugVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="convertLoading" @click="submitBug">创建 Bug</el-button>
      </div>
    </el-dialog>

    <el-dialog title="转为用例" :visible.sync="caseVisible" width="640px" :close-on-click-modal="false">
      <el-form ref="caseForm" :model="caseForm" :rules="caseRules" label-width="90px" size="small">
        <el-form-item label="标题" prop="title">
          <el-input v-model.trim="caseForm.title" maxlength="200" />
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="caseForm.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="步骤" prop="steps">
          <el-input
            v-model="caseForm.steps"
            type="textarea"
            :rows="8"
            placeholder="由勾选的时间线条目自动生成，可继续编辑"
          />
          <div class="hint" style="margin-left:0;margin-top:4px;">已根据勾选的 {{ selectedIds.length }} 条时间线生成，确认后写入用例</div>
        </el-form-item>
        <el-form-item label="预期结果">
          <el-input v-model="caseForm.expectedResults" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="落库">
          <el-switch v-model="caseForm.create" active-text="直接创建用例" inactive-text="仅预览草稿" />
        </el-form-item>
      </el-form>
      <div v-if="caseDraftPreview" class="draft-preview">
        <div class="panel-title">草稿预览</div>
        <pre>{{ caseDraftPreview }}</pre>
      </div>
      <div slot="footer">
        <el-button size="small" @click="caseVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="convertLoading" @click="submitCase">确认</el-button>
      </div>
    </el-dialog>

    <el-dialog title="编辑条目" :visible.sync="editVisible" width="520px" :close-on-click-modal="false">
      <el-form label-width="80px" size="small">
        <el-form-item label="类型">
          <el-select v-model="editEntryForm.entryType" style="width:100%;">
            <el-option label="备注" value="note" />
            <el-option label="步骤" value="step" />
            <el-option label="发现" value="finding" />
            <el-option label="阻塞" value="blocker" />
            <el-option label="截图" value="screenshot" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editEntryForm.content" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="editVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="editLoading" @click="submitEditEntry">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  addExploreEntry,
  archiveExploreSession,
  deleteExploreEntry,
  endExploreSession,
  exploreToBug,
  exploreToCaseDraft,
  getExploreSessionDetail,
  startExploreSession,
  updateExploreEntry,
  updateExploreSession,
  uploadExploreScreenshot
} from '@/api/exploreSessionApi'

const STATUS_MAP = {
  draft: { label: '草稿', tag: 'info' },
  active: { label: '进行中', tag: 'success' },
  ended: { label: '已结束', tag: 'warning' },
  archived: { label: '已归档', tag: '' }
}

const ENTRY_MAP = {
  note: { label: '备注', tag: 'info' },
  step: { label: '步骤', tag: '' },
  finding: { label: '发现', tag: 'warning' },
  blocker: { label: '阻塞', tag: 'danger' },
  screenshot: { label: '截图', tag: 'success' }
}

export default {
  name: 'ExploreSessionWorkspace',
  components: { PageSection },
  data() {
    return {
      loading: false,
      lifecycleLoading: false,
      addLoading: false,
      uploadLoading: false,
      convertLoading: false,
      editLoading: false,
      session: {},
      entries: [],
      selectedIds: [],
      quickType: 'note',
      quickContent: '',
      editForm: { charter: '', outOfScope: '', environment: '' },
      endVisible: false,
      endForm: { summary: '', useAiSummary: false },
      bugVisible: false,
      bugForm: { title: '', description: '' },
      bugRules: { title: [{ required: true, message: '请输入 Bug 标题', trigger: 'blur' }] },
      caseVisible: false,
      caseForm: { title: '', preconditions: '', steps: '', expectedResults: '', create: true },
      caseRules: {
        title: [{ required: true, message: '请输入用例标题', trigger: 'blur' }],
        steps: [{ required: true, message: '请填写用例步骤', trigger: 'blur' }]
      },
      caseDraftPreview: '',
      editVisible: false,
      editEntryForm: { id: null, entryType: 'note', content: '' }
    }
  },
  computed: {
    sessionId() {
      return this.$route.query.id || this.$route.query.sessionId
    },
    pageTitle() {
      return this.session.title ? `探索工作台 · ${this.session.title}` : '探索工作台'
    },
    canWrite() {
      return this.session.status === 'active'
    },
    canEditMeta() {
      return this.session.status === 'draft' || this.session.status === 'active'
    },
    canConvert() {
      return this.session.status === 'active' || this.session.status === 'ended'
    },
    readonlyHint() {
      if (this.session.status === 'draft') return '请先开始 Session，再写入时间线'
      if (this.session.status === 'ended') return '已结束：时间线只读，仍可转 Bug / 用例'
      if (this.session.status === 'archived') return '已归档：只读'
      return '当前状态不可写入'
    }
  },
  watch: {
    '$route.query.id'() {
      this.loadDetail()
    }
  },
  created() {
    this.loadDetail()
  },
  methods: {
    apiData(res) {
      return (res && res.data) || res || {}
    },
    statusLabel(value) {
      return (STATUS_MAP[value] || {}).label || value || '-'
    },
    statusTag(value) {
      return (STATUS_MAP[value] || {}).tag || 'info'
    },
    entryLabel(value) {
      return (ENTRY_MAP[value] || {}).label || value || '-'
    },
    entryTag(value) {
      return (ENTRY_MAP[value] || {}).tag || 'info'
    },
    screenshotUrl(entry) {
      const payload = entry.payload || {}
      const url = payload.url || payload.path || ''
      if (!url) return ''
      return url.startsWith('/') ? url : `/${url}`
    },
    goList() {
      this.$router.push({ path: '/explore-session' })
    },
    goBug(bugId) {
      this.$router.push({ path: '/bug/detail', query: { bugId } })
    },
    goCase(caseId) {
      this.$router.push({
        path: '/test-platform/case/editor',
        query: { projectId: this.session.projectId, caseId }
      })
    },
    loadDetail() {
      if (!this.sessionId) {
        this.$message.warning('缺少 sessionId')
        this.goList()
        return
      }
      this.loading = true
      getExploreSessionDetail({ sessionId: this.sessionId }).then(res => {
        const data = this.apiData(res)
        this.session = data || {}
        this.entries = data.entries || []
        this.editForm = {
          charter: data.charter || '',
          outOfScope: data.outOfScope || '',
          environment: data.environment || ''
        }
        this.selectedIds = this.selectedIds.filter(id => this.entries.some(e => e.id === id))
      }).finally(() => { this.loading = false })
    },
    saveMeta() {
      if (!this.canEditMeta) return
      const payload = {
        sessionId: this.sessionId,
        charter: this.editForm.charter,
        outOfScope: this.editForm.outOfScope,
        environment: this.editForm.environment
      }
      updateExploreSession(payload).then(res => {
        const data = this.apiData(res)
        this.session = Object.assign({}, this.session, data)
        if (data.entries) this.entries = data.entries
      })
    },
    doStart() {
      this.lifecycleLoading = true
      startExploreSession({ sessionId: this.sessionId }).then(res => {
        this.$message.success('已开始探索')
        const data = this.apiData(res)
        this.session = data || this.session
        this.entries = data.entries || this.entries
      }).finally(() => { this.lifecycleLoading = false })
    },
    openEndDialog() {
      this.endForm = { summary: '', useAiSummary: false }
      this.endVisible = true
    },
    doEnd() {
      this.lifecycleLoading = true
      endExploreSession({
        sessionId: this.sessionId,
        summary: this.endForm.summary,
        useAiSummary: this.endForm.useAiSummary
      }).then(res => {
        this.$message.success('Session 已结束')
        this.endVisible = false
        const data = this.apiData(res)
        this.session = data || this.session
        this.entries = data.entries || this.entries
      }).finally(() => { this.lifecycleLoading = false })
    },
    doArchive() {
      this.lifecycleLoading = true
      archiveExploreSession({ sessionId: this.sessionId }).then(res => {
        this.$message.success('已归档')
        const data = this.apiData(res)
        this.session = data || this.session
        this.entries = data.entries || this.entries
      }).finally(() => { this.lifecycleLoading = false })
    },
    submitQuickAdd() {
      const content = (this.quickContent || '').trim()
      if (!content) {
        this.$message.warning('请输入内容')
        return
      }
      this.addLoading = true
      addExploreEntry({
        sessionId: this.sessionId,
        entryType: this.quickType,
        content
      }).then(res => {
        const entry = this.apiData(res)
        if (entry && entry.id) this.entries.push(entry)
        this.quickContent = ''
        this.$message.success('已添加')
      }).finally(() => { this.addLoading = false })
    },
    uploadScreenshot({ file }) {
      if (!this.canWrite) {
        this.$message.warning('仅进行中的 Session 可上传截图')
        return
      }
      const formData = new FormData()
      formData.append('file', file)
      formData.append('sessionId', this.sessionId)
      formData.append('content', file.name || '截图')
      this.uploadLoading = true
      uploadExploreScreenshot(formData).then(res => {
        const entry = this.apiData(res)
        if (entry && entry.id) this.entries.push(entry)
        this.$message.success('截图已上传')
      }).finally(() => { this.uploadLoading = false })
    },
    onPaste(event) {
      if (!this.canWrite) return
      const items = (event.clipboardData && event.clipboardData.items) || []
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type && item.type.indexOf('image') === 0) {
          event.preventDefault()
          const blob = item.getAsFile()
          if (!blob) return
          const file = new File([blob], `paste-${Date.now()}.png`, { type: blob.type || 'image/png' })
          this.uploadScreenshot({ file })
          return
        }
      }
    },
    toggleSelect(id, checked) {
      const idx = this.selectedIds.indexOf(id)
      if (checked && idx < 0) this.selectedIds.push(id)
      if (!checked && idx >= 0) this.selectedIds.splice(idx, 1)
    },
    openEditEntry(entry) {
      this.editEntryForm = {
        id: entry.id,
        entryType: entry.entryType,
        content: entry.content || ''
      }
      this.editVisible = true
    },
    submitEditEntry() {
      this.editLoading = true
      updateExploreEntry({
        entryId: this.editEntryForm.id,
        entryType: this.editEntryForm.entryType,
        content: this.editEntryForm.content
      }).then(res => {
        const updated = this.apiData(res)
        const idx = this.entries.findIndex(e => e.id === updated.id)
        if (idx >= 0) this.$set(this.entries, idx, updated)
        this.editVisible = false
        this.$message.success('已更新')
      }).finally(() => { this.editLoading = false })
    },
    removeEntry(entry) {
      this.$confirm('确认删除该条目？', '提示', { type: 'warning' }).then(() => {
        return deleteExploreEntry({ entryId: entry.id })
      }).then(() => {
        this.entries = this.entries.filter(e => e.id !== entry.id)
        this.selectedIds = this.selectedIds.filter(id => id !== entry.id)
        this.$message.success('已删除')
      }).catch(() => {})
    },
    openBugDialog() {
      const finding = this.entries.find(e => this.selectedIds.indexOf(e.id) >= 0 && e.entryType === 'finding')
      this.bugForm = {
        title: finding ? finding.content.slice(0, 120) : `探索发现-${this.session.title || ''}`.slice(0, 120),
        description: `来自探索 Session ${this.session.sessionNo || ''}：${this.session.title || ''}`
      }
      this.bugVisible = true
      this.$nextTick(() => { this.$refs.bugForm && this.$refs.bugForm.clearValidate() })
    },
    submitBug() {
      this.$refs.bugForm.validate(valid => {
        if (!valid) return
        this.convertLoading = true
        exploreToBug({
          sessionId: this.sessionId,
          title: this.bugForm.title,
          description: this.bugForm.description,
          entryIds: this.selectedIds
        }).then(res => {
          const data = this.apiData(res)
          this.$message.success(`Bug 已创建：${data.bugKey || data.bugId}`)
          this.bugVisible = false
          this.loadDetail()
          if (data.bugId) this.goBug(data.bugId)
        }).finally(() => { this.convertLoading = false })
      })
    },
    buildStepsFromSelected() {
      const selected = this.entries.filter(e => this.selectedIds.indexOf(e.id) >= 0)
      const lines = []
      let idx = 1
      selected.forEach(entry => {
        const text = (entry.content || '').trim()
        if (entry.entryType === 'screenshot') {
          const payload = entry.payload || {}
          const path = payload.path || payload.url || ''
          lines.push(`${idx}. [截图] ${text || '见附件'} ${path}`.trim())
          idx += 1
          return
        }
        if (['step', 'note', 'finding', 'blocker'].indexOf(entry.entryType) >= 0 && text) {
          const label = this.entryLabel(entry.entryType)
          lines.push(`${idx}. [${label}] ${text}`)
          idx += 1
        }
      })
      return lines.join('\n')
    },
    openCaseDialog() {
      const steps = this.buildStepsFromSelected()
      if (!steps) {
        this.$message.warning('勾选的条目没有可转成步骤的内容，请勾选步骤/备注/发现等')
        return
      }
      this.caseForm = {
        title: `探索用例-${this.session.title || ''}`.slice(0, 120),
        preconditions: `探索 Session：${this.session.sessionNo || ''}（${this.session.environment || '未填环境'}）`,
        steps,
        expectedResults: '与探索发现一致，无异常阻断',
        create: true
      }
      this.caseDraftPreview = ''
      this.caseVisible = true
      this.$nextTick(() => { this.$refs.caseForm && this.$refs.caseForm.clearValidate() })
    },
    submitCase() {
      this.$refs.caseForm.validate(valid => {
        if (!valid) return
        this.convertLoading = true
        exploreToCaseDraft({
          sessionId: this.sessionId,
          title: this.caseForm.title,
          preconditions: this.caseForm.preconditions,
          steps: this.caseForm.steps,
          expectedResults: this.caseForm.expectedResults,
          entryIds: this.selectedIds,
          create: this.caseForm.create
        }).then(res => {
          const data = this.apiData(res)
          if (data.created && data.caseId) {
            this.$message.success(`用例已创建：${data.caseKey || data.caseId}`)
            this.caseVisible = false
            this.loadDetail()
            this.goCase(data.caseId)
          } else {
            const draft = data.draft || {}
            this.caseDraftPreview = [
              `标题：${draft.title || ''}`,
              `前置：${draft.preconditions || ''}`,
              `步骤：\n${draft.steps || ''}`,
              `预期：${draft.expectedResults || ''}`
            ].join('\n\n')
            this.$message.success('草稿已生成，可再勾选「直接创建用例」落库')
          }
        }).finally(() => { this.convertLoading = false })
      })
    }
  }
}
</script>

<style scoped>
.workspace-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  min-height: 520px;
}
.charter-panel,
.timeline-panel {
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px 14px;
}
.panel-title {
  font-weight: 600;
  margin-bottom: 10px;
  color: #303133;
}
.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.panel-title-row .panel-title { margin-bottom: 0; }
.text-block {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #606266;
}
.summary-block {
  background: #fff;
  border: 1px dashed #dcdfe6;
  padding: 8px 10px;
  border-radius: 4px;
}
.quick-add {
  margin-bottom: 14px;
  padding: 10px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}
.quick-add .el-radio-group { margin-bottom: 8px; }
.quick-add-footer {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.entry-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.entry-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
}
.entry-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.entry-time {
  color: #909399;
  font-size: 12px;
}
.entry-ops {
  margin-left: auto;
}
.entry-body {
  margin-top: 8px;
  white-space: pre-wrap;
  line-height: 1.5;
  color: #303133;
}
.entry-shot {
  margin-top: 8px;
}
.entry-shot img {
  max-width: 100%;
  max-height: 220px;
  border: 1px solid #ebeef5;
  border-radius: 2px;
}
.entry-links {
  margin-top: 8px;
  display: flex;
  gap: 12px;
}
.empty-tip {
  color: #909399;
  text-align: center;
  padding: 40px 0;
}
.hint {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}
.draft-preview {
  margin-top: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
}
.draft-preview pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.5;
}
@media (max-width: 960px) {
  .workspace-layout {
    grid-template-columns: 1fr;
  }
}
</style>
