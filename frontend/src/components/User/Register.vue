<template>
  <div id="backgroud" :class="themeClass">
    <button class="register-theme-switch" type="button" @click="toggleTheme">
      <i :class="themeIcon"></i>
      <span>{{ themeLabel }}</span>
    </button>
    <div class="register-hero">
      <div class="register-brand-mark">Q</div>
      <h1>QualiSync</h1>
      <p>创建账号后即可进入统一测试协作、用例管理与质量工作台。</p>
      <div class="register-feature-list">
        <span>测试协作</span>
        <span>用例管理</span>
        <span>质量工作台</span>
      </div>
    </div>
    <div class="model">
      <div class="location-title">
        <span class="register-card-kicker">Create Account</span>
        <h1>创建账号</h1>
        <p>注册后开启你的质量效能工作区</p>
      </div>

      <el-form ref="ruleForm" :model="ruleForm" status-icon :rules="rules" label-position="top" class="demo-ruleForm">
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="ruleForm.username" type="text" placeholder="用户名" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="ruleForm.password" type="password" placeholder="密码" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="checkPass">
          <el-input v-model="ruleForm.checkPass" type="password" placeholder="确认密码" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="手机号" prop="mobile">
          <el-input v-model.trim="ruleForm.mobile" placeholder="手机号" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="ruleForm.email" type="text" placeholder="邮箱" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item class="register-actions">
          <el-button class="enter-btn" type="primary" :disabled="!select" @click="submitForm('ruleForm')">
            立即注册
          </el-button>
          <el-button class="login-link-btn" type="text" @click="goLogin">去登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { Register } from '@/api/Userapi'

export default {
  name: 'Register',
  data() {
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'))
        return
      }
      if (this.ruleForm.password !== '') {
        this.$refs.ruleForm.validateField('checkPass')
      }
      callback()
    }
    const validatePass2 = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== this.ruleForm.password) {
        callback(new Error('两次输入密码不一致!'))
      } else {
        callback()
      }
    }
    const validateUsername = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入用户名'))
        return
      }
      callback()
    }

    return {
      select: true,
      ruleForm: {
        username: '',
        password: '',
        checkPass: '',
        mobile: '',
        email: ''
      },
      rules: {
        username: [{ required: true, validator: validateUsername, trigger: 'blur' }],
        password: [{ required: true, validator: validatePass, trigger: 'blur' }],
        checkPass: [{ required: true, validator: validatePass2, trigger: 'blur' }]
      },
      uiTheme: localStorage.getItem('uiTheme') || 'light'
    }
  },
  computed: {
    themeClass() {
      return this.uiTheme === 'light' ? 'theme-register-light' : 'theme-register-dark'
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
    open(message) {
      this.$alert(message, '提示', {
        confirmButtonText: '确定'
      })
    },
    handleRegister() {
      Register({
        username: this.ruleForm.username,
        password: this.ruleForm.password,
        mobile: this.ruleForm.mobile,
        email: this.ruleForm.email,
        createdBy: 1
      }).then(data => {
        if (data && data.id) {
          this.open('注册成功')
          this.$router.push({ name: 'login' })
        } else {
          this.open(data.message || '注册失败')
        }
      })
    },
    submitForm(formName) {
      this.$refs[formName].validate(valid => {
        if (valid) {
          this.handleRegister()
        }
      })
    },
    goLogin() {
      this.$router.push({ name: 'login' })
    }
  }
}
</script>

<style scoped>
#backgroud {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 72px;
  width: 100vw;
  min-height: 100vh;
  padding: 72px 48px;
  overflow: auto;
  box-sizing: border-box;
}

#backgroud.theme-register-light {
  background: linear-gradient(135deg, #eef2ff 0%, #fafbfc 40%, #fff7ed 100%);
}

#backgroud.theme-register-dark {
  background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
}

.register-hero {
  flex: 0 0 420px;
  max-width: 420px;
  color: #111827;
}

.theme-register-dark .register-hero {
  color: #f9fafb;
}

