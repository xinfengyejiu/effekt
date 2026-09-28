<template>
  <div class="page-wrap">
    <page-section title="造数工厂 · 场景模板">
      <template slot="extra">
        <el-button type="primary" size="small" :disabled="!projectId" @click="openAiDialog">对话造数</el-button>
        <el-button size="small" :disabled="!projectId" @click="goEditor()">手工新建</el-button>
        <el-button size="small" :disabled="!projectId" @click="goTasks">任务历史</el-button>
        <el-button size="small" @click="goMock">Mock服务</el-button>
      </template>
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select
            v-model="productId"
            filterable
            clearable
            placeholder="请选择产品"
            style="width: 200px;"
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
            style="width: 220px;"
            :disabled="!productId"
            @change="onProjectChange">
            <el-option
              v-for="item in projectOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="tag" placeholder="如 AI" clearable style="width: 120px;"></el-input>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="source" clearable placeholder="全部" style="width: 140px;">
            <el-option label="手工" value="manual"></el-option>
            <el-option label="AI" value="ai"></el-option>
            <el-option label="任务另存" value="saved_from_task"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :disabled="!projectId" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="tableData" border style="margin-top: 16px;">
        <el-table-column prop="name" label="场景名称" min-width="160"></el-table-column>
        <el-table-column label="标签" min-width="140">
          <template slot-scope="scope">
            <el-tag
              v-for="t in (scope.row.tags || [])"
              :key="t"
              size="mini"
              style="margin-right: 4px;">{{ t }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="110">
          <template slot-scope="scope">{{ sourceLabel(scope.row.source) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip></el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openRun(scope.row)">一键跑</el-button>
            <el-button type="text" @click="goEditor(scope.row)">编辑</el-button>
            <el-button type="text" @click="goTasks(scope.row)">任务</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; text-align: right;">
        <el-pagination
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange">
        </el-pagination>
      </div>
    </page-section>

    <ai-data-chat-dialog
      :visible.sync="aiVisible"
      :project-id="projectId"
      :product-id="productId"
      :product-name="selectedProductName"
      :project-name="selectedProjectName"
      @executed="onChatExecuted" />

    <el-dialog title="确认执行场景" :visible.sync="runVisible" width="640px" :close-on-click-modal="false">
      <p class="hint">场景：{{ runRow && runRow.name }}。请确认参数后执行（会写目标库，请勿选生产）。</p>
      <el-input v-model="paramsText" type="textarea" :rows="8" placeholder='参数 JSON，如 {"phone":"13800000000"}'></el-input>
      <div v-if="lastResult" style="margin-top: 12px;">
        <div class="hint">最近执行结果</div>
        <json-viewer :value="lastResult"></json-viewer>
      </div>
      <div slot="footer">
        <el-button @click="runVisible = false">取消</el-button>
        <el-button type="primary" :loading="runLoading" @click="doExecute">确认执行</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import JsonViewer from '@/components/TestPlatform/common/JsonViewer'
import AiDataChatDialog from '@/components/TestPlatform/DataFactory/AiDataChatDialog'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { executeBuilder, getBuilderList } from '@/api/dataFactoryApi'
import {
  pickIdFromOptions,
  readLastProductProjectCache,
  saveLastProductProjectCache
} from '@/utils/lastProductProjectCache'

export default {
  name: 'BuilderList',
  components: { PageSection, JsonViewer, AiDataChatDialog },
  data() {
    return {
      loading: false,
      productId: '',
      projectId: '',
      productOptions: [],
      projectOptions: [],
      tag: '',
      source: '',
      pageNo: 1,
      pageSize: 10,
      total: 0,
      tableData: [],
      aiVisible: false,
      runVisible: false,
      runLoading: false,
      runRow: null,
      paramsText: '{\n  "phone": "",\n  "count": 1\n}',
      lastResult: null
    }
  },
  computed: {
    selectedProductName() {
      const hit = (this.productOptions || []).find(item => String(item.id) === String(this.productId))
      return (hit && hit.name) || ''
    },
    selectedProjectName() {
      const hit = (this.projectOptions || []).find(item => String(item.id) === String(this.projectId))
      return (hit && hit.name) || ''
    }
  },
  methods: {
    listOf(res) {
      const data = (res && res.data) || res || {}
      return data.list || data.items || data.data || []
    },
    sourceLabel(v) {
      return ({ manual: '手工', ai: 'AI', saved_from_task: '任务另存' })[v] || (v || '手工')
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
      }).catch(() => {
        this.productOptions = []
      })
    },
    loadProjects(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        this.projectOptions = this.listOf(res)
      }).catch(() => {
        this.projectOptions = []
      })
    },
    onProductChange(val) {
      this.projectId = ''
      this.tableData = []
      this.total = 0
      this.loadProjects(val)
    },
    onProjectChange(val) {
      if (this.productId && val) {
        saveLastProductProjectCache(this.productId, val)
      }
      this.pageNo = 1
      if (val) this.fetchList()
      else {
        this.tableData = []
        this.total = 0
      }
    },
    restoreSelection() {
      // 未选中时保持为空：不沿用孤立的 projectId（如历史默认 ?projectId=1），避免误查报错
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
          if (!has) return
          this.projectId = pickIdFromOptions(this.projectOptions, projectId)
        })
      })
    },
    fetchList() {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        this.tableData = []
        this.total = 0
        return
      }
      this.loading = true
      const params = {
        pageNo: this.pageNo,
        pageSize: this.pageSize
      }
      if (this.tag) params.tag = this.tag
      if (this.source) params.source = this.source
      getBuilderList(this.projectId, params).then(res => {
        const data = (res && res.data) || res || {}
        this.tableData = data.list || data.items || []
        this.total = data.total || this.tableData.length
      }).catch(() => {
        this.tableData = []
        this.total = 0
      }).finally(() => {
        this.loading = false
      })
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchList()
    },
    handleCurrentChange(page) {
      this.pageNo = page
      this.fetchList()
    },
    goEditor(row) {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      this.$router.push({
        path: '/data-tools/factory/editor',
        query: Object.assign({}, this.routeQuery(), { builderId: row && row.id })
      })
    },
    goTasks(row) {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      const query = this.routeQuery()
      if (row && row.id) query.builderId = row.id
      this.$router.push({ path: '/data-tools/factory/task', query })
    },
    goMock() {
      this.$router.push({ path: '/data-tools/factory/mock', query: this.routeQuery() })
    },
    openAiDialog() {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      this.aiVisible = true
    },
    onChatExecuted() {
      this.fetchList()
    },
    openRun(row) {
      this.runRow = row
      this.lastResult = null
      const schema = row.input_schema || row.inputSchema || {}
      const props = (schema && schema.properties) || {}
      const defaults = {}
      Object.keys(props).forEach(key => {
        defaults[key] = props[key].default != null ? props[key].default : ''
      })
      if (!Object.keys(defaults).length) {
        defaults.phone = ''
        defaults.count = 1
      }
      this.paramsText = JSON.stringify(defaults, null, 2)
      this.runVisible = true
    },
    doExecute() {
      let params = {}
      try {
        params = JSON.parse(this.paramsText || '{}')
      } catch (e) {
        this.$message({ type: 'error', message: '参数 JSON 格式错误' })
        return
      }
      this.runLoading = true
      executeBuilder(this.projectId, this.runRow.id, { params }).then(res => {
        const data = (res && res.data) || res || {}
        this.lastResult = data
        this.$message({ type: 'success', message: '执行成功，任务ID：' + (data.taskId || '-') })
        this.fetchList()
      }).finally(() => {
        this.runLoading = false
      })
    }
  },
  created() {
    this.restoreSelection().then(() => {
      if (this.projectId) this.fetchList()
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
