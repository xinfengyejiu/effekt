<template>
  <div class="knowledge-workspace">
    <header class="workspace-header">
      <div>
        <h1>需求问答</h1>
        <p>按产品和项目维护知识资料，基于当前项目知识库持续提问。</p>
      </div>
      <div class="header-actions">
        <el-button size="small" icon="el-icon-setting" :disabled="!queryForm.projectId" @click="settingVisible = true">模型设置</el-button>
        <el-button size="small" type="primary" icon="el-icon-upload2" :disabled="!queryForm.projectId" @click="openUpload">上传资料</el-button>
      </div>
    </header>

    <div class="workspace-body">
      <aside class="context-panel">
        <div class="panel-heading">知识库范围</div>
        <div class="field-label">产品</div>
        <el-select v-model="queryForm.productId" size="small" filterable placeholder="选择产品" @change="loadProjects">
          <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <div class="field-label project-label">项目</div>
        <div v-if="!queryForm.productId" class="context-empty">请先选择产品</div>
        <div v-else-if="!projectOptions.length" class="context-empty">暂无项目</div>
        <button
          v-for="item in projectOptions"
          :key="item.id"
          type="button"
          :class="['project-item', { active: queryForm.projectId === item.id }]"
          @click="selectProject(item)">
          <i class="el-icon-folder-opened" />
          <span>{{ item.name }}</span>
        </button>
        <div class="scope-note">
          <i class="el-icon-info" />
          问答会检索当前产品与项目下全部已解析资料。
        </div>
      </aside>

      <section class="document-panel">
        <div class="panel-topline">
          <div>
            <div class="panel-heading">项目资料</div>
            <div class="panel-subtitle">{{ currentProjectName || '选择项目后查看资料' }}</div>
          </div>
          <el-button type="text" icon="el-icon-refresh" :disabled="!queryForm.projectId" @click="fetchList">刷新</el-button>
        </div>
        <el-input
          v-model="queryForm.keyword"
          size="small"
          prefix-icon="el-icon-search"
          clearable
          placeholder="搜索文件名"
          :disabled="!queryForm.projectId"
          @keyup.enter.native="fetchList"
          @clear="fetchList" />
        <div class="document-summary">
          <span>{{ total }} 份资料</span>
          <span>{{ parsedCount }} 份已解析</span>
        </div>
        <div v-loading="loading" class="document-list">
          <div v-if="!queryForm.projectId" class="document-empty">选择左侧项目，建立项目知识库。</div>
          <div v-else-if="!tableData.length && !loading" class="document-empty">暂无资料，上传需求文档后即可开始问答。</div>
          <div v-for="item in tableData" :key="item.id" class="document-item">
            <div class="document-icon"><i class="el-icon-document" /></div>
            <div class="document-main">
              <div class="document-name" :title="item.source">{{ item.source }}</div>
              <div class="document-meta">
                <span>{{ typeText(item.type) }}</span>
                <span>{{ item.chunkCount || 0 }} 个分片</span>
                <span :class="['document-status', { ready: item.chunkCount }]">{{ item.chunkCount ? '已入库' : '待解析' }}</span>
              </div>
            </div>
            <el-dropdown trigger="click" @command="handleDocumentCommand($event, item)">
              <button type="button" class="more-button"><i class="el-icon-more" /></button>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="parse">解析入库</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除资料</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
        </div>
        <div v-if="total > queryForm.pageSize" class="document-pager">
          <el-pagination small layout="prev, pager, next" :total="total" :page-size="queryForm.pageSize" :current-page.sync="queryForm.pageNo" @current-change="fetchList" />
        </div>
      </section>

      <knowledge-chat-dialog
        class="chat-panel"
        :product-id="queryForm.productId"
        :project-id="queryForm.projectId"
        :project-name="currentProjectName" />
    </div>

    <el-dialog title="上传项目知识库资料" :visible.sync="uploadVisible" width="520px" append-to-body>
      <el-form :model="uploadForm" label-width="88px" size="small">
        <el-form-item label="知识库范围">
          <div>{{ currentProductName }} / {{ currentProjectName }}</div>
        </el-form-item>
        <el-form-item label="文件" required>
          <input type="file" accept=".pdf,.txt,.md,.docx" @change="onFileChange" />
        </el-form-item>
        <el-form-item label="自动解析">
          <el-switch v-model="uploadForm.autoParse" />
          <span class="form-tip">上传后直接写入当前项目知识库</span>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </div>
    </el-dialog>

    <el-dialog title="项目模型设置" :visible.sync="settingVisible" width="640px" append-to-body>
      <model-setting-panel :product-id="queryForm.productId" :project-id="queryForm.projectId" />
    </el-dialog>
  </div>
