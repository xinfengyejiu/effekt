<template>
  <div class="page-wrap">
    <page-section title="计划执行">
      <div class="filter-toolbar">
        <el-form :inline="true" size="small" class="filter-toolbar-form" @submit.native.prevent>
          <el-form-item label="产品名称">
            <el-input :value="productName" disabled style="width: 220px;"></el-input>
          </el-form-item>
          <el-form-item label="项目名称">
            <el-input :value="projectName" disabled style="width: 220px;"></el-input>
          </el-form-item>
          <el-form-item label="计划名称">
            <el-input :value="planNameDisplay" disabled style="width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchPlanCases">刷新</el-button>
            <el-button type="success" :loading="aiExecuting" @click="handleAiExecute()">AI执行</el-button>
          </el-form-item>
        </el-form>
        <div class="filter-toolbar-actions">
          <el-button size="small" @click="goBack">返回</el-button>
        </div>
      </div>
      <el-table
        v-loading="loading"
        :data="planCaseTableData"
        border
        style="margin-top: 12px;">
        <el-table-column prop="planCaseId" label="计划用例ID" width="120"></el-table-column>
        <el-table-column prop="caseKey" label="用例编号" min-width="120"></el-table-column>
        <el-table-column label="模块路径" min-width="200" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.modulePath || '—' }}</template>
        </el-table-column>
        <el-table-column label="模块名称" min-width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.moduleName || '—' }}</template>
        </el-table-column>
        <el-table-column prop="caseTitle" label="用例名称" min-width="220"></el-table-column>
        <el-table-column prop="actualResult" label="执行结果" min-width="180"></el-table-column>
        <el-table-column label="执行状态" width="110">
          <template slot-scope="scope">
            <el-tag size="mini" :type="formatExecuteStatusTag(scope.row.status)">{{ scope.row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template slot-scope="scope">
            <el-button type="text" @click="openExecuteDialog(scope.row)">执行</el-button>
            <el-button type="text" :loading="aiExecutingCaseId === scope.row.planCaseId" @click="handleAiExecute(scope.row)">AI执行</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 12px; text-align: right;"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="pageNo"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange">
      </el-pagination>

      <el-dialog
        title=""
        :visible.sync="executeDialogVisible"
        width="760px">
        <div class="detail-title">{{ selectedPlanCase ? (selectedPlanCase.caseTitle || selectedPlanCase.title || selectedPlanCase.caseKey || selectedPlanCase.caseId) : '' }}</div>
        <div class="detail-section">
          <div class="detail-section-title">前置条件</div>
          <div class="detail-text">{{ caseDetail.preconditions || '-' }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">执行步骤</div>
          <div class="detail-text">{{ formatSteps(caseDetail.steps) || '-' }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">预期结果</div>
          <div class="detail-text">{{ caseDetail.expected_results || caseDetail.expectedResults || '-' }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">执行结果</div>
          <el-input
            v-model="executeResultText"
            type="textarea"
            :rows="3"
            placeholder="失败或阻塞时必填">
          </el-input>
        </div>
        <span slot="footer">
          <el-button @click="executeDialogVisible = false">取消</el-button>
          <el-button type="success" :loading="submitting" @click="submitExecute(1)">通过</el-button>
          <el-button type="danger" :loading="submitting" @click="submitExecute(2)">失败</el-button>
          <el-button type="warning" :loading="submitting" @click="submitExecute(3)">阻塞</el-button>
        </span>
      </el-dialog>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getCaseDetail } from '@/api/caseApi'
import { aiExecutePlanCase, executePlanCase, getPlanCaseList } from '@/api/planApi'

export default {
  name: 'PlanExecute',
  components: { PageSection },
  data() {
    return {
      projectId: this.$route.query.projectId || '',
      planId: this.$route.query.planId || '',
      loading: false,
      planCaseTableData: [],
      total: 0,
      selectedPlanCase: null,
      caseDetail: {},
      executeDialogVisible: false,
      submitting: false,
      aiExecuting: false,
      aiExecutingCaseId: '',
      executeResultText: '',
      pageNo: 1,
      pageSize: 10
    }
  },
  computed: {
    productName() {
      return this.$route.query.productName || ''
    },
    projectName() {
      return this.$route.query.projectName || ''
    },
    planNameDisplay() {
      return this.$route.query.planName || ''
    }
  },
  methods: {
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchPlanCases()
    },
    handleCurrentChange(page) {
      this.pageNo = page
      this.fetchPlanCases()
    },
    fetchPlanCases() {
      if (!this.planId || !this.projectId) {
        this.planCaseTableData = []
        this.total = 0
        this.selectedPlanCase = null
        this.caseDetail = {}
        return
      }
      this.loading = true
      getPlanCaseList(this.projectId, this.planId, { pageNo: this.pageNo, pageSize: this.pageSize })
        .then(listRes => {
          const data = (listRes && listRes.data) || listRes || {}
          const list = data.list || data.items || []
          this.total = Number(data.total != null ? data.total : (Array.isArray(list) ? list.length : 0))
          this.planCaseTableData = (Array.isArray(list) ? list : []).map(item => ({
            planCaseId: item.id,
            caseId: item.case_id || item.caseId,
            status: item.status,
            statusLabel: this.formatExecuteStatus(item.status),
            actualResult: item.actual_result || item.actualResult || '',
            caseKey: item.case_key || item.caseKey || '',
            modulePath: item.module_path || item.modulePath || '',
            moduleName: item.module_name || item.moduleName || '',
            caseTitle: item.case_title || item.caseTitle || item.title || '',
            title: item.title || item.case_title || item.caseTitle || ''
          }))
        })
        .catch(() => {
          this.planCaseTableData = []
          this.total = 0
        })
        .finally(() => {
          this.loading = false
        })
    },
    openExecuteDialog(row) {
      if (!row) return
      this.selectedPlanCase = row
      this.executeResultText = ''
      if (!row.caseId) {
        this.caseDetail = {}
        this.executeDialogVisible = true
        return
      }
      getCaseDetail(this.projectId, row.caseId).then(res => {
        const data = (res && res.data) || res || {}
        this.caseDetail = data
        this.executeDialogVisible = true
      }).catch(() => {
        this.caseDetail = {}
        this.executeDialogVisible = true
      })
    },
    submitExecute(status) {
      if (!this.selectedPlanCase || !this.selectedPlanCase.planCaseId) {
        this.$message({ type: 'warning', message: '请先选择要执行的用例' })
        return
      }
      if ((status === 2 || status === 3) && !String(this.executeResultText || '').trim()) {
        this.$message({ type: 'warning', message: '失败或阻塞时请填写执行结果' })
        return
      }
      this.submitting = true
      executePlanCase(this.projectId, this.planId, this.selectedPlanCase.planCaseId, {
        status,
        actualResult: this.executeResultText,
        defectLinks: [],
        attachments: []
      }).then(() => {
        this.$message({ type: 'success', message: '执行结果已提交' })
        this.executeDialogVisible = false
        this.fetchPlanCases()
      }).finally(() => {
        this.submitting = false
      })
    },
    handleAiExecute(row) {
      if (!this.planId || !this.projectId) {
        this.$message({ type: 'warning', message: '缺少计划或项目信息' })
        return
      }
      const planCaseId = row && row.planCaseId
      const message = planCaseId ? '确认让 AI 执行当前用例并回填结果？' : '确认让 AI 执行当前计划下待执行/未通过的用例并回填结果？'
      this.$confirm(message, 'AI执行确认', { type: 'warning' }).then(() => {
        this.aiExecuting = !planCaseId
        this.aiExecutingCaseId = planCaseId || ''
        return aiExecutePlanCase(this.projectId, this.planId, planCaseId ? { id: planCaseId } : {})
      }).then(res => {
        const data = (res && res.data) || res || {}
        this.$message({
          type: 'success',
          message: `AI执行完成：共${data.total || 0}条，通过${data.passed || 0}条，失败${data.failed || 0}条，阻塞${data.blocked || 0}条`
        })
        this.fetchPlanCases()
      }).catch(err => {
        if (err !== 'cancel' && err !== 'close') {
          this.$message({ type: 'error', message: (err && err.message) || 'AI执行失败' })
        }
      }).finally(() => {
        this.aiExecuting = false
        this.aiExecutingCaseId = ''
      })
    },
    formatSteps(steps) {
      if (!steps) return ''
      if (typeof steps === 'string') return steps
      if (Array.isArray(steps)) {
        return steps.map(item => {
          if (typeof item === 'string') return item
          return item.action || item.step || item.text || item.content || ''
        }).filter(Boolean).join('\n')
      }
      return String(steps)
    },
    formatExecuteStatus(status) {
      const map = { 0: '待执行', 1: '通过', 2: '失败', 3: '阻塞' }
      return map[status] || status
    },
    formatExecuteStatusTag(status) {
      const map = { 0: 'info', 1: 'success', 2: 'danger', 3: 'warning' }
      return map[status] || 'info'
    },
    goBack() {
      this.$router.push({
        path: '/test-platform/plan',
        query: {
          productId: this.$route.query.productId || undefined,
          projectId: this.projectId || undefined
        }
      })
    }
  },
  created() {
    this.fetchPlanCases()
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}

.filter-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.filter-toolbar-form {
  flex: 1;
  min-width: 0;
}

.filter-toolbar-actions {
  flex-shrink: 0;
  padding-top: 4px;
}

.detail-panel {
  margin-top: 16px;
}

.detail-title {
  margin-bottom: 8px;
  font-weight: 600;
  color: #303133;
  font-size: 18px;
  line-height: 1.4;
}

.detail-text {
  white-space: pre-wrap;
  color: #606266;
  line-height: 1.5;
}

.detail-section {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 10px;
}

.detail-section-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

</style>
