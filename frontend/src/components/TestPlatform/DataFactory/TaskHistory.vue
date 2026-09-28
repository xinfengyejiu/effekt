<template>
  <div class="page-wrap">
    <page-section title="造数任务历史">
      <template slot="extra">
        <el-button size="small" @click="goFactory">返回场景列表</el-button>
      </template>
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select
            v-model="productId"
            filterable
            clearable
            placeholder="请选择产品"
            style="width: 180px;"
            @change="onProductChange">
            <el-option
              v-for="item in productOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="projectId"
            filterable
            clearable
            placeholder="请选择项目"
            style="width: 200px;"
            :disabled="!productId"
            @change="onProjectChange">
            <el-option
              v-for="item in projectOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="场景ID">
          <el-input v-model="builderId" clearable style="width: 120px;"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :disabled="!projectId" @click="fetchList">查询列表</el-button>
        </el-form-item>
        <el-form-item label="任务ID">
          <el-input v-model="taskId" style="width: 140px;"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button @click="fetchStatus">查单条</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="tableData" border style="margin-top: 12px;">
        <el-table-column prop="id" label="任务ID" width="90"></el-table-column>
        <el-table-column prop="builder_id" label="场景ID" width="90"></el-table-column>
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">{{ statusLabel(scope.row.status) }}</template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" min-width="160"></el-table-column>
        <el-table-column prop="completed_time" label="完成时间" min-width="160"></el-table-column>
        <el-table-column prop="error_message" label="错误" min-width="180" show-overflow-tooltip></el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="showDetail(scope.row)">结果</el-button>
            <el-button
              v-if="scope.row.status === 2"
              type="text"
              @click="saveScene(scope.row)">另存为场景</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; text-align: right;">
        <el-pagination
          :current-page="pageNo"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handleCurrentChange">
        </el-pagination>
      </div>
      <div v-if="taskResult" style="margin-top: 16px;">
        <div class="hint">任务详情 / 结果</div>
        <json-viewer :value="taskResult"></json-viewer>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import JsonViewer from '@/components/TestPlatform/common/JsonViewer'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getBuilderDetail,
  getDataTaskList,
  getDataTaskStatus,
  saveAsScene
} from '@/api/dataFactoryApi'
import {
  pickIdFromOptions,
  readLastProductProjectCache,
  saveLastProductProjectCache
} from '@/utils/lastProductProjectCache'

export default {
  name: 'TaskHistory',
  components: { PageSection, JsonViewer },
  data() {
    return {
      loading: false,
      productId: '',
      projectId: '',
      productOptions: [],
      projectOptions: [],
      builderId: this.$route.query.builderId || '',
      taskId: this.$route.query.taskId || '',
      pageNo: 1,
      pageSize: 20,
      total: 0,
      tableData: [],
      taskResult: null
    }
  },
  methods: {
    listOf(res) {
      const data = (res && res.data) || res || {}
      return data.list || data.items || data.data || []
    },
    statusLabel(s) {
      return ({ 0: '等待', 1: '执行中', 2: '成功', 3: '失败' })[s] || s
    },
    routeQuery() {
      const q = {}
      if (this.productId) q.productId = this.productId
      if (this.projectId) q.projectId = this.projectId
      return q
    },
    loadProducts() {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.productOptions = this.listOf(res)
      }).catch(() => { this.productOptions = [] })
    },
    loadProjects(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        this.projectOptions = this.listOf(res)
      }).catch(() => { this.projectOptions = [] })
    },
    onProductChange(val) {
      this.projectId = ''
      this.tableData = []
      this.total = 0
      this.loadProjects(val)
    },
    onProjectChange(val) {
      if (this.productId && val) saveLastProductProjectCache(this.productId, val)
      this.pageNo = 1
      if (val) this.fetchList()
      else {
        this.tableData = []
        this.total = 0
      }
    },
    restoreSelection() {
      const routeProductId = this.$route.query.productId
      const routeProjectId = this.$route.query.projectId
      const cached = readLastProductProjectCache()
      this.productId = ''
      this.projectId = ''
      return this.loadProducts().then(() => {
        let productId = routeProductId
        let projectId = routeProductId ? routeProjectId : ''
        if (!productId && cached && cached.productId != null && cached.productId !== '') {
          productId = cached.productId
          projectId = cached.projectId
        }
        if (productId === '' || productId === undefined || productId === null) return
        const pickedProduct = pickIdFromOptions(this.productOptions, productId)
        const productExists = (this.productOptions || []).some(p => String(p.id) === String(pickedProduct))
        if (!productExists) return
        this.productId = pickedProduct
        return this.loadProjects(this.productId).then(() => {
          if (projectId === '' || projectId === undefined || projectId === null) return
          const has = (this.projectOptions || []).some(p => String(p.id) === String(projectId))
          if (has) this.projectId = pickIdFromOptions(this.projectOptions, projectId)
        })
      })
    },
    goFactory() {
      this.$router.push({ path: '/data-tools/factory', query: this.routeQuery() })
    },
    fetchList() {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      this.loading = true
      const params = { pageNo: this.pageNo, pageSize: this.pageSize }
      if (this.builderId) params.builderId = this.builderId
      getDataTaskList(this.projectId, params).then(res => {
        const data = (res && res.data) || res || {}
        this.tableData = data.list || []
        this.total = data.total || 0
      }).catch(() => {
        this.tableData = []
        this.total = 0
      }).finally(() => {
        this.loading = false
      })
    },
    handleCurrentChange(page) {
      this.pageNo = page
      this.fetchList()
    },
    fetchStatus() {
      if (!this.taskId) {
        this.$message({ type: 'warning', message: '请输入任务ID' })
        return
      }
      getDataTaskStatus(this.projectId, this.taskId).then(res => {
        this.taskResult = (res && res.data) || res || {}
      }).catch(() => {
        this.taskResult = {}
      })
    },
    showDetail(row) {
      this.taskId = row.id
      this.taskResult = {
        id: row.id,
        status: row.status,
        params: row.params,
        result_data: row.result_data,
        error_message: row.error_message
      }
    },
    saveScene(row) {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      const builderId = row.builder_id || row.builderId
      if (!builderId) {
        this.$message({ type: 'warning', message: '缺少场景ID' })
        return
      }
      this.$prompt('另存场景名称', '另存为场景', {
        inputValue: '场景副本-' + (row.id || ''),
        closeOnClickModal: false
      }).then(({ value }) => {
        return getBuilderDetail(this.projectId, builderId).then(res => {
          const detail = (res && res.data) || res || {}
          return saveAsScene({
            projectId: this.projectId,
            name: value,
            description: detail.description || ('从任务 ' + row.id + ' 另存'),
            definition: detail.definition,
            inputSchema: detail.input_schema || detail.inputSchema || {},
            outputExample: (row.result_data && row.result_data.output) || detail.output_example || {},
            tags: detail.tags || ['另存'],
            source: 'saved_from_task'
          })
        })
      }).then(() => {
        this.$message({ type: 'success', message: '已另存为场景' })
      }).catch(() => {})
    }
  },
  created() {
    this.restoreSelection().then(() => {
      if (this.projectId) this.fetchList()
      if (this.taskId) this.fetchStatus()
    })
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.hint {
  color: #666;
  font-size: 13px;
  margin-bottom: 8px;
}
</style>
