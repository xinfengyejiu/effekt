<template>
  <div class="page-wrap ai-workload-estimate-page">
    <page-section title="AI工作量预估详情">
      <template slot="extra">
        <el-button size="small" @click="$router.push({ path: '/ai-workload-estimate' })">返回列表</el-button>
        <el-button size="small" type="primary" :loading="executeLoading" @click="executeEstimate">执行AI预估</el-button>
        <el-button size="small" :loading="retryLoading" @click="retryEstimate">重新预估</el-button>
        <el-button size="small" @click="openAssign">分配负责人</el-button>
        <el-button size="small" :loading="confirmLoading" @click="confirmEstimate">确认预估</el-button>
        <el-button size="small" type="success" :loading="exportLoading" @click="exportExcel">导出Excel</el-button>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else>
        <div class="summary-grid">
          <div class="summary-item"><span>预估编号</span><b>{{ estimate.estimate_no || estimate.estimateNo || '-' }}</b></div>
          <div class="summary-item"><span>复杂度</span><el-tag :type="complexityTag(estimate.complexity_level || estimate.complexityLevel)">{{ complexityLabel(estimate.complexity_level || estimate.complexityLevel) }}</el-tag></div>
          <div class="summary-item"><span>置信度</span><b>{{ confidenceLabel(estimate.confidence) }}</b></div>
          <div class="summary-item"><span>状态</span><el-tag :type="statusTag(estimate.status)">{{ statusLabel(estimate.status) }}</el-tag></div>
        </div>

        <el-card shadow="never" class="detail-card">
          <div slot="header">基础信息</div>
          <div class="meta-grid">
            <div class="meta-item"><span>标题</span><b>{{ estimate.title || '-' }}</b></div>
            <div class="meta-item"><span>产品</span><b>{{ estimate.product_name || estimate.productName || '-' }}</b></div>
            <div class="meta-item"><span>项目</span><b>{{ estimate.project_name || estimate.projectName || '-' }}</b></div>
            <div class="meta-item"><span>负责人</span><b>{{ estimate.ownerNameDisplay || estimate.owner_name || estimate.ownerName || '未分配' }}</b></div>
            <div class="meta-item"><span>创建时间</span><b>{{ estimate.created_time || estimate.createdTime || '-' }}</b></div>
            <div class="meta-item"><span>分配时间</span><b>{{ estimate.assigned_time || estimate.assignedTime || '-' }}</b></div>
          </div>
          <el-alert v-if="estimate.failure_reason || estimate.failureReason" class="failure-alert" type="error" :closable="false" :title="estimate.failure_reason || estimate.failureReason" />
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">预估总览</div>
          <div class="metric-grid">
            <div class="metric"><span>功能点数</span><b>{{ estimate.total_function_points || estimate.totalFunctionPoints || 0 }}</b></div>
            <div class="metric"><span>用例总数</span><b>{{ estimate.total_case_count || estimate.totalCaseCount || 0 }}</b></div>
            <div class="metric"><span>设计工时</span><b>{{ estimate.case_design_hours || estimate.caseDesignHours || 0 }} h</b></div>
            <div class="metric"><span>QA工时</span><b>{{ estimate.qa_execution_hours || estimate.qaExecutionHours || 0 }} h</b></div>
            <div class="metric"><span>总工时</span><b>{{ estimate.total_effort_hours || estimate.totalEffortHours || 0 }} h</b></div>
            <div class="metric"><span>Token预估</span><b>{{ estimate.estimated_tokens || estimate.estimatedTokens || 0 }}</b></div>
          </div>
          <el-alert class="method-alert" type="success" :closable="false" :title="'预估口径：' + (resultSummary.methodVersion || 'Estimate-task/test-effort-estimation')" />
          <p class="summary-text">{{ resultSummary.summary || '-' }}</p>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">三档总览</div>
          <el-table :data="rangeRows" border style="width:100%;">
            <el-table-column label="指标" prop="name" min-width="160" />
            <el-table-column label="乐观" prop="optimistic" width="120" />
            <el-table-column label="正常" prop="normal" width="120" />
            <el-table-column label="悲观" prop="pessimistic" width="120" />
            <el-table-column label="说明" prop="description" min-width="260" show-overflow-tooltip />
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">工时线：5阶段</div>
          <el-table :data="stageHours" border style="width:100%;">
            <el-table-column label="#" width="60"><template slot-scope="scope">{{ scope.row.stageNo || scope.$index + 1 }}</template></el-table-column>
            <el-table-column label="阶段" min-width="150"><template slot-scope="scope">{{ scope.row.stageName || '-' }}</template></el-table-column>
            <el-table-column label="乐观h" width="90"><template slot-scope="scope">{{ scope.row.optimisticHours || 0 }}</template></el-table-column>
            <el-table-column label="正常h" width="90"><template slot-scope="scope">{{ scope.row.normalHours || 0 }}</template></el-table-column>
            <el-table-column label="悲观h" width="90"><template slot-scope="scope">{{ scope.row.pessimisticHours || 0 }}</template></el-table-column>
            <el-table-column label="说明" min-width="260" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.description || '-' }}</template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">Token线：6环节</div>
          <el-table :data="tokenLines" border style="width:100%;">
            <el-table-column label="#" width="60"><template slot-scope="scope">{{ scope.row.lineNo || scope.$index + 1 }}</template></el-table-column>
            <el-table-column label="环节" min-width="160"><template slot-scope="scope">{{ scope.row.lineName || '-' }}</template></el-table-column>
            <el-table-column label="调用次数" width="110"><template slot-scope="scope">{{ scope.row.callCount || '-' }}</template></el-table-column>
            <el-table-column label="乐观Token" width="120"><template slot-scope="scope">{{ scope.row.optimisticTokens || 0 }}</template></el-table-column>
            <el-table-column label="正常Token" width="120"><template slot-scope="scope">{{ scope.row.normalTokens || 0 }}</template></el-table-column>
            <el-table-column label="悲观Token" width="120"><template slot-scope="scope">{{ scope.row.pessimisticTokens || 0 }}</template></el-table-column>
            <el-table-column label="说明" min-width="260" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.description || '-' }}</template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">Agent工期线</div>
          <div class="agent-summary">
            <span>Rounds：{{ agentSummary.optimisticRounds || 0 }} / {{ agentSummary.normalRounds || 0 }} / {{ agentSummary.pessimisticRounds || 0 }}</span>
            <span>墙钟分钟：{{ agentSummary.optimisticMinutes || 0 }} / {{ agentSummary.normalMinutes || 0 }} / {{ agentSummary.pessimisticMinutes || 0 }}</span>
          </div>
          <el-table :data="agentRounds" border style="width:100%; margin-top:12px;">
            <el-table-column label="#" width="60"><template slot-scope="scope">{{ scope.row.lineNo || scope.$index + 1 }}</template></el-table-column>
            <el-table-column label="Agent模块" min-width="180"><template slot-scope="scope">{{ scope.row.moduleName || '-' }}</template></el-table-column>
            <el-table-column label="Base Rounds" width="120"><template slot-scope="scope">{{ scope.row.baseRounds || 0 }}</template></el-table-column>
            <el-table-column label="风险系数" width="100"><template slot-scope="scope">{{ scope.row.riskCoefficient || 0 }}</template></el-table-column>
            <el-table-column label="有效Rounds" width="120"><template slot-scope="scope">{{ scope.row.effectiveRounds || 0 }}</template></el-table-column>
            <el-table-column label="说明" min-width="260" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.description || '-' }}</template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">本次PRD</div>
          <el-alert type="info" :closable="false" title="本次PRD是预估范围；历史文档仅用于复杂度参考。" />
          <el-table :data="prdSnapshot" border style="width:100%; margin-top:12px;">
            <el-table-column label="文档名称" min-width="260" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.source || '-' }}</template></el-table-column>
            <el-table-column label="版本" width="80"><template slot-scope="scope">{{ scope.row.version || '-' }}</template></el-table-column>
            <el-table-column label="状态" width="90"><template slot-scope="scope">{{ scope.row.status }}</template></el-table-column>
            <el-table-column label="内容长度" width="110"><template slot-scope="scope">{{ scope.row.contentLength || 0 }}</template></el-table-column>
            <el-table-column label="创建时间" min-width="160" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.createdTime || '-' }}</template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">历史参考</div>
          <div class="reference-row">
            <span>参考文档数：{{ referenceSummary.documentCount || 0 }}</span>
            <el-tag v-for="item in referenceSummary.riskKeywords || []" :key="item" size="mini" type="warning">{{ item }}</el-tag>
          </div>
          <p class="summary-text">{{ referenceSummary.note || '历史文档仅用于复杂度参考，不作为本次范围' }}</p>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">模块明细</div>
          <el-table :data="modules" border style="width:100%;">
            <el-table-column label="模块" min-width="150" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.module_name || scope.row.moduleName || '-' }}</template></el-table-column>
            <el-table-column label="复杂度" width="90"><template slot-scope="scope"><el-tag size="mini" :type="complexityTag(scope.row.complexity_level || scope.row.complexityLevel)">{{ complexityLabel(scope.row.complexity_level || scope.row.complexityLevel) }}</el-tag></template></el-table-column>
            <el-table-column label="功能点" width="80"><template slot-scope="scope">{{ scope.row.function_point_count || scope.row.functionPointCount || 0 }}</template></el-table-column>
            <el-table-column label="用例数" width="80"><template slot-scope="scope">{{ scope.row.case_count || scope.row.caseCount || 0 }}</template></el-table-column>
            <el-table-column label="设计h" width="90"><template slot-scope="scope">{{ scope.row.case_design_hours || scope.row.caseDesignHours || 0 }}</template></el-table-column>
            <el-table-column label="QA h" width="90"><template slot-scope="scope">{{ scope.row.qa_execution_hours || scope.row.qaExecutionHours || 0 }}</template></el-table-column>
            <el-table-column label="总h" width="90"><template slot-scope="scope">{{ scope.row.total_hours || scope.row.totalHours || 0 }}</template></el-table-column>
            <el-table-column label="风险摘要" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ riskText(scope.row.risk_summary || scope.row.riskSummary) }}</template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">功能点明细</div>
          <el-table :data="functions" border style="width:100%;">
            <el-table-column label="模块" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.module_name || scope.row.moduleName || '-' }}</template></el-table-column>
            <el-table-column label="功能点" min-width="180" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.function_name || scope.row.functionName || '-' }}</template></el-table-column>
            <el-table-column label="测试范围" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.test_scope || scope.row.testScope || '-' }}</template></el-table-column>
            <el-table-column label="正向" width="70"><template slot-scope="scope">{{ scope.row.positive_case_count || scope.row.positiveCaseCount || 0 }}</template></el-table-column>
            <el-table-column label="反向" width="70"><template slot-scope="scope">{{ scope.row.negative_case_count || scope.row.negativeCaseCount || 0 }}</template></el-table-column>
            <el-table-column label="边界" width="70"><template slot-scope="scope">{{ scope.row.boundary_case_count || scope.row.boundaryCaseCount || 0 }}</template></el-table-column>
            <el-table-column label="权限" width="70"><template slot-scope="scope">{{ scope.row.permission_case_count || scope.row.permissionCaseCount || 0 }}</template></el-table-column>
            <el-table-column label="集成" width="70"><template slot-scope="scope">{{ scope.row.integration_case_count || scope.row.integrationCaseCount || 0 }}</template></el-table-column>
            <el-table-column label="总数" width="70"><template slot-scope="scope">{{ scope.row.case_count || scope.row.caseCount || 0 }}</template></el-table-column>
            <el-table-column label="设计h" width="80"><template slot-scope="scope">{{ scope.row.case_design_hours || scope.row.caseDesignHours || 0 }}</template></el-table-column>
            <el-table-column label="QA h" width="80"><template slot-scope="scope">{{ scope.row.qa_execution_hours || scope.row.qaExecutionHours || 0 }}</template></el-table-column>
            <el-table-column label="Token" width="100"><template slot-scope="scope">{{ scope.row.estimated_tokens || scope.row.estimatedTokens || 0 }}</template></el-table-column>
            <el-table-column label="风险" width="90"><template slot-scope="scope"><el-tag size="mini" :type="complexityTag(scope.row.risk_level || scope.row.riskLevel)">{{ complexityLabel(scope.row.risk_level || scope.row.riskLevel) }}</el-tag></template></el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">风险与假设</div>
          <div class="tag-block">
            <el-tag v-for="item in resultSummary.risks || []" :key="'risk-' + item" type="danger" size="small">{{ item }}</el-tag>
            <el-tag v-for="item in resultSummary.assumptions || []" :key="'assumption-' + item" type="info" size="small">{{ item }}</el-tag>
          </div>
        </el-card>
      </div>
    </page-section>

    <el-dialog title="分配负责人" :visible.sync="assignDialogVisible" width="420px">
      <el-form label-width="90px" size="small">
        <el-form-item label="负责人">
          <el-select v-model="assignForm.ownerId" clearable filterable placeholder="选择项目成员" style="width:100%;" :loading="memberLoading">
            <el-option v-for="item in memberOptions" :key="item.user_id" :label="memberLabel(item)" :value="String(item.user_id)" />
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="assignDialogVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="assignSaving" @click="saveAssign">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProjectMembers } from '@/api/projectApi'
import { assignWorkloadEstimateOwner, confirmWorkloadEstimate, executeWorkloadEstimate, exportWorkloadEstimateExcel, getWorkloadEstimateDetail, retryWorkloadEstimate } from '@/api/aiWorkloadEstimateApi'