</template>

<script>
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { deleteKnowledgeDocument, getKnowledgeDocumentList, parseKnowledgeDocument, uploadKnowledgeDocument } from '@/api/knowledgeApi'
import KnowledgeChatDialog from './KnowledgeChatDialog.vue'
import ModelSettingPanel from './ModelSettingPanel.vue'

export default {
  name: 'RequirementQaList',
  components: { KnowledgeChatDialog, ModelSettingPanel },
  data() {
    return {
      loading: false,
      uploading: false,
      uploadVisible: false,
      settingVisible: false,
      tableData: [],
      total: 0,
      productOptions: [],
      projectOptions: [],
      queryForm: { productId: '', projectId: '', keyword: '', pageNo: 1, pageSize: 20 },
      uploadForm: { file: null, autoParse: true }
    }
  },
  computed: {
    currentProductName() {
      const item = this.productOptions.find(item => item.id === this.queryForm.productId)
      return item ? item.name : '-'
    },
    currentProjectName() {
      const item = this.projectOptions.find(item => item.id === this.queryForm.projectId)
      return item ? item.name : ''
    },
    parsedCount() {
      return this.tableData.filter(item => Number(item.chunkCount) > 0).length
    }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        this.productOptions = (res.data && res.data.list) || []
      })
    },
    loadProjects() {
      this.queryForm.projectId = ''
      this.projectOptions = []
      this.tableData = []
      this.total = 0
      if (!this.queryForm.productId) return
      getProjectList({ productId: this.queryForm.productId, pageNo: 1, pageSize: 200 }).then(res => {
        this.projectOptions = (res.data && res.data.list) || []
      })
    },
    selectProject(item) {
      this.queryForm.projectId = item.id
      this.queryForm.keyword = ''
      this.queryForm.pageNo = 1
      this.fetchList()
    },
    fetchList() {
      if (!this.queryForm.projectId) return
      this.loading = true
      getKnowledgeDocumentList(this.queryForm).then(res => {
        const data = res.data || {}
        this.tableData = data.list || []
        this.total = data.total || 0
      }).catch(() => {
        this.tableData = []
        this.total = 0
      }).finally(() => {
        this.loading = false
      })
    },
    openUpload() {
      if (!this.queryForm.projectId) return
      this.uploadForm = { file: null, autoParse: true }
      this.uploadVisible = true
    },
    onFileChange(e) {
      this.uploadForm.file = e.target.files && e.target.files[0]
    },
    submitUpload() {
      if (!this.uploadForm.file) {
        this.$message.warning('请选择文件')
        return
      }
      this.uploading = true
      uploadKnowledgeDocument(Object.assign({}, this.uploadForm, {
        productId: this.queryForm.productId,
        projectId: this.queryForm.projectId
      })).then(() => {
        this.$message.success('资料已上传至当前项目知识库')
        this.uploadVisible = false
        this.fetchList()
      }).finally(() => {
        this.uploading = false
      })
    },
    handleDocumentCommand(command, row) {
      if (command === 'parse') this.parseDoc(row)
      if (command === 'delete') this.deleteDoc(row)
    },
    parseDoc(row) {
      this.$confirm('确认解析该资料并写入当前项目知识库？', '提示').then(() => {
        return parseKnowledgeDocument({ documentId: row.id })
      }).then(res => {
        const data = res.data || {}
        this.$message.success(`解析完成，已生成 ${data.chunkCount || 0} 个分片`)
        this.fetchList()
      })
    },
    deleteDoc(row) {
      this.$confirm('确认从当前项目知识库删除该资料？', '提示').then(() => {
        return deleteKnowledgeDocument({ documentId: row.id })
      }).then(() => {
        this.$message.success('资料已删除')
        this.fetchList()
      })
    },
    typeText(type) {
      return Number(type) === 2 ? '飞书' : '文件'
    }
  }
}
</script>

