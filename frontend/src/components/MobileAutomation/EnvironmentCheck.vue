<template>
  <div class="page-wrap">
    <page-section title="移动自动化环境">
      <template slot="extra">
        <el-button
          v-if="!appiumReady"
          size="small"
          type="warning"
          :loading="startingAppium"
          @click="startAppium"
        >启动 Appium</el-button>
        <el-button size="small" :loading="loading" @click="fetchCheck">重新检查</el-button>
      </template>
      <el-alert
        title="平台会检查本机依赖。可一键启动 Appium；其余依赖仍需按部署规范完成本机准备。"
        type="info"
        :closable="false"
        show-icon
      />
      <div v-loading="loading" class="check-grid">
        <div v-for="item in checkItems" :key="item.key" class="check-item">
          <div>
            <b>{{ item.name }}</b>
            <p>{{ item.detail }}</p>
          </div>
          <el-tag size="mini" :type="item.available ? 'success' : 'danger'">{{ item.available ? '可用' : '不可用' }}</el-tag>
        </div>
      </div>
      <div v-if="missingItems.length" class="hint">
        缺失项：{{ missingItems.join('、') }}。
        <template v-if="!appiumReady">可点击右上角「启动 Appium」。</template>
        <template v-else>请按部署规范完成本机准备后再创建任务。</template>
      </div>
    </page-section>
    <mobile-device-list ref="devices" />
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import MobileDeviceList from './DeviceList'
import { getMobileEnvironmentCheck, startMobileAppium } from '@/api/mobileAutomationApi'

export default {
  name: 'MobileAutomationEnvironmentCheck',
  components: { PageSection, MobileDeviceList },
  data () {
    return {
      loading: false,
      startingAppium: false,
      diagnostic: {}
    }
  },
  computed: {
    appiumReady () {
      const d = this.diagnostic || {}
      return !!(d.appium && d.appium.available)
    },
    checkItems () {
      const d = this.diagnostic || {}
      const modules = d.modules || {}
      const repo = d.script_repository || {}
      return [
        { key: 'adb', name: 'ADB', available: !!(d.adb && d.adb.available), detail: (d.adb && (d.adb.error || d.adb.version)) || '-' },
        { key: 'python', name: 'Python', available: !!(d.python && d.python.available), detail: (d.python && d.python.path) || '-' },
        { key: 'pytest', name: 'pytest', available: !!(modules.pytest && modules.pytest.installed), detail: modules.pytest && modules.pytest.error },
        { key: 'uiautomator2', name: 'uiautomator2', available: !!(modules.uiautomator2 && modules.uiautomator2.installed), detail: modules.uiautomator2 && modules.uiautomator2.error },
        { key: 'allure', name: 'allure-pytest', available: !!(modules.allure_pytest && modules.allure_pytest.installed), detail: modules.allure_pytest && modules.allure_pytest.error },
        { key: 'server', name: 'Appium 服务', available: !!(d.appium && d.appium.available), detail: (d.appium && (d.appium.error || d.appium.url)) || '-' },
        { key: 'repo', name: '脚本仓库', available: !!repo.available && !!repo.pytest_ini_exists, detail: repo.path || '-' }
      ]
    },
    missingItems () {
      return this.checkItems.filter(item => !item.available).map(item => item.name)
    }
  },
  created () {
    this.fetchCheck()
  },
  methods: {
    dataOf (res) {
      return (res && res.data) || res || {}
    },
    fetchCheck () {
      this.loading = true
      return getMobileEnvironmentCheck().then(res => {
        this.diagnostic = this.dataOf(res)
      }).finally(() => {
        this.loading = false
      })
    },
    startAppium () {
      this.startingAppium = true
      startMobileAppium().then(res => {
        const d = this.dataOf(res)
        if (d.diagnostic) this.diagnostic = d.diagnostic
        this.$message.success(d.message || 'Appium 已就绪')
        return this.fetchCheck()
      }).catch(err => {
        const msg = (err && (err.message || err.msg)) || '启动 Appium 失败'
        this.$message.error(msg)
      }).finally(() => {
        this.startingAppium = false
      })
    }
  }
}
</script>

<style scoped>
.check-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; margin-top: 16px; }
.check-item { min-height: 70px; display: flex; justify-content: space-between; gap: 12px; padding: 12px; border: 1px solid #e4e7ed; border-radius: 4px; }
.check-item p { margin: 6px 0 0; color: #909399; font-size: 12px; word-break: break-all; white-space: pre-line; }
.hint { margin-top: 14px; color: #e6a23c; }
</style>
