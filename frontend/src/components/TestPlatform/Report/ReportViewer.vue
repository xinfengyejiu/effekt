<template>
  <div class="page-wrap">
    <page-section title="报告查看">
      <div style="margin-bottom: 12px;">
        <el-button size="small" @click="goBack">返回</el-button>
      </div>
      <el-alert
        v-if="!report.content"
        title="当前无可展示内容，待后端返回 report.content HTML"
        type="info"
        :closable="false"
        style="margin-bottom: 16px;">
      </el-alert>
      <iframe
        v-if="report.content"
        class="report-frame"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
        :srcdoc="report.content">
      </iframe>
      <el-divider></el-divider>
      <json-viewer :value="report.summary || {}"></json-viewer>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import JsonViewer from '@/components/TestPlatform/common/JsonViewer'
import { getReportDetail } from '@/api/reportApi'

export default {
  name: 'ReportViewer',
  components: { PageSection, JsonViewer },
  data() {
    return {
      projectId: this.$route.query.projectId || 1,
      reportId: this.$route.query.reportId || '',
      report: {}
    }
  },
  methods: {
    fetchDetail() {
      if (!this.reportId) {
        return
      }
      getReportDetail(this.reportId, this.projectId).then(res => {
        this.report = (res && res.data) || res || {}
      }).catch(() => {
        this.report = {}
      })
    },
    goBack() {
      this.$router.push({
        path: '/test-platform/report',
        query: {
          projectId: this.projectId || undefined
        }
      })
    }
  },
  created() {
    this.fetchDetail()
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.report-frame {
  width: 100%;
  min-height: calc(100vh - 210px);
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #fff;
}
</style>
