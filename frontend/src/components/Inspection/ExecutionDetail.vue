<template>
  <div class="page-wrap">
    <page-section title="执行详情">
      <template slot="extra">
        <el-button size="small" @click="$router.push('/inspection/executions')">返回列表</el-button>
      </template>

      <div v-loading="loading">
        <el-descriptions :column="4" border size="small" style="margin-bottom: 20px">
          <el-descriptions-item label="任务ID">{{ detail.task_id || '组级执行' }}</el-descriptions-item>
          <el-descriptions-item label="任务/组名称">{{ detail.task_name || detail.group_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="mini" :type="statusType(detail.status)">{{ statusText(detail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="触发方式">{{ detail.trigger_type === 'manual' ? '手动' : '定时' }}</el-descriptions-item>
          <el-descriptions-item label="通过/总数">
            <span style="color: #67C23A">{{ detail.pass_count }}</span> / {{ detail.total_count }}
          </el-descriptions-item>
          <el-descriptions-item label="失败">{{ detail.fail_count }}</el-descriptions-item>
          <el-descriptions-item label="异常">{{ detail.error_count }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ formatDuration(detail.duration_ms) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间" :span="2">{{ detail.start_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结束时间" :span="2">{{ detail.end_time || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 16px 0 8px">巡检项结果（含 AI 判定）</h4>
        <el-collapse accordion>
          <el-collapse-item v-for="item in detail.items" :key="item.id">
            <template slot="title">
              <el-tag size="mini" :type="itemStatusType(item.status)" style="margin-right: 8px">{{ itemStatusText(item.status) }}</el-tag>
              <span>[{{ item.item_type }}] 巡检项 #{{ item.item_id }}</span>
              <span style="margin-left: 12px; color: #909399; font-size: 12px">{{ formatDuration(item.duration_ms) }}</span>
              <el-tag
                v-if="item.result && item.result.ai_verdict"
                size="mini"
                :type="item.result.ai_verdict.passed ? 'success' : 'danger'"
                style="margin-left: 8px"
              >AI</el-tag>
            </template>
            <div v-if="item.error_message" style="color: #F56C6C; margin-bottom: 8px">错误: {{ item.error_message }}</div>

            <div v-if="item.result && item.result.ai_verdict" class="ai-box ai-verdict">
              <div>
                <strong>AI 判定：</strong>
                {{ item.result.ai_verdict.passed ? '通过' : '未通过' }}
                <span v-if="item.result.ai_verdict.confidence != null" class="muted">
                  置信度 {{ item.result.ai_verdict.confidence }}
                </span>
              </div>
              <div style="margin-top: 6px">{{ item.result.ai_verdict.reason }}</div>
              <ul v-if="item.result.ai_verdict.evidence_highlights && item.result.ai_verdict.evidence_highlights.length" class="hint-list">
                <li v-for="(h, i) in item.result.ai_verdict.evidence_highlights" :key="'h'+i">{{ h }}</li>
              </ul>
            </div>

            <div v-if="item.result && item.result.ai_analysis" class="ai-box ai-analysis">
              <div>
                <strong>失败自动分析：</strong>
                [{{ item.result.ai_analysis.category || '未知' }}]
                {{ item.result.ai_analysis.root_cause }}
              </div>
              <div v-if="item.result.ai_analysis.impact" style="margin-top: 4px">影响：{{ item.result.ai_analysis.impact }}</div>
              <ul v-if="item.result.ai_analysis.suggestions && item.result.ai_analysis.suggestions.length" class="hint-list">
                <li v-for="(s, i) in item.result.ai_analysis.suggestions" :key="'s'+i">{{ s }}</li>
              </ul>
            </div>

            <div v-if="item.result && item.result.assertion_results && item.result.assertion_results.length">
              <div style="margin: 8px 0 4px; color: #606266">规则断言（高级预检）</div>
              <el-table :data="item.result.assertion_results" size="mini" border>
                <el-table-column label="断言类型" prop="type" width="120"></el-table-column>
                <el-table-column label="运算符" prop="operator" width="80"></el-table-column>
                <el-table-column label="期望值" width="150">
                  <template slot-scope="scope">{{ JSON.stringify(scope.row.expected) }}</template>
                </el-table-column>
                <el-table-column label="实际值" width="150">
                  <template slot-scope="scope">{{ JSON.stringify(scope.row.actual) }}</template>
                </el-table-column>
                <el-table-column label="结果" width="80">
                  <template slot-scope="scope">
                    <el-tag size="mini" :type="scope.row.passed ? 'success' : 'danger'">{{ scope.row.passed ? '通过' : '失败' }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <pre v-if="item.result" class="raw-json">{{ JSON.stringify(item.result, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getInspectionExecutionDetail } from '@/api/inspectionApi'

export default {
  name: 'InspectionExecutionDetail',
  components: { PageSection },
  data () {
    return { loading: false, detail: {} }
  },
  created () {
    var id = this.$route.query.detail_id || this.$route.query.id
    if (id) this.fetchDetail(id)
  },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    fetchDetail (id) {
      this.loading = true
      getInspectionExecutionDetail(id).then(res => {
        this.detail = this.dataOf(res)
      }).finally(() => { this.loading = false })
    },
    statusText (s) { return { 0: '待执行', 1: '执行中', 2: '全部通过', 3: '部分失败', 4: '全部失败', 5: '异常' }[s] || '未知' },
    statusType (s) { return { 0: 'info', 1: 'warning', 2: 'success', 3: 'warning', 4: 'danger', 5: 'danger' }[s] || 'info' },
    itemStatusText (s) { return { 0: '待执行', 1: '执行中', 2: '通过', 3: '失败', 4: '异常' }[s] || '未知' },
    itemStatusType (s) { return { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger', 4: 'danger' }[s] || 'info' },
    formatDuration (ms) { if (!ms) return '-'; return ms < 1000 ? ms + 'ms' : (ms / 1000).toFixed(1) + 's' }
  }
}
</script>

<style scoped>
.ai-box {
  margin: 8px 0;
  padding: 10px 12px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
}
.ai-verdict {
  background: #f5f9ff;
  border: 1px solid #d6e4ff;
}
.ai-analysis {
  background: #fff7f0;
  border: 1px solid #ffd8bf;
}
.muted {
  color: #909399;
  margin-left: 8px;
}
.hint-list {
  margin: 6px 0 0;
  padding-left: 18px;
}
.raw-json {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  margin-top: 8px;
  max-height: 200px;
  overflow: auto;
  font-size: 12px;
}
</style>
