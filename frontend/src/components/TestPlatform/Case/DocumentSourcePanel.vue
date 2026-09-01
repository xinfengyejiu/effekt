<template>
  <div class="document-source-panel">
    <div v-if="!compact" class="document-source-main">
    <div class="document-source-head">
      <span class="document-source-title">文档源</span>
      <span class="document-source-hint">PDF / Excel / Markdown / 飞书</span>
    </div>

    <el-form :inline="true" size="mini" class="document-source-filters" @submit.native.prevent>
      <el-form-item label="类型">
        <el-select v-model="docQuery.type" clearable placeholder="全部" style="width: 96px;">
          <el-option label="PDF" :value="1"></el-option>
          <el-option label="飞书" :value="2"></el-option>
          <el-option label="Excel" :value="3"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="docQuery.status" clearable placeholder="全部" style="width: 100px;">
          <el-option label="待解析" :value="0"></el-option>
          <el-option label="已解析" :value="1"></el-option>
          <el-option label="已生成用例" :value="2"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="关键词">
        <el-input
          v-model="docQuery.keyword"
          clearable
          placeholder="来源"
          style="width: 120px;"
          @keyup.enter.native="handleDocSearch">
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :disabled="!projectId" @click="handleDocSearch">查询</el-button>
      </el-form-item>
      <el-form-item>
        <el-button size="mini" :disabled="!projectId" @click="openCreateDialog">新建</el-button>
      </el-form-item>
      <el-form-item>
        <el-button size="mini" :disabled="!projectId" @click="openBatchModuleDialog">批量建模块</el-button>
      </el-form-item>
    </el-form>

    <el-table
      ref="docTable"
      v-loading="docLoading"
      :data="docTableData"
      border
      size="small"
      :height="tableHeight"
      highlight-current-row
      class="document-source-table"
      :empty-text="projectId ? '暂无文档' : '请先选择项目'"
      @row-click="handleDocRowClick">
      <el-table-column prop="id" label="ID" width="56"></el-table-column>
      <el-table-column label="类型" width="80">
        <template slot-scope="scope">
          <el-tag size="mini" :type="docTypeTagType(scope.row.type)">{{ formatDocType(scope.row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="88">
        <template slot-scope="scope">
          <el-tag size="mini" :type="docStatusTagType(scope.row.status)">{{ formatDocStatus(scope.row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="来源" min-width="100" show-overflow-tooltip>
        <template slot-scope="scope">{{ scope.row.source }}</template>
      </el-table-column>
      <el-table-column prop="updated_time" label="更新时间" width="136" show-overflow-tooltip></el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template slot-scope="scope">
          <el-button type="text" size="mini" @click.stop="openDetail(scope.row)">详情</el-button>
          <el-dropdown trigger="click" @command="cmd => handleDocCommand(cmd, scope.row)">
            <el-button type="text" size="mini">更多</el-button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item v-if="scope.row.type === 2" command="refresh">刷新飞书</el-dropdown-item>
              <el-dropdown-item command="generate">生成用例</el-dropdown-item>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <div class="document-source-pagination">
      <el-pagination
        small
        layout="total, prev, pager, next"
        :current-page="docPageNo"
        :page-size="docPageSize"
        :total="docTotal"
        @current-change="handleDocPageChange">
      </el-pagination>
    </div>
    </div>

    <!-- 详情 -->
    <el-drawer title="文档详情" :visible.sync="detailVisible" direction="rtl" size="480px" append-to-body>
      <div v-loading="detailLoading" class="document-detail-body">
        <template v-if="detailRecord">
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="ID">{{ detailRecord.id }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ formatDocType(detailRecord.type) }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ formatDocStatus(detailRecord.status) }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detailRecord.source }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ detailRecord.version }}</el-descriptions-item>
            <el-descriptions-item label="AI 模型">{{ detailRecord.ai_model || '—' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ detailRecord.created_time }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ detailRecord.updated_time }}</el-descriptions-item>
          </el-descriptions>
          <div class="document-detail-content-label">内容</div>
          <el-input v-model="detailContentDisplay" type="textarea" :rows="14" readonly></el-input>
        </template>
      </div>
    </el-drawer>

    <!-- 新建 -->
    <el-dialog title="新建文档" :visible.sync="createVisible" width="560px" append-to-body @close="resetCreateForm">
      <el-form ref="createFormRef" :model="createForm" label-width="96px" size="small">
        <el-form-item label="文档上传">
          <div class="pdf-upload-row">
            <el-button size="small" type="primary" plain :disabled="!projectId" @click="triggerPdfMultiSelect">选择文档</el-button>
            <span class="pdf-upload-hint">支持 PDF、Excel、Markdown</span>
          </div>
          <input
            ref="pdfMultiInput"
            type="file"
            class="hidden-pdf-input"
            :accept="currentUploadAccept"
            @change="onPdfMultiInputChange">
          <ul v-if="pdfPendingFiles.length" class="pdf-pending-list">
            <li v-for="(f, idx) in pdfPendingFiles" :key="idx + f.name + f.size" class="pdf-pending-item">
              <span class="pdf-pending-name">{{ f.name }}</span>
              <span class="pdf-pending-size">（{{ formatFileSize(f.size) }}）</span>
              <el-button type="text" size="mini" @click="removePdfPending(idx)">移除</el-button>
            </li>
          </ul>
          <p v-else class="pdf-upload-empty">未选择文件</p>
        </el-form-item>
        <el-form-item label="飞书链接">
          <el-input v-model="createForm.source" placeholder="也可以粘贴飞书文档链接"></el-input>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="createForm.content" type="textarea" :rows="4" placeholder="飞书链接可选补充内容"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="createVisible = false">取消</el-button>
        <el-button
          type="primary"
          size="small"
          :loading="pdfUploading || createSubmitting"
          :disabled="!projectId || (!pdfPendingFiles.length && !createForm.source)"
          @click="submitCreate">
          确定
        </el-button>
      </span>
    </el-dialog>

    <!-- 编辑 -->
    <el-dialog title="编辑文档" :visible.sync="editVisible" width="520px" append-to-body @close="resetEditForm">
      <el-form ref="editFormRef" :model="editForm" label-width="96px" size="small">
        <el-form-item label="类型">
          <el-select v-model="editForm.type" style="width: 100%;">
            <el-option label="PDF" :value="1"></el-option>
            <el-option label="飞书链接" :value="2"></el-option>
            <el-option label="Excel" :value="3"></el-option>
            <el-option label="Markdown" :value="4"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editForm.source"></el-input>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editForm.content" type="textarea" :rows="5"></el-input>
        </el-form-item>
        <el-form-item label="AI 模型">
          <el-input v-model="editForm.ai_model" placeholder="可选"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="editVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="editSubmitting" @click="submitEdit">保存</el-button>
      </span>
    </el-dialog>

    <!-- 生成 / 匹配 / 导入 -->
    <el-drawer
      title="从文档生成用例"
      :visible.sync="generateVisible"
      direction="rtl"
      size="640px"
      append-to-body
      @close="resetGenerateState">
      <div v-if="activeDocument" class="generate-drawer-head">
        <el-tag size="small">文档 #{{ activeDocument.id }}</el-tag>
        <span class="generate-drawer-source">{{ activeDocument.source }}</span>
      </div>
      <el-form :inline="true" size="small" class="generate-form">
        <el-form-item label="默认优先级">
          <el-select v-model="genForm.priority" style="width: 100px;">
            <el-option label="P0" :value="1"></el-option>
            <el-option label="P1" :value="2"></el-option>
            <el-option label="P2" :value="3"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="用例类型">
          <el-input-number v-model="genForm.caseType" :min="1" :max="99" size="small"></el-input-number>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="generateLoading" @click="runGenerate">生成预览</el-button>
          <el-button :loading="matchLoading" :disabled="!previewCases.length" @click="runMatch">匹配模块</el-button>
          <el-button type="success" :loading="importLoading" :disabled="!previewCases.length" @click="runImport">导入选中</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="previewCases" border size="small" max-height="420">
        <el-table-column width="48">
          <template slot-scope="scope">
            <el-checkbox v-model="scope.row.selected"></el-checkbox>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column label="模块" width="120">
          <template slot-scope="scope">
            <span>{{ scope.row.module_name || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="模块ID" width="88">
          <template slot-scope="scope">
            <el-input v-model.number="scope.row.module_id" size="mini" placeholder="必填"></el-input>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="previewTotal" class="generate-total-hint">共 {{ previewTotal }} 条预览（导入前请为每行填写模块ID）</p>
    </el-drawer>

    <!-- 批量建模块 -->
    <el-dialog title="批量创建模块" :visible.sync="batchModuleVisible" width="480px" append-to-body>
      <p class="batch-module-tip">每行一个模块名称，将创建在当前项目下。</p>
      <el-input v-model="batchModuleText" type="textarea" :rows="8" placeholder="例如：用户管理&#10;订单中心"></el-input>
      <span slot="footer">
        <el-button size="small" @click="batchModuleVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="batchModuleSubmitting" @click="submitBatchModules">创建</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import {
  getDocumentList,
  getDocumentDetail,
  uploadDocumentPdf,
  createDocument,
  updateDocument,
  deleteDocument,
  refreshDocument,
  generateDocumentCases,
  generateDocumentCasesStreaming,
  matchDocumentModules,
  importDocumentCases,
  batchCreateDocumentModules
} from '@/api/documentApi'

export default {
  name: 'DocumentSourcePanel',
  props: {
    productId: {
      type: [Number, String],
      default: ''
    },
    projectId: {
      type: [Number, String],
      default: ''
    },
    /** 文档列表表格高度（独立 Tab 可传更大值） */
    tableHeight: {
      type: [Number, String],
      default: 360
    },
    /** 仅保留新建/编辑等弹窗，不展示列表与筛选；不自动请求文档列表 */
    compact: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      docQuery: {
        type: '',
        status: '',
        keyword: ''
      },
      docPageNo: 1,
      docPageSize: 10,
      docTotal: 0,
      docTableData: [],
      docLoading: false,
      detailVisible: false,
      detailLoading: false,
      detailRecord: null,
      createVisible: false,
      createSubmitting: false,
      pdfUploading: false,
      pdfPendingFiles: [],
      createForm: {
        source: '',
        content: ''
      },
      editVisible: false,
      editSubmitting: false,
      editForm: {
        documentId: null,
        type: 1,
        source: '',
        content: '',
        ai_model: ''
      },
      generateVisible: false,
      generateLoading: false,
      matchLoading: false,
      importLoading: false,
      activeDocument: null,
      genForm: {
        priority: 2,
        caseType: 1
      },
      previewCases: [],
      previewTotal: 0,
      batchModuleVisible: false,
      batchModuleText: '',
      batchModuleSubmitting: false
    }
  },
  computed: {
    ...mapState(['currentUser']),
    detailContentDisplay() {
      if (!this.detailRecord) return ''
      return this.detailRecord.content || ''
    },
    currentUploadAccept() {
      return '.pdf,.xlsx,.xls,.md,.markdown,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/markdown,text/x-markdown,text/plain'
    }
  },
  watch: {
    projectId: {
      immediate: true,
      handler(val) {
        this.docPageNo = 1
        if (this.compact) {
          if (!val) {
            this.docTableData = []
            this.docTotal = 0
          }
          return
        }
        if (val) {
          this.fetchDocuments()
        } else {
          this.docTableData = []
          this.docTotal = 0
        }
      }
    }
  },
  methods: {
    formatDocType(type) {
      if (type === 2) return '飞书'
      if (type === 1) return 'PDF'
      if (type === 3) return 'Excel'
      if (type === 4) return 'Markdown'
      return '—'
    },
    docTypeTagType(type) {
      if (type === 2) return 'warning'
      if (type === 3) return 'success'
      if (type === 4) return 'primary'
      return 'info'
    },
    formatDocStatus(status) {
      const map = { 0: '待解析', 1: '已解析', 2: '已生成用例' }
      return map[status] !== undefined ? map[status] : '—'
    },
    docStatusTagType(status) {
      if (status === 0) return 'info'
      if (status === 1) return 'success'
      if (status === 2) return 'warning'
      return ''
    },
    cleanParams(obj) {
      return Object.keys(obj || {}).reduce((acc, key) => {
        const v = obj[key]
        if (v !== '' && v !== undefined && v !== null) {
          acc[key] = v
        }
        return acc
      }, {})
    },
    fetchDocuments() {
      if (!this.projectId) {
        this.docTableData = []
        this.docTotal = 0
        return
      }
      this.docLoading = true
      const params = this.cleanParams({
        productId: this.productId || undefined,
        projectId: this.projectId,
        type: this.docQuery.type,
        status: this.docQuery.status,
        keyword: this.docQuery.keyword,
        pageNo: this.docPageNo,
        pageSize: this.docPageSize
      })
      getDocumentList(params)
        .then(res => {
          const data = (res && res.data) || res || {}
          const list = data.list || data.items || []
          this.docTableData = Array.isArray(list) ? list : []
          this.docTotal = Number(data.total || 0)
        })
        .catch(() => {
          this.docTableData = []
          this.docTotal = 0
        })
        .finally(() => {
          this.docLoading = false
        })
    },
    handleDocSearch() {
      this.docPageNo = 1
      this.fetchDocuments()
    },
    handleDocPageChange(p) {
      this.docPageNo = p
      this.fetchDocuments()
    },
    handleDocRowClick(row) {
      if (this.compact || !this.$refs.docTable) return
      if (this.$refs.docTable.setCurrentRow) {
        this.$refs.docTable.setCurrentRow(row)
      }
    },
    syncDocumentListAfterMutation() {
      if (this.compact) {
        this.$emit('document-changed')
      } else {
        this.fetchDocuments()
      }
    },
    openDetail(row) {
      this.detailVisible = true
      this.detailRecord = Object.assign({}, row)
      this.detailLoading = true
      getDocumentDetail({ documentId: row.id })
        .then(res => {
          const data = (res && res.data) || res || {}
          this.detailRecord = data
        })
        .catch(() => {})
        .finally(() => {
          this.detailLoading = false
        })
    },
    openCreateDialog() {
      if (!this.productId || !this.projectId) {
        this.$message.warning('请先选择产品与项目')
        return
      }
      this.createForm = {
        source: '',
        content: ''
      }
      this.pdfPendingFiles = []
      this.createVisible = true
    },
    resetCreateForm() {
      this.createForm = { source: '', content: '' }
      this.pdfPendingFiles = []
      if (this.$refs.pdfMultiInput) {
        this.$refs.pdfMultiInput.value = ''
      }
    },
    triggerPdfMultiSelect() {
      this.$refs.pdfMultiInput && this.$refs.pdfMultiInput.click()
    },
    onPdfMultiInputChange(e) {
      const input = e && e.target
      const picked = input && input.files ? Array.from(input.files) : []
      if (input) {
        input.value = ''
      }
      const matched = picked.filter(f => this.isSupportedDocumentFile(f))
      if (picked.length && matched.length < picked.length) {
        this.$message.warning('已忽略非 PDF / Excel / Markdown 文件')
      }
      if (matched.length > 1) {
        this.$message.warning('一次仅支持上传一个文档，已保留第一个文件')
      }
      this.pdfPendingFiles = matched.slice(0, 1)
    },
    isSupportedDocumentFile(file) {
      const name = String(file && file.name ? file.name : '').toLowerCase()
      const type = String(file && file.type ? file.type : '').toLowerCase()
      return name.endsWith('.pdf') ||
        name.endsWith('.xlsx') ||
        name.endsWith('.xls') ||
        name.endsWith('.md') ||
        name.endsWith('.markdown') ||
        type === 'application/pdf' ||
        type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        type === 'application/vnd.ms-excel' ||
        type === 'text/markdown' ||
        type === 'text/x-markdown'
    },
    removePdfPending(index) {
      this.pdfPendingFiles.splice(index, 1)
    },
    formatFileSize(bytes) {
      const n = Number(bytes)
      if (!Number.isFinite(n) || n < 0) return '—'
      if (n < 1024) return `${n} B`
      if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
      return `${(n / 1024 / 1024).toFixed(1)} MB`
    },
    async submitAllPdfUploads() {
      if (!this.productId || !this.projectId) {
        this.$message.warning('请先选择产品与项目')
        return
      }
      const files = this.pdfPendingFiles.slice(0, 1)
      if (!files.length) {
        this.$message.warning('请先选择 PDF、Excel 或 Markdown 文件')
        return
      }
      const productId = Number(this.productId)
      const projectId = Number(this.projectId)
      const createdBy = this.currentUser && this.currentUser.id ? this.currentUser.id : undefined
      this.pdfUploading = true
      try {
        await uploadDocumentPdf({ file: files[0], productId, projectId, createdBy })
        this.pdfPendingFiles = []
        this.syncDocumentListAfterMutation()
        this.$message.success('上传成功')
        this.createVisible = false
      } catch (e) {
        this.$message.error('上传失败，请检查网络或文件后重试')
      } finally {
        this.pdfUploading = false
      }
    },
    submitCreate() {
      if (this.pdfPendingFiles.length) {
        this.submitAllPdfUploads()
        return
      }
      if (!this.createForm.source) {
        this.$message.warning('请选择一个文档，或填写飞书链接')
        return
      }
      this.createSubmitting = true
      const payload = {
        productId: Number(this.productId),
        projectId: Number(this.projectId),
        type: 2,
        source: this.createForm.source,
        content: this.createForm.content || undefined
      }
      if (this.currentUser && this.currentUser.id) {
        payload.createdBy = this.currentUser.id
      }
      createDocument(payload)
        .then(() => {
          this.$message.success('创建成功')
          this.createVisible = false
          this.syncDocumentListAfterMutation()
        })
        .finally(() => {
          this.createSubmitting = false
        })
    },
    handleDocCommand(cmd, row) {
      if (cmd === 'refresh') {
        this.doRefresh(row)
      } else if (cmd === 'generate') {
        this.openGenerate(row)
      } else if (cmd === 'edit') {
        this.openEdit(row)
      } else if (cmd === 'delete') {
        this.doDelete(row)
      }
    },
    doRefresh(row) {
      this.$confirm('确认从飞书重新拉取内容？', '提示', { type: 'warning' })
        .then(() => {
          return refreshDocument({ documentId: row.id })
        })
        .then(() => {
          this.$message.success('已刷新')
          this.fetchDocuments()
        })
        .catch(() => {})
    },
    doDelete(row) {
      this.$confirm('确认删除该文档？', '提示', { type: 'warning' })
        .then(() => {
          return deleteDocument({ documentId: row.id })
        })
        .then(() => {
          this.$message.success('已删除')
          this.fetchDocuments()
        })
        .catch(() => {})
    },
    openEdit(row) {
      this.editForm = {
        documentId: row.id,
        type: row.type,
        source: row.source || '',
        content: row.content || '',
        ai_model: row.ai_model || ''
      }
      this.editVisible = true
    },
    resetEditForm() {
      this.editForm = { documentId: null, type: 1, source: '', content: '', ai_model: '' }
    },
    submitEdit() {
      if (!this.editForm.documentId) return
      this.editSubmitting = true
      updateDocument({
        documentId: this.editForm.documentId,
        type: this.editForm.type,
        source: this.editForm.source,
        content: this.editForm.content,
        ai_model: this.editForm.ai_model || undefined
      })
        .then(() => {
          this.$message.success('保存成功')
          this.editVisible = false
          this.fetchDocuments()
        })
        .finally(() => {
          this.editSubmitting = false
        })
    },
    openGenerate(row) {
      this.activeDocument = row
      this.previewCases = []
      this.previewTotal = 0
      this.genForm = { priority: 2, caseType: 1 }
      this.generateVisible = true
    },
    resetGenerateState() {
      this.activeDocument = null
      this.previewCases = []
      this.previewTotal = 0
    },
    runGenerate() {
      if (!this.activeDocument || !this.projectId) return
      this.generateLoading = true
      this.previewCases = []
      this.previewTotal = 0

      const payload = {
        documentIds: [this.activeDocument.id],
        projectId: Number(this.projectId),
        priority: this.genForm.priority,
        caseType: this.genForm.caseType,
        tags: ['AI生成']
      }

      generateDocumentCasesStreaming(
        payload,
        (parsed) => {
          const event = parsed.event
          const data = parsed.data || {}
          if (event === 'progress') {
            // 实时更新进度提示
            this.previewTotal = data.totalCasesSoFar || 0
          } else if (event === 'done') {
            const totalCases = data.totalCases || 0
            const importedCount = data.importedCount || 0
            if (totalCases > 0) {
              this.$message.success(`生成完成，共${totalCases}条用例，已导入${importedCount}条`)
            } else {
              this.$message.warning('AI未生成任何测试用例，请检查文档内容')
            }
            if (data.hasError || (data.failedChunks && data.failedChunks.length)) {
              const errMsgs = (data.failedChunks || []).map(f => f.error || '未知错误').join('; ')
              if (errMsgs) {
                this.$message.warning(`部分分段生成失败: ${errMsgs}`)
              }
            }
          } else if (event === 'error') {
            this.$message.error(data.message || '生成失败')
            this.previewCases = []
            this.previewTotal = 0
          }
        },
        (err) => {
          this.$message.error(`生成失败: ${err.message || '网络错误'}`)
          this.previewCases = []
          this.previewTotal = 0
        },
        () => {
          this.generateLoading = false
        }
      )
    },
    runMatch() {
      if (!this.activeDocument || !this.previewCases.length) return
      this.matchLoading = true
      const casesPayload = this.previewCases.map(c => ({
        title: c.title,
        precondition: c.precondition,
        steps: c.steps,
        expected_result: c.expected_result,
        priority: c.priority,
        case_type: c.case_type,
        tags: c.tags,
        module_name: c.module_name,
        module_id: c.module_id
      }))
      matchDocumentModules({
        documentId: this.activeDocument.id,
        cases: casesPayload
      })
        .then(res => {
          const data = (res && res.data) || res || []
          const arr = Array.isArray(data) ? data : []
          const byTitle = {}
          arr.forEach(row => {
            if (row && row.title) byTitle[row.title] = row
          })
          this.previewCases = this.previewCases.map(row => {
            const m = byTitle[row.title]
            if (m) {
              return Object.assign({}, row, {
                module_name: m.module_name != null ? m.module_name : row.module_name,
                module_id: m.module_id != null ? Number(m.module_id) : row.module_id
              })
            }
            return row
          })
          this.$message.success('匹配完成')
        })
        .finally(() => {
          this.matchLoading = false
        })
    },
    runImport() {
      if (!this.activeDocument || !this.currentUser || !this.currentUser.id) {
        this.$message.warning('未获取到当前用户，请重新登录')
        return
      }
      const selected = this.previewCases.filter(c => c.selected)
      if (!selected.length) {
        this.$message.warning('请至少选择一条用例')
        return
      }
      for (let i = 0; i < selected.length; i++) {
        const c = selected[i]
        if (!c.module_id && c.module_id !== 0) {
          this.$message.warning(`请填写模块ID：${c.title || ''}`)
          return
        }
        if (!c.title || !c.steps) {
          this.$message.warning('标题与步骤为必填')
          return
        }
      }
      const cases = selected.map(c => ({
        selected: true,
        module_id: Number(c.module_id),
        title: c.title,
        precondition: c.precondition || '',
        steps: c.steps,
        expected_result: c.expected_result || '',
        priority: c.priority != null ? Number(c.priority) : 2,
        case_type: c.case_type != null ? Number(c.case_type) : 1,
        tags: Array.isArray(c.tags) ? c.tags : ['AI生成']
      }))
      this.$confirm(
        '请确认已完成对预览用例的审核。导入选中行后将写入正式用例列表，是否继续？',
        '确认导入',
        { type: 'warning', confirmButtonText: '确认导入' }
      )
        .then(() => {
          this.importLoading = true
          return importDocumentCases({
            documentId: this.activeDocument.id,
            userId: this.currentUser.id,
            cases
          })
        })
        .then(res => {
          if (!res) return
          const data = (res && res.data) || res || {}
          const n = data.successCount != null ? data.successCount : cases.length
          this.$message.success(`导入成功 ${n} 条`)
          this.generateVisible = false
          this.$emit('refresh-cases')
        })
        .catch(() => {})
        .finally(() => {
          this.importLoading = false
        })
    },
    openBatchModuleDialog() {
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.batchModuleText = ''
      this.batchModuleVisible = true
    },
    submitBatchModules() {
      const lines = String(this.batchModuleText || '')
        .split(/\r?\n/)
        .map(s => s.trim())
        .filter(Boolean)
      if (!lines.length) {
        this.$message.warning('请输入至少一个模块名称')
        return
      }
      this.batchModuleSubmitting = true
      batchCreateDocumentModules({
        projectId: Number(this.projectId),
        moduleNames: lines
      })
        .then(() => {
          this.$message.success('模块创建成功')
          this.batchModuleVisible = false
          this.$emit('refresh-modules')
        })
        .finally(() => {
          this.batchModuleSubmitting = false
        })
    }
  }
}
</script>

<style scoped>
.document-source-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.document-source-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 0 2px 8px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 8px;
}

