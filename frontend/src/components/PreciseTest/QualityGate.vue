<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-质量门禁">
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="分析ID"><el-input v-model.trim="analysisId" clearable style="width:160px;" /></el-form-item>
        <el-form-item><el-button type="primary" @click="evaluate">执行门禁</el-button><el-button @click="load">查询结果</el-button></el-form-item>
      </el-form>
      <el-card shadow="never" style="margin-top:12px;">
        <div slot="header">门禁结论</div>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="状态"><el-tag :type="gateTag(result.gate_status || result.gateStatus)">{{ gateLabel(result.gate_status || result.gateStatus) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="风险等级">{{ result.risk_level || result.riskLevel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="阈值">{{ result.line_rate_threshold || result.lineRateThreshold || '-' }}</el-descriptions-item>
          <el-descriptions-item label="实际增量覆盖率">{{ result.actual_line_rate || result.actualLineRate || '-' }}</el-descriptions-item>
          <el-descriptions-item label="P0通过率">{{ result.p0_case_pass_rate || result.p0CasePassRate || '-' }}</el-descriptions-item>
          <el-descriptions-item label="P1通过率">{{ result.p1_case_pass_rate || result.p1CasePassRate || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-row :gutter="16" style="margin-top:16px;"><el-col :span="12"><h4>阻断原因</h4><pre class="json-box">{{ pretty(result.block_reasons || result.blockReasons || []) }}</pre></el-col><el-col :span="12"><h4>AI结论/建议</h4><pre class="json-box">{{ pretty(result.ai_conclusion || result.aiConclusion || result.suggestions || []) }}</pre></el-col></el-row>
      </el-card>
    </page-section>
  </div>
</template>
<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { evaluatePreciseGate, getPreciseGateResult } from '@/api/preciseTestApi'
export default { name: 'PreciseQualityGate', components: { PageSection }, data() { return { analysisId: this.$route.query.analysisId || '', result: {} } }, created() { this.load() }, methods: { evaluate() { if (!this.analysisId) return this.$message.warning('请输入分析ID'); evaluatePreciseGate({ analysisId: this.analysisId }).then(res => { this.result = (res && res.data) || res || {}; this.$message.success('门禁评估完成') }) }, load() { if (!this.analysisId) return; getPreciseGateResult(this.analysisId).then(res => { this.result = (res && res.data) || res || {} }) }, gateLabel(v) { return { 1: '通过', 2: '警告', 3: '不通过', passed: '通过', warning: '警告', blocked: '不通过' }[v] || (v || '-') }, gateTag(v) { return { 1: 'success', 2: 'warning', 3: 'danger', passed: 'success', warning: 'warning', blocked: 'danger' }[v] || 'info' }, pretty(v) { try { return JSON.stringify(typeof v === 'string' ? JSON.parse(v) : v, null, 2) } catch (e) { return String(v || '') } } } }
</script>
<style scoped>.json-box{background:#f7f8fa;border:1px solid #ebeef5;padding:12px;min-height:120px;white-space:pre-wrap;word-break:break-all;}</style>
