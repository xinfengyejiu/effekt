<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-回归推荐">
      <template slot="extra">
        <el-button size="small" :loading="loading" @click="fetchList">刷新</el-button>
        <el-button size="small" type="primary" :loading="generating" @click="generate">生成推荐</el-button>
        <el-button size="small" type="success" :loading="executing" @click="execute">发起精准回归</el-button>
      </template>

      <el-alert
        v-if="analysisId"
        :title="'当前分析：' + (analysis.analysis_no || analysis.analysisNo || analysisId)"
        type="info"
        :closable="false"
        style="margin-bottom:12px;"
      />
      <el-alert
        v-else
        title="正在自动选择最新变更分析，也可以从变更分析详情进入。"
        type="warning"
        :closable="false"
        style="margin-bottom:12px;"
      />

      <el-table v-loading="loading" :data="rows" border style="width:100%;" @selection-change="selected=$event">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="recommend_level" label="等级" width="90" />
        <el-table-column prop="risk_level" label="风险" width="90" />
        <el-table-column prop="case_id" label="用例ID" width="90" />
        <el-table-column prop="case_key" label="用例编号" width="150" show-overflow-tooltip />
        <el-table-column prop="case_title" label="用例标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="script_id" label="脚本ID" width="90" />
        <el-table-column prop="module_name" label="模块" min-width="130" show-overflow-tooltip />
        <el-table-column prop="api_path" label="接口" min-width="180" show-overflow-tooltip />
        <el-table-column prop="reason" label="规则原因" min-width="240" show-overflow-tooltip />
        <el-table-column prop="ai_reason" label="AI原因" min-width="240" show-overflow-tooltip />
        <el-table-column label="采纳" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.accepted ? 'success' : 'info'">{{ scope.row.accepted ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="accept([scope.row.id], 1)">采纳</el-button>
            <el-button type="text" @click="accept([scope.row.id], 0)">忽略</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="actions">
        <el-button size="small" @click="acceptSelected(1)">批量采纳</el-button>
        <el-button size="small" @click="acceptSelected(0)">批量忽略</el-button>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  getPreciseAnalysisList,
  getPreciseRecommendations,
  generatePreciseRecommendations,
  acceptPreciseRecommendations,
  executePreciseAnalysis
} from '@/api/preciseTestApi'

export default {
  name: 'PreciseRecommendation',
  components: { PageSection },
  data() {
    return {
      loading: false,
      generating: false,
      executing: false,
      currentAnalysisId: this.$route.query.analysisId || this.$route.query.id || '',
      analysis: {},
      rows: [],
      selected: []
    }
  },
  computed: {
    analysisId() {
      return this.currentAnalysisId || this.$route.query.analysisId || this.$route.query.id || ''
    }
  },
  created() {
    this.initPage()
  },
  methods: {
    listOf(res) {
      const d = res && res.data ? res.data : res || {}
      return d.items || d.list || d.data || []
    },
    initPage() {
      if (this.analysisId) return this.fetchList()
      return this.loadLatestAnalysis().then(() => this.fetchList())
    },
    loadLatestAnalysis() {
      this.loading = true
      return getPreciseAnalysisList({ pageNo: 1, pageSize: 20 })
        .then(res => {
          const rows = this.listOf(res)
          const latest = rows.slice().sort((a, b) => Number(b.id || 0) - Number(a.id || 0))[0]
          if (latest && latest.id) {
            this.analysis = latest
            this.currentAnalysisId = String(latest.id)
          }
        })
        .finally(() => {
          this.loading = false
        })
    },
    fetchList() {
      if (!this.analysisId) return Promise.resolve()
      this.loading = true
      return getPreciseRecommendations(this.analysisId)
        .then(res => {
          this.rows = this.listOf(res)
        })
        .finally(() => {
          this.loading = false
        })
    },
    generate() {
      if (!this.analysisId) return this.$message.warning('未找到可生成推荐的分析任务')
      this.generating = true
      return generatePreciseRecommendations(this.analysisId)
        .then(res => {
          const rows = this.listOf(res)
          if (rows.length) this.rows = rows
          this.$message.success('推荐生成完成，共 ' + (rows.length || this.rows.length) + ' 条')
          return this.fetchList()
        })
        .finally(() => {
          this.generating = false
        })
    },
    accept(ids, accepted) {
      return acceptPreciseRecommendations({ ids, accepted }).then(() => {
        this.$message.success('操作成功')
        this.fetchList()
      })
    },
    acceptSelected(accepted) {
      const ids = this.selected.map(i => i.id)
      if (!ids.length) return this.$message.warning('请先选择推荐项')
      return this.accept(ids, accepted)
    },
    execute() {
      if (!this.analysisId) return this.$message.warning('未找到可执行的分析任务')
      this.executing = true
      return executePreciseAnalysis(this.analysisId)
        .then(res => {
          const data = (res && res.data) || res || {}
          const no = data.execution_no || data.executionNo || data.id || ''
          this.$message.success('精准回归已提交' + (no ? '：' + no : ''))
          this.$router.push({ path: '/precise/coverage', query: { analysisId: this.analysisId } })
        })
        .finally(() => {
          this.executing = false
        })
    }
  }
}
</script>

<style scoped>
.actions {
  margin-top: 12px;
}
</style>