const STATUSES = { draft: '草稿', estimating: '预估中', completed: '已完成', failed: '失败', confirmed: '已确认', archived: '已归档' }
const COMPLEXITIES = { low: '低', medium: '中', high: '高' }
const CONFIDENCES = { low: '低', medium: '中', high: '高' }

export default {
  name: 'AiWorkloadEstimateDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      executeLoading: false,
      retryLoading: false,
      confirmLoading: false,
      exportLoading: false,
      assignDialogVisible: false,
      assignSaving: false,
      memberLoading: false,
      detail: {},
      memberOptions: [],
      assignForm: { ownerId: '' }
    }
  },
  computed: {
    estimateId() { return this.$route.query.id },
    estimate() { return this.detail.estimate || {} },
    modules() { return this.detail.modules || [] },
    functions() { return this.detail.functions || [] },
    prdSnapshot() { return this.detail.prdSnapshot || this.detail.prd_snapshot || [] },
    referenceSummary() { return this.detail.referenceSummary || this.detail.reference_summary || {} },
    resultSummary() { return this.detail.resultSummary || this.detail.result_summary || {} },
    stageHours() { return this.resultSummary.stageHours || [] },
    tokenLines() { return this.resultSummary.tokenLines || [] },
    agentRounds() { return this.resultSummary.agentRounds || [] },
    agentSummary() { return this.resultSummary.agentSummary || {} },
    rangeRows() {
      return [
        { name: '功能用例数', description: '正常档按功能点明细汇总', range: this.resultSummary.caseCountRange },
        { name: '人工测试工时', description: '固定5阶段合计，单位：小时', range: this.resultSummary.totalEffortRange },
        { name: 'AI token总量', description: '固定6环节合计', range: this.resultSummary.tokenRange },
        { name: 'Token成本(元)', description: '默认按15元/百万token', range: this.resultSummary.tokenCostRange }
      ].map(item => ({
        name: item.name,
        optimistic: this.rangeValue(item.range, 'optimistic'),
        normal: this.rangeValue(item.range, 'normal'),
        pessimistic: this.rangeValue(item.range, 'pessimistic'),
        description: item.description
      }))
    }
  },
  created() {
    this.fetchDetail()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    fetchDetail() {
      this.loading = true
      getWorkloadEstimateDetail({ estimateId: this.estimateId }).then(res => {
        const d = this.apiData(res)
        this.detail = d.estimate ? d : { estimate: d, modules: d.modules || [], functions: d.functions || [] }
      }).finally(() => { this.loading = false })
    },
    executeEstimate() {
      this.executeLoading = true
      executeWorkloadEstimate({ estimateId: this.estimateId }).then(() => {
        this.$message.success('预估执行完成')
        this.fetchDetail()
      }).finally(() => { this.executeLoading = false })
    },
    retryEstimate() {
      this.retryLoading = true
      retryWorkloadEstimate({ estimateId: this.estimateId }).then(() => {
        this.$message.success('重新预估完成')
        this.fetchDetail()
      }).finally(() => { this.retryLoading = false })
    },
    confirmEstimate() {
      this.$prompt('请输入确认备注', '确认预估', { inputType: 'textarea' }).then(({ value }) => {
        this.confirmLoading = true
        return confirmWorkloadEstimate({ estimateId: this.estimateId, comment: value || '' })
      }).then(() => {
        this.$message.success('预估已确认')
        this.fetchDetail()
      }).catch(() => {}).finally(() => { this.confirmLoading = false })
    },
    exportExcel() {
      this.exportLoading = true
      exportWorkloadEstimateExcel({ estimateId: this.estimateId }).then(blob => {
        const title = this.safeFileName(this.estimate.title || this.estimate.estimate_no || this.estimate.estimateNo || 'AI工作量预估')
        const fileBlob = blob instanceof Blob ? blob : new Blob([blob], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const url = window.URL.createObjectURL(fileBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${title}-测试工时Token预估明细.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }).finally(() => { this.exportLoading = false })
    },
    openAssign() {
      this.assignForm.ownerId = String(this.estimate.owner_id || this.estimate.ownerId || '')
      this.assignDialogVisible = true
      this.loadMembers()
    },
    loadMembers() {
      const projectId = this.estimate.project_id || this.estimate.projectId
      if (!projectId) { this.memberOptions = []; return }
      this.memberLoading = true
      getProjectMembers(projectId, { pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.memberOptions = d.list || d.items || []
      }).finally(() => { this.memberLoading = false })
    },
    saveAssign() {
      this.assignSaving = true
      assignWorkloadEstimateOwner({ estimateId: this.estimateId, ownerId: this.assignForm.ownerId }).then(() => {
        this.$message.success('负责人已更新')
        this.assignDialogVisible = false
        this.fetchDetail()
      }).finally(() => { this.assignSaving = false })
    },
    memberLabel(item) { return item.real_name || item.username || ('用户' + item.user_id) },
    riskText(value) {
      if (!value) return '-'
      if (Array.isArray(value)) return value.join('，') || '-'
      if (typeof value === 'object') return JSON.stringify(value)
      return String(value)
    },
    rangeValue(range, key) {
      return range && range[key] !== undefined && range[key] !== null ? range[key] : 0
    },
    safeFileName(value) {
      return String(value || '').replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80) || 'AI工作量预估'
    },
    statusLabel(v) { return STATUSES[v] || v || '-' },
    statusTag(v) { return { draft: 'info', estimating: 'warning', completed: 'success', failed: 'danger', confirmed: 'success', archived: 'info' }[v] || 'info' },
    complexityLabel(v) { return COMPLEXITIES[v] || v || '-' },
    complexityTag(v) { return { low: 'success', medium: 'warning', high: 'danger' }[v] || 'info' },
    confidenceLabel(v) { return CONFIDENCES[v] || v || '-' }
  }
}
</script>

