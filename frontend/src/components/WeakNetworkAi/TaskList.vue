<template>
  <div class="page-wrap">
    <page-section title="弱网 AI 任务">
      <template slot="extra">
        <el-button size="small" type="primary" icon="el-icon-plus" @click="openCreate">新建任务</el-button>
      </template>
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="一期半自动：AI 出检查点 → 下载弱网包手测 → 上传证据 → AI 标存疑 → 人确认才转 Bug。AI 不改控网参数。"
        style="margin-bottom:12px;"
      />
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width:120px;">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%;margin-top:12px;">
        <el-table-column label="任务编号" min-width="150">
          <template slot-scope="scope">
            <el-link type="primary" @click="goDetail(scope.row)">{{ scope.row.taskNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220" prop="title" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="产品" min-width="120" prop="productName" show-overflow-tooltip />
        <el-table-column label="项目" min-width="120" prop="projectName" show-overflow-tooltip />
        <el-table-column label="创建时间" min-width="160" prop="createdTime" />
        <el-table-column label="操作" width="100" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row)">进入</el-button>
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

    <el-dialog title="新建弱网 AI 任务" :visible.sync="createVisible" width="640px" :close-on-click-modal="false">
      <el-form ref="createForm" :model="createForm" :rules="createRules" label-width="90px" size="small">
        <el-form-item label="产品" prop="productId">
          <el-select v-model="createForm.productId" filterable style="width:100%;" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="createForm.projectId" filterable :disabled="!createForm.productId" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model.trim="createForm.title" placeholder="可空，默认取 brief 前几字" />
        </el-form-item>
        <el-form-item label="功能描述" prop="brief">
          <el-input v-model="createForm.brief" type="textarea" :rows="6" placeholder="例如：登录后进入首页，弱网下应能加载列表并允许重试…" />
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
import { getWeakNetworkAiTasks, createWeakNetworkAiTask } from '@/api/weakNetworkAiApi'

const STATUSES = [
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '已确认' },
  { value: 'collecting', label: '收集证据' },
  { value: 'judged', label: '已判定' },
  { value: 'closed', label: '已关闭' }
]

export default {
  name: 'WeakNetworkAiTaskList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      queryForm: { status: '', keyword: '' },
      statusOptions: STATUSES,
      createVisible: false,
      createLoading: false,
      createForm: { productId: '', projectId: '', title: '', brief: '' },
      createRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        brief: [{ required: true, message: '请填写功能描述', trigger: 'blur' }]
      },
      productOptions: [],
      projectOptions: []
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    statusLabel(v) {
      const hit = STATUSES.find(s => s.value === v)
      return hit ? hit.label : v
    },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        const data = (res && res.data) || res || {}
        this.productOptions = data.list || data.records || []
      }).catch(() => {})
    },
    onProductChange() {
      this.createForm.projectId = ''
      this.projectOptions = []
      if (!this.createForm.productId) return
      getProjectList({ productId: this.createForm.productId, pageNo: 1, pageSize: 200 }).then(res => {
        const data = (res && res.data) || res || {}
        this.projectOptions = data.list || data.records || []
      }).catch(() => {})
    },
    fetchList() {
      this.loading = true
      getWeakNetworkAiTasks(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize }))
        .then(res => {
          const data = (res && res.data) || res || {}
          this.rows = data.list || []
          this.total = data.total || 0
        })
        .finally(() => { this.loading = false })
    },
    openCreate() {
      this.createForm = { productId: '', projectId: '', title: '', brief: '' }
      this.createVisible = true
    },
    submitCreate() {
      this.$refs.createForm.validate(valid => {
        if (!valid) return
        const product = this.productOptions.find(p => String(p.id) === String(this.createForm.productId))
        const project = this.projectOptions.find(p => String(p.id) === String(this.createForm.projectId))
        this.createLoading = true
        createWeakNetworkAiTask({
          title: this.createForm.title,
          brief: this.createForm.brief,
          productId: this.createForm.productId,
          productName: product ? product.name : '',
          projectId: this.createForm.projectId,
          projectName: project ? project.name : ''
        }).then(res => {
          const data = (res && res.data) || res || {}
          const task = data.task || data
          this.createVisible = false
          this.$message.success('已创建')
          if (task.taskId) this.goDetail({ taskId: task.taskId })
          else this.fetchList()
        }).finally(() => { this.createLoading = false })
      })
    },
    goDetail(row) {
      this.$router.push({ path: '/weak-network-ai/detail', query: { taskId: row.taskId } })
    }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 12px; text-align: right; }
</style>
