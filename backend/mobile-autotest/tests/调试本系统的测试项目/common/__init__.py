# encoding: UTF-8
"""
通用移动端自动化测试方法 - 供各项目的测试脚本 import 复用。
包含：设备初始化、解锁、清数据、权限授予、登录流程等。

用法：
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from tests.调试本系统的测试项目.common import init_device, clear_data_and_launch, login_joyhub
"""
import json
import os
import time

import pytest
import uiautomator2 as u2


# ── 从环境变量获取配置 ──
PACKAGE_NAME = os.environ.get('MOBILE_APP_PACKAGE', 'mini1.net.joyhub')
DEVICE_SERIAL = os.environ.get('MOBILE_DEVICE_SERIAL', '')
ARTIFACT_DIR = os.environ.get('MOBILE_ARTIFACT_DIR', '.')
RUNTIME_STEPS_FILE = os.environ.get(
    'MOBILE_RUNTIME_STEPS_FILE',
    os.environ.get('MOBILE_RUNTIME_RUNTIME_STEPS_FILE', '')
)

DEFAULT_EMAIL = os.environ.get('JOYHUB_TEST_EMAIL', os.environ.get('JOYHUB_TEST_USERNAME', '1222csz02@qq.com'))
DEFAULT_CODE = os.environ.get('JOYHUB_TEST_CODE', os.environ.get('JOYHUB_TEST_PASSWORD', '998877'))

# ── 常用控件 ID ──
EMAIL_ID = '{0}:id/etEmail'.format(PACKAGE_NAME)
CODE_ID = '{0}:id/etCode'.format(PACKAGE_NAME)
SEND_ID = '{0}:id/btnSend'.format(PACKAGE_NAME)
SUBMIT_ID = '{0}:id/btnRegisterOrLogin'.format(PACKAGE_NAME)
AGE_CHECK_ID = '{0}:id/cbAgreeOld'.format(PACKAGE_NAME)
POLICY_CHECK_ID = '{0}:id/cbAgreePrivate'.format(PACKAGE_NAME)
NEXT_ID = '{0}:id/ivNext'.format(PACKAGE_NAME)
START_ID = '{0}:id/stv_start'.format(PACKAGE_NAME)
HOME_TAB_ID = '{0}:id/btn_home'.format(PACKAGE_NAME)
ME_TAB_ID = '{0}:id/btn_me'.format(PACKAGE_NAME)
COMMUNITY_TAB_ID = '{0}:id/btn_community'.format(PACKAGE_NAME)
CHATS_TAB_ID = '{0}:id/btn_friends'.format(PACKAGE_NAME)


# ═══════════════════════════════════════════════
# 步骤上报（复用 mobile_steps 模块，如果可用）
# ═══════════════════════════════════════════════
def _try_import_mobile_steps():
    """尝试导入 mobile_steps 模块，失败则用空实现。"""
    try:
        from mobile_steps import finish_step as _finish, fail_step as _fail, reset_steps as _reset, bind_device as _bind
        return _finish, _fail, _reset, _bind
    except Exception:
        def _noop(*args, **kwargs):
            return None
        return _noop, _noop, _noop, _noop


_finish_step, _fail_step, _reset_steps, _bind_device = _try_import_mobile_steps()


