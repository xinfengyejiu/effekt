<template>
  <div id="backgroud" :class="themeClass">
    <button class="login-theme-switch" type="button" @click="toggleTheme">
      <i :class="themeIcon"></i>
      <span>{{ themeLabel }}</span>
    </button>
    <div class="login-hero">
      <div class="login-brand-mark">Q</div>
      <h1>QualiSync</h1>
      <p>统一管理测试协作、缺陷跟踪、用例周期与数据工具。</p>
    </div>
    <div class="content_right">
      <div class="login-body-title">
        <h2>欢迎登录</h2>
        <p>Quality Management Platform</p>
      </div>
      <div class="messge">
        <span>{{ msg }}</span>
      </div>
      <div class="cr_top">
        <div class="ct_input">
          <span class="ct-img-yhm">&nbsp;</span>
          <input
            id="username"
            v-model.trim="username"
            name="username"
            class="input_text"
            tabindex="1"
            accesskey="n"
            type="text"
            size="25"
            autocomplete="off"
            placeholder="用户名"
            @keyup.enter="handleLogin">
        </div>
        <div class="ct_input">
          <span class="ct_img_mm">&nbsp;</span>
          <input
            id="password"
            v-model="password"
            name="password"
            class="input_text"
            tabindex="2"
            accesskey="p"
            type="password"
            size="25"
            autocomplete="off"
            placeholder="密码"
            @keyup.enter="handleLogin">
        </div>
        <input class="btn_login" value="登录" @click="handleLogin">
      </div>
      <div class="account-oprate clearfix">
        <router-link :to="{ name: 'register' }" class="regist-btn">注册</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { Login } from '@/api/Userapi'
import { getRoleList, parseMenusFromRoleListResponse } from '@/api/rbacApi'

