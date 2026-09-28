<template>
  <div class="page-wrap" v-loading="loading">
    <page-section :title="'弱网 AI 任务 · ' + ((task && task.taskNo) || '')">
      <template slot="extra">
        <el-button size="small" @click="$router.push('/weak-network-ai')">返回列表</el-button>
      </template>
      <el-steps :active="stepActive" finish-status="success" align-center style="margin-bottom:20px;">
        <el-step title="编排检查点" />
        <el-step title="确认下载包" />
        <el-step title="证据与判定" />
        <el-step title="确认转 Bug" />
      </el-steps>

      <el-card shadow="never" class="block">
        <div slot="header">1. 功能描述与 AI 编排</div>
        <el-input v-model="brief" type="textarea" :rows="4" :disabled="!editable" placeholder="描述要测的功能路径…" />
        <div style="margin-top:10px;">
          <el-button size="small" type="primary" :loading="orchLoading" :disabled="!editable" @click="doOrchestrate">AI 生成检查点</el-button>
          <el-tag v-if="orchSource" size="mini" style="margin-left:8px;">来源: {{ orchSource }}</el-tag>
          <el-tag size="mini" style="margin-left:8px;">状态: {{ statusLabel(task && task.status) }}</el-tag>
        </div>
        <div v-if="profiles.length" style="margin-top:12px;">
          <div class="label">推荐/已选画像（最多 3 个）</div>
          <el-checkbox-group v-model="selectedProfileIds" :disabled="!editable">
            <el-checkbox v-for="p in profiles" :key="p.profileId" :label="p.profileId">
              {{ p.name }}（{{ p.presetCode }}）{{ p.reason ? ' - ' + p.reason : '' }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div style="margin-top:12px;">
          <div class="label">检查点（可编辑）</div>
          <el-table :data="checkpoints" border size="small">
            <el-table-column label="#" width="50" prop="sortNo" />
            <el-table-column label="标题" min-width="200">
              <template slot-scope="scope">
                <el-input v-if="editable" v-model="scope.row.title" size="mini" />
                <span v-else>{{ scope.row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="期望" min-width="180">
              <template slot-scope="scope">
                <el-input v-if="editable" v-model="scope.row.expect" size="mini" />
                <span v-else>{{ scope.row.expect }}</span>
              </template>
            </el-table-column>
            <el-table-column label="画像" width="110" prop="profilePreset" />
            <el-table-column label="判定" width="110">
              <template slot-scope="scope">
                <el-tag v-if="scope.row.lastVerdict" size="mini" :type="verdictType(scope.row.lastVerdict)">
                  {{ scope.row.lastVerdict }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
          <el-button v-if="editable" size="mini" style="margin-top:8px;" @click="addCheckpoint">新增检查点</el-button>
          <el-button v-if="editable" size="mini" type="primary" plain style="margin-top:8px;" :loading="saveLoading" @click="saveDraft">保存草稿</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="block">
        <div slot="header">2. 确认并下载弱网包（AI 不改网络参数）</div>
        <el-button size="small" type="success" :loading="confirmLoading" :disabled="!canConfirm" @click="doConfirm">确认任务并生成会话</el-button>
        <div v-if="sessionIds.length" style="margin-top:12px;">
          <el-button
            v-for="sid in sessionIds"
            :key="sid"
            size="mini"
            icon="el-icon-download"
            :loading="downloadLoading === sid"
            @click="doDownload(sid)"
          >下载 session #{{ sid }}</el-button>
          <p class="hint">解压后执行 .\weaknet.ps1 apply → 手测 → restore</p>
        </div>
      </el-card>

      <el-card shadow="never" class="block">
        <div slot="header">3. 上传证据并 AI 判定</div>
        <el-form :inline="true" size="small">
          <el-form-item label="检查点">
            <el-select v-model="evidenceForm.checkpointId" clearable placeholder="任务级" style="width:220px;">
              <el-option v-for="c in checkpoints" :key="c.checkpointId" :label="c.title" :value="c.checkpointId" />
            </el-select>
          </el-form-item>
          <el-form-item label="现象备注">
            <el-input v-model="evidenceForm.note" style="width:280px;" placeholder="如：白屏 10 秒无错误提示" />
          </el-form-item>
          <el-form-item label="执行ID">
            <el-input v-model="evidenceForm.mobileExecutionId" style="width:120px;" placeholder="可选" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="evidenceLoading" @click="submitEvidenceNote">提交备注</el-button>
            <input ref="fileInput" type="file" accept="image/*" style="margin-left:8px;" @change="onFileChange" />
          </el-form-item>
        </el-form>
        <el-table :data="evidence" border size="small" style="margin-top:8px;">
          <el-table-column label="检查点" width="100" prop="checkpointId" />
          <el-table-column label="备注" min-width="200" prop="note" show-overflow-tooltip />
          <el-table-column label="文件" min-width="180" prop="filePath" show-overflow-tooltip />
        </el-table>
        <el-button style="margin-top:10px;" size="small" type="warning" :loading="judgeLoading" @click="doJudge">AI 判定</el-button>
      </el-card>

      <el-card shadow="never" class="block">
        <div slot="header">4. 存疑候选 → 确认转 Bug</div>
        <el-table :data="findings" border size="small" @selection-change="rows => { selectedFindings = rows }">
          <el-table-column type="selection" width="45" :selectable="row => row.status === 'open'" />
          <el-table-column label="标题" min-width="180" prop="title" show-overflow-tooltip />
          <el-table-column label="观察" min-width="220" prop="detail" show-overflow-tooltip />
          <el-table-column label="状态" width="100" prop="status" />
          <el-table-column label="Bug" width="90">
            <template slot-scope="scope">{{ scope.row.linkedBugId || '-' }}</template>
          </el-table-column>
        </el-table>
        <div style="margin-top:10px;">
          <el-button size="small" type="danger" :disabled="!selectedFindings.length" :loading="bugLoading" @click="doConfirmBugs">确认转正式 Bug</el-button>
          <el-button size="small" :disabled="!selectedFindings.length" @click="doDismiss">放弃</el-button>
        </div>
      </el-card>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { downloadWeakNetworkSession } from '@/api/weakNetworkApi'
import {
  getWeakNetworkAiTaskDetail,
  updateWeakNetworkAiTask,
  orchestrateWeakNetworkAiTask,
  confirmWeakNetworkAiTask,
  addWeakNetworkAiEvidence,
  uploadWeakNetworkAiEvidence,
  judgeWeakNetworkAiTask,
  dismissWeakNetworkAiFindings,
  confirmWeakNetworkAiFindingsToBug
} from '@/api/weakNetworkAiApi'

export default {
  name: 'WeakNetworkAiTaskDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      task: null,
      brief: '',
      checkpoints: [],
      profiles: [],
      selectedProfileIds: [],
      evidence: [],
      findings: [],
      selectedFindings: [],
      orchSource: '',
      orchLoading: false,
      saveLoading: false,
      confirmLoading: false,
      downloadLoading: null,
      evidenceLoading: false,
      judgeLoading: false,
      bugLoading: false,
      evidenceForm: { checkpointId: null, note: '', mobileExecutionId: '' }
    }
  },
  computed: {
    taskId() {
      return this.$route.query.taskId
    },
    editable() {
      const s = this.task && this.task.status
      return s === 'draft' || s === 'ready' || s === 'collecting'
    },
    canConfirm() {
      return this.editable && this.checkpoints.length && this.selectedProfileIds.length
    },
    sessionIds() {
      return (this.task && this.task.weakNetworkSessionIds) || []
    },
    stepActive() {
      const s = this.task && this.task.status
      if (s === 'judged' || s === 'closed') return 3
      if (s === 'collecting') return 2
      if (s === 'ready') return 1
      return 0
    }
  },
  created() {
    this.loadDetail()
  },
  methods: {
    statusLabel(v) {
      return ({ draft: '草稿', ready: '已确认', collecting: '收集证据', judged: '已判定', closed: '已关闭' })[v] || v
    },
    verdictType(v) {
      return ({ acceptable: 'success', suspect: 'danger', insufficient: 'info' })[v] || ''
    },
    applyDetail(data) {
      this.task = data.task || {}
      this.brief = this.task.brief || ''
      this.checkpoints = (data.checkpoints || []).map(c => Object.assign({}, c))
      this.profiles = this.task.recommendedProfiles || []
      this.selectedProfileIds = (this.task.selectedProfileIds || []).map(Number)
      this.evidence = data.evidence || []
      this.findings = data.findings || []
    },
    loadDetail() {
      if (!this.taskId) return
      this.loading = true
      getWeakNetworkAiTaskDetail({ taskId: this.taskId })
        .then(res => {
          this.applyDetail((res && res.data) || res || {})
        })
        .finally(() => { this.loading = false })
    },
    doOrchestrate() {
      this.orchLoading = true
      orchestrateWeakNetworkAiTask({ taskId: this.taskId, brief: this.brief })
        .then(res => {
          const data = (res && res.data) || res || {}
          this.applyDetail(data)
          this.orchSource = data.orchestrateSource || 'ai'
          this.$message.success('已生成检查点，请确认后下载')
        })
        .finally(() => { this.orchLoading = false })
    },
    addCheckpoint() {
      this.checkpoints.push({
        title: '',
        expect: '',
        profilePreset: (this.profiles[0] && this.profiles[0].presetCode) || 'subway',
        sortNo: this.checkpoints.length + 1
      })
    },
    saveDraft() {
      this.saveLoading = true
      updateWeakNetworkAiTask({
        taskId: this.taskId,
        brief: this.brief,
        selectedProfileIds: this.selectedProfileIds,
        checkpoints: this.checkpoints
      }).then(res => {
        this.applyDetail((res && res.data) || res || {})
        this.$message.success('已保存')
      }).finally(() => { this.saveLoading = false })
    },
    doConfirm() {
      this.saveDraft()
      this.confirmLoading = true
      updateWeakNetworkAiTask({
        taskId: this.taskId,
        brief: this.brief,
        selectedProfileIds: this.selectedProfileIds,
        checkpoints: this.checkpoints
      }).then(() => confirmWeakNetworkAiTask({ taskId: this.taskId }))
        .then(res => {
          this.applyDetail((res && res.data) || res || {})
          this.$message.success('已生成弱网会话，请下载')
        })
        .finally(() => { this.confirmLoading = false })
    },
    doDownload(sessionId) {
      this.downloadLoading = sessionId
      downloadWeakNetworkSession(sessionId).then(blob => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'weaknet-ai-session-' + sessionId + '.zip'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }).finally(() => { this.downloadLoading = null })
    },
    submitEvidenceNote() {
      this.evidenceLoading = true
      addWeakNetworkAiEvidence({
        taskId: this.taskId,
        checkpointId: this.evidenceForm.checkpointId,
        note: this.evidenceForm.note,
        mobileExecutionId: this.evidenceForm.mobileExecutionId || null
      }).then(res => {
        this.applyDetail((res && res.data) || res || {})
        this.evidenceForm.note = ''
        this.$message.success('已记录证据')
      }).finally(() => { this.evidenceLoading = false })
    },
    onFileChange(e) {
      const file = e.target.files && e.target.files[0]
      if (!file) return
      const fd = new FormData()
      fd.append('file', file)
      fd.append('taskId', this.taskId)
      if (this.evidenceForm.checkpointId) fd.append('checkpointId', this.evidenceForm.checkpointId)
      fd.append('note', this.evidenceForm.note || '')
      if (this.evidenceForm.mobileExecutionId) fd.append('mobileExecutionId', this.evidenceForm.mobileExecutionId)
      this.evidenceLoading = true
      uploadWeakNetworkAiEvidence(fd).then(res => {
        this.applyDetail((res && res.data) || res || {})
        this.$message.success('截图已上传')
      }).finally(() => {
        this.evidenceLoading = false
        e.target.value = ''
      })
    },
    doJudge() {
      this.judgeLoading = true
      judgeWeakNetworkAiTask({ taskId: this.taskId }).then(res => {
        this.applyDetail((res && res.data) || res || {})
        this.$message.success('判定完成')
      }).finally(() => { this.judgeLoading = false })
    },
    doDismiss() {
      const ids = this.selectedFindings.map(f => f.findingId)
      dismissWeakNetworkAiFindings({ taskId: this.taskId, findingIds: ids }).then(res => {
        this.applyDetail((res && res.data) || res || {})
        this.selectedFindings = []
      })
    },
    doConfirmBugs() {
      const ids = this.selectedFindings.map(f => f.findingId)
      this.bugLoading = true
      confirmWeakNetworkAiFindingsToBug({ taskId: this.taskId, findingIds: ids, appendAiObservation: true })
        .then(res => {
          const data = (res && res.data) || res || {}
          if (data.detail) this.applyDetail(data.detail)
          else this.loadDetail()
          this.$message.success('已创建 Bug：' + ((data.created || []).map(x => x.bugId).join(',') || ''))
          this.selectedFindings = []
        })
        .finally(() => { this.bugLoading = false })
    }
  }
}
</script>

<style scoped>
.block { margin-bottom: 16px; }
.label { font-weight: 600; margin-bottom: 6px; color: #303133; }
.hint { color: #909399; font-size: 12px; margin-top: 8px; }
</style>
