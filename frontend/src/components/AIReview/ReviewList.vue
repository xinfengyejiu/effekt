<template>
  <div class="page-wrap ai-review-page">
    <page-section title="AI测试评审">
      <template slot="extra">
        <el-button size="small" type="primary" @click="$router.push({ path: '/ai-review/create' })">新建评审</el-button>
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
        <el-form-item label="类型">
          <el-select v-model="queryForm.reviewType" clearable placeholder="全部" style="width:140px;">
            <el-option v-for="item in reviewTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="queryForm.sourceType" clearable placeholder="全部" style="width:150px;">
            <el-option v-for="item in sourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width:130px;">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险">
          <el-select v-model="queryForm.riskLevel" clearable placeholder="全部" style="width:120px;">
            <el-option v-for="item in riskOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:160px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchList">查询</el-button>
          <el-button :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="评审编号" min-width="170" show-overflow-tooltip>
          <template slot-scope="scope"><el-link type="primary" @click="goDetail(scope.row)">{{ field(scope.row, 'review_no', 'reviewNo') }}</el-link></template>
        </el-table-column>
        <el-table-column label="标题" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.title || '-' }}</template></el-table-column>
        <el-table-column label="产品" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'product_name', 'productName') || '-' }}</template></el-table-column>
        <el-table-column label="项目" min-width="140" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'project_name', 'projectName') || '-' }}</template></el-table-column>
        <el-table-column label="类型" width="110"><template slot-scope="scope">{{ reviewTypeLabel(field(scope.row, 'review_type', 'reviewType')) }}</template></el-table-column>
        <el-table-column label="来源" width="130"><template slot-scope="scope">{{ sourceTypeLabel(field(scope.row, 'source_type', 'sourceType')) }}</template></el-table-column>
        <el-table-column label="风险" width="100"><template slot-scope="scope"><el-tag size="mini" :type="riskTag(field(scope.row, 'risk_level', 'riskLevel'))">{{ field(scope.row, 'risk_level', 'riskLevel') || '-' }}</el-tag></template></el-table-column>
        <el-table-column label="评分" width="80"><template slot-scope="scope">{{ scope.row.score == null ? '-' : scope.row.score }}</template></el-table-column>
        <el-table-column label="状态" width="110"><template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="创建时间" min-width="160" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'created_time', 'createdTime') || '-' }}</template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row)">详情</el-button>
            <el-button type="text" :loading="rowLoading(scope.row, 'execute')" @click="executeReview(scope.row)">执行</el-button>
            <el-button type="text" :loading="rowLoading(scope.row, 'confirm')" @click="confirmReview(scope.row)">确认</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { getAiReviewList, executeAiReview, confirmAiReview } from '@/api/aiReviewApi'

const REVIEW_TYPES = [
  { value: 'requirement', label: '需求评审' },
  { value: 'change', label: '变更评审' },
  { value: 'case', label: '用例评审' },
  { value: 'bug', label: '缺陷评审' },
  { value: 'release', label: '发布评审' }
]
const SOURCE_TYPES = [
  { value: 'manual', label: '手工输入' },
  { value: 'document', label: '需求文档' },
  { value: 'precise_analysis', label: '精准测试' },
  { value: 'case', label: '测试用例' },
  { value: 'bug', label: '缺陷' },
  { value: 'release', label: '发布' }
]
const STATUSES = [
  { value: 'pending', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'success', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'confirmed', label: '已确认' }
]

export default {
  name: 'AiReviewList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      actionLoading: {},
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      productOptions: [],
      projectOptions: [],
      queryForm: { productId: '', projectId: '', reviewType: '', sourceType: '', status: '', riskLevel: '', keyword: '' },
      reviewTypeOptions: REVIEW_TYPES,
      sourceTypeOptions: SOURCE_TYPES,
      statusOptions: STATUSES,
      riskOptions: [{ value: 'low', label: '低' }, { value: 'medium', label: '中' }, { value: 'high', label: '高' }, { value: 'critical', label: '严重' }]
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    field(row, snake, camel) { return row[snake] !== undefined ? row[snake] : row[camel] },
    loadProducts() { getProductList({ pageNo: 1, pageSize: 200 }).then(res => { const d = this.apiData(res); this.productOptions = d.list || d.items || [] }) },
    loadProjects(productId) { if (!productId) { this.projectOptions = []; return }; getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => { const d = this.apiData(res); this.projectOptions = d.list || d.items || [] }) },
    onProductChange(productId) { this.queryForm.projectId = ''; this.loadProjects(productId) },
    fetchList() {
      this.loading = true
      getAiReviewList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => {
        const d = this.apiData(res)
        this.rows = d.list || d.items || []
        this.total = d.total || this.rows.length
      }).finally(() => { this.loading = false })
    },
    resetQuery() { this.queryForm = { productId: '', projectId: '', reviewType: '', sourceType: '', status: '', riskLevel: '', keyword: '' }; this.projectOptions = []; this.pageNo = 1; this.fetchList() },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    goDetail(row) { this.$router.push({ path: '/ai-review/detail', query: { id: row.id } }) },
    actionKey(row, action) { return row.id + ':' + action },
    rowLoading(row, action) { return !!this.actionLoading[this.actionKey(row, action)] },
    runAction(row, action, fn) {
      const key = this.actionKey(row, action)
      this.$set(this.actionLoading, key, true)
      return fn().finally(() => { this.$delete(this.actionLoading, key) })
    },
    executeReview(row) { this.runAction(row, 'execute', () => executeAiReview({ reviewId: row.id }).then(() => { this.$message.success('评审执行完成'); this.fetchList() })) },
    confirmReview(row) { this.runAction(row, 'confirm', () => confirmAiReview({ reviewId: row.id }).then(() => { this.$message.success('评审已确认'); this.fetchList() })) },
    reviewTypeLabel(v) { return (REVIEW_TYPES.find(item => item.value === v) || {}).label || v || '-' },
    sourceTypeLabel(v) { return (SOURCE_TYPES.find(item => item.value === v) || {}).label || v || '-' },
    statusLabel(v) { return (STATUSES.find(item => item.value === v) || {}).label || v || '-' },
    statusTag(v) { return { pending: 'info', running: 'warning', success: 'success', failed: 'danger', confirmed: 'primary' }[v] || 'info' },
    riskTag(v) { return { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }[String(v || '').toLowerCase()] || 'info' }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
</style>
