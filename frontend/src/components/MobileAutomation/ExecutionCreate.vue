<template>
  <div class="page-wrap">
    <page-section :title="configId ? '编辑移动执行配置' : '新增移动执行配置'">
      <el-alert
        title="先保存执行配置，再从配置列表发起执行；测试用例支持多选。保存配置不要求设备在线，只有执行时才检查设备和环境。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-form ref="form" :model="form" :rules="rules" label-width="120px" size="small" class="run-form">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model.trim="form.name" placeholder="例如 Joyhub 登录回归" style="width:360px" />
        </el-form-item>
        <el-form-item label="项目" prop="project_id">
          <el-select v-model="form.project_id" filterable placeholder="选择项目" style="width:360px" @change="onProjectChange">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="移动应用" prop="mobile_app_id">
          <el-select v-model="form.mobile_app_id" filterable :disabled="!form.project_id" placeholder="选择应用" style="width:360px">
            <el-option v-for="item in apps" :key="item.id" :label="item.name + ' · ' + item.package_name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行设备" prop="device_serial">
          <el-select v-model="form.device_serial" filterable placeholder="选择设备" style="width:360px">
            <el-option
              v-for="item in devices"
              :key="item.serial_no"
              :label="(item.display_name || item.model || item.serial_no) + ' · ' + item.serial_no"
              :value="item.serial_no"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="环境编码" prop="env_code">
          <el-input v-model.trim="form.env_code" placeholder="例如 test" style="width:360px" />
        </el-form-item>
        <el-form-item label="测试用例" prop="case_ids">
          <el-select
            v-model="form.case_ids"
            multiple
            collapse-tags
            filterable
            :disabled="!form.project_id"
            placeholder="选择多个测试用例"
            style="width:560px"
            @change="onCaseIdsChange"
          >
            <el-option
              v-for="item in cases"
              :key="item.id"
              :label="(item.case_key || item.id) + ' · ' + (item.title || '')"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.case_ids.length" label="AI 生成脚本">
          <el-button type="primary" plain size="small" icon="el-icon-magic-stick" :loading="aiGenerating" :disabled="!form.project_id || !form.case_ids.length || !form.mobile_app_id || !form.device_serial" @click="handleAiGenerate">
            AI 生成并调试脚本
          </el-button>
          <el-input-number v-model="aiMaxRetries" :min="1" :max="10" size="small" style="width:130px;margin-left:12px" title="最大调试重试次数" />
          <span class="form-hint" style="margin-left:8px">最大重试</span>
          <div class="form-hint" style="margin-top:4px">AI 生成脚本后自动在设备上执行调试，失败则 AI 自动修复，循环直到通过或达到最大重试次数。</div>
        </el-form-item>
        <el-form-item
          v-for="caseId in form.case_ids"
          :key="'script-' + caseId"
          :label="caseScriptLabel(caseId)"
          :required="true"
        >
          <el-input
            v-model.trim="form.case_script_map[caseId]"
            placeholder="例如 tests/test_joyhub_login.py::test_login_success"
            style="width:560px"
          />
        </el-form-item>
        <el-form-item v-if="!form.case_ids.length" label="脚本选择器" prop="script_selector">
          <el-input
            v-model.trim="form.script_selector"
            placeholder="先选择测试用例后，再为每条用例配置脚本"
            style="width:560px"
            disabled
          />
          <div class="form-hint">每条用例对应一个 pytest nodeid；多选用例会串行执行各自脚本。</div>
        </el-form-item>
        <el-form-item v-else label="说明">
          <div class="form-hint">每条用例对应一个 pytest nodeid；保存后将按用例顺序串行执行，过程步骤会分别归属到各用例。</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model.trim="form.remark" type="textarea" :rows="3" style="width:560px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit(false)">{{ configId ? '保存修改' : '保存配置' }}</el-button>
          <el-button type="success" :disabled="!ready" :loading="running" @click="submit(true)">保存并执行</el-button>
          <el-button
            v-if="!appiumReady"
            type="warning"
            plain
            :loading="startingAppium"
            @click="startAppium"
          >启动 Appium</el-button>
          <el-button @click="$router.push({ path: '/mobile-automation/run' })">取消</el-button>
          <span v-if="!ready" class="not-ready">{{ readinessMessage }}</span>
          <span v-else-if="appiumReady" class="ready-tip">Appium 已就绪，可执行</span>
        </el-form-item>
      </el-form>
    </page-section>

    <!-- AI 脚本生成与调试结果弹窗 -->
    <el-dialog
      :title="aiDialogTitle"
      :visible.sync="aiDialogVisible"
      width="70%"
      :close-on-click-modal="false"
    >
      <!-- 基本信息 -->
      <el-alert
        v-if="aiDialogData && aiDialogData.project_dir"
        :title="'脚本目录：' + aiDialogData.project_dir"
        type="success"
        :closable="false"
        show-icon
        style="margin-bottom:12px"
      />
      <el-alert
        v-if="aiDialogData && aiDialogData.scripts && aiDialogData.scripts.length"
        :title="'关联用例：' + aiDialogData.scripts.map(s => s.case_key || s.case_id).join('、')"
        type="info"
        :closable="false"
        style="margin-bottom:12px"
      />

      <!-- 调试结果汇总 -->
      <el-alert
        v-if="aiDialogData && aiDialogData.logs"
        :title="aiResultSummary"
        :type="aiDialogData.passed ? 'success' : 'error'"
        :closable="false"
        show-icon
        style="margin-bottom:12px"
      />

      <!-- 调试过程日志 -->
      <div v-if="aiDialogData && aiDialogData.logs && aiDialogData.logs.length" class="debug-logs">
        <div v-for="(log, idx) in aiDialogData.logs" :key="idx" class="debug-log-item">
          <div class="debug-log-header">
            <el-tag :type="log.passed ? 'success' : 'danger'" size="small" style="margin-right:8px">
              {{ log.passed ? '✅ 通过' : '❌ 失败' }}
            </el-tag>
            <span class="debug-log-round">第 {{ log.round }} 轮</span>
            <span class="debug-log-exit">exit_code={{ log.exit_code }}</span>
          </div>
          <div v-if="log.output" class="debug-log-output">
            <div class="debug-log-label">pytest 输出：</div>
            <pre class="debug-log-text">{{ log.output }}</pre>
          </div>
          <div v-if="log.ai_fix" class="debug-log-ai-fix">
            <div class="debug-log-label">🤖 AI 修复：</div>
            <div class="debug-log-fix-text">{{ log.ai_fix }}</div>
          </div>
        </div>
      </div>

      <!-- 代码预览 -->
      <div class="ai-code-section">
        <div class="ai-code-header">最终代码</div>
        <pre class="ai-code-block">{{ aiDialogCode }}</pre>
      </div>

      <span slot="footer">
        <el-button @click="aiDialogVisible = false">关闭</el-button>
        <el-button
          v-if="aiDialogData && aiDialogData.passed"
          type="primary"
          @click="applyAiScript"
        >应用到配置</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProjectList } from '@/api/projectApi'
