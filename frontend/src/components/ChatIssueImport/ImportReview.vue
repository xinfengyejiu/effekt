<template>
  <div class="page-wrap chat-issue-review" v-loading="loading">
    <page-section :title="pageTitle">
      <template slot="extra">
        <el-button size="small" icon="el-icon-back" @click="$router.push('/chat-issue')">返回列表</el-button>
        <el-button size="small" :disabled="!selectedIds.length" :loading="analyzeLoading" @click="runAnalyze">AI 分析</el-button>
        <el-button size="small" type="warning" :disabled="!selectedIds.length" @click="runDismiss">放弃</el-button>
        <el-button size="small" type="danger" :disabled="!selectedIds.length" :loading="bugLoading" @click="runConfirmBug">确认转 Bug</el-button>
        <el-button size="small" type="primary" :disabled="!selectedIds.length" :loading="caseLoading" @click="runToCase">转用例</el-button>
      </template>

      <div class="meta-row" v-if="batch.id">
        <el-tag size="mini">{{ batch.sessionNo }}</el-tag>
        <el-tag size="mini" type="info" v-if="batch.dayLabel">{{ batch.dayLabel }}</el-tag>
        <span>{{ batch.productName }} / {{ batch.projectName }}</span>
        <el-tag size="mini" :type="statusTag(batch.status)">{{ statusLabel(batch.status) }}</el-tag>
      </div>

      <el-table
        :data="items"
        border
        style="width:100%;margin-top:12px;"
        @selection-change="onSelect"
      >
        <el-table-column type="selection" width="45" :selectable="row => row.itemStatus !== 'dismissed'" />
        <el-table-column label="#" width="50" prop="sourceRef" />
        <el-table-column label="标题" min-width="200" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-input v-if="editingId === scope.row.id" v-model="editDraft.title" size="mini" />
            <span v-else>{{ scope.row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="itemStatusTag(scope.row.itemStatus)">{{ itemStatusLabel(scope.row.itemStatus) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AI 分析" min-width="260">
          <template slot-scope="scope">
            <div v-if="scope.row.aiAnalysis && (scope.row.aiAnalysis.possibleCauses || []).length" class="ai-block">
              <div><b>原因：</b>{{ (scope.row.aiAnalysis.possibleCauses || []).join('；') }}</div>
              <div><b>建议：</b>{{ (scope.row.aiAnalysis.suggestions || []).join('；') }}</div>
            </div>
            <span v-else class="muted">未分析</span>
          </template>
        </el-table-column>
        <el-table-column label="关联" width="140">
          <template slot-scope="scope">
            <el-link v-if="scope.row.linkedBugId" type="danger" @click="goBug(scope.row.linkedBugId)">Bug #{{ scope.row.linkedBugId }}</el-link>
            <el-link v-if="scope.row.linkedCaseId" type="primary" @click="goCase(scope.row.linkedCaseId)">用例 #{{ scope.row.linkedCaseId }}</el-link>
            <span v-if="!scope.row.linkedBugId && !scope.row.linkedCaseId">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openDetail(scope.row)">详情</el-button>
            <el-button type="text" @click="saveTitle(scope.row)" v-if="editingId === scope.row.id">保存</el-button>
            <el-button type="text" @click="startEdit(scope.row)" v-else>改标题</el-button>
          </template>
        </el-table-column>
      </el-table>
    </page-section>

    <el-dialog title="候选详情" :visible.sync="detailVisible" width="680px">
      <el-form label-width="80px" size="small" v-if="current">
        <el-form-item label="标题"><el-input v-model="current.title" /></el-form-item>
        <el-form-item label="详情"><el-input v-model="current.detail" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="current.suggestType" style="width:160px;">
            <el-option label="Bug" value="bug" />
            <el-option label="用例" value="case" />
            <el-option label="两者" value="both" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI原因">
          <el-input :value="(current.aiAnalysis.possibleCauses || []).join('\n')" type="textarea" :rows="3" @input="v => setCauses(v)" />
        </el-form-item>
        <el-form-item label="AI建议">
          <el-input :value="(current.aiAnalysis.suggestions || []).join('\n')" type="textarea" :rows="3" @input="v => setSuggestions(v)" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="detailVisible = false">关闭</el-button>
        <el-button size="small" type="primary" :loading="saveLoading" @click="saveDetail">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  analyzeChatIssue,
  chatIssueToCase,
  confirmChatIssueToBug,
  dismissChatIssue,
  getChatIssueDetail,
  updateChatIssueItem
} from '@/api/chatIssueApi'

const BATCH_STATUS = {
  draft: { label: '草稿', tag: 'info' },
  ready: { label: '待处理', tag: '' },
  partial: { label: '部分转正', tag: 'warning' },
  done: { label: '已完成', tag: 'success' }
}
const ITEM_STATUS = {
  parsed: { label: '已解析', tag: 'info' },
  analyzed: { label: '已分析', tag: 'warning' },
  confirmed: { label: '已转正', tag: 'success' },
  dismissed: { label: '已放弃', tag: 'info' }
}

export default {
  name: 'ChatIssueImportReview',
  components: { PageSection },
  data() {
    return {
      loading: false,
      analyzeLoading: false,
      bugLoading: false,
      caseLoading: false,
      saveLoading: false,
      batch: {},
      items: [],
      selectedIds: [],
      detailVisible: false,
      current: null,
      editingId: null,
      editDraft: { title: '' }
    }
  },
  computed: {
    importId() { return this.$route.query.id },
    pageTitle() { return this.batch.title ? `核对转正 · ${this.batch.title}` : '核对转正' }
  },
  watch: {
    '$route.query.id'() { this.loadDetail() }
  },
  created() { this.loadDetail() },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    statusLabel(v) { return (BATCH_STATUS[v] || {}).label || v || '-' },
    statusTag(v) { return (BATCH_STATUS[v] || {}).tag || 'info' },
    itemStatusLabel(v) { return (ITEM_STATUS[v] || {}).label || v || '-' },
    itemStatusTag(v) { return (ITEM_STATUS[v] || {}).tag || 'info' },
    loadDetail() {
      if (!this.importId) {
        this.$message.warning('缺少 importId')
        this.$router.push('/chat-issue')
        return
      }
      this.loading = true
      getChatIssueDetail({ importId: this.importId }).then(res => {
        const data = this.apiData(res)
        this.batch = data || {}
        this.items = data.items || []
      }).finally(() => { this.loading = false })
    },
    onSelect(rows) { this.selectedIds = rows.map(r => r.id) },
    startEdit(row) {
      this.editingId = row.id
      this.editDraft = { title: row.title }
    },
    saveTitle(row) {
      updateChatIssueItem({ itemId: row.id, title: this.editDraft.title }).then(() => {
        row.title = this.editDraft.title
        this.editingId = null
        this.$message.success('已保存')
      })
    },
    openDetail(row) {
      this.current = {
        id: row.id,
        title: row.title,
        detail: row.detail,
        suggestType: row.suggestType || 'bug',
        aiAnalysis: Object.assign({ possibleCauses: [], suggestions: [] }, row.aiAnalysis || {})
      }
      this.detailVisible = true
    },
    setCauses(v) {
      this.current.aiAnalysis.possibleCauses = String(v || '').split('\n').map(s => s.trim()).filter(Boolean)
    },
    setSuggestions(v) {
      this.current.aiAnalysis.suggestions = String(v || '').split('\n').map(s => s.trim()).filter(Boolean)
    },
    saveDetail() {
      this.saveLoading = true
      updateChatIssueItem({
        itemId: this.current.id,
        title: this.current.title,
        detail: this.current.detail,
        suggestType: this.current.suggestType,
        aiAnalysis: this.current.aiAnalysis
      }).then(() => {
        this.$message.success('已保存')
        this.detailVisible = false
        this.loadDetail()
      }).finally(() => { this.saveLoading = false })
    },
    runAnalyze() {
      this.analyzeLoading = true
      analyzeChatIssue({ importId: this.importId, itemIds: this.selectedIds }).then(res => {
        const data = this.apiData(res)
        const errCount = (data.errors || []).length
        this.$message.success(`分析完成${errCount ? `，失败 ${errCount} 条` : ''}`)
        this.loadDetail()
      }).finally(() => { this.analyzeLoading = false })
    },
    runDismiss() {
      this.$confirm('放弃选中候选？不会创建 Bug。', '提示', { type: 'warning' }).then(() => {
        return dismissChatIssue({ importId: this.importId, itemIds: this.selectedIds })
      }).then(() => {
        this.$message.success('已放弃')
        this.loadDetail()
      }).catch(() => {})
    },
    runConfirmBug() {
      this.$confirm('确认将选中候选转为正式 Bug？会附带 AI 分析结果到描述。', '确认转正', { type: 'warning' }).then(() => {
        this.bugLoading = true
        return confirmChatIssueToBug({
          importId: this.importId,
          itemIds: this.selectedIds,
          appendAiAnalysis: true
        })
      }).then(res => {
        const data = this.apiData(res)
        const created = (data.created || []).length
        this.$message.success(`已创建 ${created} 个 Bug`)
        this.loadDetail()
      }).catch(() => {}).finally(() => { this.bugLoading = false })
    },
    runToCase() {
      this.caseLoading = true
      chatIssueToCase({ importId: this.importId, itemIds: this.selectedIds, create: true }).then(res => {
        const data = this.apiData(res)
        const n = (data.results || []).filter(r => r.created).length
        this.$message.success(`已创建 ${n} 个用例`)
        this.loadDetail()
      }).finally(() => { this.caseLoading = false })
    },
    goBug(id) { this.$router.push({ path: '/bug/detail', query: { bugId: id } }) },
    goCase(id) {
      this.$router.push({
        path: '/test-platform/case/editor',
        query: { projectId: this.batch.projectId, caseId: id }
      })
    }
  }
}
</script>

<style scoped>
.meta-row { display: flex; gap: 10px; align-items: center; color: #606266; flex-wrap: wrap; }
.ai-block { font-size: 12px; line-height: 1.5; color: #606266; }
.muted { color: #c0c4cc; }
</style>
