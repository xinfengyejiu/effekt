<template>
  <div class="page-wrap performance-page">
    <page-section title="性能场景">
      <template slot="extra">
        <el-button size="small" @click="openUploadScript">上传脚本</el-button>
        <el-button size="small" type="primary" @click="openCreate">新建场景</el-button>
      </template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable placeholder="场景名称/编码" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width: 120px;">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width: 100%; margin-top: 12px;">
        <el-table-column prop="name" label="场景名称" min-width="160" />
        <el-table-column prop="code" label="场景编码" min-width="140" />
        <el-table-column label="环境" width="100">
          <template slot-scope="scope">{{ scope.row.env_code || scope.row.envCode || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template slot-scope="scope">
            <el-tag size="mini" :type="Number(scope.row.status) === 1 ? 'success' : 'info'">{{ Number(scope.row.status) === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template slot-scope="scope">{{ scope.row.created_time || scope.row.createdTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
            <el-button type="text" @click="openScript(scope.row)">脚本资产</el-button>
            <el-button type="text" @click="goRun(scope.row)">发起压测</el-button>
            <el-button type="text" style="color:#F56C6C;" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10, 20, 50, 100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </page-section>

    <el-dialog :title="dialogMode === 'create' ? '新建性能场景' : '编辑性能场景'" :visible.sync="dialogVisible" width="560px" @close="resetForm">
      <el-form ref="form" :model="form" :rules="rules" label-width="96px" size="small">
        <el-form-item label="产品名称">
          <el-select v-model="form.productId" clearable filterable placeholder="请选择产品" style="width:100%;" @change="handleProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="请先选择产品" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="场景名称" prop="name"><el-input v-model.trim="form.name" maxlength="128" /></el-form-item>
        <el-form-item label="场景编码" prop="code"><el-input v-model.trim="form.code" maxlength="64" :disabled="dialogMode === 'edit'" /></el-form-item>
        <el-form-item label="环境编码"><el-input v-model.trim="form.envCode" maxlength="32" placeholder="dev/st/pre/prod" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status" style="width:100%;"><el-option label="启用" :value="1" /><el-option label="禁用" :value="0" /></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model.trim="form.description" type="textarea" :rows="4" maxlength="500" show-word-limit /></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="dialogVisible = false">取消</el-button><el-button size="small" type="primary" :loading="submitting" @click="submitForm">确定</el-button></span>
    </el-dialog>

    <el-dialog title="上传脚本" :visible.sync="uploadDialogVisible" width="620px" @close="resetUploadForm">
      <el-form ref="uploadForm" :model="uploadForm" :rules="uploadRules" label-width="96px" size="small">
        <el-form-item label="产品名称" prop="productId">
          <el-select v-model="uploadForm.productId" clearable filterable placeholder="请选择产品" style="width:100%;" @change="handleUploadProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="projectId">
          <el-select v-model="uploadForm.projectId" clearable filterable :disabled="!uploadForm.productId" placeholder="请先选择产品" style="width:100%;" @change="handleUploadProjectChange">
            <el-option v-for="item in uploadProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="性能场景" prop="scenarioId">
          <el-select v-model="uploadForm.scenarioId" clearable filterable :disabled="!uploadForm.projectId" placeholder="请选择性能场景" style="width:100%;">
            <el-option v-for="item in uploadScenarioOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具方式" prop="toolType">
          <el-select v-model="uploadForm.toolType" style="width:100%;">
            <el-option label="JMeter" value="jmeter" />
            <el-option label="k6" value="k6" />
            <el-option label="Locust" value="locust" />
          </el-select>
        </el-form-item>
        <el-form-item label="脚本名称" prop="name"><el-input v-model.trim="uploadForm.name" maxlength="128" placeholder="默认取文件名" /></el-form-item>
        <el-form-item label="脚本文件" prop="file">
          <el-upload action="" :auto-upload="false" :limit="1" :file-list="uploadFiles" :on-change="handleUploadFileChange" :on-remove="handleUploadFileRemove">
            <el-button size="small">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="uploadDialogVisible = false">取消</el-button><el-button size="small" type="primary" :loading="uploadSubmitting" @click="submitUploadScript">上传</el-button></span>
    </el-dialog>

    <el-dialog title="脚本资产" :visible.sync="scriptDialogVisible" width="820px">
      <div class="dialog-title-line">{{ currentScenario ? currentScenario.name : '' }}</div>
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="脚本名称"><el-input v-model.trim="scriptForm.name" placeholder="脚本名称" /></el-form-item>
        <el-form-item label="工具"><el-select v-model="scriptForm.toolType" style="width:120px;"><el-option label="JMeter" value="jmeter" /><el-option label="k6" value="k6" /><el-option label="Locust" value="locust" /></el-select></el-form-item>
        <el-form-item label="脚本文件">
          <el-upload action="" :auto-upload="false" :limit="1" :file-list="scriptFiles" :on-change="handleScriptFileChange" :on-remove="handleScriptFileRemove">
            <el-button size="small">选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item><el-button type="primary" :loading="scriptSubmitting" @click="submitScript">上传脚本</el-button></el-form-item>
      </el-form>
      <el-input v-model.trim="nlPrompt" type="textarea" :rows="3" placeholder="输入自然语言压测目标，生成结构化压测方案" />
      <div class="action-line"><el-button size="small" :loading="planLoading" @click="generatePlan">生成方案</el-button><el-button size="small" type="primary" :loading="scriptLoading" @click="generateScript">人工确认后生成脚本</el-button></div>
      <pre v-if="generatedPlan" class="plan-preview">{{ generatedPlan }}</pre>
      <el-table :data="scripts" border size="small" style="margin-top:12px;">
        <el-table-column prop="name" label="脚本名称" min-width="180" />
        <el-table-column prop="tool_type" label="工具" width="100" />
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column prop="created_time" label="创建时间" min-width="160" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { createPerformanceScenario, deletePerformanceScenario, generatePerformancePlan, generatePerformanceScript, getPerformanceScenarioList, getPerformanceScriptList, updatePerformanceScenario, uploadPerformanceScript } from '@/api/performanceApi'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'

const defaultForm = () => ({ id: '', name: '', code: '', description: '', projectId: '', productId: '', envCode: '', status: 1 })
const defaultUploadForm = () => ({ productId: '', projectId: '', scenarioId: '', toolType: 'jmeter', name: '' })

export default {
  name: 'PerformanceScenarioList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      submitting: false,
      scriptSubmitting: false,
      uploadSubmitting: false,
      planLoading: false,
      scriptLoading: false,
      dialogVisible: false,
      scriptDialogVisible: false,
      uploadDialogVisible: false,
      dialogMode: 'create',
      queryForm: { keyword: '', status: '' },
      form: defaultForm(),
      rules: { name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }], code: [{ required: true, message: '请输入场景编码', trigger: 'blur' }] },
      uploadRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        scenarioId: [{ required: true, message: '请选择性能场景', trigger: 'change' }],
        toolType: [{ required: true, message: '请选择工具方式', trigger: 'change' }],
        name: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }]
      },
      rows: [],
      productOptions: [],
      projectOptions: [],
      uploadProjectOptions: [],
      uploadScenarioOptions: [],
      pageNo: 1,
      pageSize: 20,
      total: 0,
      currentScenario: null,
      scripts: [],
      scriptForm: { name: '', toolType: 'jmeter' },
      scriptFiles: [],
      uploadForm: defaultUploadForm(),
      uploadFiles: [],
      nlPrompt: '',
      generatedPlan: ''
    }
  },
  created() { this.fetchList(); this.fetchProducts() },
  methods: {
    normalizeList(res) { const d = res && res.data ? res.data : res || {}; return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 } },
    fetchProducts() {
      getProductList({ pageNo: 1, pageSize: 200, status: 1 }).then(res => { this.productOptions = this.normalizeList(res).rows })
    },
    fetchProjects(productId) {
      if (!productId) { this.projectOptions = []; return Promise.resolve() }
      return getProjectList({ productId, pageNo: 1, pageSize: 200, status: 1 }).then(res => { this.projectOptions = this.normalizeList(res).rows })
    },
    handleProductChange(productId) { this.form.projectId = ''; this.fetchProjects(productId) },
    openUploadScript() {
      this.uploadForm = defaultUploadForm()
      this.uploadFiles = []
      this.uploadProjectOptions = []
      this.uploadScenarioOptions = []
      this.uploadDialogVisible = true
    },
    resetUploadForm() {
      this.uploadForm = defaultUploadForm()
      this.uploadFiles = []
      this.uploadProjectOptions = []
      this.uploadScenarioOptions = []
      this.uploadSubmitting = false
      if (this.$refs.uploadForm) this.$refs.uploadForm.resetFields()
    },
    handleUploadProductChange(productId) {
      this.uploadForm.projectId = ''
      this.uploadForm.scenarioId = ''
      this.uploadProjectOptions = []
      this.uploadScenarioOptions = []
      if (!productId) return
      getProjectList({ productId, pageNo: 1, pageSize: 200, status: 1 }).then(res => { this.uploadProjectOptions = this.normalizeList(res).rows })
    },
    handleUploadProjectChange(projectId) {
      this.uploadForm.scenarioId = ''
      this.uploadScenarioOptions = []
      if (!projectId) return
      getPerformanceScenarioList({ productId: this.uploadForm.productId, projectId, pageNo: 1, pageSize: 200, status: 1 }).then(res => { this.uploadScenarioOptions = this.normalizeList(res).rows })
    },
    handleUploadFileChange(file, fileList) {
      this.uploadFiles = fileList.slice(-1)
      if (!this.uploadForm.name && file && file.name) this.uploadForm.name = file.name.replace(/\.[^.]+$/, '')
    },
    handleUploadFileRemove(file, fileList) { this.uploadFiles = fileList },
    submitUploadScript() {
      this.$refs.uploadForm.validate(valid => {
        if (!valid) return
        if (!this.uploadFiles.length || !this.uploadFiles[0].raw) { this.$message.warning('请选择脚本文件'); return }
        const formData = new FormData()
        formData.append('scenarioId', this.uploadForm.scenarioId)
        formData.append('name', this.uploadForm.name)
        formData.append('toolType', this.uploadForm.toolType)
        formData.append('file', this.uploadFiles[0].raw)
        this.uploadSubmitting = true
        uploadPerformanceScript(formData).then(() => {
          this.$message.success('上传成功')
          this.uploadDialogVisible = false
          if (this.currentScenario && String(this.currentScenario.id) === String(this.uploadForm.scenarioId)) this.fetchScripts()
        }).finally(() => { this.uploadSubmitting = false })
      })
    },
    fetchList() {
      this.loading = true
      getPerformanceScenarioList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => {
        const data = this.normalizeList(res); this.rows = data.rows; this.total = data.total || this.rows.length
      }).catch(() => { this.rows = []; this.total = 0 }).finally(() => { this.loading = false })
    },
    resetQuery() { this.queryForm = { keyword: '', status: '' }; this.pageNo = 1; this.fetchList() },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    openCreate() { this.dialogMode = 'create'; this.form = defaultForm(); this.projectOptions = []; this.dialogVisible = true },
    openEdit(row) {
      this.dialogMode = 'edit'
      const productId = row.productId || row.product_id || ''
      this.form = Object.assign(defaultForm(), row, { envCode: row.envCode || row.env_code || '', projectId: String(row.projectId || row.project_id || ''), productId: String(productId) })
      this.dialogVisible = true
      this.fetchProjects(productId)
    },
    resetForm() { this.form = defaultForm(); this.submitting = false; if (this.$refs.form) this.$refs.form.resetFields() },
    submitForm() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        this.submitting = true
        const req = this.dialogMode === 'create' ? createPerformanceScenario(this.form) : updatePerformanceScenario(this.form.id, this.form)
        req.then(() => { this.$message.success('保存成功'); this.dialogVisible = false; this.fetchList() }).finally(() => { this.submitting = false })
      })
    },
    handleDelete(row) { this.$confirm('确认删除该性能场景？', '提示').then(() => deletePerformanceScenario(row.id).then(() => { this.$message.success('删除成功'); this.fetchList() })).catch(() => {}) },
    goRun(row) { this.$router.push({ path: '/performance/run-wizard', query: { scenarioId: row.id, scenarioName: row.name } }) },
    openScript(row) { this.currentScenario = row; this.scriptForm = { name: '', toolType: 'jmeter' }; this.scriptFiles = []; this.nlPrompt = ''; this.generatedPlan = ''; this.scriptDialogVisible = true; this.fetchScripts() },
    fetchScripts() { if (!this.currentScenario) return; getPerformanceScriptList({ scenarioId: this.currentScenario.id, pageNo: 1, pageSize: 50 }).then(res => { this.scripts = this.normalizeList(res).rows }) },
    handleScriptFileChange(file, fileList) {
      this.scriptFiles = fileList.slice(-1)
      if (!this.scriptForm.name && file && file.name) this.scriptForm.name = file.name.replace(/\.[^.]+$/, '')
    },
    handleScriptFileRemove(file, fileList) { this.scriptFiles = fileList },
    submitScript() {
      if (!this.currentScenario || !this.scriptForm.name) { this.$message.warning('请填写脚本名称'); return }
      if (!this.scriptFiles.length || !this.scriptFiles[0].raw) { this.$message.warning('请选择脚本文件'); return }
      const formData = new FormData()
      formData.append('scenarioId', this.currentScenario.id)
      formData.append('name', this.scriptForm.name)
      formData.append('toolType', this.scriptForm.toolType)
      formData.append('file', this.scriptFiles[0].raw)
      this.scriptSubmitting = true
      uploadPerformanceScript(formData).then(() => { this.$message.success('上传成功'); this.scriptForm.name = ''; this.scriptFiles = []; this.fetchScripts() }).finally(() => { this.scriptSubmitting = false })
    },
    generatePlan() {
      if (!this.currentScenario) { this.$message.warning('请先选择性能场景'); return }
      if (!this.nlPrompt) { this.$message.warning('请输入自然语言压测目标'); return }
      this.planLoading = true
      generatePerformancePlan({ scenarioId: this.currentScenario.id, toolType: this.scriptForm.toolType, prompt: this.nlPrompt }).then(res => { this.generatedPlan = JSON.stringify((res && res.data) || res || {}, null, 2) }).finally(() => { this.planLoading = false })
    },
    generateScript() {
      if (!this.currentScenario) { this.$message.warning('请先选择性能场景'); return }
      if (!this.nlPrompt && !this.generatedPlan) { this.$message.warning('请输入自然语言压测目标或先生成方案'); return }
      this.scriptLoading = true
      generatePerformanceScript({ scenarioId: this.currentScenario.id, name: this.scriptForm.name, toolType: this.scriptForm.toolType, prompt: this.nlPrompt, plan: this.generatedPlan }).then(() => { this.$message.success('AI脚本生成成功'); this.scriptForm.name = ''; this.fetchScripts() }).finally(() => { this.scriptLoading = false })
    }
  }
}
</script>

<style scoped>
.performance-page .pager-wrap { margin-top: 16px; text-align: right; }
.dialog-title-line { margin-bottom: 12px; color: #606266; }
.action-line { margin-top: 10px; }
.plan-preview { padding: 12px; overflow: auto; max-height: 220px; background: #1e293b; color: #dbeafe; border-radius: 4px; }
</style>
