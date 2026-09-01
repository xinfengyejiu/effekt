<template>
  <div class="page-wrap asset-governance-page">
    <page-section title="测试资产治理">
      <template slot="extra">
        <el-button size="small" type="primary" icon="el-icon-plus" @click="openCreate">新建扫描</el-button>
      </template>

      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="选择产品" style="width:160px;" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="选择项目" style="width:160px;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width:130px;">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重等级">
          <el-select v-model="queryForm.riskLevel" clearable placeholder="全部" style="width:130px;">
            <el-option v-for="item in severityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题类型">
          <el-select v-model="queryForm.issueType" clearable placeholder="全部" style="width:150px;">
            <el-option v-for="item in issueTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
          <el-button icon="el-icon-refresh" :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="visibleRows" border style="width:100%; margin-top:12px;">
        <el-table-column label="扫描编号" min-width="170" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-link type="primary" @click="goDetail(scope.row)">{{ field(scope.row, 'scan_no', 'scanNo') }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.title || '-' }}</template>
        </el-table-column>
        <el-table-column label="产品" min-width="120" show-overflow-tooltip>
          <template slot-scope="scope">{{ field(scope.row, 'product_name', 'productName') || '-' }}</template>
        </el-table-column>
        <el-table-column label="项目" min-width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ field(scope.row, 'project_name', 'projectName') || '-' }}</template>
        </el-table-column>
        <el-table-column label="健康分" width="90">
          <template slot-scope="scope">
            <el-tag size="mini" :type="healthTag(healthScore(scope.row))">{{ healthScore(scope.row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="问题数" width="90">
          <template slot-scope="scope">{{ summary(scope.row).issueCount || 0 }}</template>
        </el-table-column>
        <el-table-column label="高风险" width="90">
          <template slot-scope="scope">{{ highRiskCount(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160" show-overflow-tooltip>
          <template slot-scope="scope">{{ field(scope.row, 'created_time', 'createdTime') || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" icon="el-icon-view" @click="goDetail(scope.row)">详情</el-button>
            <el-button type="text" icon="el-icon-caret-right" :loading="rowLoading(scope.row)" @click="executeScan(scope.row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="displayTotal" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </page-section>

    <el-dialog title="新建治理扫描" :visible.sync="createVisible" width="620px" :close-on-click-modal="false">
      <el-form ref="createForm" :model="createForm" :rules="createRules" label-width="100px" size="small">
        <el-form-item label="产品" prop="productId">
          <el-select v-model="createForm.productId" clearable filterable placeholder="选择产品" style="width:100%;" @change="onCreateProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="createForm.projectId" filterable :disabled="!createForm.productId" placeholder="选择项目" style="width:100%;">
            <el-option v-for="item in createProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="扫描标题" prop="title">
          <el-input v-model.trim="createForm.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="扫描类型">
          <el-select v-model="createForm.scanType" style="width:100%;">
            <el-option label="全量扫描" value="full" />
            <el-option label="快速扫描" value="quick" />
          </el-select>
        </el-form-item>
        <el-form-item label="过期天数">
          <el-input-number v-model="createForm.staleDays" :min="30" :max="720" :step="30" controls-position="right" style="width:180px;" />
        </el-form-item>
        <el-form-item label="重复阈值">
          <el-input-number v-model="createForm.duplicateThreshold" :min="0.9" :max="0.95" :step="0.01" :precision="2" controls-position="right" style="width:180px;" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="createVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="createLoading" @click="submitCreate">创建</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { createAssetGovernanceScan, executeAssetGovernanceScan, getAssetGovernanceScanList } from '@/api/testAssetGovernanceApi'

const STATUSES = [
  { value: 'pending', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'success', label: '已完成' },
  { value: 'failed', label: '失败' }
]
const SEVERITIES = [
  { value: 'critical', label: '严重' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' }
]
const ISSUE_TYPES = [
  { value: 'duplicate_case', label: '重复用例' },
  { value: 'weak_case', label: '低质量用例' },
  { value: 'stale_case', label: '过期用例' },
  { value: 'coverage_gap', label: '覆盖缺口' },
  { value: 'ai_suggestion', label: 'AI建议待处理' }
]

export default {
  name: 'TestAssetGovernanceScanList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      createVisible: false,
      createLoading: false,
      actionLoading: {},
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      productOptions: [],
      projectOptions: [],
      createProjectOptions: [],
      queryForm: { productId: '', projectId: '', status: '', riskLevel: '', issueType: '', keyword: '' },
      createForm: this.defaultCreateForm(),
      createRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        title: [{ required: true, message: '请输入扫描标题', trigger: 'blur' }]
      },
      statusOptions: STATUSES,
      severityOptions: SEVERITIES,
      issueTypeOptions: ISSUE_TYPES
    }
  },
  computed: {
    visibleRows() {
      return this.rows.filter(row => {
        const rowSummary = this.summary(row)
        if (this.queryForm.riskLevel && !((rowSummary.severityCounts || {})[this.queryForm.riskLevel] > 0)) return false
        if (this.queryForm.issueType && !((rowSummary.issueTypeCounts || {})[this.queryForm.issueType] > 0)) return false
        return true
      })
    },
    displayTotal() {
      return (this.queryForm.riskLevel || this.queryForm.issueType) ? this.visibleRows.length : this.total
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    defaultCreateForm() {
      return { productId: '', projectId: '', title: '', scanType: 'full', staleDays: 180, duplicateThreshold: 0.9 }
    },
    apiData(res) { return (res && res.data) || res || {} },
    field(row, snake, camel) { return row && row[snake] !== undefined ? row[snake] : row ? row[camel] : undefined },
    summary(row) { return this.field(row, 'summary_json', 'summaryJson') || {} },
    healthScore(row) {
      const summary = this.summary(row)
      const score = row.health_score !== undefined ? row.health_score : row.healthScore
      return score == null ? (summary.healthScore == null ? '-' : summary.healthScore) : score
    },
    highRiskCount(row) {
      const counts = this.summary(row).severityCounts || {}
      return (counts.critical || 0) + (counts.high || 0)
    },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        const data = this.apiData(res)
        this.productOptions = data.list || data.items || []
      })
    },
    loadProjects(productId, target) {
      if (!productId) {
        this[target] = []
        return
      }
      getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => {
        const data = this.apiData(res)
        this[target] = data.list || data.items || []
      })
    },
    onProductChange(productId) {
      this.queryForm.projectId = ''
      this.loadProjects(productId, 'projectOptions')
    },
    onCreateProductChange(productId) {
      this.createForm.projectId = ''
      this.loadProjects(productId, 'createProjectOptions')
    },
    fetchList() {
      this.loading = true
      const params = Object.assign({}, this.queryForm, { riskLevel: undefined, issueType: undefined, pageNo: this.pageNo, pageSize: this.pageSize })
      getAssetGovernanceScanList(params).then(res => {
        const data = this.apiData(res)
        this.rows = data.list || data.items || []
        this.total = data.total || this.rows.length
      }).finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', status: '', riskLevel: '', issueType: '', keyword: '' }
      this.projectOptions = []
      this.pageNo = 1
      this.fetchList()
    },
    handleSizeChange(value) {
      this.pageSize = value
      this.pageNo = 1
      this.fetchList()
    },
    handleCurrentChange(value) {
      this.pageNo = value
      this.fetchList()
    },
    openCreate() {
      this.createForm = this.defaultCreateForm()
      this.createProjectOptions = []
      this.createVisible = true
      this.$nextTick(() => { this.$refs.createForm && this.$refs.createForm.clearValidate() })
    },
    submitCreate() {
      this.$refs.createForm.validate(valid => {
        if (!valid) return
        this.createLoading = true
        createAssetGovernanceScan(Object.assign({}, this.createForm, {
          optionsJson: {
            staleDays: this.createForm.staleDays,
            duplicateThreshold: this.createForm.duplicateThreshold
          }
        })).then(res => {
          const data = this.apiData(res)
          const scanId = data.scanId || data.id
          this.$message.success('扫描已创建')
          this.createVisible = false
          if (scanId) {
            this.$router.push({ path: '/test-asset-governance/detail', query: { id: scanId } })
          } else {
            this.fetchList()
          }
        }).finally(() => { this.createLoading = false })
      })
    },
    goDetail(row) {
      this.$router.push({ path: '/test-asset-governance/detail', query: { id: row.id } })
    },
    rowLoading(row) {
      return !!this.actionLoading[row.id]
    },
    executeScan(row) {
      this.$set(this.actionLoading, row.id, true)
      executeAssetGovernanceScan({ scanId: row.id }).then(() => {
        this.$message.success('扫描执行完成')
        this.fetchList()
      }).finally(() => { this.$delete(this.actionLoading, row.id) })
    },
    statusLabel(value) { return (STATUSES.find(item => item.value === value) || {}).label || value || '-' },
    statusTag(value) { return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[value] || 'info' },
    healthTag(value) {
      const score = Number(value)
      if (Number.isNaN(score)) return 'info'
      if (score >= 85) return 'success'
      if (score >= 60) return 'warning'
      return 'danger'
    }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
@media (max-width: 768px) {
  .asset-governance-page /deep/ .el-dialog { width: 94% !important; }
}
</style>
