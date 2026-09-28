<template>
  <div class="page-wrap explore-session-page">
    <page-section title="探索 Session">
      <template slot="extra">
        <el-button size="small" type="primary" icon="el-icon-plus" @click="openCreate">新建 Session</el-button>
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
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable placeholder="编号/标题" style="width:180px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
          <el-button icon="el-icon-refresh" :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="Session 编号" min-width="150" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-link type="primary" @click="goWorkspace(scope.row)">{{ scope.row.sessionNo || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="200" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.title || '-' }}</template>
        </el-table-column>
        <el-table-column label="产品" min-width="120" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.productName || '-' }}</template>
        </el-table-column>
        <el-table-column label="项目" min-width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.projectName || '-' }}</template>
        </el-table-column>
        <el-table-column label="环境" width="100" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.environment || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.createdTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" icon="el-icon-view" @click="goWorkspace(scope.row)">工作台</el-button>
            <el-button
              v-if="scope.row.status === 'draft'"
              type="text"
              icon="el-icon-video-play"
              :loading="rowLoading(scope.row, 'start')"
              @click="startSession(scope.row)"
            >开始</el-button>
            <el-button
              v-if="scope.row.status === 'ended'"
              type="text"
              icon="el-icon-folder-checked"
              :loading="rowLoading(scope.row, 'archive')"
              @click="archiveSession(scope.row)"
            >归档</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10,20,50,100]"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </page-section>

    <el-dialog title="新建探索 Session" :visible.sync="createVisible" width="620px" :close-on-click-modal="false">
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
        <el-form-item label="标题" prop="title">
          <el-input v-model.trim="createForm.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="章程">
          <el-input v-model="createForm.charter" type="textarea" :rows="3" placeholder="本次探索要测什么" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="不测什么">
          <el-input v-model="createForm.outOfScope" type="textarea" :rows="2" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item label="环境">
          <el-input v-model.trim="createForm.environment" maxlength="64" placeholder="如 test / staging" />
        </el-form-item>
        <el-form-item label="创建后">
          <el-radio-group v-model="createForm.status">
            <el-radio label="draft">保存草稿</el-radio>
            <el-radio label="active">立即开始</el-radio>
          </el-radio-group>
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
import {
  archiveExploreSession,
  createExploreSession,
  getExploreSessionList,
  startExploreSession
} from '@/api/exploreSessionApi'

const STATUSES = [
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '进行中' },
  { value: 'ended', label: '已结束' },
  { value: 'archived', label: '已归档' }
]

export default {
  name: 'ExploreSessionList',
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
      queryForm: { productId: '', projectId: '', status: '', keyword: '' },
      createForm: this.defaultCreateForm(),
      createRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
      },
      statusOptions: STATUSES
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    defaultCreateForm() {
      return {
        productId: '',
        projectId: '',
        title: '',
        charter: '',
        outOfScope: '',
        environment: '',
        status: 'draft'
      }
    },
    apiData(res) {
      return (res && res.data) || res || {}
    },
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
      getExploreSessionList(Object.assign({}, this.queryForm, {
        pageNo: this.pageNo,
        pageSize: this.pageSize
      })).then(res => {
        const data = this.apiData(res)
        this.rows = data.list || data.items || []
        this.total = data.total || this.rows.length
      }).finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', status: '', keyword: '' }
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
        const payload = Object.assign({}, this.createForm, {
          productName: this.productName(this.createForm.productId),
          projectName: this.projectName(this.createForm.projectId, this.createProjectOptions)
        })
        createExploreSession(payload).then(res => {
          const data = this.apiData(res)
          this.$message.success('Session 已创建')
          this.createVisible = false
          if (data.id) {
            this.$router.push({ path: '/explore-session/workspace', query: { id: data.id } })
          } else {
            this.fetchList()
          }
        }).finally(() => { this.createLoading = false })
      })
    },
    goWorkspace(row) {
      this.$router.push({ path: '/explore-session/workspace', query: { id: row.id } })
    },
    rowLoading(row, action) {
      return !!this.actionLoading[`${row.id}:${action}`]
    },
    startSession(row) {
      this.$set(this.actionLoading, `${row.id}:start`, true)
      startExploreSession({ sessionId: row.id }).then(() => {
        this.$message.success('已开始')
        this.goWorkspace(row)
      }).finally(() => { this.$delete(this.actionLoading, `${row.id}:start`) })
    },
    archiveSession(row) {
      this.$set(this.actionLoading, `${row.id}:archive`, true)
      archiveExploreSession({ sessionId: row.id }).then(() => {
        this.$message.success('已归档')
        this.fetchList()
      }).finally(() => { this.$delete(this.actionLoading, `${row.id}:archive`) })
    },
    statusLabel(value) {
      return (STATUSES.find(item => item.value === value) || {}).label || value || '-'
    },
    statusTag(value) {
      return { draft: 'info', active: 'success', ended: 'warning', archived: '' }[value] || 'info'
    }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
@media (max-width: 768px) {
  .explore-session-page /deep/ .el-dialog { width: 94% !important; }
}
</style>
