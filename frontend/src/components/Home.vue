<template>
  <div class="auto-test-main" :class="themeClass">
    <el-container class="app-shell">
      <aside class="aside" :class="{ 'aside--collapse': isCollapse }">
        <div class="brand-panel">
          <div class="brand-mark">效</div>
          <div v-show="!isCollapse" class="brand-copy">
            <div class="brand-name">{{ systemName }}</div>
            <div class="brand-subtitle">Quality Workspace</div>
          </div>
        </div>
        <div class="aside-menu-scroll">
        <el-menu
          :default-active="$route.path"
          class="el-menu-vertical-demo"
          :collapse="isCollapse"
          :background-color="menuBackgroundColor"
          :text-color="menuTextColor"
          :active-text-color="menuActiveTextColor"
          :router="true">
          <template v-for="menu in displayMenus">
            <el-submenu v-if="menu.children && menu.children.length > 0" :index="menuIndex(menu)" :key="'sub-' + menuKey(menu)">
              <template slot="title">
                <i :class="menuIcon(menu)"></i>
                <span slot="title">{{ menu.name }}</span>
              </template>
              <template v-for="child in menu.children">
                <!-- 处理可能有第三级菜单的情况 -->
                <el-submenu v-if="child.children && child.children.length > 0" :index="menuIndex(child)" :key="'child-sub-' + menuKey(child)">
                  <template slot="title">
                    <i v-if="child.icon" :class="menuIcon(child)"></i>
                    <span slot="title">{{ child.name }}</span>
                  </template>
                  <el-menu-item v-for="subChild in child.children" :index="menuPath(subChild)" :key="'subchild-item-' + menuKey(subChild)">
                    <i v-if="subChild.icon" :class="menuIcon(subChild)"></i>
                    <span slot="title">{{ subChild.name }}</span>
                  </el-menu-item>
                </el-submenu>
                <!-- 只有两级菜单 -->
                <el-menu-item v-else :index="menuPath(child)" :key="'child-item-' + menuKey(child)">
                  <i v-if="child.icon" :class="menuIcon(child)"></i>
                  <span slot="title">{{ child.name }}</span>
                </el-menu-item>
              </template>
            </el-submenu>
            <el-menu-item v-else :index="menuPath(menu)" :key="'item-' + menuKey(menu)">
              <i :class="menuIcon(menu)"></i>
              <span slot="title">{{ menu.name }}</span>
            </el-menu-item>
          </template>
        </el-menu>
        </div>
      </aside>
      <el-container class="workspace-shell">
        <el-header class="header">
          <div class="header-left">
            <button class="header-icon" type="button" @click="setCollapse">
              <i v-if="isCollapse" class="el-icon-s-unfold"></i>
              <i v-else class="el-icon-s-fold"></i>
            </button>
            <div class="system-name">
              <span>{{ systemName }}</span>
              <small>测试协作与效能管理平台</small>
            </div>
          </div>
          <div class="header-user">
            <button class="theme-switch" type="button" @click="toggleTheme">
              <i :class="themeIcon"></i>
              <span>{{ themeLabel }}</span>
            </button>
            <el-dropdown v-if="currentUser" trigger="click" @command="handleUserCommand">
              <span class="user-name-dropdown">
                {{ displayName }}<i class="el-icon-arrow-down el-icon--right"></i>
              </span>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
            <span v-else class="login-label" @click="goLogin">登录</span>
          </div>
        </el-header>
        <el-main class="main-canvas">
          <router-view class="main-form" name="Manage"></router-view>
        </el-main>
      </el-container>
    </el-container>
    <quality-assistant-panel />
  </div>
</template>

<script>
import QualityAssistantPanel from '@/components/QualityAssistant/QualityAssistantPanel.vue'

