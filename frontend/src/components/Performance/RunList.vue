<template>
  <div class="page-wrap performance-page">
    <page-section title="执行记录">
      <template slot="extra"><el-button size="small" type="primary" @click="$router.push('/performance/run-wizard')">发起压测</el-button></template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="场景ID"><el-input v-model.trim="queryForm.scenarioId" clearable style="width:120px;" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="queryForm.status" clearable placeholder="全部" style="width:130px;"><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="fetchList">查询</el-button><el-button @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="执行编号" min-width="170" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.run_no || scope.row.runNo || scope.row.id }}</template></el-table-column>
        <el-table-column label="场景ID" width="90"><template slot-scope="scope">{{ scope.row.scenario_id || scope.row.scenarioId || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="110"><template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="Jenkins" min-width="220" show-overflow-tooltip><template slot-scope="scope"><span>{{ scope.row.jenkins_job_name || scope.row.jenkinsJobName || '-' }}</span><el-link v-if="jenkinsUrl(scope.row)" :href="jenkinsUrl(scope.row)" target="_blank" type="primary" style="margin-left:8px;">构建</el-link><el-link v-if="consoleUrl(scope.row)" :href="consoleUrl(scope.row)" target="_blank" type="primary" style="margin-left:8px;">日志</el-link></template></el-table-column>
        <el-table-column label="报告" min-width="170" show-overflow-tooltip><template slot-scope="scope"><el-link v-if="nativeUrl(scope.row)" :href="nativeUrl(scope.row)" target="_blank" type="primary">原生报告</el-link><span v-else>-</span></template></el-table-column>
        <el-table-column label="开始时间" min-width="160"><template slot-scope="scope">{{ scope.row.start_time || scope.row.startTime || '-' }}</template></el-table-column>
        <el-table-column label="结束时间" min-width="160"><template slot-scope="scope">{{ scope.row.end_time || scope.row.endTime || '-' }}</template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right"><template slot-scope="scope"><el-button type="text" @click="goReport(scope.row)">报告</el-button><el-button type="text" @click="retry(scope.row)">重试</el-button><el-button type="text" style="color:#F56C6C;" @click="stop(scope.row)">停止</el-button></template></el-table-column>
      </el-table>
      <div class="pager-wrap"><el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" /></div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPerformanceRunList, retryPerformanceRun, stopPerformanceRun } from '@/api/performanceApi'

const STATUS = { 0: '待触发', 1: '触发中', 2: '排队中', 3: '执行中', 4: '成功', 5: '失败', 6: '已取消', 7: '超时', 8: '解析失败' }
export default {
  name: 'PerformanceRunList',
  components: { PageSection },
  data() { return { loading: false, pollingTimer: null, rows: [], total: 0, pageNo: 1, pageSize: 20, queryForm: { scenarioId: this.$route.query.scenarioId || '', status: '' }, statusOptions: Object.keys(STATUS).map(k => ({ value: Number(k), label: STATUS[k] })) } },
  created() { this.fetchList().then(() => this.startPolling()) },
  beforeDestroy() { this.stopPolling() },
  methods: {
    listOf(res) { const d = res && res.data ? res.data : res || {}; return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 } },
    fetchList(silent) {
      if (!silent) this.loading = true
      return getPerformanceRunList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => {
        const d = this.listOf(res)
        this.rows = d.rows
        this.total = d.total || this.rows.length
      }).catch(() => {
        if (!silent) { this.rows = []; this.total = 0 }
      }).finally(() => { if (!silent) this.loading = false })
    },
    startPolling() { this.stopPolling(); this.pollingTimer = setInterval(() => { this.fetchList(true) }, 5000) },
    stopPolling() { if (this.pollingTimer) { clearInterval(this.pollingTimer); this.pollingTimer = null } },
    resetQuery() { this.queryForm = { scenarioId: '', status: '' }; this.pageNo = 1; this.fetchList() },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    statusLabel(s) { return STATUS[s] || (s == null ? '-' : String(s)) },
    statusTag(s) { return { 0: 'info', 1: 'warning', 2: 'warning', 3: 'primary', 4: 'success', 5: 'danger', 6: 'info', 7: 'danger', 8: 'danger' }[s] || 'info' },
    nativeUrl(row) { return row.native_report_url || row.nativeReportUrl || row.report_url || row.reportUrl || '' },
    jenkinsUrl(row) { return row.jenkins_build_url || row.jenkinsBuildUrl || '' },
    consoleUrl(row) { return row.console_url || row.consoleUrl || (this.jenkinsUrl(row) ? this.jenkinsUrl(row).replace(/\/$/, '') + '/console' : '') },
    goReport(row) { this.$router.push({ path: '/performance/reports', query: { runId: row.id } }) },
    stop(row) { this.$confirm('确认停止该压测执行？', '提示').then(() => stopPerformanceRun(row.id).then(() => { this.$message.success('停止请求已提交'); this.fetchList() })).catch(() => {}) },
    retry(row) { retryPerformanceRun(row.id).then(() => { this.$message.success('重试请求已提交'); this.fetchList() }) }
  }
}
</script>

<style scoped>.pager-wrap { margin-top: 16px; text-align: right; }</style>