export default {
  name: 'Login',
  data() {
    return {
      msg: '',
      username: '',
      password: '',
      uiTheme: localStorage.getItem('uiTheme') || 'light'
    }
  },
  computed: {
    themeClass() {
      return this.uiTheme === 'light' ? 'theme-login-light' : 'theme-login-dark'
    },
    themeLabel() {
      return this.uiTheme === 'light' ? '深色' : '浅色'
    },
    themeIcon() {
      return this.uiTheme === 'light' ? 'el-icon-moon' : 'el-icon-sunny'
    }
  },
  mounted() {
    this.applyTheme()
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
    handleLogin() {
      if (!this.username || !this.password) {
        this.msg = 'username、password 为必传参数'
        return
      }
      Login({
        username: this.username,
        password: this.password
      }).then(res => {
        if (res && res.code === 20000) {
          const data = res.data || {}
          const user = {
            id: data.id,
            username: data.username,
            realName: data.real_name,
            mobile: data.mobile,
            email: data.email,
            avatar: data.avatar,
            status: data.status,
            lastLoginTime: data.last_login_time,
            createdBy: data.created_by,
            createdTime: data.created_time,
            updatedTime: data.updated_time,
            roleIds: data.role_ids || []
          }
          localStorage.setItem('authUser', JSON.stringify(user))
          if (data.token) {
            localStorage.setItem('accessToken', data.token)
          } else {
            localStorage.removeItem('accessToken')
          }
          const rt = data.refresh_token || data.refreshToken
          if (rt) {
            localStorage.setItem('refreshToken', rt)
          } else {
            localStorage.removeItem('refreshToken')
          }
          this.$store.commit('SetCurrentUser', user)
          this.$store.commit('SetRole', user.roleIds)
          this.$store.commit('SetUserMenus', [])
          this.loadUserMenus(user)
          this.msg = ''
          this.$message.success('登录成功')
          this.$router.push({ path: '/effekt' })
        } else {
          this.msg = (res && res.message) || '用户名或密码错误！'
        }
      })
    },
    loadUserMenus(user) {
      const roleId = user && user.roleIds && user.roleIds.length ? user.roleIds[0] : undefined
      if (!roleId) {
        return
      }
      getRoleList({ roleId }).then(res => {
        this.$store.commit('SetUserMenus', parseMenusFromRoleListResponse(res))
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
@import "../../assets/css/Form.css";

#backgroud {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 80px;
  background: linear-gradient(135deg, #eef2ff 0%, #fafbfc 40%, #fff7ed 100%);
  overflow: hidden;
}

.login-hero {
  width: 420px;
  color: #111827;
}

.login-brand-mark {
  width: 48px;
  height: 48px;
  line-height: 48px;
  text-align: center;
  border-radius: 50%;
  font-size: 24px;
  font-weight: 800;
  color: #ffffff;
  background: linear-gradient(135deg, #1e40af 0%, #f97316 100%);
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.25);
}

.login-hero h1 {
  margin: 24px 0 14px;
  font-size: 40px;
  line-height: 1.15;
  letter-spacing: 0.5px;
  font-weight: 700;
  color: #111827;
}

.login-hero p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
  line-height: 1.8;
}

.login-theme-switch {
  position: fixed;
  right: 28px;
  top: 24px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  background: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s ease, color 0.2s ease;
}

.login-theme-switch:hover {
  background: #fff7ed;
  color: #f97316;
  border-color: #f97316;
}

.content_right {
  padding: 34px 36px 30px;
  background: #ffffff;
  color: #111827;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
  position: static;
  width: 340px;
  min-height: 340px;
  text-align: center;
}

.login-body-title h2 {
  font-size: 24px;
  color: #111827;
  margin-bottom: 6px;
  font-weight: 700;
}

.login-body-title p {
  color: #f97316;
  font-size: 12px;
  letter-spacing: 0.8px;
  font-weight: 600;
  text-transform: uppercase;
}

.cr_top .ct_input {
  position: relative;
  height: 44px;
  width: 100%;
  margin-bottom: 14px;
}

.account-oprate .regist-btn {
  float: right;
  font-size: 14px;
  color: #1e40af;
  text-decoration: none;
  font-weight: 600;
}

.account-oprate .regist-btn:hover {
  color: #f97316;
}

.messge {
  font-size: 12px;
  margin-top: 14px;
  height: 22px;
  text-align: left;
  color: #dc2626;
}

.content_right .cr_top {
  position: relative;
  margin: 0;
}

.content_right .input_text {
  background: #ffffff;
}

.account-oprate {
  width: 100%;
}

.ct_img_mm,
.ct-img-yhm {
  position: absolute;
  top: 14px;
  left: 14px;
  width: 16px;
  height: 16px;
  opacity: 0.6;
}

.ct_img_mm::before {
  content: '\e6b4';
  font-family: 'element-icons';
  font-size: 16px;
  color: #9ca3af;
}

.ct-img-yhm::before {
  content: '\e6e3';
  font-family: 'element-icons';
  font-size: 16px;
  color: #9ca3af;
}

.ct-img-yhm {
  background-position: -16px 0;
}

.input_text {
  display: inline-block;
  box-sizing: border-box;
  width: 100%;
  height: 44px;
  padding: 0 14px 0 42px;
  font-size: 14px;
  color: #111827;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  vertical-align: middle;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.input_text::placeholder {
  color: #9ca3af;
}

.input_text:hover {
  border-color: #9ca3af;
  background: #ffffff;
}

.input_text:focus {
  border-color: #1e40af;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.08);
  outline: 0;
}

.btn_login {
  text-align: center;
  box-sizing: border-box;
  width: 100%;
  height: 44px;
  font-size: 16px;
  cursor: pointer;
  border-radius: 6px;
  color: #ffffff;
  border: none;
  background: #f97316;
  margin-bottom: 16px;
  -webkit-appearance: none;
  transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  font-weight: 700;
}

.btn_login:hover {
  background: #ea580c;
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(249, 115, 22, 0.3);
}

button,
input,
optgroup,
option,
select,
textarea {
  font-family: inherit;
  font-size: inherit;
  font-style: inherit;
  font-weight: inherit;
  resize: none;
}

blockquote,
body,
button,
code,
dd,
div,
dl,
dt,
fieldset,
form,
h1,
h2,
h3,
h4,
h5,
h6,
input,
legend,
li,
ol,
p,
pre,
td,
textarea,
th,
ul {
  margin: 0;
  padding: 0;
  font-family: '\5FAE\8F6F\96C5\9ED1', '\5B8B\4F53', Arial, Helvetica, sans-serif;
}

/* Dark theme for login */
.theme-login-dark#backgroud {
  background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
}

.theme-login-dark .login-theme-switch {
  color: #d1d5db;
  background: rgba(31, 41, 55, 0.9);
  border-color: #374151;
}

.theme-login-dark .login-theme-switch:hover {
  background: #374151;
  color: #fb923c;
  border-color: #fb923c;
}

.theme-login-dark .login-hero {
  color: #f9fafb;
}

.theme-login-dark .login-brand-mark {
  background: linear-gradient(135deg, #3b82f6 0%, #fb923c 100%);
  box-shadow: 0 6px 20px rgba(251, 146, 60, 0.3);
}

.theme-login-dark .login-hero h1 {
  color: #f9fafb;
}

.theme-login-dark .login-hero p {
  color: #9ca3af;
}

.theme-login-dark .content_right {
  background: #1f2937;
  color: #f9fafb;
  border-color: #374151;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.theme-login-dark .login-body-title h2 {
  color: #f9fafb;
}

.theme-login-dark .login-body-title p,
.theme-login-dark .account-oprate .regist-btn {
  color: #fb923c;
}

.theme-login-dark .content_right .input_text {
  background: #111827;
}

.theme-login-dark .input_text {
  color: #f9fafb;
  border-color: #374151;
}

.theme-login-dark .input_text::placeholder {
  color: #6b7280;
}

.theme-login-dark .input_text:hover {
  border-color: #6b7280;
  background: #111827;
}

.theme-login-dark .input_text:focus {
  border-color: #3b82f6;
  background: #111827;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.theme-login-dark .ct_img_mm::before,
.theme-login-dark .ct-img-yhm::before {
  color: #6b7280;
}

.theme-login-dark .btn_login {
  background: #fb923c;
}

.theme-login-dark .btn_login:hover {
  background: #f97316;
  box-shadow: 0 6px 18px rgba(251, 146, 60, 0.3);
}

.theme-login-dark .messge {
  color: #f87171;
}
</style>