import { getCaseList } from '@/api/caseApi'
import {
  getMobileAppList,
  getMobileDeviceList,
  getMobileEnvironmentCheck,
  getMobileExecutionConfig,
  runMobileExecutionConfig,
  saveMobileExecutionConfig,
  startMobileAppium,
  aiGenerateMobileScripts,
  aiGenerateAndDebugMobileScripts
} from '@/api/mobileAutomationApi'

export default {
  name: 'MobileAutomationExecutionConfigEdit',
  components: { PageSection },
  data () {
    return {
      configId: '',
      projects: [],
      apps: [],
      devices: [],
      cases: [],
      diagnostic: {},
      saving: false,
      running: false,
      startingAppium: false,
      aiGenerating: false,
      aiMaxRetries: 3,
      aiDialogVisible: false,
      aiDialogData: null,
      aiDialogCode: '',
      form: {
        name: '',
        project_id: '',
        mobile_app_id: '',
        device_serial: '',
        env_code: 'test',
        case_ids: [],
        case_script_map: {},
        script_selector: 'tests/test_joyhub_login.py::test_login_success',
        remark: ''
      },
      rules: {
        name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
        project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
        mobile_app_id: [{ required: true, message: '请选择应用', trigger: 'change' }],
        device_serial: [{ required: true, message: '请选择设备', trigger: 'change' }],
        env_code: [{ required: true, message: '请输入环境编码', trigger: 'blur' }],
        case_ids: [{ required: true, type: 'array', min: 1, message: '请选择至少一个用例', trigger: 'change' }]
      }
    }
  },
  computed: {
    aiDialogTitle () {
      if (!this.aiDialogData) return 'AI 脚本生成与调试结果'
      if (this.aiDialogData.passed) return '✅ AI 脚本调试通过'
      return ' AI 脚本调试未通过'
    },
    aiResultSummary () {
      if (!this.aiDialogData) return ''
      const d = this.aiDialogData
      if (d.passed) {
        return '脚本在第 ' + d.attempts + ' 轮调试后通过验证，共尝试 ' + d.attempts + ' 次。'
      }
      return '脚本经过 ' + d.attempts + ' 轮调试后仍未通过，请检查代码或手动修改。'
    },
    appiumReady () {
      const d = this.diagnostic || {}
      const m = d.modules || {}
      return !!(d.appium && d.appium.available) || !!(m.appium && m.appium.installed)
    },
    missingReadyReasons () {
      const d = this.diagnostic || {}
      const m = d.modules || {}
      const reasons = []
      if (!(d.adb && d.adb.available)) reasons.push('ADB 不可用')
      if (!(d.python && d.python.available)) reasons.push('自动化 Python 解释器不可用')
      if (!this.appiumReady) reasons.push('Appium 服务未启动（可点击「启动 Appium」）')
      if (!(d.script_repository && d.script_repository.available && d.script_repository.pytest_ini_exists)) {
        reasons.push('脚本仓库或 pytest.ini 缺失')
      }
      if (!(m.pytest && m.pytest.installed)) reasons.push('未安装 pytest')
      if (!(m.uiautomator2 && m.uiautomator2.installed)) reasons.push('未安装 uiautomator2')
      if (!(m.allure_pytest && m.allure_pytest.installed)) reasons.push('未安装 allure-pytest')
      if (!this.devices.some(item => item.adb_status === 'online' && item.usage_status === 'idle')) {
        reasons.push('没有在线且空闲的 Android 设备')
      }
      return reasons
    },
    ready () {
      return this.missingReadyReasons.length === 0
    },
    readinessMessage () {
      return this.missingReadyReasons[0] || '环境依赖未就绪，无法执行'
    }
  },
  created () {
    this.configId = this.$route.query.id || ''
    this.reload().then(() => this.loadConfig())
  },
  methods: {
    dataOf (res) {
      return (res && res.data) || res || {}
    },
    caseMeta (caseId) {
      return this.cases.find(item => String(item.id) === String(caseId)) || {}
    },
    caseScriptLabel (caseId) {
      const item = this.caseMeta(caseId)
      const title = item.title || item.case_key || caseId
      return '脚本 · ' + String(title).slice(0, 12)
    },
    guessSelector (caseItem) {
      const text = ((caseItem && (caseItem.case_key || '')) + ' ' + (caseItem && (caseItem.title || ''))).toLowerCase()
      if (/日语|日本語|语言|japanese|language/.test(text)) {
        return 'tests/test_joyhub_login.py::test_change_language_to_japanese'
      }
      if (/登录|登陆|login/.test(text)) {
        return 'tests/test_joyhub_login.py::test_login_success'
      }
      return 'tests/test_joyhub_login.py::test_login_success'
    },
    onCaseIdsChange (caseIds) {
      const next = Object.assign({}, this.form.case_script_map)
      ;(caseIds || []).forEach(caseId => {
        if (!next[caseId]) {
          next[caseId] = this.guessSelector(this.caseMeta(caseId))
        }
      })
      Object.keys(next).forEach(key => {
        if (!(caseIds || []).map(String).includes(String(key))) delete next[key]
      })
      this.$set(this.form, 'case_script_map', next)
      this.form.script_selector = (caseIds || []).map(id => next[id]).filter(Boolean).join(';')
    },
    buildPayload () {
      const selectors = (this.form.case_ids || []).map(id => (this.form.case_script_map[id] || '').trim())
      if (!selectors.length || selectors.some(item => !item)) {
        this.$message.warning('请为每条用例填写脚本选择器')
        return null
      }
      return Object.assign({}, this.form, {
        script_selector: selectors.join(';'),
        script_selectors: selectors
      }, this.configId ? { id: this.configId } : {})
    },
    reload () {
      return Promise.all([
        getProjectList({ pageNo: 1, pageSize: 500 }),
        getMobileDeviceList(),
        getMobileEnvironmentCheck()
      ]).then(values => {
        this.projects = this.dataOf(values[0]).list || this.dataOf(values[0]).items || []
        this.devices = this.dataOf(values[1]).list || []
        this.diagnostic = this.dataOf(values[2])
      })
    },
    loadConfig () {
      if (!this.configId) return
      return getMobileExecutionConfig(this.configId).then(res => {
        const d = this.dataOf(res)
        const caseIds = d.case_ids || []
        const selectors = d.script_selectors || String(d.script_selector || '').split(/[;\n]+/).map(s => s.trim()).filter(Boolean)
        const caseScriptMap = {}
        caseIds.forEach((caseId, index) => {
          caseScriptMap[caseId] = selectors[index] || selectors[0] || 'tests/test_joyhub_login.py::test_login_success'
        })
        Object.assign(this.form, {
          name: d.name || '',
          project_id: d.project_id,
          mobile_app_id: d.mobile_app_id,
          device_serial: d.device_serial,
          env_code: d.env_code || 'test',
          case_ids: caseIds,
          case_script_map: caseScriptMap,
          script_selector: selectors.join(';') || '',
          remark: d.remark || ''
        })
        return this.onProjectChange(d.project_id, d.mobile_app_id, caseIds)
      })
    },
    onProjectChange (projectId, selectedAppId, selectedCaseIds) {
      this.apps = []
      this.cases = []
      if (!projectId) {
        this.form.mobile_app_id = ''
        this.form.case_ids = []
        this.form.case_script_map = {}
        return Promise.resolve()
      }
      return Promise.all([
        getMobileAppList({ project_id: projectId }),
        getCaseList(projectId, { pageNo: 1, pageSize: 500 })
      ]).then(values => {
        this.apps = this.dataOf(values[0]).list || []
        this.cases = this.dataOf(values[1]).list || this.dataOf(values[1]).items || []
        if (selectedAppId !== undefined) this.form.mobile_app_id = selectedAppId
        if (selectedCaseIds) {
          this.form.case_ids = selectedCaseIds
          this.onCaseIdsChange(selectedCaseIds)
        }
      })
    },
    startAppium () {
      this.startingAppium = true
      startMobileAppium().then(res => {
        const d = this.dataOf(res)
        if (d.diagnostic) this.diagnostic = d.diagnostic
        this.$message.success(d.message || 'Appium 已就绪')
        return Promise.all([getMobileDeviceList(), getMobileEnvironmentCheck()])
      }).then(values => {
        if (!values) return
        this.devices = this.dataOf(values[0]).list || []
        this.diagnostic = this.dataOf(values[1])
      }).catch(err => {
        const msg = (err && (err.message || err.msg)) || '启动 Appium 失败'
        this.$message.error(msg)
      }).finally(() => {
        this.startingAppium = false
      })
    },
    handleAiGenerate () {
      if (!this.form.project_id || !this.form.case_ids.length) {
        this.$message.warning('请先选择项目和测试用例')
        return
      }
      if (!this.form.mobile_app_id) {
        this.$message.warning('请先选择移动应用')
        return
      }
      if (!this.form.device_serial) {
        this.$message.warning('请先选择执行设备')
        return
      }
      this.aiGenerating = true
      aiGenerateAndDebugMobileScripts({
        project_id: this.form.project_id,
        case_ids: this.form.case_ids,
        device_serial: this.form.device_serial,
        mobile_app_id: this.form.mobile_app_id,
        max_retries: this.aiMaxRetries
      }).then(res => {
        const d = this.dataOf(res)
        this.aiDialogData = d
        this.aiDialogCode = d.code || '// AI 未返回代码内容'
        this.aiDialogVisible = true
        if (d.passed) {
          this.$message.success('AI 脚本调试通过，共 ' + d.attempts + ' 轮')
        } else {
          this.$message.warning('AI 脚本调试 ' + d.attempts + ' 轮后未通过')
        }
      }).catch(err => {
        const msg = (err && (err.message || err.msg)) || 'AI 脚本生成与调试失败'
        this.$message.error(msg)
      }).finally(() => {
        this.aiGenerating = false
      })
    },
    applyAiScript () {
      if (!this.aiDialogData || !this.aiDialogData.scripts || !this.aiDialogData.scripts.length) {
        this.$message.warning('无可应用的脚本路径')
        return
      }
      // 使用 scripts 数组中的相对路径，转为 pytest nodeid 格式
      const firstScript = this.aiDialogData.scripts[0]
      const filePath = (firstScript.file_path || '').replace(/\\/g, '/')
      if (!filePath) {
        this.$message.warning('脚本路径为空')
        return
      }
      // 去掉 .py 后缀，加上 ::test_xxx（用文件名推断）
      const pyFile = filePath.replace(/\.py$/, '')
      const lastSegment = pyFile.split('/').pop() || 'test'
      const nodeId = pyFile + '::' + lastSegment
      // 将生成的脚本路径应用到每个用例的 case_script_map
      this.$set(this.form, 'case_script_map', {})
      this.form.case_ids.forEach(id => {
        this.$set(this.form.case_script_map, id, nodeId)
      })
      this.form.script_selector = (this.form.case_ids || []).map(() => nodeId).join(';')
      this.aiDialogVisible = false
      this.$message.success('已将 AI 调试通过的脚本应用到所有用例')
    },
    submit (execute) {
      this.$refs.form.validate(valid => {
        if (!valid) return
        if (execute && !this.ready) return
        const payload = this.buildPayload()
        if (!payload) return
        this[execute ? 'running' : 'saving'] = true
        saveMobileExecutionConfig(payload).then(res => {
          const d = this.dataOf(res)
          this.configId = d.id || this.configId
          this.$message.success('配置已保存')
          if (!execute) {
            this.$router.push({ path: '/mobile-automation/run' })
            return
          }
          return runMobileExecutionConfig(this.configId)
        }).then(res => {
          if (execute && res) {
            const d = this.dataOf(res)
            this.$message.success('移动执行已创建')
            this.$router.push({ path: '/mobile-automation/execution/detail', query: { execution_id: d.id } })
          }
        }).finally(() => {
          this.saving = false
          this.running = false
        })
      })
    }
  }
}
</script>