export default {
  name: 'Home',
  components: { QualityAssistantPanel },
  data() {
    return {
      isCollapse: false,
      systemName: '效能平台',
      uiTheme: localStorage.getItem('uiTheme') || 'dark'
    }
  },
  mounted() {
    this.applyTheme()
  },
  computed: {
    currentUser() {
      return this.$store.state.currentUser
    },
    userMenus() {
      return this.$store.state.userMenus || []
    },
    displayMenus() {
      const homeMenu = { name: '首页', path: '/effekt', icon: 'el-icon-house', children: [] }
      if (!this.userMenus.length) {
        return [homeMenu]
      }
      const filteredMenus = this.filterMenus(this.userMenus)
      const menus = this.renameTestPlatformToCycle(filteredMenus)
      const withSkillMenu = this.injectBusinessSkillConfigMenu(menus)
      const withAiMenu = this.injectAiPlatformMenu(withSkillMenu)
      const withAiReviewMenu = this.injectAiReviewMenu(withAiMenu)
      const withAiWorkloadEstimateMenu = this.injectAiWorkloadEstimateMenu(withAiReviewMenu)
      const withMockMenu = this.injectMockServiceMenu(withAiWorkloadEstimateMenu)
      const withRequirementQaMenu = this.injectRequirementQaMenu(withMockMenu)
      const withPerformanceMenu = this.injectPerformanceMenu(withRequirementQaMenu)
      const withMobileAutomationMenu = this.injectMobileAutomationMenu(withPerformanceMenu)
      const withInspectionMenu = this.injectInspectionMenu(withMobileAutomationMenu)
      const withContractMenu = this.injectContractMenu(withInspectionMenu)
      const regroupedMenus = this.regroupProductProjectMenus(withContractMenu)
      const sorted = this.sortMenusByProductOrder(regroupedMenus)
      const hasHome = sorted.some(menu => menu.path === '/effekt' || menu.name === '首页')
      if (hasHome) {
        return sorted
      }
      return [homeMenu, ...sorted]
    },
    displayName() {
      if (!this.currentUser) {
        return ''
      }
      return this.currentUser.username || this.currentUser.realName || '未命名用户'
    },
    themeClass() {
      return this.uiTheme === 'light' ? 'theme-shell-light' : 'theme-shell-dark'
    },
    themeLabel() {
      return this.uiTheme === 'light' ? '深色' : '浅色'
    },
    themeIcon() {
      return this.uiTheme === 'light' ? 'el-icon-moon' : 'el-icon-sunny'
    },
    menuBackgroundColor() {
      return this.uiTheme === 'light' ? '#ffffff' : '#07111f'
    },
    menuTextColor() {
      return this.uiTheme === 'light' ? '#64748b' : '#93a9c7'
    },
    menuActiveTextColor() {
      return this.uiTheme === 'light' ? '#ffffff' : '#e0f2fe'
    }
  },
  methods: {
    applyTheme() {
      document.body.classList.remove('theme-dark', 'theme-light')
      document.body.classList.add(this.uiTheme === 'light' ? 'theme-light' : 'theme-dark')
    },
    toggleTheme() {
      this.uiTheme = this.uiTheme === 'light' ? 'dark' : 'light'
      localStorage.setItem('uiTheme', this.uiTheme)
      this.applyTheme()
    },
    setCollapse() {
      this.isCollapse = !this.isCollapse
    },
    goLogin() {
      this.$router.push({ name: 'login' })
    },
    menuKey(item) {
      return String(item.menuId || item.id || item.path || item.name)
    },
    menuIndex(item) {
      return String(item.path || item.code || item.menuId || item.id || item.name)
    },
    menuPath(item) {
      const pathMap = {
        '/system/role': '/system/role',
        '/system/user': '/system/user',
        '/system/menu': '/system/menu',
        '/system/permission': '/system/permission',
        '/test-platform/skill-rules': '/test-platform/skill-rules',
        '/test-platform/ai-platform': '/test-platform/ai-platform',
        '/ai-review': '/ai-review',
        '/ai-workload-estimate': '/ai-workload-estimate',
        '/bug': '/bug/list',
        '/bug/list': '/bug/list',
        '/bug/detail': '/bug/detail',
        '/bug/create': '/bug/create',
        '/bug/edit': '/bug/edit',
        '/bug/stats': '/bug/stats',
        '/requirement-qa': '/requirement-qa',
        '/performance': '/performance/scenarios',
        '/performance/scenarios': '/performance/scenarios',
        '/performance/run-wizard': '/performance/run-wizard',
        '/performance/runs': '/performance/runs',
        '/performance/reports': '/performance/reports',
        '/performance/machines': '/performance/machines',
        '/mobile-automation': '/mobile-automation/devices',
        '/mobile-automation/devices': '/mobile-automation/devices',
        '/mobile-automation/apps': '/mobile-automation/apps',
        '/mobile-automation/run': '/mobile-automation/run',
        '/mobile-automation/executions': '/mobile-automation/executions',
        '/mock': '/mock/interface',
        '/mock/document': '/mock/document',
        '/mock/interface': '/mock/interface',
        '/mock/log': '/mock/log',
        '/inspection': '/inspection/dashboard',
        '/inspection/dashboard': '/inspection/dashboard',
        '/inspection/groups': '/inspection/tasks',
        '/inspection/tasks': '/inspection/tasks',
        '/inspection/task/edit': '/inspection/task/edit',
        '/inspection/db-configs': '/inspection/db-configs',
        '/inspection/executions': '/inspection/executions',
        '/inspection/execution/detail': '/inspection/execution/detail',
        '/inspection/reports': '/inspection/reports',
        '/contract': '/contract/suites',
        '/contract/suites': '/contract/suites',
        '/contract/suite/edit': '/contract/suite/edit',
        '/contract/runs': '/contract/runs',
        '/contract/run/detail': '/contract/run/detail'
      }
      return pathMap[item.path] || item.path || '/effekt'
    },
    menuIcon(item) {
      const path = String(item.path || '')
      const pathIconMap = {
        '/bug': 'el-icon-s-claim',
        '/bug/create': 'el-icon-document-add',
        '/bug/list': 'el-icon-document',
        '/bug/stats': 'el-icon-data-line',
        '/bug/detail': 'el-icon-view',
        '/bug/edit': 'el-icon-edit-outline',
        '/mock': 'el-icon-connection',
        '/mock/document': 'el-icon-document-copy',
        '/mock/interface': 'el-icon-link',
        '/mock/log': 'el-icon-tickets',
        '/requirement-qa': 'el-icon-chat-dot-round',
        '/performance': 'el-icon-data-analysis',
        '/performance/scenarios': 'el-icon-document',
        '/performance/run-wizard': 'el-icon-video-play',
        '/performance/runs': 'el-icon-tickets',
        '/performance/reports': 'el-icon-data-line',
        '/performance/machines': 'el-icon-cpu',
        '/mobile-automation': 'el-icon-mobile-phone',
        '/mobile-automation/devices': 'el-icon-mobile-phone',
        '/mobile-automation/apps': 'el-icon-box',
        '/mobile-automation/run': 'el-icon-video-play',
        '/mobile-automation/executions': 'el-icon-tickets',
        '/test-platform/ai-platform': 'el-icon-cpu',
        '/ai-review': 'el-icon-s-check',
        '/ai-workload-estimate': 'el-icon-time'
      }
      if (path && pathIconMap[path]) {
        return pathIconMap[path]
      }
      // 按照原来的静态菜单名称映射图标
      const nameIconMap = {
        '首页': 'el-icon-house',
        '项目工作台': 'el-icon-s-operation',
        'AI质量助手': 'el-icon-cpu',
        '测试支撑工具': 'el-icon-s-tools',
        '基础配置': 'el-icon-setting',
        '测试协作工作台': 'el-icon-s-operation',
        '测试平台': 'el-icon-s-platform',
        '用例周期': 'el-icon-s-platform',
        'Bug管理': 'el-icon-s-claim',
        '新建 Bug': 'el-icon-document-add',
        '创建Bug': 'el-icon-document-add',
        '创建 Bug': 'el-icon-document-add',
        'Bug 列表': 'el-icon-document',
        'Bug 统计': 'el-icon-data-line',
        '产品管理': 'el-icon-box',
        '项目管理': 'el-icon-s-management',
        '用例管理': 'el-icon-document',
        '业务技能配置': 'el-icon-collection',
        'AI测试中枢': 'el-icon-cpu',
        'AI测试评审': 'el-icon-s-check',
        'AI工作量预估': 'el-icon-time',
        '测试资产治理': 'el-icon-s-data',
        '探索Session': 'el-icon-edit-outline',
        '移动自动化': 'el-icon-mobile-phone',
        '弱网配置': 'el-icon-connection',
        '弱网AI任务': 'el-icon-magic-stick',
        '聊天问题导入': 'el-icon-chat-dot-round',
        '精准测试': 'el-icon-share',
        '测试计划': 'el-icon-date',
        '测试报告': 'el-icon-data-line',
        '测试工具': 'el-icon-s-tools',
        '造数工具': 'el-icon-magic-stick',
        '数据库造数': 'el-icon-coin',
        '造数工厂': 'el-icon-set-up',
        '造数结果历史': 'el-icon-document',
        '数据库造数': 'el-icon-coin',
        'mock服务': 'el-icon-connection',
        'Mock文档': 'el-icon-document-copy',
        'Mock接口': 'el-icon-link',
        'Mock调用日志': 'el-icon-tickets',
        '需求问答': 'el-icon-chat-dot-round',
        '性能测试': 'el-icon-data-analysis',
        '性能场景': 'el-icon-document',
        '发起压测': 'el-icon-video-play',
        '执行记录': 'el-icon-tickets',
        '性能报告': 'el-icon-data-line',
        '测试机资源池': 'el-icon-cpu',
        '移动自动化': 'el-icon-mobile-phone',
        '环境与设备': 'el-icon-mobile-phone',
        '应用配置': 'el-icon-box',
        '发起移动执行': 'el-icon-video-play',
        '移动执行记录': 'el-icon-tickets',
        '系统管理': 'el-icon-setting',
        '角色管理': 'el-icon-user-solid',
        '用户管理': 'el-icon-user',
        '权限管理': 'el-icon-lock',
        '菜单管理': 'el-icon-menu'
      }

      const iconMap = {
        setting: 'el-icon-setting',
        peoples: 'el-icon-user-solid',
        user: 'el-icon-user',
        lock: 'el-icon-lock',
        menu: 'el-icon-menu',
        warning: 'el-icon-warning-outline',
        edit: 'el-icon-edit',
        document: 'el-icon-document'
      }

      // 优先级：先匹配名称，再匹配接口中指定的 icon，最后返回默认图标 el-icon-menu
      if (item.name && nameIconMap[item.name]) {
        return nameIconMap[item.name]
      }
      return iconMap[item.icon] || (item.icon && item.icon.indexOf('el-icon-') === 0 ? item.icon : 'el-icon-menu')
    },
    filterMenus(menus) {
      return (menus || []).filter(item => item.visible !== 0 && item.status !== 0).map(item => {
        const children = this.filterMenus(item.children || [])
        return Object.assign({}, item, { children })
      }).filter(item => {
        if (item.children && item.children.length) {
          return true
        }
        return !!item.path && !!this.menuPath(item)
      })
    },
    renameTestPlatformToCycle(menus) {
      return (menus || []).map(item => {
        const name = item.name === '测试平台' ? '用例周期' : item.name
        const children = item.children && item.children.length
          ? this.renameTestPlatformToCycle(item.children)
          : item.children
        return Object.assign({}, item, { name, children })
      })
    },
    /**
     * 在「用例周期」分组下、「用例管理」上方插入「业务技能配置」（与后端菜单并存时去重）。
     */
    injectBusinessSkillConfigMenu(menus) {
      const INJECT_PATH = '/test-platform/skill-rules'
      const INJECT_KEY = '__inject_business_skill__'
      const makeItem = () => ({
        name: '业务技能配置',
        path: INJECT_PATH,
        icon: 'el-icon-collection',
        menuId: INJECT_KEY,
        id: INJECT_KEY,
        visible: 1,
        status: 1,
        children: []
      })
      const hasInjected = list =>
        (list || []).some(c => c.path === INJECT_PATH || c.menuId === INJECT_KEY || c.id === INJECT_KEY)
      const mergeCycleChildren = children => {
        if (!children || !children.length) return children || []
        if (hasInjected(children)) {
          return children.map(c =>
            c.children && c.children.length
              ? Object.assign({}, c, { children: this.injectBusinessSkillConfigMenu(c.children) })
              : c
          )
        }
        const next = children.map(c =>
          c.children && c.children.length
            ? Object.assign({}, c, { children: this.injectBusinessSkillConfigMenu(c.children) })
            : c
        )
        const idx = next.findIndex(c => {
          const p = String(c.path || '')
          return p === '/test-platform/case' || c.name === '用例管理'
        })
        if (idx >= 0) {
          next.splice(idx, 0, makeItem())
        } else {
          next.unshift(makeItem())
        }
        return next
      }
      return (menus || []).map(item => {
        if (item.name === '用例周期' && item.children && item.children.length) {
          return Object.assign({}, item, { children: mergeCycleChildren(item.children.slice()) })
        }
        if (item.children && item.children.length) {
          return Object.assign({}, item, { children: this.injectBusinessSkillConfigMenu(item.children) })
        }
        return item
      })
    },
    injectAiPlatformMenu(menus) {
      const INJECT_PATH = '/test-platform/ai-platform'
      const INJECT_KEY = '__inject_ai_platform__'
      const makeItem = () => ({
        name: 'AI测试中枢',
        path: INJECT_PATH,
        icon: 'el-icon-cpu',
        menuId: INJECT_KEY,
        id: INJECT_KEY,
        visible: 1,
        status: 1,
        children: []
      })
      const hasInjected = list =>
        (list || []).some(c => c.path === INJECT_PATH || c.menuId === INJECT_KEY || c.id === INJECT_KEY)
      const mergeCycleChildren = children => {
        if (!children || !children.length) return children || []
        if (hasInjected(children)) return children
        const next = children.slice()
        const idx = next.findIndex(c => String(c.path || '') === '/test-platform/skill-rules' || c.name === '业务技能配置')
        if (idx >= 0) {
          next.splice(idx + 1, 0, makeItem())
        } else {
          next.unshift(makeItem())
        }
        return next
      }
      return (menus || []).map(item => {
        if (item.name === '用例周期' && item.children && item.children.length) {
          return Object.assign({}, item, { children: mergeCycleChildren(item.children.slice()) })
        }
        if (item.children && item.children.length) {
          return Object.assign({}, item, { children: this.injectAiPlatformMenu(item.children) })
        }
        return item
      })
    },
    injectAiReviewMenu(menus) {
      const INJECT_PATH = '/ai-review'
      const INJECT_KEY = '__inject_ai_review__'
      const makeItem = () => ({
        name: 'AI测试评审',
        path: INJECT_PATH,
        icon: 'el-icon-s-check',
        menuId: INJECT_KEY,
        id: INJECT_KEY,
        visible: 1,
        status: 1,
        children: []
      })
      const hasInjected = list =>
        (list || []).some(c => c.path === INJECT_PATH || c.menuId === INJECT_KEY || c.id === INJECT_KEY || c.name === 'AI测试评审')
      const mergeCycleChildren = children => {
        if (!children || !children.length) return children || []
        if (hasInjected(children)) return children
        const next = children.slice()
        const idx = next.findIndex(c => String(c.path || '') === '/test-platform/ai-platform' || c.name === 'AI测试中枢')
        if (idx >= 0) {
          next.splice(idx + 1, 0, makeItem())
        } else {
          next.unshift(makeItem())
        }
        return next
      }
      return (menus || []).map(item => {
        if (item.name === '用例周期' && item.children && item.children.length) {
          return Object.assign({}, item, { children: mergeCycleChildren(item.children.slice()) })
        }
        if (item.children && item.children.length) {
          return Object.assign({}, item, { children: this.injectAiReviewMenu(item.children) })
        }
        return item
      })
    },
    injectAiWorkloadEstimateMenu(menus) {
      const INJECT_PATH = '/ai-workload-estimate'
      const INJECT_KEY = '__inject_ai_workload_estimate__'
      const makeItem = () => ({
        name: 'AI工作量预估',
        path: INJECT_PATH,
        icon: 'el-icon-time',
        menuId: INJECT_KEY,
        id: INJECT_KEY,
        visible: 1,
        status: 1,
        children: []
      })
      const hasInjected = list =>
        (list || []).some(c => c.path === INJECT_PATH || c.menuId === INJECT_KEY || c.id === INJECT_KEY || c.name === 'AI工作量预估')
      const mergeChildren = children => {
        if (!children || !children.length) return children || []
        if (hasInjected(children)) return children
        const next = children.slice()
        const idx = next.findIndex(c => String(c.path || '') === '/ai-review' || c.name === 'AI测试评审')
        if (idx >= 0) {
          next.splice(idx + 1, 0, makeItem())
        } else {
          next.unshift(makeItem())
        }
        return next
      }
      return (menus || []).map(item => {
        if ((item.name === '用例周期' || item.name === 'AI质量助手') && item.children && item.children.length) {
          return Object.assign({}, item, { children: mergeChildren(item.children.slice()) })
        }
        if (item.children && item.children.length) {
          return Object.assign({}, item, { children: this.injectAiWorkloadEstimateMenu(item.children) })
        }
        return item
      })
    },
    injectMockServiceMenu(menus) {
      const makeMockChildren = () => [
        { name: 'Mock文档', path: '/mock/document', icon: 'el-icon-document-copy', menuId: '__inject_mock_document__', id: '__inject_mock_document__', visible: 1, status: 1, children: [] },
        { name: 'Mock接口', path: '/mock/interface', icon: 'el-icon-link', menuId: '__inject_mock_interface__', id: '__inject_mock_interface__', visible: 1, status: 1, children: [] },
        { name: 'Mock调用日志', path: '/mock/log', icon: 'el-icon-tickets', menuId: '__inject_mock_log__', id: '__inject_mock_log__', visible: 1, status: 1, children: [] }
      ]
      const makeMockGroup = () => ({
        name: 'mock服务',
        path: '/mock',
        icon: 'el-icon-connection',
        menuId: '__inject_mock_service__',
        id: '__inject_mock_service__',
        visible: 1,
        status: 1,
        children: makeMockChildren()
      })
      const isMockTopGroup = item => {
        if (!item) return false
        const p = String(item.path || '')
        const n = String(item.name || '')
        return (
          n === 'mock服务' ||
          n === 'Mock服务' ||
          item.menuId === '__inject_mock_service__' ||
          item.id === '__inject_mock_service__' ||
          (p === '/mock' && item.children && item.children.length)
        )
      }
      /** 从其它菜单的子级里去掉误挂的 mock（mock 仅作一级菜单展示） */
      const stripNestedMockGroups = list =>
        (list || []).map(item => {
          const children = stripNestedMockGroups(
            (item.children || []).filter(child => !isMockTopGroup(child))
          )
          return Object.assign({}, item, { children })
        })
      let result = stripNestedMockGroups(menus || [])
      if (!result.some(isMockTopGroup)) {
        result = [...result, makeMockGroup()]
      } else {
        result = result.map(item => (isMockTopGroup(item) ? makeMockGroup() : item))
      }
      return result
    },
    injectRequirementQaMenu(menus) {
      const exists = (menus || []).some(item => String(item.path || '') === '/requirement-qa' || item.name === '需求问答')
      if (exists) return menus
      return [...(menus || []), {
        name: '需求问答',
        path: '/requirement-qa',
        icon: 'el-icon-chat-dot-round',
        menuId: '__inject_requirement_qa__',
        id: '__inject_requirement_qa__',
        visible: 1,
        status: 1,
        children: []
      }]
    },
    injectPerformanceMenu(menus) {
      const makeChildren = () => [
        { name: '性能场景', path: '/performance/scenarios', icon: 'el-icon-document', menuId: '__inject_performance_scenarios__', id: '__inject_performance_scenarios__', visible: 1, status: 1, children: [] },
        { name: '发起压测', path: '/performance/run-wizard', icon: 'el-icon-video-play', menuId: '__inject_performance_run_wizard__', id: '__inject_performance_run_wizard__', visible: 1, status: 1, children: [] },
        { name: '执行记录', path: '/performance/runs', icon: 'el-icon-tickets', menuId: '__inject_performance_runs__', id: '__inject_performance_runs__', visible: 1, status: 1, children: [] },
        { name: '性能报告', path: '/performance/reports', icon: 'el-icon-data-line', menuId: '__inject_performance_reports__', id: '__inject_performance_reports__', visible: 1, status: 1, children: [] },
        { name: '测试机资源池', path: '/performance/machines', icon: 'el-icon-cpu', menuId: '__inject_performance_machines__', id: '__inject_performance_machines__', visible: 1, status: 1, children: [] }
      ]
      const isPerformanceGroup = item => item && (String(item.path || '') === '/performance' || item.name === '性能测试' || item.menuId === '__inject_performance__' || item.id === '__inject_performance__')
      const mergeChildren = children => {
        const next = (children || []).slice()
        makeChildren().forEach(child => {
          if (!next.some(item => String(item.path || '') === child.path || item.name === child.name || item.menuId === child.menuId || item.id === child.id)) {
            next.push(child)
          }
        })
        return next
      }
      let hasGroup = false
      const result = (menus || []).map(item => {
        if (!isPerformanceGroup(item)) return item
        hasGroup = true
        return Object.assign({}, item, { name: '性能测试', path: '/performance', icon: item.icon || 'el-icon-data-analysis', children: mergeChildren(item.children) })
      })
      if (!hasGroup) {
        result.push({ name: '性能测试', path: '/performance', icon: 'el-icon-data-analysis', menuId: '__inject_performance__', id: '__inject_performance__', visible: 1, status: 1, children: makeChildren() })
      }
      return result
    },
    injectMobileAutomationMenu(menus) {
      const makeChildren = () => [
        { name: '环境与设备', path: '/mobile-automation/devices', icon: 'el-icon-mobile-phone', menuId: '__inject_mobile_devices__', id: '__inject_mobile_devices__', visible: 1, status: 1, children: [] },
        { name: '应用配置', path: '/mobile-automation/apps', icon: 'el-icon-box', menuId: '__inject_mobile_apps__', id: '__inject_mobile_apps__', visible: 1, status: 1, children: [] },
        { name: '发起移动执行', path: '/mobile-automation/run', icon: 'el-icon-video-play', menuId: '__inject_mobile_run__', id: '__inject_mobile_run__', visible: 1, status: 1, children: [] },
        { name: '移动执行记录', path: '/mobile-automation/executions', icon: 'el-icon-tickets', menuId: '__inject_mobile_executions__', id: '__inject_mobile_executions__', visible: 1, status: 1, children: [] },
        { name: '弱网配置', path: '/weak-network', icon: 'el-icon-connection', menuId: '__inject_weak_network__', id: '__inject_weak_network__', visible: 1, status: 1, children: [] },
        { name: '弱网AI任务', path: '/weak-network-ai', icon: 'el-icon-magic-stick', menuId: '__inject_weak_network_ai__', id: '__inject_weak_network_ai__', visible: 1, status: 1, children: [] }
      ]
      const isGroup = item => item && (String(item.path || '') === '/mobile-automation' || item.name === '移动自动化' || item.menuId === '__inject_mobile_automation__' || item.id === '__inject_mobile_automation__')
      const mergeChildren = children => {
        const next = (children || []).slice()
        makeChildren().forEach(child => {
          if (!next.some(item => String(item.path || '') === child.path || item.name === child.name || item.menuId === child.menuId || item.id === child.id)) next.push(child)
        })
        return next
      }
      let hasGroup = false
      const result = (menus || []).map(item => {
        if (!isGroup(item)) return item
        hasGroup = true
        return Object.assign({}, item, { name: '移动自动化', path: '/mobile-automation', icon: item.icon || 'el-icon-mobile-phone', children: mergeChildren(item.children) })
      })
      if (!hasGroup) result.push({ name: '移动自动化', path: '/mobile-automation', icon: 'el-icon-mobile-phone', menuId: '__inject_mobile_automation__', id: '__inject_mobile_automation__', visible: 1, status: 1, children: makeChildren() })
      return result
    },
    injectInspectionMenu(menus) {
      const makeChildren = () => [
        { name: '巡检概览', path: '/inspection/dashboard', icon: 'el-icon-data-analysis', menuId: '__inject_inspection_dashboard__', id: '__inject_inspection_dashboard__', visible: 1, status: 1, children: [] },
        { name: '定时任务', path: '/inspection/tasks', icon: 'el-icon-s-claim', menuId: '__inject_inspection_tasks__', id: '__inject_inspection_tasks__', visible: 1, status: 1, children: [] },
        { name: '数据库连接', path: '/inspection/db-configs', icon: 'el-icon-connection', menuId: '__inject_inspection_dbconfigs__', id: '__inject_inspection_dbconfigs__', visible: 1, status: 1, children: [] },
        { name: '执行记录', path: '/inspection/executions', icon: 'el-icon-tickets', menuId: '__inject_inspection_executions__', id: '__inject_inspection_executions__', visible: 1, status: 1, children: [] },
        { name: '巡检报告', path: '/inspection/reports', icon: 'el-icon-s-data', menuId: '__inject_inspection_reports__', id: '__inject_inspection_reports__', visible: 1, status: 1, children: [] }
      ]
      const isGroup = item => item && (String(item.path || '') === '/inspection' || item.name === '巡检管理' || item.menuId === '__inject_inspection__' || item.id === '__inject_inspection__')
      const normalizeChildren = children => {
        const desired = makeChildren()
        const next = []
        const used = new Set()
        desired.forEach(child => {
          const existing = (children || []).find(item =>
            String(item.path || '') === child.path ||
            item.name === child.name ||
            item.menuId === child.menuId ||
            item.id === child.id ||
            // 收敛旧「巡检组 / 巡检任务」入口
            (child.path === '/inspection/tasks' && (
              String(item.path || '') === '/inspection/groups' ||
              item.name === '巡检组' ||
              item.name === '巡检任务'
            ))
          )
          if (existing) {
            next.push(Object.assign({}, existing, {
              name: child.name,
              path: child.path,
              icon: existing.icon || child.icon
            }))
            used.add(existing)
          } else {
            next.push(child)
          }
        })
        ;(children || []).forEach(item => {
          if (used.has(item)) return
          const path = String(item.path || '')
          if (path === '/inspection/groups' || item.name === '巡检组') return
          next.push(item)
        })
        return next
      }
      let hasGroup = false
      const result = (menus || []).map(item => {
        if (!isGroup(item)) return item
        hasGroup = true
        return Object.assign({}, item, {
          name: '巡检管理',
          path: '/inspection',
          icon: item.icon || 'el-icon-monitor',
          children: normalizeChildren(item.children)
        })
      })
      if (!hasGroup) {
        result.push({
          name: '巡检管理',
          path: '/inspection',
          icon: 'el-icon-monitor',
          menuId: '__inject_inspection__',
          id: '__inject_inspection__',
          visible: 1,
          status: 1,
          children: makeChildren()
        })
      }
      return result
    },
    injectContractMenu(menus) {
      const makeChildren = () => [
        { name: '契约套件', path: '/contract/suites', icon: 'el-icon-document-checked', menuId: '__inject_contract_suites__', id: '__inject_contract_suites__', visible: 1, status: 1, children: [] },
        { name: '执行记录', path: '/contract/runs', icon: 'el-icon-tickets', menuId: '__inject_contract_runs__', id: '__inject_contract_runs__', visible: 1, status: 1, children: [] }
      ]
      const isGroup = item => item && (
        String(item.path || '') === '/contract' ||
        item.name === '契约守护' ||
        item.menuId === '__inject_contract__' ||
        item.id === '__inject_contract__'
      )
      let hasGroup = false
      const result = (menus || []).map(item => {
        if (!isGroup(item)) return item
        hasGroup = true
        return Object.assign({}, item, {
          name: '契约守护',
          path: '/contract',
          icon: item.icon || 'el-icon-document-checked',
          children: makeChildren()
        })
      })
      if (!hasGroup) {
        result.push({
          name: '契约守护',
          path: '/contract',
          icon: 'el-icon-document-checked',
          menuId: '__inject_contract__',
          id: '__inject_contract__',
          visible: 1,
          status: 1,
          children: makeChildren()
        })
      }
      return result
    },
    cloneMenuItem(item) {
      return Object.assign({}, item, {
        children: (item.children || []).map(child => this.cloneMenuItem(child))
      })
    },
    regroupProductProjectMenus(menus) {
      const buckets = {
        home: [],
        project: [],
        ai: [],
        support: [],
        config: [],
        system: [],
        other: []
      }
      const addUnique = (list, item) => {
        const key = String(item.path || item.code || item.menuId || item.id || item.name || '')
        if (!key) return
        if (!list.some(existing => String(existing.path || existing.code || existing.menuId || existing.id || existing.name || '') === key)) {
          list.push(item)
        }
      }
      const addByBucket = item => {
        const bucket = this.menuGroupBucket(item)
        if (bucket === 'container') {
          ;(item.children || []).forEach(child => addByBucket(child))
          return
        }
        addUnique(buckets[bucket] || buckets.other, item)
      }
      ;(menus || []).map(item => this.cloneMenuItem(item)).forEach(item => addByBucket(item))
      const groups = []
      buckets.home.forEach(item => addUnique(groups, item))
      this.pushMenuGroup(groups, '基础配置', 'base_config', 'el-icon-setting', buckets.config, 'config')
      this.pushMenuGroup(groups, '项目工作台', 'project_workspace', 'el-icon-s-operation', buckets.project, 'project')
      this.pushMenuGroup(groups, 'AI质量助手', 'ai_quality_assistant', 'el-icon-cpu', buckets.ai, 'ai')
      this.pushMenuGroup(groups, '测试支撑工具', 'test_support_tools', 'el-icon-s-tools', buckets.support, 'support')
      buckets.system.forEach(item => addUnique(groups, item))
      buckets.other.forEach(item => addUnique(groups, item))
      return groups
    },
    pushMenuGroup(groups, name, code, icon, children, groupKey) {
      const sortedChildren = this.sortMenuGroupChildren(children, groupKey)
      if (!sortedChildren.length) return
      groups.push({
        name,
        code,
        icon,
        menuId: `__group_${code}__`,
        id: `__group_${code}__`,
        visible: 1,
        status: 1,
        children: sortedChildren
      })
    },
    menuGroupBucket(menu) {
      const directPath = String((menu && menu.path) || '').trim()
      const path = this.representativeMenuPath(menu)
      const name = String((menu && menu.name) || '').trim()
      if (directPath === '/effekt' || path === '/effekt' || name === '首页') return 'home'
      if (path.indexOf('/system') === 0 || name === '系统管理') return 'system'
      if (/^(用例周期|测试平台|智能质量协同|项目工作台|AI质量助手|测试支撑工具|基础配置)$/.test(name)) return 'container'
      if (
        path.indexOf('/test-platform/product') === 0 ||
        path.indexOf('/test-platform/project') === 0 ||
        path.indexOf('/test-platform/skill-rules') === 0 ||
        /^(产品管理|项目管理|业务技能配置|配置技能与规则|测试 Skills|业务规则)$/.test(name)
      ) {
        return 'config'
      }
      if (
        path.indexOf('/test-platform/ai-platform') === 0 ||
        path.indexOf('/ai-review') === 0 ||
        path.indexOf('/ai-workload-estimate') === 0 ||
        path.indexOf('/test-asset-governance') === 0 ||
        path.indexOf('/precise') === 0 ||
        /^(AI测试中枢|AI测试评审|AI工作量预估|测试资产治理|精准测试)$/.test(name)
      ) {
        return 'ai'
      }
      if (
        path.indexOf('/data-tools') === 0 ||
        path.indexOf('/create') === 0 ||
        path.indexOf('/performance') === 0 ||
        path.indexOf('/mobile-automation') === 0 ||
        path.indexOf('/weak-network') === 0 ||
        path.indexOf('/mock') === 0 ||
        path.indexOf('/contract') === 0 ||
        /造数|造数工具|造数工厂|造数结果历史|数据库造数|性能测试|移动自动化|弱网配置|弱网AI任务|mock服务|Mock服务|契约守护|契约测试|探索Session|探索会话|聊天问题导入/.test(name)
      ) {
        return 'support'
      }
      if (
        path.indexOf('/inspection') === 0 ||
        /巡检管理|巡检概览|巡检组|巡检任务|巡检报告/.test(name)
      ) {
        return 'other'
      }
      if (
        path.indexOf('/test-platform/case') === 0 ||
        path.indexOf('/test-platform/plan') === 0 ||
        path.indexOf('/test-platform/report') === 0 ||
        path.indexOf('/bug') === 0 ||
        path.indexOf('/requirement-qa') === 0 ||
        /^(需求问答|用例管理|测试计划|测试报告|Bug管理|Bug 列表|Bug统计|Bug 统计)$/.test(name)
      ) {
        return 'project'
      }
      return 'other'
    },
    sortMenuGroupChildren(children, groupKey) {
      const weight = item => {
        const path = this.representativeMenuPath(item)
        const name = String((item && item.name) || '').trim()
        if (groupKey === 'project') {
          if (path.indexOf('/requirement-qa') === 0 || name === '需求问答') return 10
          if (path.indexOf('/test-platform/case') === 0 || name === '用例管理') return 20
          if (path.indexOf('/test-platform/plan') === 0 || name === '测试计划') return 30
          if (path.indexOf('/test-platform/report') === 0 || name === '测试报告') return 40
          if (path.indexOf('/bug') === 0 || name === 'Bug管理' || name.indexOf('Bug') === 0) return 50
        }
        if (groupKey === 'ai') {
          if (path.indexOf('/test-platform/ai-platform') === 0 || name === 'AI测试中枢') return 10
          if (path.indexOf('/ai-review') === 0 || name === 'AI测试评审') return 20
          if (path.indexOf('/ai-workload-estimate') === 0 || name === 'AI工作量预估') return 25
          if (path.indexOf('/test-asset-governance') === 0 || name === '测试资产治理') return 30
          if (path.indexOf('/precise') === 0 || name === '精准测试') return 40
        }
        if (groupKey === 'support') {
          if ((path.indexOf('/data-tools/factory') === 0 && path.indexOf('/task') < 0) || name === '造数工厂') return 10
          if (path.indexOf('/data-tools/factory/task') === 0 || name === '造数结果历史') return 20
          if (path.indexOf('/explore-session') === 0 || name === '探索Session') return 30
          if (path.indexOf('/chat-issue') === 0 || name === '聊天问题导入') return 35
          if (path.indexOf('/data-tools') === 0 || path.indexOf('/create') === 0 || /造数/.test(name)) return 15
          if (path.indexOf('/performance') === 0 || name === '性能测试') return 40
          if (path.indexOf('/mobile-automation') === 0 || name === '移动自动化') return 45
          if (path.indexOf('/mock') === 0 || name === 'mock服务' || name === 'Mock服务') return 50
        }
        if (groupKey === 'config') {
          if (path.indexOf('/test-platform/product') === 0 || name === '产品管理') return 10
          if (path.indexOf('/test-platform/project') === 0 || name === '项目管理') return 20
          if (path.indexOf('/test-platform/skill-rules') === 0 || /业务技能|配置技能|测试 Skills|业务规则/.test(name)) return 30
        }
        return 90
      }
      return (children || [])
        .map((item, index) => ({ item, index }))
        .sort((a, b) => {
          const wa = weight(a.item)
          const wb = weight(b.item)
          if (wa !== wb) return wa - wb
          return a.index - b.index
        })
        .map(entry => {
          const item = entry.item
          if (groupKey === 'support' && item && item.children && item.children.length) {
            const name = String(item.name || '').trim()
            const path = this.representativeMenuPath(item)
            if (/造数工具/.test(name) || path.indexOf('/data-tools') === 0) {
              return Object.assign({}, item, { children: this.sortDataToolChildren(item.children) })
            }
          }
          return item
        })
    },
    sortDataToolChildren(children) {
      const weight = item => {
        const path = this.representativeMenuPath(item)
        const name = String((item && item.name) || '').trim()
        if ((path.indexOf('/data-tools/factory') === 0 && path.indexOf('/task') < 0) || name === '造数工厂') return 10
        if (path.indexOf('/data-tools/factory/task') === 0 || name === '造数结果历史' || /造数结果/.test(name)) return 20
        if (path.indexOf('/explore-session') === 0 || name === '探索Session' || /探索会话/.test(name)) return 30
        if (path.indexOf('/chat-issue') === 0 || name === '聊天问题导入') return 40
        return 90
      }
      return (children || [])
        .map((item, index) => ({ item, index }))
        .sort((a, b) => {
          const wa = weight(a.item)
          const wb = weight(b.item)
          if (wa !== wb) return wa - wb
          return a.index - b.index
        })
        .map(entry => entry.item)
    },
    /** 左侧栏顶级顺序：首页 → 基础配置 → 项目工作台 → AI质量助手 → 测试支撑工具 → 系统管理 → 其它 */
    representativeMenuPath(menu) {
      const direct = String((menu && menu.path) || '').trim()
      if (direct) return direct
      const walk = m => {
        const q = String((m && m.path) || '').trim()
        if (q) return q
        const ch = (m && m.children) || []
        for (let i = 0; i < ch.length; i++) {
          const r = walk(ch[i])
          if (r) return r
        }
        return ''
      }
      return walk(menu)
    },
    menuSortWeight(menu) {
      const p = this.representativeMenuPath(menu)
      const n = String((menu && menu.name) || '').trim()
      if (p === '/effekt' || n === '首页') return 0
      if (n === '基础配置') return 10
      if (n === '项目工作台') return 20
      if (n === 'AI质量助手') return 30
      if (n === '测试支撑工具') return 40
      if (
        p.indexOf('/test-platform') === 0 ||
        p.indexOf('/ai-review') === 0 ||
        p.indexOf('/ai-workload-estimate') === 0 ||
        p.indexOf('/test-asset-governance') === 0 ||
        p.indexOf('/bug') === 0 ||
        p.indexOf('/requirement-qa') === 0 ||
        p.indexOf('/create') === 0 ||
        p.indexOf('/data-tools') === 0 ||
        p.indexOf('/performance') === 0 ||
        p.indexOf('/mobile-automation') === 0 ||
        p.indexOf('/mock') === 0 ||
        p.indexOf('/inspection') === 0 ||
        p.indexOf('/precise') === 0 ||
        n === '用例周期' ||
        n === '测试平台' ||
        n === 'AI测试评审' ||
        n === 'AI工作量预估' ||
        n === 'Bug管理' ||
        n.indexOf('Bug') === 0 ||
        /造数|造数工具|造数工厂|造数结果历史|数据库造数|需求问答|性能测试|移动自动化|弱网配置|弱网AI任务|mock服务|Mock服务|精准测试|测试资产治理|探索Session|聊天问题导入|AI工作量预估|巡检管理/.test(n)
      ) {
        return 50
      }
      if (p.indexOf('/system') === 0 || n === '系统管理') return 60
      return 70
    },
    sortMenusByProductOrder(menus) {
      const arr = menus || []
      return arr
        .map((m, i) => ({ m, i }))
        .sort((a, b) => {
          const wa = this.menuSortWeight(a.m)
          const wb = this.menuSortWeight(b.m)
          if (wa !== wb) return wa - wb
          return a.i - b.i
        })
        .map(x => x.m)
    },
    handleUserCommand(command) {
      if (command === 'logout') {
        localStorage.removeItem('authUser')
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userMenus')
        this.$store.commit('ClearCurrentUser')
        this.$message.success('已退出登录')
        this.$router.push({ name: 'login' })
      }
    }
  }
}
</script>