def _report_step(step_no, instruction, action_type='ui', action_payload=None, status='success', error_message='', screenshot_rel=''):
    """上报单步执行结果到 JSONL 文件。"""
    if not RUNTIME_STEPS_FILE:
        return
    entry = {
        'step_no': step_no,
        'instruction': instruction,
        'action_type': action_type,
        'action_payload': action_payload or {},
        'status': status,
        'error_message': error_message,
        'screenshot_rel': screenshot_rel,
    }
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(RUNTIME_STEPS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _screenshot(driver, name):
    """截图并返回相对路径。"""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    filename = 'step_{}_{}.png'.format(name, int(time.time() * 1000))
    filepath = os.path.join(ARTIFACT_DIR, filename)
    try:
        driver.screenshot(filepath)
        return filename
    except Exception:
        return ''


# ═══════════════════════════════════════════════
# 设备初始化
# ═══════════════════════════════════════════════
def init_device():
    """初始化 uiautomator2 设备连接，亮屏并解锁。

    Returns:
        uiautomator2.Device: 已解锁的设备对象
    """
    if not DEVICE_SERIAL:
        pytest.fail('缺少 MOBILE_DEVICE_SERIAL，必须由移动执行平台注入设备序列号')

    device = u2.connect(DEVICE_SERIAL)
    _reset_steps()
    _bind_device(device)

    # 亮屏
    if not device.info.get('screenOn'):
        device.screen_on()
        time.sleep(0.5)

    # 解锁
    _ensure_unlocked(device)

    finish_step('设备初始化完成：{0}'.format(DEVICE_SERIAL), action_type='device_init')
    return device


def _ensure_unlocked(device, timeout=12):
    """亮屏并尝试上滑解锁。"""
    if not device.info.get('screenOn'):
        device.screen_on()
        time.sleep(0.5)
    if not _is_locked(device):
        return
    finish_step('检测到锁屏，尝试自动解锁', action_type='unlock')
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not device.info.get('screenOn'):
            device.screen_on()
            time.sleep(0.3)
        try:
            device.swipe_ext('up', scale=0.8)
        except Exception:
            width, height = device.window_size()
            device.swipe(width // 2, int(height * 0.82), width // 2, int(height * 0.25), 0.15)
        time.sleep(1.0)
        if not _is_locked(device):
            finish_step('设备已解锁', action_type='unlock')
            return
        if device(password=True).exists or device(textContains='PIN').exists or device(textContains='密码').exists:
            pytest.fail('设备处于锁屏状态且有 PIN/密码，请手动解锁或关闭锁屏密码')
    pytest.fail('设备解锁超时')


def _is_locked(device):
    return _keyguard_showing(device) or _lock_ui_visible(device)


def _keyguard_showing(device):
    try:
        output = device.shell('dumpsys window').output or ''
    except Exception:
        output = ''
    for line in output.splitlines():
        text = line.strip().replace(' ', '')
        if 'mDreamingLockscreen=true' in text:
            return True
        if 'isStatusBarKeyguard=true' in text:
            return True
        if 'mKeyguardShowing=true' in text:
            return True
    return False


def _lock_ui_visible(device):
    lock_texts = (
        '滑动来打开', '滑动解锁', '向上滑动解锁', 'Swipe to unlock', 'Swipe to open',
        '紧急呼叫', 'Emergency', 'Emergency call',
        '输入密码', '输入 PIN', 'Enter PIN', 'Enter password',
    )
    for text in lock_texts:
        if device(packageName='com.android.systemui', text=text).exists:
            return True
        if device(packageName='com.android.systemui', textContains=text).exists:
            return True
    return bool(device(packageName='com.android.systemui', textMatches='.*(滑动来打开|滑动解锁|输入.*密码|紧急呼叫|Swipe to unlock|Enter PIN).*').exists)


# ═══════════════════════════════════════════════
# 应用管理：清数据、启动、权限
# ═══════════════════════════════════════════════
def clear_data_and_launch(device, package_name=None, clear_data=True):
    """清除应用数据、预授权权限、启动应用。

    Args:
        device: uiautomator2 设备对象
        package_name: 应用包名，默认使用 MOBILE_APP_PACKAGE 环境变量
        clear_data: 是否清除数据，默认 True

    Returns:
        device: 同一设备对象，方便链式调用
    """
    pkg = package_name or PACKAGE_NAME

    # 确认应用已安装
    try:
        device.app_info(pkg)
    except Exception:
        pytest.fail('设备未安装应用：{0}，请先安装 debug 包'.format(pkg))

    if clear_data:
        finish_step('清除应用数据', action_type='app_clear')
        device.app_clear(pkg)
        time.sleep(0.5)
        _grant_runtime_permissions(device)

    finish_step('启动应用：{0}'.format(pkg), action_type='app_start', package=pkg)
    device.app_stop(pkg)
    device.app_start(pkg, use_monkey=True)
    if not device.app_wait(pkg, timeout=20):
        pytest.fail('应用未在 20 秒内启动：{0}'.format(pkg))
    time.sleep(1.5)
    return device


def _grant_runtime_permissions(device, package_name=None):
    """清数据后预授权常用权限，减少系统弹窗。"""
    pkg = package_name or PACKAGE_NAME
    permissions = (
        'android.permission.ACCESS_FINE_LOCATION',
        'android.permission.ACCESS_COARSE_LOCATION',
        'android.permission.POST_NOTIFICATIONS',
        'android.permission.CAMERA',
        'android.permission.RECORD_AUDIO',
        'android.permission.READ_EXTERNAL_STORAGE',
        'android.permission.READ_MEDIA_IMAGES',
        'android.permission.READ_MEDIA_VIDEO',
        'android.permission.READ_MEDIA_AUDIO',
        'android.permission.BLUETOOTH_CONNECT',
        'android.permission.BLUETOOTH_SCAN',
        'android.permission.READ_PHONE_STATE',
        'android.permission.BODY_SENSORS',
    )
    for permission in permissions:
        try:
            device.shell('pm grant {0} {1}'.format(pkg, permission))
        except Exception:
            pass


def dismiss_permission_dialogs(device, rounds=6):
    """处理登录后可能出现的系统权限弹窗。"""
    pkg = PACKAGE_NAME
    allow_texts = (
        '仅在使用该应用时允许', '使用应用时允许', '始终允许', '允许',
        'While using the app', 'Allow only while using the app', 'Allow', 'ALLOW',
        '确定', 'OK',
    )
    for _ in range(rounds):
        current = device.app_current().get('package', '')
        if current == pkg and _is_home(device):
            return
        clicked = False
        for text in allow_texts:
            btn = device(text=text)
            if btn.exists:
                btn.click()
                clicked = True
                time.sleep(0.8)
                break
        if not clicked:
            for rid in (
                'com.android.permissioncontroller:id/permission_allow_foreground_only_button',
                'com.android.permissioncontroller:id/permission_allow_button',
                'com.android.packageinstaller:id/permission_allow_button',
            ):
                btn = device(resourceId=rid)
                if btn.exists:
                    btn.click()
                    clicked = True
                    time.sleep(0.8)
                    break
        if not clicked:
            break


# ══════════════════════════════════════════════
# 引导页处理
# ═══════════════════════════════════════════════
def pass_onboarding(device, timeout=30):
    """处理首次安装的引导页（WelcomeActivity），点 Next / Start。"""
    deadline = time.time() + timeout
    advanced = False
    while time.time() < deadline:
        if _is_home(device) or device(resourceId=EMAIL_ID).exists:
            return
        if device(resourceId=SUBMIT_ID).exists or (
            device(text='Register/Login').exists and not device(resourceId=NEXT_ID).exists
        ):
            return
        start_btn = device(resourceId=START_ID)
        if not start_btn.exists:
            start_btn = device(text='start')
        if start_btn.exists:
            if not advanced:
                finish_step('处理首次引导页', action_type='onboarding')
                advanced = True
            start_btn.click()
            time.sleep(1.5)
            continue
        next_btn = device(resourceId=NEXT_ID)
        if next_btn.exists:
            if not advanced:
                finish_step('处理首次引导页', action_type='onboarding')
                advanced = True
            next_btn.click()
            time.sleep(1.2)
            continue
        time.sleep(0.4)


# ═══════════════════════════════════════════════
# 登录流程
# ═══════════════════════════════════════════════
def login_joyhub(device, email=None, code=None, send_code=False):
    """完整 Joyhub 登录流程：引导页 -> 登录页 -> 填表单 -> 校验首页。

    Args:
        device: uiautomator2 设备对象
        email: 登录邮箱，默认从环境变量读取
        code: 验证码，默认从环境变量读取
        send_code: 是否点击发送验证码按钮

    Returns:
        dict: {'activity': str, 'home': True, 'tabs': [...]}
    """
    mail = email or DEFAULT_EMAIL
    pwd = code or DEFAULT_CODE

    # 处理引导页
    pass_onboarding(device)

    # 如果已在首页，跳过登录
    if _is_home(device):
        finish_step('已在首页，跳过登录', action_type='assert')
        return {'activity': device.app_current().get('activity'), 'home': True, 'tabs': ['Home', 'Community', 'Chats', 'Me']}

    # 进入登录页
    if not device(resourceId=EMAIL_ID).exists:
        finish_step('点击 Register/Login 进入登录页', action_type='click')
        welcome_btn = device(resourceId=SUBMIT_ID, text='Register/Login')
        if not welcome_btn.exists:
            welcome_btn = device(text='Register/Login')
        _wait_exists(welcome_btn, message='未找到 Register/Login 按钮')
        welcome_btn.click()
        _wait_exists(device(resourceId=EMAIL_ID), message='点击后未进入邮箱登录页')

    finish_step('已进入邮箱验证码登录页', action_type='assert')

    # 填写登录表单
    finish_step('输入邮箱：{0}'.format(mail), action_type='input', field='email')
    email_input = _wait_exists(device(resourceId=EMAIL_ID), message='未找到邮箱输入框')
    email_input.click()
    email_input.clear_text()
    email_input.set_text(mail)

    if send_code:
        finish_step('点击 Send 发送验证码', action_type='click')
        send_btn = _wait_exists(device(resourceId=SEND_ID), message='未找到 Send 按钮')
        send_btn.click()
        time.sleep(1)

    finish_step('输入验证码', action_type='input', field='code')
    code_input = _wait_exists(device(resourceId=CODE_ID), message='未找到验证码输入框')
    code_input.click()
    code_input.clear_text()
    code_input.set_text(pwd)

    # 勾选协议
    finish_step('勾选年龄与隐私协议', action_type='checkbox')
    _hide_keyboard_and_reveal_agreements(device)
    _ensure_checked(device, AGE_CHECK_ID)
    _ensure_checked(device, POLICY_CHECK_ID)

    # 提交登录
    finish_step('点击 Register/Login 提交登录', action_type='click')
    submit = _wait_exists(device(resourceId=SUBMIT_ID), message='未找到提交按钮')
    deadline = time.time() + 5
    while time.time() < deadline:
        if submit.info.get('enabled', True):
            break
        time.sleep(0.3)
    submit.click()

    # 校验登录结果
    return _assert_logged_in_home(device)


def _assert_logged_in_home(device, timeout=30):
    """登录成功后校验首页 Tab。"""
    finish_step('等待进入首页并校验登录态', action_type='assert')
    pkg = PACKAGE_NAME
    deadline = time.time() + timeout
    while time.time() < deadline:
        dismiss_permission_dialogs(device)
        current = device.app_current()
        cur_pkg = current.get('package')
        if cur_pkg and cur_pkg != pkg and 'permission' not in cur_pkg:
            pytest.fail('登录后应用离开前台：{0}'.format(current))
        if cur_pkg == pkg and _is_home(device):
            assert device(resourceId=HOME_TAB_ID).exists or device(text='Home').exists, '首页缺少 Home Tab'
            assert device(resourceId=ME_TAB_ID).exists or device(text='Me').exists, '首页缺少 Me Tab'
            assert device(resourceId=COMMUNITY_TAB_ID).exists or device(text='Community').exists, '首页缺少 Community Tab'
            assert device(resourceId=CHATS_TAB_ID).exists or device(text='Chats').exists, '首页缺少 Chats Tab'
            finish_step('首页 Tab 校验通过', action_type='assert')
            if device(resourceId=ME_TAB_ID).exists:
                device(resourceId=ME_TAB_ID).click()
            else:
                device(text='Me').click()
            time.sleep(1.5)
            dismiss_permission_dialogs(device)
            finish_step('进入 Me 页确认登录信息', action_type='assert', activity=device.app_current().get('activity'))
            return {
                'activity': device.app_current().get('activity'),
                'home': True,
                'tabs': ['Home', 'Community', 'Chats', 'Me'],
            }
        time.sleep(0.8)
    pytest.fail('登录后未进入首页')


# ═══════════════════════════════════════════════
# 社区协议
# ═══════════════════════════════════════════════
def agree_community_guidelines(device, timeout=10):
    """如果弹出社区协议页面，点击 Agree 同意。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        agree_btn = device(resourceId='{0}:id/btn_agree'.format(PACKAGE_NAME))
        if agree_btn.exists:
            finish_step('同意社区协议', action_type='click')
            agree_btn.click()
            time.sleep(2)
            return True
        time.sleep(0.5)
    return False


# ═══════════════════════════════════════════════
# 工具方法
# ═══════════════════════════════════════════════
def _is_home(device):
    return device(resourceId=HOME_TAB_ID).exists or (
        device(text='Home').exists and device(text='Me').exists
    )


def _wait_exists(selector, timeout=15, message='等待控件超时'):
    """等待控件出现，超时则 pytest.fail。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if selector.exists:
            return selector
        time.sleep(0.4)
    pytest.fail(message)


def _hide_keyboard_and_reveal_agreements(device):
    """收起软键盘并滚到底部，让协议勾选框可见。"""
    try:
        device.hide_keyboard()
    except Exception:
        device.press('back')
    time.sleep(0.5)
    scroll = device(resourceId='{0}:id/scrollView'.format(PACKAGE_NAME))
    if scroll.exists:
        try:
            scroll.scroll.toEnd(max_swipes=5)
        except Exception:
            device.swipe_ext('up', scale=0.6)
    else:
        device.swipe_ext('up', scale=0.6)
    time.sleep(0.4)


def _ensure_checked(device, resource_id):
    """确保勾选框已勾选。"""
    checkbox = _wait_exists(device(resourceId=resource_id), message='未找到勾选框：{0}'.format(resource_id))
    if not checkbox.info.get('checked'):
        checkbox.click()
        time.sleep(0.3)
        if not checkbox.info.get('checked'):
            if resource_id == AGE_CHECK_ID:
                device(textContains='I am over 18').click()
            else:
                device(textContains='I have read and agreed').click()
            time.sleep(0.3)
    if not checkbox.info.get('checked'):
        pytest.fail('勾选失败：{0}'.format(resource_id))


# 别名，方便外部调用
finish_step = _finish_step
fail_step = _fail_step