<style scoped>
.run-form { margin-top: 20px; }
.form-hint { font-size: 12px; color: #909399; line-height: 20px; }
.not-ready { margin-left: 12px; color: #e6a23c; font-size: 12px; }
.ready-tip { margin-left: 12px; color: #67c23a; font-size: 12px; }
.ai-code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'Consolas', 'Courier New', monospace;
  line-height: 1.5;
  max-height: 500px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-code-section { margin-top: 16px; }
.ai-code-header { font-weight: bold; margin-bottom: 8px; font-size: 14px; }
.debug-logs { margin-bottom: 16px; }
.debug-log-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  background: #fafafa;
}
.debug-log-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.debug-log-round { font-weight: bold; margin-right: 12px; }
.debug-log-exit { color: #909399; font-size: 12px; }
.debug-log-label { font-size: 12px; color: #606266; margin-bottom: 4px; font-weight: bold; }
.debug-log-output { margin-bottom: 8px; }
.debug-log-text {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  font-family: 'Consolas', 'Courier New', monospace;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: #606266;
}
.debug-log-ai-fix {
  background: #ecf5ff;
  border-radius: 4px;
  padding: 8px;
  border-left: 3px solid #1e40af;
}
.debug-log-fix-text { font-size: 13px; color: #1e40af; }
</style>