.document-source-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.document-source-hint {
  font-size: 12px;
  color: #909399;
}

.document-source-filters {
  margin-bottom: 4px;
}

.document-source-filters /deep/ .el-form-item {
  margin-bottom: 6px;
}

.document-source-table {
  flex: 1;
  min-height: 0;
}

.document-source-table /deep/ .el-table__body tr.current-row > td {
  background-color: #ecf5ff !important;
}

.document-source-pagination {
  margin-top: 8px;
  text-align: right;
}

.document-detail-body {
  padding: 0 4px 16px;
}

.document-detail-content-label {
  margin: 12px 0 6px;
  font-weight: 600;
  color: #606266;
}

.generate-drawer-head {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.generate-drawer-source {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

.generate-form {
  margin-bottom: 12px;
}

.generate-total-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.batch-module-tip {
  font-size: 13px;
  color: #606266;
  margin: 0 0 8px;
}

.hidden-pdf-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.pdf-upload-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.pdf-upload-hint {
  font-size: 12px;
  color: #909399;
}

.pdf-upload-empty {
  margin: 0;
  font-size: 12px;
  color: #c0c4cc;
}

.pdf-pending-list {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 200px;
  overflow: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.pdf-pending-item {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  font-size: 13px;
  border-bottom: 1px solid #f0f0f0;
}

.pdf-pending-item:last-child {
  border-bottom: none;
}

.pdf-pending-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.pdf-pending-size {
  color: #909399;
  margin-right: 8px;
  flex-shrink: 0;
}
</style>