<style scoped>
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.summary-item { border: 1px solid #ebeef5; padding: 12px; border-radius: 4px; background: #fff; }
.summary-item span { display: block; color: #909399; font-size: 12px; margin-bottom: 8px; }
.summary-item b { font-size: 16px; color: #303133; }
.detail-card { margin-top: 14px; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border-top: 1px solid #ebeef5; border-left: 1px solid #ebeef5; }
.meta-item { display: grid; grid-template-columns: 110px minmax(0, 1fr); min-height: 40px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.meta-item span { padding: 10px 12px; color: #606266; background: #fafafa; }
.meta-item b { padding: 10px 12px; color: #303133; font-weight: 400; word-break: break-all; }
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.metric { border: 1px solid #ebeef5; border-radius: 4px; padding: 12px; background: #fafafa; }
.metric span { display: block; font-size: 12px; color: #909399; margin-bottom: 8px; }
.metric b { font-size: 18px; color: #303133; }
.summary-text { margin: 12px 0 0; color: #606266; line-height: 1.7; }
.reference-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tag-block { display: flex; gap: 8px; flex-wrap: wrap; }
.failure-alert { margin-top: 12px; }
.method-alert { margin-top: 12px; }
.agent-summary { display: flex; gap: 20px; flex-wrap: wrap; color: #606266; }
@media (max-width: 1200px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 768px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .meta-grid { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
