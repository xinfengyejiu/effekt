<template>
  <div class="page-wrap weak-network-page">
    <page-section title="弱网配置">
      <template slot="extra">
        <el-button size="small" icon="el-icon-plus" type="primary" @click="openCreate">新建画像</el-button>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="真机弱网：选画像 → 下载 zip → 本机 .\weaknet.ps1 apply。用完务必 restore。不解密 HTTPS，不自动提 Bug。"
        style="margin-bottom:12px;"
      />

      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="选择产品" style="width:160px;" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="选择项目" style="width:160px;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:160px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="名称" min-width="140" prop="name" show-overflow-tooltip />
        <el-table-column label="预设" width="110" prop="presetCode" />
        <el-table-column label="延迟(ms)" width="100" prop="latencyMs" />
        <el-table-column label="带宽(kbps)" width="110" prop="bandwidthKbps" />
        <el-table-column label="丢包(%)" width="90" prop="lossPercent" />
        <el-table-column label="断网规则" min-width="140" show-overflow-tooltip>
          <template slot-scope="scope">{{ formatRules(scope.row.disconnectRules) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.isSystem ? 'warning' : 'info'">{{ scope.row.isSystem ? '系统' : '自定义' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.enabled ? 'success' : 'info'">{{ scope.row.enabled ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openDownload(scope.row)">下载脚本包</el-button>
            <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
            <el-button v-if="!scope.row.isSystem" type="text" style="color:#F56C6C;" @click="onDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10,20,50]"
          :total="total"
          @size-change="v => { pageSize = v; pageNo = 1; fetchList() }"
          @current-change="v => { pageNo = v; fetchList() }"
        />
      </div>
    </page-section>

    <page-section title="使用说明" style="margin-top:16px;">
      <ol class="usage-list">
        <li>下载 zip 并解压到连着真机的 Windows 电脑。</li>
        <li>确认 <code>adb devices</code> 可见设备，Python 在 PATH。</li>
        <li>执行 <code>.\weaknet.ps1 apply</code> → <code>status</code> 应显示 active=True。</li>
        <li>测完执行 <code>.\weaknet.ps1 restore</code>（可重复执行）。若仍异常：手机设置里关掉代理 / <code>adb shell settings delete global http_proxy</code>。</li>
        <li>若 App 不走系统代理：手机 Wi‑Fi 手动代理指向电脑局域网 IP + 端口（默认 18888）。</li>
      </ol>
    </page-section>

    <el-dialog :title="formMode === 'create' ? '新建弱网画像' : '编辑弱网画像'" :visible.sync="formVisible" width="560px" :close-on-click-modal="false">
      <el-form ref="form" :model="form" :rules="formRules" label-width="110px" size="small">
        <el-form-item label="名称" prop="name">
          <el-input v-model.trim="form.name" maxlength="128" />
        </el-form-item>
        <el-form-item v-if="formMode === 'create'" label="预设码">
          <el-select v-model="form.presetCode" style="width:100%;">
            <el-option label="自定义 custom" value="custom" />
            <el-option label="地铁 subway" value="subway" />
            <el-option label="电梯 elevator" value="elevator" />
            <el-option label="差Wi-Fi poor_wifi" value="poor_wifi" />
          </el-select>
        </el-form-item>
        <el-form-item label="延迟(ms)" prop="latencyMs">
          <el-input-number v-model="form.latencyMs" :min="0" :max="10000" :step="50" />
        </el-form-item>
        <el-form-item label="带宽(kbps)">
          <el-input-number v-model="form.bandwidthKbps" :min="0" :max="100000" :step="50" />
          <span class="hint">0 = 不限速</span>
        </el-form-item>
        <el-form-item label="丢包(%)">
          <el-input-number v-model="form.lossPercent" :min="0" :max="100" :step="0.5" />
        </el-form-item>
        <el-form-item label="断网周期(秒)">
          <el-input-number v-model="form.cycleSec" :min="0" :max="600" />
          <span class="hint">0 = 不断网</span>
        </el-form-item>
        <el-form-item label="断网持续(秒)">
          <el-input-number v-model="form.downSec" :min="0" :max="120" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="formVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="formLoading" @click="submitForm">保存</el-button>
      </div>
    </el-dialog>

    <el-dialog title="下载弱网脚本包" :visible.sync="downloadVisible" width="520px" :close-on-click-modal="false">
      <el-form label-width="110px" size="small">
        <el-form-item label="画像">
          <span>{{ downloadRow && downloadRow.name }}（{{ downloadRow && downloadRow.presetCode }}）</span>
        </el-form-item>
        <el-form-item label="设备 serial">
          <el-input v-model.trim="downloadForm.deviceSerial" placeholder="可选，预填到 session.json" />
        </el-form-item>
        <el-form-item label="代理端口">
          <el-input-number v-model="downloadForm.proxyPort" :min="1024" :max="65000" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="downloadVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="downloadLoading" @click="submitDownload">创建会话并下载</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getWeakNetworkProfiles,
  createWeakNetworkProfile,
  updateWeakNetworkProfile,
  deleteWeakNetworkProfile,
  createWeakNetworkSession,
  downloadWeakNetworkSession
} from '@/api/weakNetworkApi'

export default {
  name: 'WeakNetworkProfileList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      queryForm: { productId: '', projectId: '', keyword: '' },
      productOptions: [],
      projectOptions: [],
      formVisible: false,
      formLoading: false,
      formMode: 'create',
      form: this.emptyForm(),
      formRules: {
        name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
      },
      downloadVisible: false,
      downloadLoading: false,
      downloadRow: null,
      downloadForm: { deviceSerial: '', proxyPort: 18888 }
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    emptyForm() {
      return {
        profileId: null,
        name: '',
        presetCode: 'custom',
        latencyMs: 300,
        bandwidthKbps: 0,
        lossPercent: 0,
        cycleSec: 0,
        downSec: 0,
        remark: '',
        enabled: 1
      }
    },
    formatRules(rules) {
      if (!rules || !Object.keys(rules).length) return '-'
      const c = rules.cycle_sec || rules.cycleSec
      const d = rules.down_sec || rules.downSec
      if (c && d) return '每' + c + 's 断' + d + 's'
      return JSON.stringify(rules)
    },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        const data = (res && res.data) || res || {}
        this.productOptions = data.list || data.records || []
      }).catch(() => {})
    },
    onProductChange() {
      this.queryForm.projectId = ''
      this.projectOptions = []
      if (!this.queryForm.productId) return
      getProjectList({ productId: this.queryForm.productId, pageNo: 1, pageSize: 200 }).then(res => {
        const data = (res && res.data) || res || {}
        this.projectOptions = data.list || data.records || []
      }).catch(() => {})
    },
    fetchList() {
      this.loading = true
      getWeakNetworkProfiles(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize }))
        .then(res => {
          const data = (res && res.data) || res || {}
          this.rows = data.list || []
          this.total = data.total || 0
        })
        .finally(() => { this.loading = false })
    },
    openCreate() {
      this.formMode = 'create'
      this.form = this.emptyForm()
      this.formVisible = true
    },
    openEdit(row) {
      this.formMode = 'edit'
      const rules = row.disconnectRules || {}
      this.form = {
        profileId: row.profileId,
        name: row.name,
        presetCode: row.presetCode,
        latencyMs: row.latencyMs,
        bandwidthKbps: row.bandwidthKbps,
        lossPercent: Number(row.lossPercent || 0),
        cycleSec: Number(rules.cycle_sec || rules.cycleSec || 0),
        downSec: Number(rules.down_sec || rules.downSec || 0),
        remark: row.remark || '',
        enabled: row.enabled
      }
      this.formVisible = true
    },
    buildDisconnectRules() {
      if (!this.form.cycleSec || !this.form.downSec) return {}
      return { cycle_sec: this.form.cycleSec, down_sec: this.form.downSec }
    },
    submitForm() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        const payload = {
          profileId: this.form.profileId,
          name: this.form.name,
          presetCode: this.form.presetCode,
          latencyMs: this.form.latencyMs,
          bandwidthKbps: this.form.bandwidthKbps,
          lossPercent: this.form.lossPercent,
          disconnectRules: this.buildDisconnectRules(),
          remark: this.form.remark,
          enabled: this.form.enabled,
          productId: this.queryForm.productId || null,
          projectId: this.queryForm.projectId || null
        }
        this.formLoading = true
        const req = this.formMode === 'create' ? createWeakNetworkProfile(payload) : updateWeakNetworkProfile(payload)
        req.then(() => {
          this.$message.success('已保存')
          this.formVisible = false
          this.fetchList()
        }).finally(() => { this.formLoading = false })
      })
    },
    onDelete(row) {
      this.$confirm('确认删除该自定义画像？', '提示', { type: 'warning' }).then(() => {
        return deleteWeakNetworkProfile({ profileId: row.profileId })
      }).then(() => {
        this.$message.success('已删除')
        this.fetchList()
      }).catch(() => {})
    },
    openDownload(row) {
      this.downloadRow = row
      this.downloadForm = { deviceSerial: '', proxyPort: 18888 }
      this.downloadVisible = true
    },
    submitDownload() {
      if (!this.downloadRow) return
      this.downloadLoading = true
      createWeakNetworkSession({
        profileId: this.downloadRow.profileId,
        deviceSerial: this.downloadForm.deviceSerial || '',
        proxyPort: this.downloadForm.proxyPort,
        productId: this.queryForm.productId || null,
        projectId: this.queryForm.projectId || null
      }).then(res => {
        const data = (res && res.data) || res || {}
        const sessionId = data.sessionId
        if (!sessionId) {
          this.$message.error('未返回 sessionId')
          return null
        }
        return downloadWeakNetworkSession(sessionId).then(blob => {
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'weaknet-' + (this.downloadRow.presetCode || 'custom') + '-' + (data.sessionNo || sessionId) + '.zip'
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          window.URL.revokeObjectURL(url)
          this.$message.success('已下载，请解压后执行 weaknet.ps1 apply')
          this.downloadVisible = false
        })
      }).finally(() => { this.downloadLoading = false })
    }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 12px; text-align: right; }
.usage-list { margin: 0; padding-left: 20px; line-height: 1.8; color: #606266; }
.usage-list code { background: #f5f7fa; padding: 1px 6px; border-radius: 3px; }
.hint { margin-left: 8px; color: #909399; font-size: 12px; }
</style>
