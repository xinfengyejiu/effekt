<template>
  <div class="page-wrap">
    <page-section title="契约执行详情">
      <template slot="extra">
        <el-button size="small" @click="$router.back()">返回</el-button>
      </template>

      <el-descriptions v-if="detail" :column="3" border size="small" style="margin-bottom:16px;">
        <el-descriptions-item label="执行号">{{ detail.run_no }}</el-descriptions-item>
        <el-descriptions-item label="套件">{{ detail.suite_name }}</el-descriptions-item>
        <el-descriptions-item label="触发">{{ detail.trigger_type }}</el-descriptions-item>
        <el-descriptions-item label="Base URL">{{ detail.base_url }}</el-descriptions-item>
        <el-descriptions-item label="汇总">
          pass {{ detail.pass_count }} / drift {{ detail.drift_count }} / err {{ detail.error_count }} / breaking {{ detail.breaking_count }}
        </el-descriptions-item>
        <el-descriptions-item label="耗时">{{ detail.duration_ms }} ms</el-descriptions-item>
      </el-descriptions>

      <el-table v-loading="loading" :data="(detail && detail.items) || []" border>
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="path" label="路径" min-width="180" show-overflow-tooltip />
        <el-table-column prop="http_status" label="HTTP" width="80" />
        <el-table-column label="结果" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="resultTag(scope.row.result_status)">{{ scope.row.result_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_severity" label="最高级别" width="110">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.max_severity" size="mini" :type="sevTag(scope.row.max_severity)">{{ scope.row.max_severity }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时ms" width="90" />
        <el-table-column prop="error_message" label="错误" min-width="140" show-overflow-tooltip />
      </el-table>

      <div v-for="item in (detail && detail.items) || []" :key="item.id" class="findings-block">
        <h4>{{ item.method }} {{ item.path }} — findings</h4>

        <div v-if="item.ai_analysis" class="ai-box">
          <div class="ai-head">
            <span>AI 漂移分析</span>
            <el-button
              type="text"
              size="mini"
              :loading="analyzingId === item.id"
              @click="reAnalyze(item)"
            >AI 重新分析</el-button>
          </div>
          <p><b>结论：</b>{{ item.ai_analysis.summary || '-' }}</p>
          <p>
            <b>分类：</b>{{ item.ai_analysis.category || '-' }}
            &nbsp;|&nbsp;
            <b>建议动作：</b>{{ actionLabel(item.ai_analysis.action) }}
            &nbsp;|&nbsp;
            <b>置信度：</b>{{ formatConfidence(item.ai_analysis.confidence) }}
          </p>
          <p><b>根因：</b>{{ item.ai_analysis.root_cause || '-' }}</p>
          <p><b>影响：</b>{{ item.ai_analysis.impact || '-' }}</p>
          <ul v-if="item.ai_analysis.suggestions && item.ai_analysis.suggestions.length">
            <li v-for="(s, idx) in item.ai_analysis.suggestions" :key="idx">{{ s }}</li>
          </ul>
          <p v-if="item.ai_analysis.ai_error" class="ai-err">AI 调用备注：{{ item.ai_analysis.ai_error }}</p>
        </div>
        <div v-else-if="item.result_status === 'drift' || item.result_status === 'error'" class="ai-box">
          <el-button size="mini" type="primary" plain :loading="analyzingId === item.id" @click="reAnalyze(item)">
            生成 AI 分析
          </el-button>
        </div>

        <el-table v-if="item.findings && item.findings.length" :data="item.findings" border size="mini">
          <el-table-column prop="severity" label="级别" width="110">
            <template slot-scope="scope">
              <el-tag size="mini" :type="sevTag(scope.row.severity)">{{ scope.row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="drift_type" label="类型" width="140" />
          <el-table-column prop="json_path" label="路径" min-width="180" show-overflow-tooltip />
          <el-table-column prop="expected" label="期望" min-width="120" show-overflow-tooltip />
          <el-table-column prop="actual" label="实际" min-width="120" show-overflow-tooltip />
          <el-table-column prop="message" label="说明" min-width="200" show-overflow-tooltip />
        </el-table>
        <el-alert v-else type="success" :closable="false" title="无漂移 findings" />
        <el-collapse v-if="item.response_excerpt" style="margin-top:8px;">
          <el-collapse-item title="响应摘录">
            <pre class="excerpt">{{ item.response_excerpt }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getContractRunDetail, analyzeContractRunItem } from '@/api/contractApi'

export default {
  name: 'ContractRunDetail',
  components: { PageSection },
  data () {
    return { loading: false, detail: null, analyzingId: null }
  },
  created () {
    const id = this.$route.query.id
    if (id) this.load(id)
  },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    load (id) {
      this.loading = true
      getContractRunDetail(id).then(res => {
        this.detail = this.dataOf(res)
      }).finally(() => { this.loading = false })
    },
    resultTag (s) {
      return { pass: 'success', drift: 'warning', error: 'danger' }[s] || 'info'
    },
    sevTag (s) {
      return { breaking: 'danger', compatible: 'warning', info: 'info' }[s] || 'info'
    },
    actionLabel (a) {
      return {
        fix_backend: '改后端实现',
        update_schema: '更新契约',
        ignore_compatible: '可忽略（兼容扩展）',
        check_env: '检查环境/鉴权'
      }[a] || (a || '-')
    },
    formatConfidence (c) {
      if (c == null || c === '') return '-'
      const n = Number(c)
      if (Number.isNaN(n)) return '-'
      return (n * 100).toFixed(0) + '%'
    },
    reAnalyze (item) {
      this.analyzingId = item.id
      analyzeContractRunItem({ run_item_id: item.id, use_llm: true }).then(res => {
        const data = this.dataOf(res)
        if (data && data.ai_analysis) {
          this.$set(item, 'ai_analysis', data.ai_analysis)
          this.$message.success('AI 分析完成')
        }
      }).finally(() => { this.analyzingId = null })
    }
  }
}
</script>

<style scoped>
.findings-block { margin-top: 20px; }
.findings-block h4 { margin: 0 0 8px; font-size: 14px; }
.excerpt { white-space: pre-wrap; word-break: break-all; font-size: 12px; max-height: 240px; overflow: auto; }
.ai-box {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.6;
}
.ai-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  margin-bottom: 4px;
}
.ai-box ul { margin: 4px 0 0 18px; padding: 0; }
.ai-err { color: #e6a23c; margin-bottom: 0; }
</style>
