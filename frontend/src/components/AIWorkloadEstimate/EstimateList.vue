<template>
  <div class="page-wrap ai-workload-estimate-page">
    <page-section title="AI工作量预估">
      <template slot="extra">
        <el-button size="small" type="primary" @click="$router.push({ path: '/ai-workload-estimate/create' })">新建预估</el-button>
      </template>

        <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品名称">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="选择产品" style="width:150px;" :loading="productLoading" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="选择项目" style="width:150px;" :loading="projectLoading">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model.trim="queryForm.ownerName" clearable placeholder="模糊搜索" style="width:130px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable placeholder="编号/标题" style="width:150px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width:130px;">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="复杂度">
          <el-select v-model="queryForm.complexityLevel" clearable placeholder="全部" style="width:120px;">
            <el-option v-for="item in complexityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="yyyy-MM-dd" style="width:240px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchList">查询</el-button>
          <el-button :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="预估编号" min-width="170" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-link type="primary" @click="goDetail(scope.row)">{{ field(scope.row, 'estimate_no', 'estimateNo') }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.title || '-' }}</template></el-table-column>
        <el-table-column label="产品名称" min-width="130" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'product_name', 'productName') || '-' }}</template></el-table-column>
        <el-table-column label="项目名称" min-width="140" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'project_name', 'projectName') || '-' }}</template></el-table-column>
        <el-table-column label="负责人" width="110" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.ownerNameDisplay || field(scope.row, 'owner_name', 'ownerName') || '未分配' }}</template></el-table-column>
        <el-table-column label="PRD数" width="80"><template slot-scope="scope">{{ scope.row.documentCount || 0 }}</template></el-table-column>
        <el-table-column label="功能点" width="80"><template slot-scope="scope">{{ field(scope.row, 'total_function_points', 'totalFunctionPoints') || 0 }}</template></el-table-column>
        <el-table-column label="用例数" width="80"><template slot-scope="scope">{{ field(scope.row, 'total_case_count', 'totalCaseCount') || 0 }}</template></el-table-column>
        <el-table-column label="设计h" width="90"><template slot-scope="scope">{{ field(scope.row, 'case_design_hours', 'caseDesignHours') || 0 }}</template></el-table-column>
        <el-table-column label="QA h" width="90"><template slot-scope="scope">{{ field(scope.row, 'qa_execution_hours', 'qaExecutionHours') || 0 }}</template></el-table-column>
        <el-table-column label="总h" width="90"><template slot-scope="scope">{{ field(scope.row, 'total_effort_hours', 'totalEffortHours') || 0 }}</template></el-table-column>
        <el-table-column label="Token" width="110"><template slot-scope="scope">{{ field(scope.row, 'estimated_tokens', 'estimatedTokens') || 0 }}</template></el-table-column>
        <el-table-column label="复杂度" width="90"><template slot-scope="scope"><el-tag size="mini" :type="complexityTag(field(scope.row, 'complexity_level', 'complexityLevel'))">{{ complexityLabel(field(scope.row, 'complexity_level', 'complexityLevel')) }}</el-tag></template></el-table-column>
        <el-table-column label="置信度" width="90"><template slot-scope="scope">{{ confidenceLabel(scope.row.confidence) }}</template></el-table-column>
        <el-table-column label="状态" width="100"><template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="创建时间" min-width="160" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'created_time', 'createdTime') || '-' }}</template></el-table-column>
        <el-table-column label="操作" width="380" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row)">详情</el-button>
            <el-button type="text" :loading="rowLoading(scope.row, 'execute')" @click="executeEstimate(scope.row)">执行</el-button>
            <el-button type="text" :loading="rowLoading(scope.row, 'retry')" @click="retryEstimate(scope.row)">重估</el-button>
            <el-button type="text" @click="openAssign(scope.row)">分配</el-button>
            <el-button type="text" @click="openActual(scope.row)">真实数据</el-button>
            <el-button type="text" :loading="rowLoading(scope.row, 'confirm')" @click="confirmEstimate(scope.row)">确认</el-button>
            <el-button type="text" style="color:#f56c6c;" :loading="rowLoading(scope.row, 'delete')" @click="deleteEstimate(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
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

    <el-dialog title="维护真实数据" :visible.sync="actualDialogVisible" width="660px">
      <el-alert class="actual-alert" type="info" :closable="false" title="真实数据用于后续校准预估模型；未填写的字段按0保存，总工时未填写时会按各阶段实际工时自动汇总。" />
      <el-form label-width="130px" size="small" class="actual-form">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="实际用例数">
              <el-input-number v-model="actualForm.actualCaseCount" :min="0" :step="1" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际Token">
              <el-input-number v-model="actualForm.actualTokens" :min="0" :step="1000" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="需求梳理h">
              <el-input-number v-model="actualForm.actualRequirementAnalysisHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用例设计h">
              <el-input-number v-model="actualForm.actualCaseDesignHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="QA执行h">
              <el-input-number v-model="actualForm.actualQaExecutionHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上线验证h">
              <el-input-number v-model="actualForm.actualReleaseVerificationHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="培训文档h">
              <el-input-number v-model="actualForm.actualTrainingDocHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际总h">
              <el-input-number v-model="actualForm.actualTotalEffortHours" :min="0" :step="0.5" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Agent Rounds">
              <el-input-number v-model="actualForm.actualAgentRounds" :min="0" :step="1" controls-position="right" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="actualForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="actualDialogVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="actualSaving" @click="saveActual">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectMembers } from '@/api/projectApi'
