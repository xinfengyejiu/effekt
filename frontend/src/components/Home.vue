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
  </div>
</template>

<script>
export default {
  name: 'Home',
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
      const withMockMenu = this.injectMockServiceMenu(withAiMenu)
      const withRequirementQaMenu = this.injectRequirementQaMenu(withMockMenu)
      const sorted = this.sortMenusByProductOrder(withRequirementQaMenu)
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
        '/bug': '/bug/list',
        '/bug/list': '/bug/list',
        '/bug/detail': '/bug/detail',
        '/bug/create': '/bug/create',
        '/bug/edit': '/bug/edit',
        '/bug/stats': '/bug/stats',
        '/requirement-qa': '/requirement-qa',
        '/mock': '/mock/interface',
        '/mock/document': '/mock/document',
        '/mock/interface': '/mock/interface',
        '/mock/log': '/mock/log'
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
        '/test-platform/ai-platform': 'el-icon-cpu'
      }
      if (path && pathIconMap[path]) {
        return pathIconMap[path]
      }
      // 按照原来的静态菜单名称映射图标
      const nameIconMap = {
        '首页': 'el-icon-house',
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
        '测试计划': 'el-icon-date',
        '测试报告': 'el-icon-data-line',
        '测试工具': 'el-icon-s-tools',
        '造数工具': 'el-icon-magic-stick',
        '数据库造数': 'el-icon-coin',
        '造数工厂': 'el-icon-set-up',
        'mock服务': 'el-icon-connection',
        'Mock文档': 'el-icon-document-copy',
        'Mock接口': 'el-icon-link',
        'Mock调用日志': 'el-icon-tickets',
        '需求问答': 'el-icon-chat-dot-round',
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
    /** 左侧栏顶级顺序：首页 → 用例周期 → Bug管理 → 造数工具 → 需求问答 → mock服务 → 系统管理 → 其它 */
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
      if (p.indexOf('/test-platform') === 0 || n === '用例周期' || n === '测试平台') return 10
      if (p.indexOf('/bug') === 0 || n === 'Bug管理' || n.indexOf('Bug') === 0) return 20
      if (
        p.indexOf('/create') === 0 ||
        p.indexOf('/data-tools') === 0 ||
        /造数|造数工具|造数工厂|数据库造数/.test(n)
      ) {
        return 30
      }
      if (p.indexOf('/requirement-qa') === 0 || n === '需求问答') return 34
      if (p.indexOf('/mock') === 0 || n === 'mock服务' || n === 'Mock服务') return 35
      if (p.indexOf('/system') === 0 || n === '系统管理') return 40
      return 50
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
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #07111f 0%, #081426 46%, #050914 100%);
  box-shadow: 12px 0 38px rgba(0, 0, 0, 0.42), inset -1px 0 0 rgba(56, 189, 248, 0.14);
  transition: width 0.25s ease;
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

.brand-mark {
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
}

.el-menu-vertical-demo {
  border-right: none;
}

.el-menu-vertical-demo >>> .el-menu-item,
.el-menu-vertical-demo >>> .el-submenu__title {
  height: 48px;
  line-height: 48px;
  margin: 4px 10px;
  border-radius: 13px;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
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