.register-brand-mark {
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

.theme-register-dark .register-brand-mark {
  background: linear-gradient(135deg, #3b82f6 0%, #fb923c 100%);
  box-shadow: 0 6px 20px rgba(251, 146, 60, 0.3);
}

.register-hero h1 {
  margin: 24px 0 14px;
  font-size: 40px;
  line-height: 1.15;
  letter-spacing: 0.5px;
  font-weight: 700;
  color: #111827;
}

.theme-register-dark .register-hero h1 {
  color: #f9fafb;
}

.register-hero p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
  line-height: 1.8;
}

.theme-register-dark .register-hero p {
  color: #9ca3af;
}

.register-feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.register-feature-list span {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 14px;
  border-radius: 6px;
  color: #1e40af;
  background: rgba(30, 64, 175, 0.06);
  border: 1px solid rgba(30, 64, 175, 0.15);
  font-size: 13px;
  font-weight: 600;
}

.theme-register-dark .register-feature-list span {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.register-theme-switch {
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

.register-theme-switch:hover {
  background: #fff7ed;
  color: #f97316;
  border-color: #f97316;
}

.theme-register-dark .register-theme-switch {
  color: #d1d5db;
  background: rgba(31, 41, 55, 0.9);
  border-color: #374151;
}

.theme-register-dark .register-theme-switch:hover {
  background: #374151;
  color: #fb923c;
  border-color: #fb923c;
}

.model {
  position: relative;
  flex: 0 0 420px;
  width: 420px;
  min-height: auto;
  height: auto;
  margin: 0;
  padding: 34px 36px 30px;
  border-radius: 8px;
  text-align: left;
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.theme-register-dark .model {
  background: #1f2937;
  color: #f9fafb;
  border-color: #374151;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.location-title {
  text-align: center;
  margin-bottom: 22px;
}

.register-card-kicker {
  display: inline-flex;
  margin-bottom: 10px;
  color: #f97316;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.6px;
  text-transform: uppercase;
}

.location-title h1 {
  margin: 0 0 8px;
  font-size: 26px;
  color: #111827;
  font-weight: 700;
}

.theme-register-dark .location-title h1 {
  color: #f9fafb;
}

.location-title p {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
  letter-spacing: 0.4px;
}

.theme-register-dark .location-title p {
  color: #9ca3af;
}

.register-head {
  position: absolute;
}

.demo-ruleForm {
  width: 100%;
}

.demo-ruleForm >>> .el-form-item {
  margin-bottom: 15px;
}

.el-input {
  float: none;
  width: 100%;
}

.model >>> .el-form-item__label {
  padding: 0 0 7px;
  color: #374151;
  line-height: 1.2;
  font-size: 13px;
  font-weight: 600;
}

.theme-register-dark .model >>> .el-form-item__label {
  color: #d1d5db;
}

.model >>> .el-input__inner {
  height: 40px;
  background: #ffffff;
  border-color: #d1d5db;
  color: #111827;
  border-radius: 6px;
}

.theme-register-dark .model >>> .el-input__inner {
  background: #111827;
  border-color: #374151;
  color: #f9fafb;
}

.model >>> .el-input__inner:hover {
  border-color: #9ca3af;
}

.model >>> .el-input__inner:focus {
  border-color: #1e40af;
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.08);
}

.theme-register-dark .model >>> .el-input__inner:hover {
  border-color: #6b7280;
}

.theme-register-dark .model >>> .el-input__inner:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.register-actions {
  margin-top: 4px;
  margin-bottom: 0 !important;
}

.register-actions >>> .el-form-item__content {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  margin-left: 0 !important;
}

.enter-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 6px;
  color: #ffffff;
  font-weight: 700;
  background: #f97316;
  box-shadow: 0 4px 14px rgba(249, 115, 22, 0.2);
  transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.enter-btn:hover {
  background: #ea580c;
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(249, 115, 22, 0.3);
}

.theme-register-dark .enter-btn {
  background: #fb923c;
}

.theme-register-dark .enter-btn:hover {
  background: #f97316;
}

.login-link-btn {
  align-self: flex-end;
  padding-right: 0;
  margin-top: 10px;
  color: #1e40af;
}

.theme-register-dark .login-link-btn {
  color: #3b82f6;
}

@media (max-width: 1080px) {
  #backgroud {
    gap: 40px;
    padding: 72px 28px 36px;
  }

  .register-hero {
    flex-basis: 360px;
    max-width: 360px;
  }
}

@media (max-width: 920px) {
  #backgroud {
    flex-direction: column;
    gap: 28px;
    padding: 80px 18px 28px;
  }

  .register-hero,
  .model {
    flex: none;
    width: 100%;
    max-width: 430px;
  }

  .register-hero {
    text-align: center;
  }

  .register-brand-mark,
  .register-feature-list {
    margin-left: auto;
    margin-right: auto;
    justify-content: center;
  }
}
</style>
