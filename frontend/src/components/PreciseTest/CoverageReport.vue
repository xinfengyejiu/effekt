<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-覆盖率报告">
      <template slot="extra">
        <el-button size="small" :loading="loading" @click="fetchList">刷新</el-button>
        <el-button size="small" type="primary" @click="dialogVisible = true">上传 JaCoCo XML</el-button>
      </template>

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
        <el-form-item label="报告编号">
          <el-input v-model.trim="queryForm.reportNo" clearable placeholder="请输入报告编号" style="width:180px;" />
        </el-form-item>
        <el-form-item label="分析编号">
          <el-input v-model.trim="queryForm.analysisNo" clearable placeholder="请输入分析编号" style="width:180px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="search">查询</el-button>
          <el-button :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="coverages" border style="width:100%;">
        <el-table-column prop="report_no" label="报告编号" min-width="150" />
        <el-table-column label="产品名称" min-width="120" show-overflow-tooltip>
          <template slot-scope="scope">{{ preciseProductName(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="项目名称" min-width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ preciseProjectName(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="分析编号" min-width="170" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.analysis_no || scope.row.analysisNo || scope.row.analysis_id || scope.row.analysisId || '-' }}</template>
        </el-table-column>
        <el-table-column prop="coverage_type" label="类型" width="110" />
        <el-table-column prop="tool_type" label="工具" width="110" />
        <el-table-column label="摘要" min-width="240" show-overflow-tooltip>
          <template slot-scope="scope">{{ summaryText(scope.row.summary_json || scope.row.summaryJson) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template slot-scope="scope">
            <el-button type="text" :loading="isRowActionLoading(scope.row, 'view')" :disabled="isRowBusy(scope.row)" @click="view(scope.row)">查看</el-button>
            <el-button type="text" :loading="isRowActionLoading(scope.row, 'calc')" :disabled="isRowBusy(scope.row)" @click="calc(scope.row)">算增量</el-button>
            <el-button type="text" :loading="isRowActionLoading(scope.row, 'ai')" :disabled="isRowBusy(scope.row)" @click="aiRisk(scope.row)">AI风险</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </page-section>

    <el-dialog title="上传 JaCoCo XML" :visible.sync="dialogVisible" width="520px">
      <el-form label-width="100px" size="small">
        <el-form-item label="分析ID"><el-input v-model.trim="uploadForm.analysisId" /></el-form-item>
        <el-form-item label="执行ID"><el-input v-model.trim="uploadForm.executionId" /></el-form-item>
        <el-form-item label="文件"><input type="file" accept=".xml" @change="onFileChange" /></el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="upload">上传</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  getPreciseCoverageList,
  uploadPreciseCoverage,
  calculatePreciseIncremental,
  createPreciseAiRiskAnalysis
} from '@/api/preciseTestApi'
import productProjectSelectMixin from './productProjectSelectMixin'

export default {
  name: 'PreciseCoverageReport',
  components: { PageSection },
  mixins: [productProjectSelectMixin],
  data() {
    return {
      loading: false,
      uploading: false,
      rowActionLoading: {},
      dialogVisible: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      queryForm: {
        productId: '',
        projectId: '',
        reportNo: '',
        analysisNo: ''
      },
      file: null,
      uploadForm: {
        analysisId: this.$route.query.analysisId || this.$route.query.id || '',
        executionId: ''
      }
    }
  },
  computed: {
    coverages() {
      return this.rows
    }
  },
  watch: {
    '$route.query.analysisId': 'syncQueryAnalysisId',
    '$route.query.id': 'syncQueryAnalysisId'
  },
  created() {
    this.syncQueryAnalysisId()
    this.fetchList()
  },
  methods: {
    listOf(res) {
      const d = res && res.data ? res.data : res || {}
      return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 }
    },
    fetchList() {
      this.loading = true
      const params = Object.assign({}, this.queryForm, {
        analysisId: this.uploadForm.analysisId || undefined,
        pageNo: this.pageNo,
        pageSize: this.pageSize
      })
      return getPreciseCoverageList(params)
        .then(res => {
          const d = this.listOf(res)
          this.rows = d.rows
          this.total = d.total || this.rows.length
          this.fillPreciseProjectNames(this.rows)
        })
        .finally(() => {
          this.loading = false
        })
    },
    search() {
      this.pageNo = 1
      this.fetchList()
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', reportNo: '', analysisNo: '' }
      this.queryProjectOptions = []
      this.uploadForm.analysisId = ''
      this.pageNo = 1
      this.fetchList()
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchList()
    },
    handlePageChange(page) {
      this.pageNo = page
      this.fetchList()
    },
    onQueryProductChange(productId) {
      this.queryForm.projectId = ''
      this.loadProjectOptions(productId, 'queryProjectOptions')
    },
    syncQueryAnalysisId() {
      const id = this.$route.query.analysisId || this.$route.query.id
      if (id) {
        this.uploadForm.analysisId = String(id)
        this.fetchList()
      }
    },
    onFileChange(e) {
      this.file = e.target.files && e.target.files[0]
    },
    upload() {
      if (!this.uploadForm.analysisId || !this.file) return this.$message.warning('请选择分析ID和文件')
      const fd = new FormData()
      fd.append('analysisId', this.uploadForm.analysisId)
      if (this.uploadForm.executionId) fd.append('executionId', this.uploadForm.executionId)
      fd.append('file', this.file)
      this.uploading = true
      uploadPreciseCoverage(fd)
        .then(() => {
          this.$message.success('上传成功')
          this.dialogVisible = false
          this.fetchList()
        })
        .finally(() => {
          this.uploading = false
        })
    },
    rowActionKey(row, action) {
      return String(row.id) + ':' + action
    },
    isRowActionLoading(row, action) {
      return !!this.rowActionLoading[this.rowActionKey(row, action)]
    },
    isRowBusy(row) {
      return ['view', 'calc', 'ai'].some(action => this.isRowActionLoading(row, action))
    },
    runRowAction(row, action, request) {
      const key = this.rowActionKey(row, action)
      if (this.rowActionLoading[key]) return Promise.resolve()
      this.$set(this.rowActionLoading, key, true)
      return request()
        .catch(err => {
          this.$message.error((err && err.message) || '操作失败')
          throw err
        })
        .finally(() => {
          this.$delete(this.rowActionLoading, key)
        })
    },
    view(row) {
      this.$router.push({
        path: '/precise/coverage/detail',
        query: {
          coverageId: row.id,
          analysisId: row.analysis_id || row.analysisId || this.uploadForm.analysisId || ''
        }
      })
    },
    calc(row) {
      this.runRowAction(row, 'calc', () => calculatePreciseIncremental(row.id).then(() => {
        this.$message.success('增量覆盖率已计算')
        return this.fetchList()
      }))
    },
    aiRisk(row) {
      this.runRowAction(row, 'ai', () => createPreciseAiRiskAnalysis(row.id).then(() => {
        this.$message.success('AI风险分析完成')
        return this.fetchList()
      }))
    },
    summaryText(v) {
      try {
        const obj = typeof v === 'string' ? JSON.parse(v) : v
        if (!obj) return '-'
        if (obj.incremental) {
          const inc = obj.incremental
          return '变更行 ' + (inc.changedLines || 0) + '，已覆盖 ' + (inc.coveredChangedLines || 0) + '，未覆盖 ' + (inc.uncoveredChangedLines || 0) + '，覆盖率 ' + (inc.lineRate || 0) + '%'
        }
        if (obj.summary) return obj.summary
        return JSON.stringify(obj)
      } catch (e) {
        return v || '-'
      }
    }
  }
}
</script>

<style scoped>
.pager-wrap {
  margin-top: 16px;
  text-align: right;
}
</style>
