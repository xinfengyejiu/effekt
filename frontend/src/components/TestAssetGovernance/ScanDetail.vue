<template>
  <div class="page-wrap asset-governance-detail">
    <page-section title="测试资产治理详情">
      <template slot="extra">
        <el-button size="small" icon="el-icon-back" @click="$router.push({ path: '/test-asset-governance' })">返回列表</el-button>
        <el-button size="small" type="primary" icon="el-icon-caret-right" :loading="executeLoading" @click="executeScan">执行扫描</el-button>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else>
        <div class="summary-grid">
          <div class="summary-item"><span>扫描编号</span><b>{{ field(detail, 'scan_no', 'scanNo') || '-' }}</b></div>
          <div class="summary-item"><span>健康分</span><b>{{ summary.healthScore == null ? '-' : summary.healthScore }}</b></div>
          <div class="summary-item"><span>问题数</span><b>{{ summary.issueCount || 0 }}</b></div>
          <div class="summary-item"><span>状态</span><el-tag :type="statusTag(detail.status)">{{ statusLabel(detail.status) }}</el-tag></div>
          <div class="summary-item"><span>总用例</span><b>{{ summary.totalCases || 0 }}</b></div>
          <div class="summary-item"><span>AI生成用例</span><b>{{ summary.aiGeneratedCases || 0 }}</b></div>
        </div>

        <div class="plain-panel">
          <div class="panel-title">治理摘要</div>
          <p>{{ summary.summary || '暂无扫描摘要' }}</p>
          <el-tag v-for="item in summary.recommendedActions || []" :key="item" size="small" class="action-tag">{{ item }}</el-tag>
        </div>

        <div class="meta-grid">
          <div class="meta-item"><span>标题</span><b>{{ detail.title || '-' }}</b></div>
          <div class="meta-item"><span>产品</span><b>{{ field(detail, 'product_name', 'productName') || '-' }}</b></div>
          <div class="meta-item"><span>项目</span><b>{{ field(detail, 'project_name', 'projectName') || '-' }}</b></div>
          <div class="meta-item"><span>扫描类型</span><b>{{ field(detail, 'scan_type', 'scanType') || '-' }}</b></div>
          <div class="meta-item"><span>开始时间</span><b>{{ field(detail, 'started_time', 'startedTime') || '-' }}</b></div>
          <div class="meta-item"><span>完成时间</span><b>{{ field(detail, 'finished_time', 'finishedTime') || '-' }}</b></div>
        </div>

        <div class="issue-toolbar">
          <el-select v-model="issueQuery.issueType" clearable size="small" placeholder="问题类型" style="width:150px;">
            <el-option v-for="item in issueTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="issueQuery.severity" clearable size="small" placeholder="严重等级" style="width:130px;">
            <el-option v-for="item in severityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="issueQuery.actionStatus" clearable size="small" placeholder="处理状态" style="width:130px;">
            <el-option v-for="item in issueStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-input v-model.trim="issueQuery.keyword" clearable size="small" placeholder="标题/描述" style="width:200px;" />
        </div>

        <el-table :data="pagedIssues" border style="width:100%; margin-top:12px;">
          <el-table-column type="expand">
            <template slot-scope="scope">
              <div class="action-history">
                <div class="panel-title">动作历史</div>
                <el-table v-if="scope.row.actions && scope.row.actions.length" :data="scope.row.actions" size="mini" border>
                  <el-table-column label="动作" width="140"><template slot-scope="actionScope">{{ field(actionScope.row, 'action_type', 'actionType') }}</template></el-table-column>
                  <el-table-column label="状态" width="100"><template slot-scope="actionScope">{{ actionScope.row.status || '-' }}</template></el-table-column>
                  <el-table-column label="时间" width="170"><template slot-scope="actionScope">{{ field(actionScope.row, 'created_time', 'createdTime') || '-' }}</template></el-table-column>
                  <el-table-column label="结果"><template slot-scope="actionScope"><pre class="inline-json">{{ formatJson(field(actionScope.row, 'result_payload', 'resultPayload')) }}</pre></template></el-table-column>
                </el-table>
                <el-empty v-else :image-size="60" description="暂无动作记录" />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="严重" width="90">
            <template slot-scope="scope"><el-tag size="mini" :type="severityTag(scope.row.severity)">{{ severityLabel(scope.row.severity) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="类型" width="130">
            <template slot-scope="scope">{{ issueTypeLabel(field(scope.row, 'issue_type', 'issueType')) }}</template>
          </el-table-column>
          <el-table-column label="模块" min-width="130" show-overflow-tooltip>
            <template slot-scope="scope">{{ field(scope.row, 'module_name', 'moduleName') || '-' }}</template>
          </el-table-column>
          <el-table-column label="标题" min-width="220" show-overflow-tooltip>
            <template slot-scope="scope">{{ scope.row.title || '-' }}</template>
          </el-table-column>
          <el-table-column label="关联用例" width="120">
            <template slot-scope="scope">{{ relatedCaseText(scope.row) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template slot-scope="scope"><el-tag size="mini" :type="issueStatusTag(field(scope.row, 'action_status', 'actionStatus'))">{{ issueStatusLabel(field(scope.row, 'action_status', 'actionStatus')) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" icon="el-icon-document" @click="showEvidence(scope.row)">证据</el-button>
              <el-button type="text" @click="updateIssue(scope.row, 'accepted')">接收</el-button>
              <el-button type="text" @click="updateIssue(scope.row, 'ignored')">忽略</el-button>
              <el-button type="text" @click="updateIssue(scope.row, 'fixed')">修复</el-button>
              <el-dropdown trigger="click" @command="command => applyAction(scope.row, command)">
                <el-button type="text">更多<i class="el-icon-arrow-down el-icon--right" /></el-button>
                <el-dropdown-menu slot="dropdown">
                  <el-dropdown-item command="reopen">重新打开</el-dropdown-item>
                  <el-dropdown-item command="keep">保留用例</el-dropdown-item>
                  <el-dropdown-item command="merge">记录合并</el-dropdown-item>
                  <el-dropdown-item command="improve">记录改进</el-dropdown-item>
                  <el-dropdown-item command="deprecate">废弃用例</el-dropdown-item>
                  <el-dropdown-item command="accept_suggestion">采纳建议</el-dropdown-item>
                </el-dropdown-menu>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager-wrap">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next, jumper"
            :current-page="issuePageNo"
            :page-size="issuePageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredIssues.length"
            @size-change="handleIssueSizeChange"
            @current-change="handleIssueCurrentChange"
          />
        </div>
      </div>
    </page-section>

    <el-drawer title="问题证据" :visible.sync="evidenceVisible" size="52%" append-to-body>
      <div class="drawer-body">
        <h4>{{ currentIssue.title || '-' }}</h4>
        <p>{{ currentIssue.description || '-' }}</p>
        <div class="drawer-section">
          <div class="panel-title">证据</div>
          <pre class="json-preview">{{ formatJson(field(currentIssue, 'evidence_json', 'evidenceJson')) }}</pre>
        </div>
        <div class="drawer-section">
          <div class="panel-title">建议</div>
          <pre class="json-preview">{{ formatJson(field(currentIssue, 'suggestion_json', 'suggestionJson')) }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { applyAssetGovernanceAction, executeAssetGovernanceScan, getAssetGovernanceScanDetail, updateAssetGovernanceIssue } from '@/api/testAssetGovernanceApi'

const ISSUE_TYPES = [
  { value: 'duplicate_case', label: '重复用例' },
  { value: 'weak_case', label: '低质量用例' },
  { value: 'stale_case', label: '过期用例' },
  { value: 'coverage_gap', label: '覆盖缺口' },
  { value: 'ai_suggestion', label: 'AI建议待处理' }
]
const SEVERITIES = [
  { value: 'critical', label: '严重' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' }
]
const ISSUE_STATUSES = [
  { value: 'open', label: '待处理' },
  { value: 'accepted', label: '已接收' },
  { value: 'ignored', label: '已忽略' },
  { value: 'fixed', label: '已修复' },
  { value: 'reopened', label: '已重开' }
]
const SCAN_STATUSES = { pending: '待执行', running: '执行中', success: '已完成', failed: '失败' }

export default {
  name: 'TestAssetGovernanceScanDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      executeLoading: false,
      evidenceVisible: false,
      currentIssue: {},
      detail: {},
      issueQuery: { issueType: '', severity: '', actionStatus: '', keyword: '' },
      issuePageNo: 1,
      issuePageSize: 10,
      issueTypeOptions: ISSUE_TYPES,
      severityOptions: SEVERITIES,
      issueStatusOptions: ISSUE_STATUSES
    }
  },
  watch: {
    'issueQuery.issueType': 'resetIssuePage',
    'issueQuery.severity': 'resetIssuePage',
    'issueQuery.actionStatus': 'resetIssuePage',
    'issueQuery.keyword': 'resetIssuePage'
  },
  computed: {
    scanId() { return this.$route.query.id },
    summary() { return this.field(this.detail, 'summary_json', 'summaryJson') || {} },
    issues() { return this.detail.issues || [] },
    filteredIssues() {
      const keyword = String(this.issueQuery.keyword || '').toLowerCase()
      return this.issues.filter(item => {
        const issueType = this.field(item, 'issue_type', 'issueType')
        const actionStatus = this.field(item, 'action_status', 'actionStatus')
        if (this.issueQuery.issueType && issueType !== this.issueQuery.issueType) return false
        if (this.issueQuery.severity && item.severity !== this.issueQuery.severity) return false
        if (this.issueQuery.actionStatus && actionStatus !== this.issueQuery.actionStatus) return false
        if (keyword && !String((item.title || '') + (item.description || '')).toLowerCase().includes(keyword)) return false
        return true
      })
    },
    pagedIssues() {
      const start = (this.issuePageNo - 1) * this.issuePageSize
      return this.filteredIssues.slice(start, start + this.issuePageSize)
    }
  },
  created() {
    this.fetchDetail()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    field(row, snake, camel) { return row && row[snake] !== undefined ? row[snake] : row ? row[camel] : undefined },
    fetchDetail() {
      this.loading = true
      getAssetGovernanceScanDetail({ scanId: this.scanId }).then(res => {
        this.detail = this.apiData(res)
        this.$nextTick(this.syncIssuePage)
      }).finally(() => { this.loading = false })
    },
    executeScan() {
      this.executeLoading = true
      executeAssetGovernanceScan({ scanId: this.scanId }).then(() => {
        this.$message.success('扫描执行完成')
        this.fetchDetail()
      }).finally(() => { this.executeLoading = false })
    },
    updateIssue(row, status) {
      updateAssetGovernanceIssue({ issueId: row.id, status }).then(() => {
        this.$message.success('问题状态已更新')
        this.fetchDetail()
      })
    },
    applyAction(row, actionType) {
      if (actionType === 'deprecate') {
        this.$prompt('请输入要废弃的关联用例编号或ID', '废弃用例', { inputPattern: /\S+/, inputErrorMessage: '请输入用例编号或ID' }).then(({ value }) => {
          return this.submitAction(row, actionType, { caseId: value })
        }).catch(() => {})
        return
      }
      this.submitAction(row, actionType, {})
    },
    submitAction(row, actionType, extra) {
      return applyAssetGovernanceAction(Object.assign({ issueId: row.id, actionType }, extra || {})).then(() => {
        this.$message.success('治理动作已记录')
        this.fetchDetail()
      })
    },
    showEvidence(row) {
      this.currentIssue = row
      this.evidenceVisible = true
    },
    relatedCaseText(row) {
      const keys = this.field(row, 'related_case_keys', 'relatedCaseKeys') || []
      if (keys.length) return keys.join(',')
      const cases = this.field(row, 'related_cases', 'relatedCases') || []
      const labels = cases.map(item => this.field(item, 'case_key', 'caseKey')).filter(Boolean)
      return labels.length ? labels.join(',') : '-'
    },
    formatJson(value) {
      if (!value) return '{}'
      try {
        return JSON.stringify(value, null, 2)
      } catch (e) {
        return String(value)
      }
    },
    resetIssuePage() {
      this.issuePageNo = 1
    },
    syncIssuePage() {
      const maxPage = Math.max(1, Math.ceil(this.filteredIssues.length / this.issuePageSize))
      if (this.issuePageNo > maxPage) this.issuePageNo = maxPage
    },
    handleIssueSizeChange(value) {
      this.issuePageSize = value
      this.issuePageNo = 1
    },
    handleIssueCurrentChange(value) {
      this.issuePageNo = value
    },
    statusLabel(value) { return SCAN_STATUSES[value] || value || '-' },
    statusTag(value) { return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[value] || 'info' },
    issueTypeLabel(value) { return (ISSUE_TYPES.find(item => item.value === value) || {}).label || value || '-' },
    severityLabel(value) { return (SEVERITIES.find(item => item.value === value) || {}).label || value || '-' },
    severityTag(value) { return { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }[value] || 'info' },
    issueStatusLabel(value) { return (ISSUE_STATUSES.find(item => item.value === value) || {}).label || value || '-' },
    issueStatusTag(value) { return { open: 'info', accepted: 'warning', ignored: 'info', fixed: 'success', reopened: 'danger' }[value] || 'info' }
  }
}
</script>

<style scoped>
.summary-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.summary-item { border: 1px solid #ebeef5; padding: 12px; border-radius: 4px; background: #fff; min-width: 0; }
.summary-item span { display: block; color: #909399; font-size: 12px; margin-bottom: 8px; }
.summary-item b { font-size: 16px; color: #303133; word-break: break-word; }
.plain-panel { border: 1px solid #ebeef5; padding: 12px; border-radius: 4px; background: #fff; margin-bottom: 14px; }
.panel-title { font-weight: 600; color: #303133; margin-bottom: 8px; }
.action-tag { margin-right: 8px; margin-top: 8px; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border-top: 1px solid #ebeef5; border-left: 1px solid #ebeef5; margin-bottom: 14px; }
.meta-item { display: grid; grid-template-columns: 110px minmax(0, 1fr); min-height: 40px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.meta-item span { padding: 10px 12px; color: #606266; background: #fafafa; }
.meta-item b { padding: 10px 12px; color: #303133; font-weight: 400; word-break: break-all; }
.issue-toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.pager-wrap { margin-top: 16px; text-align: right; }
.action-history { padding: 8px 16px; }
.inline-json { margin: 0; white-space: pre-wrap; word-break: break-word; font-size: 12px; color: #606266; }
.drawer-body { padding: 0 20px 20px; }
.drawer-section { margin-top: 16px; }
.json-preview { margin: 0; max-height: 360px; overflow: auto; padding: 12px; background: #f6f8fa; border-radius: 4px; white-space: pre-wrap; word-break: break-word; }
@media (max-width: 1100px) {
  .summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 768px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .meta-grid { grid-template-columns: 1fr; }
  .asset-governance-detail /deep/ .el-drawer { width: 92% !important; }
}
</style>
