<template>
  <div class="page-wrap performance-page">
    <page-section title="发起压测">
      <el-steps :active="activeStep" finish-status="success" style="margin-bottom: 20px;">
        <el-step title="选择场景" />
        <el-step title="执行配置" />
        <el-step title="确认执行" />
      </el-steps>

      <el-form ref="form" :model="form" :rules="rules" label-width="110px" size="small">
        <template v-if="activeStep === 0">
          <el-form-item label="性能场景" prop="scenarioId">
            <el-select v-model="form.scenarioId" filterable clearable placeholder="请选择性能场景" style="width: 360px;" @change="onScenarioChange">
              <el-option v-for="item in scenarios" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="脚本资产" prop="scriptId">
            <el-select v-model="form.scriptId" clearable placeholder="可选脚本" style="width: 360px;">
              <el-option v-for="item in scripts" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
        </template>

        <template v-if="activeStep === 1">
          <el-form-item label="配置名称" prop="name"><el-input v-model.trim="form.name" style="width:360px;" /></el-form-item>
          <el-form-item label="工具类型" prop="toolType"><el-select v-model="form.toolType" style="width:180px;" @change="fetchMachines"><el-option label="JMeter" value="jmeter" /><el-option label="k6" value="k6" /><el-option label="Locust" value="locust" /></el-select></el-form-item>
          <el-form-item label="并发用户"><el-input-number v-model="form.virtualUsers" :min="1" :max="100000" /></el-form-item>
          <el-form-item label="持续时间"><el-input-number v-model="form.durationSeconds" :min="1" :max="86400" /> 秒</el-form-item>
          <el-form-item label="Ramp Up"><el-input-number v-model="form.rampUpSeconds" :min="0" :max="86400" /> 秒</el-form-item>
          <el-form-item label="测试机"><el-select v-model="form.machineId" clearable placeholder="选择测试机" style="width:360px;"><el-option v-for="item in machines" :key="item.id" :label="machineLabel(item)" :value="item.id" /></el-select></el-form-item>
          <el-form-item label="Jenkins Job"><el-input v-model.trim="form.jenkinsJobName" placeholder="performance-runner" style="width:360px;" /></el-form-item>
          <el-form-item label="基础门禁"><el-input v-model.trim="form.gateSummary" placeholder="如 p95 < 1000ms，错误率 < 1%" style="width:520px;" /></el-form-item>
        </template>

        <template v-if="activeStep === 2">
          <div class="confirm-grid">
            <div class="confirm-item"><span>性能场景</span><strong>{{ selectedScenarioName }}</strong></div>
            <div class="confirm-item"><span>工具类型</span><strong>{{ form.toolType }}</strong></div>
            <div class="confirm-item"><span>并发用户</span><strong>{{ form.virtualUsers }}</strong></div>
            <div class="confirm-item"><span>持续时间</span><strong>{{ form.durationSeconds }} 秒</strong></div>
            <div class="confirm-item"><span>测试机</span><strong>{{ selectedMachineName }}</strong></div>
            <div class="confirm-item"><span>Jenkins Job</span><strong>{{ form.jenkinsJobName || '-' }}</strong></div>
            <div class="confirm-item confirm-item--wide"><span>基础门禁</span><strong>{{ form.gateSummary || '-' }}</strong></div>
          </div>
        </template>
      </el-form>

      <div class="wizard-actions">
        <el-button size="small" :disabled="activeStep === 0" @click="activeStep--">上一步</el-button>
        <el-button v-if="activeStep < 2" size="small" type="primary" @click="nextStep">下一步</el-button>
        <el-button v-else size="small" type="primary" :loading="submitting" @click="submitRun">确认发起</el-button>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { createPerformanceExecutionConfig, createPerformanceRun, getAvailablePerformanceMachineList, getPerformanceScenarioList, getPerformanceScriptList } from '@/api/performanceApi'

export default {
  name: 'PerformanceRunWizard',
  components: { PageSection },
  data() {
    return {
      activeStep: 0,
      submitting: false,
      scenarios: [],
      scripts: [],
      machines: [],
      form: {
        scenarioId: this.$route.query.scenarioId ? Number(this.$route.query.scenarioId) : '',
        scriptId: '',
        name: '默认压测配置',
        toolType: 'jmeter',
        virtualUsers: 50,
        durationSeconds: 300,
        rampUpSeconds: 30,
        machineId: '',
        jenkinsJobName: 'performance-runner',
        gateSummary: ''
      },
      rules: { scenarioId: [{ required: true, message: '请选择性能场景', trigger: 'change' }], name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }], toolType: [{ required: true, message: '请选择工具类型', trigger: 'change' }] }
    }
  },
  computed: {
    selectedScenarioName() { const x = this.scenarios.find(i => i.id === this.form.scenarioId); return (x && x.name) || this.$route.query.scenarioName || '-' },
    selectedMachineName() { const x = this.machines.find(i => i.id === this.form.machineId); return x ? this.machineLabel(x) : '-' }
  },
  created() { this.fetchScenarios(); this.fetchMachines(); if (this.form.scenarioId) this.fetchScripts() },
  methods: {
    listOf(res) { const d = res && res.data ? res.data : res || {}; return d.items || d.list || d.data || [] },
    fetchScenarios() { getPerformanceScenarioList({ pageNo: 1, pageSize: 200, status: 1 }).then(res => { this.scenarios = this.listOf(res) }) },
    fetchMachines() { getAvailablePerformanceMachineList({ toolType: this.form.toolType }).then(res => { this.machines = this.listOf(res) }) },
    fetchScripts() { getPerformanceScriptList({ scenarioId: this.form.scenarioId, pageNo: 1, pageSize: 100 }).then(res => { this.scripts = this.listOf(res) }) },
    onScenarioChange() { this.form.scriptId = ''; this.fetchScripts() },
    machineLabel(row) { return [row.name, row.host || row.ip || row.host_ip, row.status === 1 ? '可用' : ''].filter(Boolean).join(' / ') },
    buildPayload() {
      return Object.assign({}, this.form, {
        concurrentUsers: this.form.virtualUsers,
        testMachineId: this.form.machineId,
        triggerType: 'jenkins'
      })
    },
    nextStep() { this.$refs.form.validate(valid => { if (valid) this.activeStep += 1 }) },
    submitRun() {
      this.submitting = true
      const payload = this.buildPayload()
      createPerformanceExecutionConfig(payload).then(res => {
        const data = res && res.data ? res.data : res || {}
        const configId = data.id || data.configId || this.form.executionConfigId
        return createPerformanceRun(Object.assign({}, payload, { executionConfigId: configId }))
      }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.$message.success('压测已发起')
        this.$router.push({ path: '/performance/runs', query: { runId: data.id || data.runId || '' } })
      }).finally(() => { this.submitting = false })
    }
  }
}
</script>

<style scoped>
.wizard-actions { margin-top: 22px; text-align: right; }
.confirm-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.confirm-item { display: flex; min-height: 42px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.confirm-item:nth-child(2n) { border-right: 0; }
.confirm-item--wide { grid-column: 1 / 3; border-right: 0; border-bottom: 0; }
.confirm-item span { width: 120px; padding: 12px; color: #909399; background: #fafafa; }
.confirm-item strong { flex: 1; padding: 12px; color: #303133; font-weight: 500; }
</style>