import { getProjectList } from '@/api/projectApi'
import { assignWorkloadEstimateOwner, confirmWorkloadEstimate, deleteWorkloadEstimate, executeWorkloadEstimate, getWorkloadEstimateList, retryWorkloadEstimate, saveWorkloadEstimateActual } from '@/api/aiWorkloadEstimateApi'

const STATUSES = [
  { value: 'draft', label: '草稿' },
  { value: 'estimating', label: '预估中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'confirmed', label: '已确认' },
  { value: 'archived', label: '已归档' }
]
const COMPLEXITIES = [{ value: 'low', label: '低' }, { value: 'medium', label: '中' }, { value: 'high', label: '高' }]
const CONFIDENCES = { low: '低', medium: '中', high: '高' }

export default {
  name: 'AiWorkloadEstimateList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      dateRange: [],
      actionLoading: {},
      assignDialogVisible: false,
      assignSaving: false,
      actualDialogVisible: false,
      actualSaving: false,
      productLoading: false,
      projectLoading: false,
      memberLoading: false,
      productOptions: [],
      projectOptions: [],
      memberOptions: [],
      assignRow: null,
      actualRow: null,
      assignForm: { ownerId: '' },
      actualForm: this.emptyActualForm(),
      queryForm: { productId: '', projectId: '', ownerName: '', ownerId: '', status: '', complexityLevel: '', keyword: '' },
      statusOptions: STATUSES,
      complexityOptions: COMPLEXITIES
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    field(row, snake, camel) { return row && row[snake] !== undefined ? row[snake] : row ? row[camel] : undefined },
    loadProducts() {
      this.productLoading = true
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.productOptions = d.list || d.items || []
      }).finally(() => { this.productLoading = false })
    },
    loadProjects(productId) {
      if (!productId) { this.projectOptions = []; return }
      this.projectLoading = true
      getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.projectOptions = d.list || d.items || []
      }).finally(() => { this.projectLoading = false })
    },
    onProductChange(productId) {
      this.queryForm.projectId = ''
      this.projectOptions = []
      this.loadProjects(productId)
    },
    fetchList() {
      this.loading = true
      const params = Object.assign({}, this.queryForm, {
        pageNo: this.pageNo,
        pageSize: this.pageSize,
        startTime: this.dateRange && this.dateRange[0] ? this.dateRange[0] + ' 00:00:00' : '',
        endTime: this.dateRange && this.dateRange[1] ? this.dateRange[1] + ' 23:59:59' : ''
      })
      getWorkloadEstimateList(params).then(res => {
        const d = this.apiData(res)
        this.rows = d.list || d.items || []
        this.total = d.total || this.rows.length
      }).finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', ownerName: '', ownerId: '', status: '', complexityLevel: '', keyword: '' }
      this.projectOptions = []
      this.dateRange = []
      this.pageNo = 1
      this.fetchList()
    },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    goDetail(row) { this.$router.push({ path: '/ai-workload-estimate/detail', query: { id: row.id } }) },
    actionKey(row, action) { return row.id + ':' + action },
    rowLoading(row, action) { return !!this.actionLoading[this.actionKey(row, action)] },
    runAction(row, action, fn) {
      const key = this.actionKey(row, action)
      this.$set(this.actionLoading, key, true)
      return fn().finally(() => { this.$delete(this.actionLoading, key) })
    },
    executeEstimate(row) { this.runAction(row, 'execute', () => executeWorkloadEstimate({ estimateId: row.id }).then(() => { this.$message.success('预估执行完成'); this.fetchList() })) },
    retryEstimate(row) { this.runAction(row, 'retry', () => retryWorkloadEstimate({ estimateId: row.id }).then(() => { this.$message.success('重新预估完成'); this.fetchList() })) },
    confirmEstimate(row) { this.runAction(row, 'confirm', () => confirmWorkloadEstimate({ estimateId: row.id }).then(() => { this.$message.success('预估已确认'); this.fetchList() })) },
    openAssign(row) {
      this.assignRow = row
      this.assignForm.ownerId = String(this.field(row, 'owner_id', 'ownerId') || '')
      this.assignDialogVisible = true
      this.loadMembers(row)
    },
    loadMembers(row) {
      const projectId = this.field(row, 'project_id', 'projectId')
      if (!projectId) { this.memberOptions = []; return }
      this.memberLoading = true
      getProjectMembers(projectId, { pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.memberOptions = d.list || d.items || []
      }).finally(() => { this.memberLoading = false })
    },
    saveAssign() {
      if (!this.assignRow) return
      this.assignSaving = true
      assignWorkloadEstimateOwner({ estimateId: this.assignRow.id, ownerId: this.assignForm.ownerId }).then(() => {
        this.$message.success('负责人已更新')
        this.assignDialogVisible = false
        this.fetchList()
      }).finally(() => { this.assignSaving = false })
    },
    memberLabel(item) { return item.real_name || item.username || ('用户' + item.user_id) },
    emptyActualForm() {
      return {
        actualCaseCount: 0,
        actualRequirementAnalysisHours: 0,
        actualCaseDesignHours: 0,
        actualQaExecutionHours: 0,
        actualReleaseVerificationHours: 0,
        actualTrainingDocHours: 0,
        actualTotalEffortHours: 0,
        actualTokens: 0,
        actualAgentRounds: 0,
        remark: ''
      }
    },
    parseSummary(row) {
      const value = this.field(row, 'result_summary', 'resultSummary') || {}
      if (typeof value === 'string') {
        try { return JSON.parse(value) } catch (e) { return {} }
      }
      return value || {}
    },
    actualData(row) {
      const summary = this.parseSummary(row)
      return summary.actualData || {}
    },
    numberValue(value) {
      const num = Number(value)
      return Number.isFinite(num) ? num : 0
    },
    openActual(row) {
      this.actualRow = row
      const data = this.actualData(row)
      this.actualForm = Object.assign(this.emptyActualForm(), {
        actualCaseCount: this.numberValue(data.actualCaseCount),
        actualRequirementAnalysisHours: this.numberValue(data.actualRequirementAnalysisHours),
        actualCaseDesignHours: this.numberValue(data.actualCaseDesignHours),
        actualQaExecutionHours: this.numberValue(data.actualQaExecutionHours),
        actualReleaseVerificationHours: this.numberValue(data.actualReleaseVerificationHours),
        actualTrainingDocHours: this.numberValue(data.actualTrainingDocHours),
        actualTotalEffortHours: this.numberValue(data.actualTotalEffortHours),
        actualTokens: this.numberValue(data.actualTokens),
        actualAgentRounds: this.numberValue(data.actualAgentRounds),
        remark: data.remark || ''
      })
      this.actualDialogVisible = true
    },
    saveActual() {
      if (!this.actualRow) return
      this.actualSaving = true
      saveWorkloadEstimateActual(Object.assign({ estimateId: this.actualRow.id }, this.actualForm)).then(() => {
        this.$message.success('真实数据已保存')
        this.actualDialogVisible = false
        this.fetchList()
      }).finally(() => { this.actualSaving = false })
    },
    deleteEstimate(row) {
      this.$confirm('删除后列表将不再展示该预估记录，是否继续？', '删除预估', { type: 'warning' }).then(() => {
        this.runAction(row, 'delete', () => deleteWorkloadEstimate({ estimateId: row.id }).then(() => {
          this.$message.success('删除成功')
          this.fetchList()
        }))
      }).catch(() => {})
    },
    statusLabel(v) { return (STATUSES.find(item => item.value === v) || {}).label || v || '-' },
    statusTag(v) { return { draft: 'info', estimating: 'warning', completed: 'success', failed: 'danger', confirmed: 'success', archived: 'info' }[v] || 'info' },
    complexityLabel(v) { return (COMPLEXITIES.find(item => item.value === v) || {}).label || v || '-' },
    complexityTag(v) { return { low: 'success', medium: 'warning', high: 'danger' }[v] || 'info' },
    confidenceLabel(v) { return CONFIDENCES[v] || v || '-' }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
</style>