<style scoped>
.auto-test-main {
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  background: #070b16;
}

.app-shell {
  height: 100vh;
  min-width: 1100px;
  overflow: hidden;
  background: radial-gradient(circle at 18% 8%, rgba(37, 99, 235, 0.22), transparent 30%), #070b16;
}

.aside {
  display: flex;
  flex-direction: column;
  flex: 0 0 220px;
  width: 220px;
  min-width: 220px;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #07111f 0%, #081426 46%, #050914 100%);
  box-shadow: 12px 0 38px rgba(0, 0, 0, 0.42), inset -1px 0 0 rgba(56, 189, 248, 0.14);
  transition: width 0.25s ease, flex-basis 0.25s ease, min-width 0.25s ease;
}

.aside--collapse {
  flex-basis: 64px;
  width: 64px;
  min-width: 64px;
}

.aside-menu-scroll {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.aside-menu-scroll::-webkit-scrollbar {
  width: 6px;
}

.aside-menu-scroll::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: rgba(148, 163, 184, 0.35);
}

.aside-menu-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.aside--collapse .brand-panel {
  justify-content: center;
  padding: 18px 8px;
}

.brand-panel {
  flex-shrink: 0;
  width: 220px;
  min-width: 220px;
  height: 72px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  color: #e0f2fe;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.18) 0%, rgba(15, 23, 42, 0.96) 100%);
  border-bottom: 1px solid rgba(56, 189, 248, 0.18);
}

