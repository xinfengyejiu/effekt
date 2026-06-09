<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-变更分析">
      <template slot="extra"><el-button size="small" type="primary" @click="openCreate">新建分析</el-button></template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品名称">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="请选择产品" style="width:180px;" @change="onQueryProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="请先选择产品" style="width:180px;">
            <el-option v-for="item in queryProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态"><el-select v-model="queryForm.status" clearable placeholder="全部" style="width:130px;"><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
        <el-form-item label="关键字"><el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" /></el-form-item>
        <el-form-item><el-button type="primary" :loading="loading" @click="fetchList">查询</el-button><el-button :disabled="loading" @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="分析编号" min-width="160" show-overflow-tooltip><template slot-scope="scope"><el-link type="primary" @click="goDetail(scope.row)">{{ scope.row.analysis_no || scope.row.analysisNo || scope.row.id }}</el-link></template></el-table-column>
        <el-table-column label="标题" min-width="180" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.title || '-' }}</template></el-table-column>
        <el-table-column label="产品名称" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ preciseProductName(scope.row) }}</template></el-table-column>
        <el-table-column label="项目名称" min-width="140" show-overflow-tooltip><template slot-scope="scope">{{ preciseProjectName(scope.row) }}</template></el-table-column>
        <el-table-column label="分支" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.branch_name || scope.row.branchName || '-' }}</template></el-table-column>
        <el-table-column label="Base" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.base_commit || scope.row.baseCommit || '-' }}</template></el-table-column>
        <el-table-column label="Target" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.target_commit || scope.row.targetCommit || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="100"><template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="风险" width="90"><template slot-scope="scope"><el-tag size="mini" :type="riskTag(scope.row.risk_level || scope.row.riskLevel)">{{ scope.row.risk_level || scope.row.riskLevel || '-' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="350" fixed="right"><template slot-scope="scope"><el-button type="text" @click="goDetail(scope.row)">详情</el-button><el-button type="text" :loading="isRowActionLoading(scope.row, 'parse')" :disabled="isRowBusy(scope.row)" @click="parseDiff(scope.row)">解析变更</el-button><el-button type="text" :loading="isRowActionLoading(scope.row, 'ai')" :disabled="isRowBusy(scope.row)" @click="aiImpact(scope.row)">AI分析</el-button><el-button type="text" :loading="isRowActionLoading(scope.row, 'recommend')" :disabled="isRowBusy(scope.row)" @click="recommend(scope.row)">推荐回归</el-button></template></el-table-column>
      </el-table>
      <div class="pager-wrap"><el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" /></div>
    </page-section>

    <el-dialog title="新建变更分析" :visible.sync="dialogVisible" width="720px">
      <el-form ref="createForm" :model="form" :rules="rules" label-width="120px" size="small">
        <el-form-item label="产品名称" prop="productId">
          <el-select v-model="form.productId" clearable filterable placeholder="请选择产品" style="width:100%;" @change="onFormProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="projectId">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="请先选择产品" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model.trim="form.title" /></el-form-item>
        <el-form-item label="Git仓库" prop="repositoryUrl"><el-input v-model.trim="form.repositoryUrl" placeholder="本地仓库路径或远程仓库地址" /></el-form-item>
        <el-form-item label="目标分支"><el-input v-model.trim="form.branchName" placeholder="main/master，可选" /></el-form-item>
        <el-form-item label="Base Commit" prop="baseCommit"><el-input v-model.trim="form.baseCommit" /></el-form-item>
        <el-form-item label="Target Commit" prop="targetCommit"><el-input v-model.trim="form.targetCommit" /></el-form-item>
        <el-form-item label="变更说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submitCreate">保存</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPreciseAnalysisList, createPreciseAnalysis, parsePreciseDiff, createPreciseAiImpact, generatePreciseRecommendations } from '@/api/preciseTestApi'
import productProjectSelectMixin from './productProjectSelectMixin'
const STATUS = { 1: '待解析', 2: '已解析', 3: 'AI已分析', 4: '已推荐', 5: '执行中', 6: '已完成' }
export default {
  name: 'PreciseAnalysisList',
  components: { PageSection },
  mixins: [productProjectSelectMixin],
  data() { return { loading: false, saving: false, dialogVisible: false, rows: [], total: 0, pageNo: 1, pageSize: 20, rowActionLoading: {}, queryForm: { productId: '', projectId: '', status: '', keyword: '' }, statusOptions: Object.keys(STATUS).map(k => ({ value: Number(k), label: STATUS[k] })), form: {}, rules: { productId: [{ required: true, message: '请选择产品名称', trigger: 'change' }], projectId: [{ required: true, message: '请选择项目名称', trigger: 'change' }], repositoryUrl: [{ required: true, message: '请输入Git仓库', trigger: 'blur' }], baseCommit: [{ required: true, message: '请输入Base Commit', trigger: 'blur' }], targetCommit: [{ required: true, message: '请输入Target Commit', trigger: 'blur' }] } } },
  created() { this.fetchList() },
  methods: {
    listOf(res) { const d = res && res.data ? res.data : res || {}; return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 } },
    fetchList() { this.loading = true; getPreciseAnalysisList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => { const d = this.listOf(res); this.rows = d.rows; this.total = d.total || this.rows.length; this.fillPreciseProjectNames(this.rows) }).finally(() => { this.loading = false }) },
    resetQuery() { this.queryForm = { productId: '', projectId: '', status: '', keyword: '' }; this.queryProjectOptions = []; this.pageNo = 1; this.fetchList() },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    onQueryProductChange(productId) { this.queryForm.projectId = ''; this.loadProjectOptions(productId, 'queryProjectOptions') },
    onFormProductChange(productId) { this.form.projectId = ''; this.loadProjectOptions(productId, 'projectOptions') },
    openCreate() { this.form = { productId: '', projectId: '' }; this.projectOptions = []; this.dialogVisible = true },
    submitCreate() { this.$refs.createForm.validate(valid => { if (!valid) return; this.saving = true; createPreciseAnalysis(this.buildPreciseProjectPayload(this.form)).then(() => { this.$message.success('创建成功'); this.dialogVisible = false; this.fetchList() }).finally(() => { this.saving = false }) }) },
    goDetail(row) { this.$router.push({ path: '/precise/analysis/detail', query: { id: row.id } }) },
    rowActionKey(row, action) { return String(row.id) + ':' + action },
    isRowActionLoading(row, action) { return !!this.rowActionLoading[this.rowActionKey(row, action)] },
    isRowBusy(row) { return ['parse', 'ai', 'recommend'].some(action => this.isRowActionLoading(row, action)) },
    runRowAction(row, action, request) {
      const key = this.rowActionKey(row, action)
      if (this.rowActionLoading[key]) return Promise.resolve()
      this.$set(this.rowActionLoading, key, true)
      return request().finally(() => { this.$delete(this.rowActionLoading, key) })
    },
    parseDiff(row) { this.runRowAction(row, 'parse', () => parsePreciseDiff(row.id).then(() => { this.$message.success('解析完成'); this.fetchList() })) },
    aiImpact(row) { this.runRowAction(row, 'ai', () => createPreciseAiImpact(row.id).then(() => { this.$message.success('AI影响分析完成'); this.fetchList() })) },
    recommend(row) { this.runRowAction(row, 'recommend', () => generatePreciseRecommendations(row.id).then(() => { this.$message.success('回归推荐已生成'); this.$router.push({ path: '/precise/recommendation', query: { analysisId: row.id } }) })) },
    statusLabel(s) { return STATUS[s] || (s == null ? '-' : String(s)) },
    statusTag(s) { return { 1: 'info', 2: 'primary', 3: 'warning', 4: 'success', 5: 'warning', 6: 'success' }[s] || 'info' },
    riskTag(v) { return { high: 'danger', medium: 'warning', low: 'success' }[String(v || '').toLowerCase()] || 'info' }
  }
}
</script>

<style scoped>.pager-wrap{margin-top:16px;text-align:right;}</style>
