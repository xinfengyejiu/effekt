<template>
  <div class="page-wrap">
    <page-section :title="task.name || '任务详情'">
      <template slot="extra">
        <el-button size="small" @click="$router.push('/inspection/tasks')">返回定时任务</el-button>
      </template>

      <!-- 任务信息 -->
      <el-descriptions :column="3" border size="small" style="margin-bottom: 20px">
        <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ task.task_type }}</el-descriptions-item>
        <el-descriptions-item label="调度">{{ task.schedule_type }} {{ task.cron_expression || '' }}</el-descriptions-item>
        <el-descriptions-item label="通知">{{ task.notify_type || '未配置' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag size="mini" :type="task.enabled === 1 ? 'success' : 'info'">{{ task.enabled === 1 ? '启用' : '禁用' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </page-section>

    <page-section title="巡检项">
      <template slot="extra">
        <el-dropdown size="small" @command="addItem">
          <el-button type="primary" size="small" icon="el-icon-plus">添加巡检项</el-button>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="api">接口巡检</el-dropdown-item>
            <el-dropdown-item command="sql">SQL 巡检</el-dropdown-item>
            <el-dropdown-item command="script">脚本巡检</el-dropdown-item>
            <el-dropdown-item command="auto_case">自动化用例</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </template>

      <!-- 类型筛选 -->
      <el-radio-group v-model="itemFilter" size="small" style="margin-bottom: 12px" @change="fetchItems">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="api">接口</el-radio-button>
        <el-radio-button label="sql">SQL</el-radio-button>
        <el-radio-button label="script">脚本</el-radio-button>
        <el-radio-button label="auto_case">用例</el-radio-button>
      </el-radio-group>

      <el-table :data="items" v-loading="itemsLoading" stripe border size="small">
        <el-table-column label="序号" type="index" width="50"></el-table-column>
        <el-table-column label="名称" prop="name" min-width="160"></el-table-column>
        <el-table-column label="类型" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="typeColor(scope.row.item_type)">{{ scope.row.item_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="配置摘要" min-width="200" show-overflow-tooltip>
          <template slot-scope="scope">{{ configSummary(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="超时(s)" prop="timeout_seconds" width="80"></el-table-column>
        <el-table-column label="操作" width="200">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="editItem(scope.row)">编辑</el-button>
            <el-button type="text" size="mini" style="color: #67C23A" @click="testItem(scope.row)">测试</el-button>
            <el-button type="text" size="mini" style="color: #F56C6C" @click="removeItem(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </page-section>

    <!-- 巡检项编辑弹窗 -->
    <el-dialog :title="itemForm.id ? '编辑巡检项' : '添加巡检项'" :visible.sync="itemDialogVisible" width="700px" top="5vh">
      <el-form :model="itemForm" label-width="100px" size="small">
        <el-form-item label="名称">
          <el-input v-model="itemForm.name" placeholder="巡检项名称"></el-input>
        </el-form-item>
        <el-form-item label="超时(秒)">
          <el-input-number v-model="itemForm.timeout_seconds" :min="5" :max="300"></el-input-number>
        </el-form-item>

        <el-divider content-position="left">AI 自然语言期望（主判定）</el-divider>
        <el-form-item label="期望说明" required>
          <el-input
            v-model="itemForm.config.expectation"
            type="textarea"
            :rows="3"
            placeholder="例如：近1小时支付成功但未发货的订单数应为0；接口应返回业务成功且响应时间合理"
          />
          <div class="form-hint">系统会先采集数据，再用 AI 根据这段自然语言判定通过/失败；失败时自动做根因分析。</div>
        </el-form-item>

        <!-- 接口巡检配置 -->
        <template v-if="itemForm.item_type === 'api'">
          <el-divider content-position="left">数据采集（接口）</el-divider>
          <el-form-item label="请求方法">
            <el-select v-model="itemForm.config.method" style="width: 120px">
              <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="URL">
            <el-input v-model="itemForm.config.url" placeholder="https://api.example.com/health"></el-input>
          </el-form-item>
          <el-form-item label="请求头">
            <el-input v-model="headersText" type="textarea" :rows="2" placeholder='{"Content-Type": "application/json"}'></el-input>
          </el-form-item>
          <el-form-item label="请求体">
            <el-input v-model="bodyText" type="textarea" :rows="3" placeholder="JSON body"></el-input>
          </el-form-item>
          <el-collapse style="margin-bottom: 8px">
            <el-collapse-item title="高级：规则断言（可选预检）" name="api-assert">
              <div v-for="(a, idx) in itemForm.config.assertions" :key="'a'+idx" style="margin-bottom: 8px">
                <el-row :gutter="8">
                  <el-col :span="5">
                    <el-select v-model="a.type" size="mini" placeholder="类型">
                      <el-option label="状态码" value="status_code"></el-option>
                      <el-option label="响应时间" value="response_time"></el-option>
                      <el-option label="JSONPath" value="json_path"></el-option>
                      <el-option label="响应头" value="header"></el-option>
                      <el-option label="包含" value="body_contains"></el-option>
                    </el-select>
                  </el-col>
                  <el-col :span="4" v-if="a.type === 'json_path'">
                    <el-input v-model="a.path" size="mini" placeholder="$.data.code"></el-input>
                  </el-col>
                  <el-col :span="4">
                    <el-select v-model="a.operator" size="mini">
                      <el-option label="=" value="eq"></el-option>
                      <el-option label="!=" value="ne"></el-option>
                      <el-option label=">" value="gt"></el-option>
                      <el-option label="<" value="lt"></el-option>
                      <el-option label=">=" value="gte"></el-option>
                      <el-option label="<=" value="lte"></el-option>
                      <el-option label="包含" value="contains"></el-option>
                      <el-option label="非空" value="not_empty"></el-option>
                    </el-select>
                  </el-col>
                  <el-col :span="5">
                    <el-input v-model="a.expected" size="mini" placeholder="期望值"></el-input>
                  </el-col>
                  <el-col :span="2">
                    <el-button type="text" size="mini" style="color: #F56C6C" icon="el-icon-delete" @click="itemForm.config.assertions.splice(idx, 1)"></el-button>
                  </el-col>
                </el-row>
              </div>
              <el-button size="mini" icon="el-icon-plus" @click="itemForm.config.assertions.push({type: 'status_code', operator: 'eq', expected: 200})">添加断言</el-button>
            </el-collapse-item>
          </el-collapse>
        </template>

        <!-- SQL 巡检配置 -->
        <template v-if="itemForm.item_type === 'sql'">
          <el-divider content-position="left">数据采集（SQL）</el-divider>
          <el-form-item label="数据库连接">
            <el-select v-model="itemForm.config.db_config_id" filterable placeholder="选择数据库连接" style="width: 100%">
              <el-option v-for="c in dbConfigs" :key="c.id" :label="c.name + ' (' + c.db_type + ')'" :value="c.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="SQL 语句">
            <el-input v-model="itemForm.config.sql" type="textarea" :rows="4" placeholder="SELECT count(*) FROM ..."></el-input>
          </el-form-item>
          <el-collapse style="margin-bottom: 8px">
            <el-collapse-item title="高级：规则断言（可选预检）" name="sql-assert">
              <div v-for="(a, idx) in itemForm.config.assertions" :key="'sa'+idx" style="margin-bottom: 8px">
                <el-row :gutter="8">
                  <el-col :span="5">
                    <el-select v-model="a.type" size="mini">
                      <el-option label="行数" value="row_count"></el-option>
                      <el-option label="列值" value="column_value"></el-option>
                      <el-option label="非空" value="not_empty"></el-option>
                      <el-option label="为空" value="is_empty"></el-option>
                    </el-select>
                  </el-col>
                  <el-col :span="4" v-if="a.type === 'column_value'">
                    <el-input v-model="a.column" size="mini" placeholder="列名"></el-input>
                  </el-col>
                  <el-col :span="4">
                    <el-select v-model="a.operator" size="mini">
                      <el-option label="=" value="eq"></el-option>
                      <el-option label="!=" value="ne"></el-option>
                      <el-option label=">" value="gt"></el-option>
                      <el-option label="<" value="lt"></el-option>
                    </el-select>
                  </el-col>
                  <el-col :span="5">
                    <el-input v-model="a.expected" size="mini" placeholder="期望值"></el-input>
                  </el-col>
                  <el-col :span="2">
                    <el-button type="text" size="mini" style="color: #F56C6C" icon="el-icon-delete" @click="itemForm.config.assertions.splice(idx, 1)"></el-button>
                  </el-col>
                </el-row>
              </div>
              <el-button size="mini" icon="el-icon-plus" @click="itemForm.config.assertions.push({type: 'row_count', operator: 'gt', expected: 0})">添加断言</el-button>
            </el-collapse-item>
          </el-collapse>
        </template>

        <!-- 脚本巡检配置 -->
        <template v-if="itemForm.item_type === 'script'">
          <el-divider content-position="left">数据采集（脚本）</el-divider>
          <el-form-item label="语言">
            <el-radio-group v-model="itemForm.config.language">
              <el-radio label="python">Python</el-radio>
              <el-radio label="shell">Shell</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="脚本内容">
            <el-input v-model="itemForm.config.script" type="textarea" :rows="8" placeholder="输入脚本内容..." style="font-family: monospace"></el-input>
          </el-form-item>
          <el-collapse style="margin-bottom: 8px">
            <el-collapse-item title="高级：规则断言（可选预检）" name="script-assert">
              <div v-for="(a, idx) in itemForm.config.assertions" :key="'pa'+idx" style="margin-bottom: 8px">
                <el-row :gutter="8">
                  <el-col :span="6">
                    <el-select v-model="a.type" size="mini">
                      <el-option label="退出码" value="exit_code"></el-option>
                      <el-option label="输出包含" value="stdout_contains"></el-option>
                      <el-option label="输出不包含" value="stdout_not_contains"></el-option>
                      <el-option label="错误为空" value="stderr_empty"></el-option>
                      <el-option label="输出正则" value="stdout_matches"></el-option>
                    </el-select>
                  </el-col>
                  <el-col :span="8">
                    <el-input v-model="a.expected" size="mini" placeholder="期望值"></el-input>
                  </el-col>
                  <el-col :span="2">
                    <el-button type="text" size="mini" style="color: #F56C6C" icon="el-icon-delete" @click="itemForm.config.assertions.splice(idx, 1)"></el-button>
                  </el-col>
                </el-row>
              </div>
              <el-button size="mini" icon="el-icon-plus" @click="itemForm.config.assertions.push({type: 'exit_code', expected: 0})">添加断言</el-button>
            </el-collapse-item>
          </el-collapse>
        </template>

        <!-- 自动化用例 -->
        <template v-if="itemForm.item_type === 'auto_case'">
          <el-divider content-position="left">用例配置</el-divider>
          <el-form-item label="用例 ID">
            <el-input-number v-model="itemForm.config.case_id" :min="1" style="width: 100%"></el-input-number>
          </el-form-item>
          <el-form-item label="设备序列号">
            <el-input v-model="itemForm.config.device_serial" placeholder="可选"></el-input>
          </el-form-item>
        </template>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="itemSaving" @click="saveItem">保存</el-button>
      </div>
    </el-dialog>

    <!-- 测试结果弹窗 -->
    <el-dialog title="测试结果" :visible.sync="testResultVisible" width="640px">
      <div v-if="testResult">
        <el-alert :title="testResult.status === 'pass' ? '通过' : (testResult.status === 'fail' ? '失败' : '异常')"
          :type="testResult.status === 'pass' ? 'success' : 'error'" :closable="false" style="margin-bottom: 12px">
        </el-alert>
        <p>耗时: {{ testResult.duration_ms }}ms</p>
        <p v-if="testResult.error_message">错误: {{ testResult.error_message }}</p>
        <div v-if="testResult.result && testResult.result.ai_verdict" style="margin: 10px 0; padding: 10px; background: #f5f9ff; border-radius: 4px">
          <div><strong>AI 判定：</strong>{{ testResult.result.ai_verdict.passed ? '通过' : '未通过' }}
            <span v-if="testResult.result.ai_verdict.confidence != null" style="color:#909399;margin-left:8px">置信度 {{ testResult.result.ai_verdict.confidence }}</span>
          </div>
          <div style="margin-top:6px">{{ testResult.result.ai_verdict.reason }}</div>
        </div>
        <div v-if="testResult.result && testResult.result.ai_analysis" style="margin: 10px 0; padding: 10px; background: #fff7f0; border-radius: 4px">
          <div><strong>失败分析：</strong>[{{ testResult.result.ai_analysis.category || '未知' }}] {{ testResult.result.ai_analysis.root_cause }}</div>
          <div v-if="testResult.result.ai_analysis.impact" style="margin-top:4px">影响：{{ testResult.result.ai_analysis.impact }}</div>
          <ul v-if="testResult.result.ai_analysis.suggestions && testResult.result.ai_analysis.suggestions.length" style="margin:6px 0 0;padding-left:18px">
            <li v-for="(s, i) in testResult.result.ai_analysis.suggestions" :key="i">{{ s }}</li>
          </ul>
        </div>
        <pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; max-height: 300px; overflow: auto; font-size: 12px">{{ JSON.stringify(testResult.result, null, 2) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import {
  getInspectionTaskDetail, createInspectionItem, updateInspectionItem,
  deleteInspectionItem, testInspectionItem, getInspectionDbConfigList
} from '@/api/inspectionApi'

export default {
  name: 'InspectionTaskForm',
  components: { PageSection },
  data() {
    return {
      taskId: null,
      task: {},
      items: [],
      itemsLoading: false,
      itemFilter: '',
      itemDialogVisible: false,
      itemSaving: false,
      itemForm: {},
      headersText: '',
      bodyText: '',
      dbConfigs: [],
      testResultVisible: false,
      testResult: null
    }
  },
  created() {
    this.taskId = this.$route.query.id
    if (this.taskId) {
      this.fetchTask()
      this.fetchItems()
      this.loadDbConfigs()
    }
  },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    fetchTask() {
      getInspectionTaskDetail(this.taskId).then(res => {
        var data = this.dataOf(res)
        this.task = data
        this.items = data.items || []
      })
    },
    fetchItems() {
      // Items are loaded with task detail, but can be refreshed
    },
    loadDbConfigs() {
      getInspectionDbConfigList({ page_size: 200 }).then(res => {
        this.dbConfigs = this.dataOf(res).items || []
      })
    },
    typeColor(type) {
      var map = { api: 'success', sql: 'warning', script: 'info', auto_case: '' }
      return map[type] || ''
    },
    configSummary(item) {
      var config = item.config || {}
      if (config.expectation) return 'AI期望: ' + String(config.expectation).substring(0, 48)
      if (item.item_type === 'api') return (config.method || 'GET') + ' ' + (config.url || '')
      if (item.item_type === 'sql') return (config.sql || '').substring(0, 60)
      if (item.item_type === 'script') return (config.language || 'python') + ' (' + (config.script || '').length + ' chars)'
      if (item.item_type === 'auto_case') return 'case_id=' + (config.case_id || '-')
      return ''
    },
    addItem(type) {
      var defaultConfig = { expectation: '', assertions: [] }
      if (type === 'api') {
        defaultConfig = { expectation: '', method: 'GET', url: '', headers: {}, body: '', body_type: 'json', timeout: 5000, assertions: [] }
      } else if (type === 'sql') {
        defaultConfig = { expectation: '', db_config_id: '', sql: '', assertions: [] }
      } else if (type === 'script') {
        defaultConfig = { expectation: '', language: 'python', script: '', assertions: [] }
      } else if (type === 'auto_case') {
        defaultConfig = { expectation: '', case_id: '' }
      }
      this.itemForm = { item_type: type, name: '', config: defaultConfig, timeout_seconds: 30, sort_order: this.items.length }
      this.headersText = type === 'api' ? '{}' : ''
      this.bodyText = ''
      this.itemDialogVisible = true
    },
    editItem(row) {
      this.itemForm = JSON.parse(JSON.stringify(row))
      if (!this.itemForm.config) this.itemForm.config = {}
      if (this.itemForm.config.expectation == null) this.$set(this.itemForm.config, 'expectation', '')
      if (!this.itemForm.config.assertions) this.itemForm.config.assertions = []
      if (row.item_type === 'api') {
        this.headersText = JSON.stringify(this.itemForm.config.headers || {}, null, 2)
        this.bodyText = typeof this.itemForm.config.body === 'string' ? this.itemForm.config.body : JSON.stringify(this.itemForm.config.body || '', null, 2)
      }
      this.itemDialogVisible = true
    },
    saveItem() {
      if (!(this.itemForm.config && String(this.itemForm.config.expectation || '').trim())) {
        this.$message.warning('请填写自然语言期望（AI 主判定）')
        return
      }
      // Parse headers and body for API type
      if (this.itemForm.item_type === 'api') {
        try { this.itemForm.config.headers = JSON.parse(this.headersText || '{}') } catch (e) { /* keep as is */ }
        this.itemForm.config.body = this.bodyText
      }
      this.itemForm.task_id = this.taskId
      this.itemSaving = true
      var action = this.itemForm.id ? updateInspectionItem(this.itemForm) : createInspectionItem(this.itemForm)
      action.then(() => {
        this.$message.success('保存成功')
        this.itemDialogVisible = false
        this.fetchTask()
      }).finally(() => { this.itemSaving = false })
    },
    testItem(row) {
      this.$message.info('正在执行测试...')
      testInspectionItem({ item_type: row.item_type, config: row.config, timeout_seconds: row.timeout_seconds }).then(res => {
        this.testResult = this.dataOf(res)
        this.testResultVisible = true
      }).catch(err => {
        this.$message.error('测试执行失败')
      })
    },
    removeItem(row) {
      this.$confirm('确定删除巡检项「' + row.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionItem(row.id).then(() => {
          this.$message.success('删除成功')
          this.fetchTask()
        })
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.form-hint {
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