.aside--collapse .brand-panel {
  width: 64px;
  min-width: 64px;
}

.brand-mark {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  line-height: 34px;
  text-align: center;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 800;
  color: #06111f;
  background: linear-gradient(135deg, #67e8f9 0%, #38bdf8 45%, #6366f1 100%);
  box-shadow: 0 0 22px rgba(56, 189, 248, 0.48), 0 12px 30px rgba(99, 102, 241, 0.25);
}

.brand-copy {
  min-width: 0;
}

.brand-name {
  font-size: 16px;
  font-weight: 800;
  line-height: 20px;
  letter-spacing: 0.6px;
}

.brand-subtitle {
  margin-top: 2px;
  font-size: 11px;
  color: #67e8f9;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 220px;
  min-width: 220px;
}

.el-menu-vertical-demo.el-menu--collapse {
  width: 64px;
  min-width: 64px;
}

.el-menu-vertical-demo {
  border-right: none;
  flex-shrink: 0;
}

.el-menu-vertical-demo >>> .el-menu-item,
.el-menu-vertical-demo >>> .el-submenu__title {
  box-sizing: border-box;
  height: 48px;
  line-height: 48px;
  margin: 4px 10px;
  border-radius: 13px;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.el-menu-vertical-demo:not(.el-menu--collapse) >>> .el-menu-item,
.el-menu-vertical-demo:not(.el-menu--collapse) >>> .el-submenu__title {
  width: 200px;
}

.el-menu-vertical-demo >>> .el-menu-item.is-active {
  color: #e0f2fe !important;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.95) 0%, rgba(79, 70, 229, 0.95) 100%) !important;
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.28), inset 0 0 0 1px rgba(255, 255, 255, 0.15);
}

.el-menu-vertical-demo >>> .el-menu-item:hover,
.el-menu-vertical-demo >>> .el-submenu__title:hover {
  background: rgba(14, 165, 233, 0.12) !important;
  color: #e0f2fe !important;
}

.workspace-shell {
  min-width: 0;
  height: 100vh;
  overflow: hidden;
}

.header {
  height: 64px !important;
  line-height: normal;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px 0 18px !important;
  background: rgba(8, 14, 30, 0.88);
  border-bottom: 1px solid rgba(56, 189, 248, 0.18);
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(16px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 12px;
  color: #7dd3fc;
  background: rgba(14, 165, 233, 0.1);
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.header-icon:hover {
  background: rgba(14, 165, 233, 0.18);
  box-shadow: 0 0 18px rgba(56, 189, 248, 0.22);
  transform: translateY(-1px);
}

.system-name span {
  display: block;
  font-size: 17px;
  line-height: 22px;
  font-weight: 800;
  color: #e0f2fe;
}

.system-name small {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: #7dd3fc;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #c4d7f2;
  font-size: 14px;
}

.theme-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  color: #dbeafe;
  background: rgba(15, 23, 42, 0.86);
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.theme-switch:hover {
  background: rgba(14, 165, 233, 0.18);
  box-shadow: 0 0 18px rgba(56, 189, 248, 0.18);
  transform: translateY(-1px);
}

.user-name-dropdown {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.86);
  border: 1px solid rgba(56, 189, 248, 0.22);
  color: #dbeafe;
  cursor: pointer;
}

.login-label {
  color: #67e8f9;
  cursor: pointer;
}

.main-canvas {
  height: calc(100vh - 64px);
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
  background: radial-gradient(circle at 82% 14%, rgba(34, 211, 238, 0.14), transparent 24%), linear-gradient(135deg, #08111f 0%, #0b1020 45%, #070b16 100%);
}

.main-form {
  min-height: calc(100vh - 104px);
}

.theme-shell-light.auto-test-main {
  background: #eef4ff;
}

.theme-shell-light .app-shell {
  background: radial-gradient(circle at 18% 8%, rgba(59, 130, 246, 0.12), transparent 30%), linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
}

.theme-shell-light .aside {
  background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 48%, #eaf2ff 100%);
  box-shadow: 10px 0 30px rgba(37, 99, 235, 0.12), inset -1px 0 0 #dbe5f3;
}

.theme-shell-light .brand-panel {
  color: #0f172a;
  background: linear-gradient(135deg, #ffffff 0%, #eaf2ff 100%);
  border-bottom-color: #dbe5f3;
}

.theme-shell-light .brand-mark {
  color: #ffffff;
  background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.24);
}

.theme-shell-light .brand-subtitle {
  color: #2563eb;
}

.theme-shell-light .el-menu-vertical-demo {
  background: #f4f8ff !important;
}

.theme-shell-light .el-menu-vertical-demo >>> .el-menu,
.theme-shell-light .el-menu-vertical-demo >>> .el-menu--inline {
  background: #f4f8ff !important;
}

.theme-shell-light .el-menu-vertical-demo >>> .el-menu-item,
.theme-shell-light .el-menu-vertical-demo >>> .el-submenu__title {
  background: transparent !important;
  color: #64748b !important;
}

.theme-shell-light .el-menu-vertical-demo >>> .el-menu-item.is-active {
  color: #ffffff !important;
  background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%) !important;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
}

.theme-shell-light .el-menu-vertical-demo >>> .el-menu-item:hover,
.theme-shell-light .el-menu-vertical-demo >>> .el-submenu__title:hover {
  background: #eaf2ff !important;
  color: #1d4ed8 !important;
}

.theme-shell-light .header {
  background: rgba(255, 255, 255, 0.9);
  border-bottom-color: #dbe5f3;
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.08);
}

.theme-shell-light .header-icon,
.theme-shell-light .theme-switch,
.theme-shell-light .user-name-dropdown {
  color: #1d4ed8;
  background: #f8fbff;
  border-color: #dbe5f3;
}

.theme-shell-light .header-icon:hover,
.theme-shell-light .theme-switch:hover {
  background: #eaf2ff;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.12);
}

.theme-shell-light .system-name span {
  color: #0f172a;
}

.theme-shell-light .system-name small,
.theme-shell-light .login-label {
  color: #2563eb;
}

.theme-shell-light .header-user {
  color: #334155;
}

.theme-shell-light .main-canvas,
.theme-shell-light .main-form {
  background: linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
}

/* 深色壳下内容区兜底：避免旧缓存 bundle 未加载 App.vue 全局样式时出现白卡片/白分页 */
.theme-shell-dark >>> .page-section.el-card {
  background: #111827;
  border-color: rgba(148, 163, 184, 0.2);
  color: #e5e7eb;
}

.theme-shell-dark >>> .page-section .el-card__header {
  background: #162033;
  border-bottom-color: rgba(148, 163, 184, 0.18);
  color: #f8fafc;
}

.theme-shell-dark >>> .page-section .el-table,
.theme-shell-dark >>> .page-section .el-table__expanded-cell,
.theme-shell-dark >>> .page-section .el-table th,
.theme-shell-dark >>> .page-section .el-table tr,
.theme-shell-dark >>> .page-section .el-table td {
  background-color: #111827 !important;
  color: #e5e7eb !important;
}

.theme-shell-dark >>> .page-section .el-table th,
.theme-shell-dark >>> .page-section .el-table thead th {
  background: #1f2937 !important;
  color: #f8fafc !important;
}

.theme-shell-dark >>> .page-section .el-form-item__label {
  color: #dbeafe;
}

.theme-shell-dark >>> .page-section .el-input__inner,
.theme-shell-dark >>> .page-section .el-textarea__inner,
.theme-shell-dark >>> .page-section .el-select .el-input__inner {
  background-color: #0f172a;
  border-color: rgba(148, 163, 184, 0.28);
  color: #f8fafc;
}

.theme-shell-dark >>> .page-section .el-pagination,
.theme-shell-dark >>> .page-section .el-pagination button,
.theme-shell-dark >>> .page-section .el-pagination span:not([class*=suffix]) {
  color: #dbeafe;
}

.theme-shell-dark >>> .page-section .el-pagination .btn-prev,
.theme-shell-dark >>> .page-section .el-pagination .btn-next,
.theme-shell-dark >>> .page-section .el-pager li {
  background: #111827;
  color: #dbeafe;
  border: 1px solid rgba(148, 163, 184, 0.18);
}
</style>
