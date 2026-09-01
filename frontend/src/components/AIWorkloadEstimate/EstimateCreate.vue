<template>
  <div class="page-wrap ai-workload-estimate-page">
    <page-section title="新建AI工作量预估">
      <template slot="extra">
        <el-button size="small" @click="$router.push({ path: '/ai-workload-estimate' })">返回列表</el-button>
      </template>

      <el-form ref="form" :model="form" :rules="rules" label-width="120px" size="small" class="estimate-form">
        <el-form-item label="预估标题" prop="title">
          <el-input v-model.trim="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="产品" prop="productId">
          <el-select v-model="form.productId" clearable filterable placeholder="选择产品" style="width:100%;" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="选择项目" style="width:100%;" @change="onProjectChange">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="form.ownerId" clearable filterable :disabled="!form.projectId" placeholder="选择项目成员" style="width:100%;" :loading="memberLoading">
            <el-option v-for="item in memberOptions" :key="item.user_id" :label="memberLabel(item)" :value="String(item.user_id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="本次PRD" prop="documentIds">
          <div class="doc-toolbar">
            <el-upload :http-request="uploadPrd" :show-file-list="false" :disabled="!form.productId || !form.projectId || uploadLoading">
              <el-button size="small" type="primary" :loading="uploadLoading" :disabled="!form.productId || !form.projectId">上传并解析</el-button>
            </el-upload>
            <el-button size="small" :disabled="!form.productId || !form.projectId" :loading="docLoading" @click="loadDocuments">刷新文档</el-button>
          </div>
          <el-table ref="docTable" v-loading="docLoading" :data="documentOptions" border size="small" class="doc-table" @selection-change="onDocumentSelectionChange">
            <el-table-column type="selection" width="48" :selectable="documentSelectable" />
            <el-table-column label="文档名称" min-width="260" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.source || '-' }}</template></el-table-column>
            <el-table-column label="版本" width="80"><template slot-scope="scope">{{ scope.row.version || '-' }}</template></el-table-column>
            <el-table-column label="状态" width="110"><template slot-scope="scope"><el-tag size="mini" :type="documentStatusTag(scope.row)">{{ documentStatusLabel(scope.row) }}</el-tag></template></el-table-column>
            <el-table-column label="分片" width="80"><template slot-scope="scope">{{ scope.row.chunkCount || 0 }}</template></el-table-column>
            <el-table-column label="创建时间" min-width="160" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.created_time || scope.row.createdTime || '-' }}</template></el-table-column>
          </el-table>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">创建预估</el-button>
          <el-button :disabled="saving" @click="$router.push({ path: '/ai-workload-estimate' })">取消</el-button>
        </el-form-item>
      </el-form>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getKnowledgeDocumentList, uploadKnowledgeDocument } from '@/api/knowledgeApi'
import { createWorkloadEstimate } from '@/api/aiWorkloadEstimateApi'
import { getProductList } from '@/api/productApi'
import { getProjectList, getProjectMembers } from '@/api/projectApi'

export default {
  name: 'AiWorkloadEstimateCreate',
  components: { PageSection },
  data() {
    return {
      saving: false,
      uploadLoading: false,
      docLoading: false,
      memberLoading: false,
      productOptions: [],
      projectOptions: [],
      memberOptions: [],
      documentOptions: [],
      form: { title: '', productId: '', projectId: '', ownerId: '', documentIds: [], remark: '' },
      rules: {
        title: [{ required: true, message: '请输入预估标题', trigger: 'blur' }],
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        documentIds: [{ type: 'array', required: true, min: 1, message: '请选择至少1个本次PRD', trigger: 'change' }]
      }
    }
  },
  computed: {
    currentUser() { return this.$store.state.currentUser || {} }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.productOptions = d.list || d.items || []
      })
    },
    loadProjects(productId) {
      if (!productId) { this.projectOptions = []; return }
      getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.projectOptions = d.list || d.items || []
      })
    },
    loadMembers() {
      if (!this.form.projectId) { this.memberOptions = []; return }
      this.memberLoading = true
      getProjectMembers(this.form.projectId, { pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.memberOptions = d.list || d.items || []
      }).finally(() => { this.memberLoading = false })
    },
    loadDocuments() {
      if (!this.form.productId || !this.form.projectId) { this.documentOptions = []; return }
      this.docLoading = true
      getKnowledgeDocumentList({ productId: this.form.productId, projectId: this.form.projectId, pageNo: 1, pageSize: 200 }).then(res => {
        const d = this.apiData(res)
        this.documentOptions = d.list || d.items || []
        this.form.documentIds = []
        this.$nextTick(() => { if (this.$refs.docTable) this.$refs.docTable.clearSelection() })
      }).finally(() => { this.docLoading = false })
    },
    onProductChange(productId) {
      this.form.projectId = ''
      this.form.ownerId = ''
      this.form.documentIds = []
      this.projectOptions = []
      this.memberOptions = []
      this.documentOptions = []
      this.loadProjects(productId)
    },
    onProjectChange() {
      this.form.ownerId = ''
      this.form.documentIds = []
      this.memberOptions = []
      this.documentOptions = []
      this.loadMembers()
      this.loadDocuments()
    },
    onDocumentSelectionChange(selection) {
      this.form.documentIds = selection.map(item => item.id)
      this.$refs.form.validateField('documentIds')
    },
    documentSelectable(row) { return Number(row.status) === 1 || Number(row.knowledgeStatus) === 1 },
    documentStatusLabel(row) {
      if (Number(row.status) === 1 || Number(row.knowledgeStatus) === 1) return '已解析'
      if (Number(row.status) === 2) return '已生成用例'
      return '待解析'
    },
    documentStatusTag(row) { return this.documentSelectable(row) ? 'success' : 'info' },
    uploadPrd(option) {
      if (!this.form.productId || !this.form.projectId) {
        this.$message.warning('请先选择产品和项目')
        return
      }
      this.uploadLoading = true
      uploadKnowledgeDocument({
        file: option.file,
        productId: this.form.productId,
        projectId: this.form.projectId,
        createdBy: this.currentUser.id,
        autoParse: true
      }).then(() => {
        this.$message.success('上传并解析完成')
        this.loadDocuments()
      }).finally(() => { this.uploadLoading = false })
    },
    memberLabel(item) { return item.real_name || item.username || ('用户' + item.user_id) },
    submit() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        if (this.memberOptions.length && !this.form.ownerId) {
          this.$message.warning('请选择负责人')
          return
        }
        const product = this.productOptions.find(item => String(item.id) === String(this.form.productId))
        const project = this.projectOptions.find(item => String(item.id) === String(this.form.projectId))
        const payload = {
          title: this.form.title,
          productId: this.form.productId,
          productName: product ? product.name : '',
          projectId: this.form.projectId,
          projectName: project ? project.name : '',
          ownerId: this.form.ownerId,
          documentIds: this.form.documentIds,
          remark: this.form.remark
        }
        this.saving = true
        createWorkloadEstimate(payload).then(res => {
          const d = this.apiData(res)
          const estimateId = d.estimateId || d.id
          this.$message.success('创建成功')
          this.$router.push({ path: '/ai-workload-estimate/detail', query: { id: estimateId } })
        }).finally(() => { this.saving = false })
      })
    }
  }
}
</script>

<style scoped>
.estimate-form { max-width: 980px; }
.doc-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.doc-table { width: 100%; }
</style>
