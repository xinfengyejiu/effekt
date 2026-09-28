<template>
  <div class="page-wrap chat-issue-page">
    <page-section title="聊天问题导入">
      <template slot="extra">
        <el-button size="small" type="primary" icon="el-icon-upload2" @click="openImport">导入 Session</el-button>
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
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width:120px;">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
          <el-button icon="el-icon-refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="Session 编号" min-width="150" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-link type="primary" @click="goReview(scope.row)">{{ scope.row.sessionNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220" show-overflow-tooltip prop="title" />
        <el-table-column label="日期段" width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.dayLabel || '-' }}</template>
        </el-table-column>
        <el-table-column label="产品" min-width="120" show-overflow-tooltip prop="productName" />
        <el-table-column label="项目" min-width="140" show-overflow-tooltip prop="projectName" />
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160" prop="createdTime" />
        <el-table-column label="操作" width="120" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goReview(scope.row)">核对转正</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10,20,50]"
          :total="total"
          @size-change="v => { pageSize = v; pageNo = 1; fetchList() }"
          @current-change="v => { pageNo = v; fetchList() }"
        />
      </div>
    </page-section>

    <el-dialog title="导入聊天问题 Session" :visible.sync="importVisible" width="760px" :close-on-click-modal="false">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="支持飞书/豆包按日整理格式：## 9月17日（周四） + **1. 问题标题** + 正文/截图链接。多日将拆成多个 Session。"
        style="margin-bottom:12px;"
      />
      <el-form ref="importForm" :model="importForm" :rules="importRules" label-width="90px" size="small">
        <el-form-item label="产品" prop="productId">
          <el-select v-model="importForm.productId" filterable style="width:100%;" @change="onImportProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="importForm.projectId" filterable :disabled="!importForm.productId" style="width:100%;">
            <el-option v-for="item in importProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="按日拆分">
          <el-switch v-model="importForm.splitByDay" active-text="每个日期一个 Session" inactive-text="合并为一个 Session" />
        </el-form-item>
        <el-form-item label="粘贴文本">
          <el-input v-model="importForm.text" type="textarea" :rows="12" placeholder="粘贴豆包整理的 Markdown…" />
        </el-form-item>
        <el-form-item label="或上传文件">
          <input ref="fileInput" type="file" accept=".md,.txt,.markdown" @change="onFileChange" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="importVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="importLoading" @click="submitImport">开始导入</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { getChatIssueList, importChatIssue, importChatIssueFile } from '@/api/chatIssueApi'

const STATUSES = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '待处理' },
  { value: 'partial', label: '部分转正' },
  { value: 'done', label: '已完成' }
]

export default {
  name: 'ChatIssueImportList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      importVisible: false,
      importLoading: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      productOptions: [],
      projectOptions: [],
      importProjectOptions: [],
      queryForm: { productId: '', projectId: '', status: '', keyword: '' },
      importForm: { productId: '', projectId: '', text: '', splitByDay: true, file: null },
      importRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }]
      },
      statusOptions: STATUSES
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    productName(id) {
      const item = this.productOptions.find(p => String(p.id) === String(id))
      return item ? item.name : ''
    },
    projectName(id, list) {
      const item = (list || []).find(p => String(p.id) === String(id))
      return item ? item.name : ''
    },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        this.productOptions = this.apiData(res).list || this.apiData(res).items || []
      })
    },
    loadProjects(productId, target) {
      if (!productId) { this[target] = []; return }
      getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => {
        this[target] = this.apiData(res).list || this.apiData(res).items || []
      })
    },
    onProductChange(v) {
      this.queryForm.projectId = ''
      this.loadProjects(v, 'projectOptions')
    },
    onImportProductChange(v) {
      this.importForm.projectId = ''
      this.loadProjects(v, 'importProjectOptions')
    },
    fetchList() {
      this.loading = true
      getChatIssueList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize }))
        .then(res => {
          const data = this.apiData(res)
          this.rows = data.list || []
          this.total = data.total || this.rows.length
        })
        .finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', status: '', keyword: '' }
      this.projectOptions = []
      this.pageNo = 1
      this.fetchList()
    },
    openImport() {
      this.importForm = { productId: '', projectId: '', text: '', splitByDay: true, file: null }
      this.importProjectOptions = []
      if (this.$refs.fileInput) this.$refs.fileInput.value = ''
      this.importVisible = true
    },
    onFileChange(e) {
      const file = e.target.files && e.target.files[0]
      this.importForm.file = file || null
    },
    submitImport() {
      this.$refs.importForm.validate(valid => {
        if (!valid) return
        if (!this.importForm.text.trim() && !this.importForm.file) {
          this.$message.warning('请粘贴文本或上传文件')
          return
        }
        this.importLoading = true
        const base = {
          productId: this.importForm.productId,
          projectId: this.importForm.projectId,
          productName: this.productName(this.importForm.productId),
          projectName: this.projectName(this.importForm.projectId, this.importProjectOptions),
          splitByDay: this.importForm.splitByDay
        }
        const req = this.importForm.file
          ? (() => {
            const fd = new FormData()
            fd.append('file', this.importForm.file)
            Object.keys(base).forEach(k => fd.append(k, base[k]))
            return importChatIssueFile(fd)
          })()
          : importChatIssue(Object.assign({}, base, { text: this.importForm.text, sourceType: 'paste' }))
        req.then(res => {
          const data = this.apiData(res)
          const list = data.list || []
          this.$message.success(`已导入 ${list.length} 个 Session`)
          this.importVisible = false
          if (list.length === 1) {
            this.$router.push({ path: '/chat-issue/review', query: { id: list[0].id } })
          } else {
            this.fetchList()
            if (list[0]) this.$router.push({ path: '/chat-issue/review', query: { id: list[0].id } })
          }
        }).finally(() => { this.importLoading = false })
      })
    },
    goReview(row) {
      this.$router.push({ path: '/chat-issue/review', query: { id: row.id } })
    },
    statusLabel(v) { return (STATUSES.find(i => i.value === v) || {}).label || v || '-' },
    statusTag(v) { return { draft: 'info', ready: '', partial: 'warning', done: 'success' }[v] || 'info' }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
</style>