<style scoped>
.knowledge-workspace { height: calc(100vh - 96px); min-height: 620px; display: flex; flex-direction: column; overflow: hidden; background: #fff; color: #253043; }
.workspace-header { height: 68px; box-sizing: border-box; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8edf3; }
h1 { margin: 0; font-size: 19px; line-height: 26px; color: #182230; }
p { margin: 2px 0 0; font-size: 12px; color: #8590a2; }
.header-actions { display: flex; gap: 8px; }
.workspace-body { flex: 1; min-height: 0; display: grid; grid-template-columns: 224px 340px minmax(480px, 1fr); }
.context-panel, .document-panel { min-height: 0; padding: 16px; border-right: 1px solid #e8edf3; overflow: auto; }
.panel-heading { color: #1f2a3d; font-size: 14px; font-weight: 700; }
.panel-subtitle { max-width: 220px; margin-top: 4px; overflow: hidden; color: #97a1b2; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.field-label { margin: 18px 0 7px; color: #7b8798; font-size: 12px; }
.project-label { margin-top: 22px; }
.context-panel .el-select { width: 100%; }
.context-empty, .document-empty { padding: 24px 4px; color: #a3adba; font-size: 12px; line-height: 1.7; text-align: center; }
.project-item { width: 100%; margin: 2px 0; padding: 9px 10px; display: flex; gap: 8px; align-items: center; border: 0; border-radius: 5px; background: transparent; color: #556173; cursor: pointer; font-size: 13px; text-align: left; transition: background .18s ease, color .18s ease; }
.project-item:hover { background: #f4f7fa; color: #324257; }
.project-item.active { background: #e9f3f1; color: #15816f; font-weight: 600; }
.project-item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scope-note { margin-top: 22px; padding-top: 15px; border-top: 1px solid #edf1f5; color: #96a0ae; font-size: 12px; line-height: 1.7; }
.scope-note i { margin-right: 3px; }
.document-panel { display: flex; flex-direction: column; }
.panel-topline { margin-bottom: 14px; display: flex; align-items: flex-start; justify-content: space-between; }
.document-summary { padding: 12px 0 8px; display: flex; gap: 12px; color: #9aa4b2; font-size: 12px; }
.document-list { flex: 1; min-height: 120px; overflow: auto; }
.document-item { padding: 11px 0; display: flex; gap: 10px; align-items: flex-start; border-top: 1px solid #f0f2f5; }
.document-icon { width: 28px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; background: #edf7f5; color: #44aa98; }
.document-main { flex: 1; min-width: 0; }
.document-name { overflow: hidden; color: #344054; font-size: 13px; line-height: 18px; text-overflow: ellipsis; white-space: nowrap; }
.document-meta { margin-top: 5px; display: flex; gap: 7px; color: #a0a9b6; font-size: 11px; }
.document-status.ready { color: #2c9c78; }
.more-button { border: 0; background: transparent; color: #a0a9b6; cursor: pointer; }
.document-pager { padding-top: 10px; border-top: 1px solid #edf1f5; text-align: center; }
.chat-panel { min-width: 0; }
.form-tip { margin-left: 9px; color: #9ba5b3; font-size: 12px; }
</style>
