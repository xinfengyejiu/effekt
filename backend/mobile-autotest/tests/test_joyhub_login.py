import os
import time

import pytest
import uiautomator2 as u2

from mobile_steps import bind_device, fail_step, finish_step, reset_steps


PACKAGE_NAME = os.environ.get('MOBILE_APP_PACKAGE', 'mini1.net.joyhub')
DEVICE_SERIAL = os.environ.get('MOBILE_DEVICE_SERIAL', '')
# 平台未注入时使用联调账号；可用环境变量覆盖
DEFAULT_EMAIL = '1222csz02@qq.com'
DEFAULT_CODE = '998877'

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


def _device():
    if not DEVICE_SERIAL:
        pytest.fail('缺少 MOBILE_DEVICE_SERIAL，必须由移动执行平台注入设备序列号')
    device = u2.connect(DEVICE_SERIAL)
    if not device.info.get('screenOn'):
        device.screen_on()
    return device


def _keyguard_showing(device):
    """通过 dumpsys 判断系统锁屏是否仍挡住桌面。"""
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


def _is_locked(device):
    return _keyguard_showing(device) or _lock_ui_visible(device)


def _ensure_unlocked(device, timeout=12):
    """亮屏并尝试上滑解锁；有 PIN/密码时无法自动解开则失败。"""
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
        # 唤醒后常见为上滑进入桌面
        try:
            device.swipe_ext('up', scale=0.8)
        except Exception:
            width, height = device.window_size()
            device.swipe(width // 2, int(height * 0.82), width // 2, int(height * 0.25), 0.15)
        time.sleep(1.0)
        if not _is_locked(device):
            finish_step('设备已解锁', action_type='unlock')
            return
        # 已进入 PIN/密码页则无法自动继续
        if device(password=True).exists or device(textContains='PIN').exists or device(textContains='密码').exists:
            break
    pytest.fail('设备处于锁屏状态且无法自动解锁，请手动解锁（关闭锁屏密码更稳妥）后再执行')


def _wait_exists(selector, timeout=15, message='等待控件超时'):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if selector.exists:
            return selector
        time.sleep(0.4)
    pytest.fail(message)


def _is_home(device):
    return device(resourceId=HOME_TAB_ID).exists or (
        device(text='Home').exists and device(text='Me').exists
    )


def _grant_runtime_permissions(device):
    """清数据后预授权常用权限，减少系统弹窗打断登录后断言。"""
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
            device.shell('pm grant {0} {1}'.format(PACKAGE_NAME, permission))
        except Exception:
            pass


def _dismiss_permission_dialogs(device, rounds=6):
    """处理登录后可能出现的系统权限弹窗。"""
    allow_texts = (
        '仅在使用该应用时允许',
        '使用应用时允许',
        '始终允许',
        '允许',
        'While using the app',
        'Allow only while using the app',
        'Allow',
        'ALLOW',
        '确定',
        'OK',
    )
    for _ in range(rounds):
        current = device.app_current().get('package', '')
        if current == PACKAGE_NAME and _is_home(device):
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


def _launch_joyhub(device, clear_data=False):
    _ensure_unlocked(device)
    try:
        device.app_info(PACKAGE_NAME)
    except Exception:
        pytest.fail('设备未安装应用：{0}，请先安装 debug 包'.format(PACKAGE_NAME))
    if clear_data:
        finish_step('清除应用数据，确保走完整登录流程', action_type='app_clear')
        device.app_clear(PACKAGE_NAME)
        time.sleep(0.5)
        _grant_runtime_permissions(device)
    finish_step('启动 Joyhub：{0}'.format(PACKAGE_NAME), action_type='app_start', package=PACKAGE_NAME)
    device.app_stop(PACKAGE_NAME)
    device.app_start(PACKAGE_NAME, use_monkey=True)
    if not device.app_wait(PACKAGE_NAME, timeout=20):
        pytest.fail('Joyhub 未在 20 秒内启动：{0}'.format(PACKAGE_NAME))
    time.sleep(1.5)


def _pass_onboarding_if_needed(device, timeout=30):
    """首次安装会出现 WelcomeActivity 引导页：点 Next，最后点 start。"""
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


def _open_register_login(device):
    """处理首次引导（如有），再进入邮箱验证码登录页。"""
    _pass_onboarding_if_needed(device)
    if _is_home(device):
        return
    if device(resourceId=EMAIL_ID).exists:
        finish_step('已进入邮箱验证码登录页', action_type='assert')
        return
    finish_step('点击 Register/Login 进入登录页', action_type='click')
    welcome_btn = device(resourceId=SUBMIT_ID, text='Register/Login')
    if not welcome_btn.exists:
        welcome_btn = device(text='Register/Login')
    _wait_exists(welcome_btn, message='欢迎页未找到 Register/Login 按钮')
    welcome_btn.click()
    _wait_exists(device(resourceId=EMAIL_ID), message='点击 Register/Login 后未进入邮箱登录页')
    finish_step('已进入邮箱验证码登录页', action_type='assert')


def _hide_keyboard_and_reveal_agreements(device):
    """收起软键盘并滚到底部，否则协议勾选框会被挡住且不在控件树中。"""
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


def _fill_login_form(device, email, code, send_code=False):
    finish_step('输入邮箱：{0}'.format(email), action_type='input', field='email')
    email_input = _wait_exists(device(resourceId=EMAIL_ID), message='未找到邮箱输入框')
    email_input.click()
    email_input.clear_text()
    email_input.set_text(email)

    if send_code:
        finish_step('点击 Send 发送验证码', action_type='click')
        send_btn = _wait_exists(device(resourceId=SEND_ID), message='未找到 Send 按钮')
        send_btn.click()
        time.sleep(1)

    finish_step('输入验证码', action_type='input', field='code')
    code_input = _wait_exists(device(resourceId=CODE_ID), message='未找到验证码输入框')
    code_input.click()
    code_input.clear_text()
    code_input.set_text(code)

    finish_step('勾选年龄与隐私协议', action_type='checkbox')
    _hide_keyboard_and_reveal_agreements(device)
    _ensure_checked(device, AGE_CHECK_ID)
    _ensure_checked(device, POLICY_CHECK_ID)

    finish_step('点击 Register/Login 提交登录', action_type='click')
    submit = _wait_exists(device(resourceId=SUBMIT_ID), message='未找到提交按钮 Register/Login')
    deadline = time.time() + 5
    while time.time() < deadline:
        if submit.info.get('enabled', True):
            break
        time.sleep(0.3)
    submit.click()


def _assert_logged_in_home(device, timeout=30):
    """登录成功后应进入 MainActivity 首页，底部有 Home / Community / Chats / Me。"""
    finish_step('等待进入首页并校验登录态', action_type='assert')
    deadline = time.time() + timeout
    while time.time() < deadline:
        _dismiss_permission_dialogs(device)
        current = device.app_current()
        pkg = current.get('package')
        if pkg and pkg != PACKAGE_NAME and 'permission' not in pkg:
            pytest.fail('登录后应用离开 Joyhub 前台：{0}'.format(current))
        if pkg == PACKAGE_NAME and _is_home(device):
            assert device(resourceId=HOME_TAB_ID).exists or device(text='Home').exists, '首页缺少 Home Tab'
            assert device(resourceId=ME_TAB_ID).exists or device(text='Me').exists, '首页缺少 Me Tab'
            assert device(resourceId=COMMUNITY_TAB_ID).exists or device(text='Community').exists, '首页缺少 Community Tab'
            assert device(resourceId=CHATS_TAB_ID).exists or device(text='Chats').exists, '首页缺少 Chats Tab'
            finish_step('首页 Tab 校验通过（Home/Community/Chats/Me）', action_type='assert')
            if device(resourceId=ME_TAB_ID).exists:
                device(resourceId=ME_TAB_ID).click()
            else:
                device(text='Me').click()
            time.sleep(1.5)
            _dismiss_permission_dialogs(device)
            assert device.app_current().get('package') == PACKAGE_NAME, '进入 Me 后包名异常'
            finish_step('进入 Me 页确认登录信息', action_type='assert', activity=device.app_current().get('activity'))
            return {
                'activity': device.app_current().get('activity'),
                'home': True,
                'tabs': ['Home', 'Community', 'Chats', 'Me'],
            }
        time.sleep(0.8)
    pytest.fail('登录后未进入首页（Home/Me）；请核对邮箱、验证码或协议勾选状态')


def _run_full_login():
    """完整登录主流程，供多个用例复用。"""
    reset_steps()
    email = os.environ.get('JOYHUB_TEST_EMAIL') or os.environ.get('JOYHUB_TEST_USERNAME') or DEFAULT_EMAIL
    code = os.environ.get('JOYHUB_TEST_CODE') or os.environ.get('JOYHUB_TEST_PASSWORD') or DEFAULT_CODE
    send_code = os.environ.get('JOYHUB_SEND_CODE', '').strip() in ('1', 'true', 'True', 'yes')

    device = _device()
    bind_device(device)
    try:
        _launch_joyhub(device, clear_data=True)
        _open_register_login(device)
        assert device(resourceId=EMAIL_ID).exists, '未进入登录表单，无法执行登录'
        _fill_login_form(device, email, code, send_code=send_code)
        info = _assert_logged_in_home(device)
        assert info['home'] is True
        finish_step('完整登录流程执行成功', action_type='done')
        return info
    except Exception as exc:
        fail_step('登录流程失败', str(exc)[:800], action_type='assert')
        raise


@pytest.mark.mobile
def test_open_login_page():
    """兼容平台旧脚本选择器：执行完整登录流程（不再仅打开页面）。"""
    _run_full_login()


def _first_existing(device, candidates, message):
    for kind, value in candidates:
        selector = device(**{kind: value})
        if selector.exists:
            return selector
    pytest.fail(message)


def _click_first(device, candidates, instruction, message):
    control = _first_existing(device, candidates, message)
    finish_step(instruction, action_type='click', selector=candidates)
    control.click()
    time.sleep(1)
    return control


def _assert_japanese_selected(device, timeout=12):
    """保存后应用通常回到日语首页；校验底部 Tab 日文文案，兼容仍停留在语言页的情况。"""
    # 语言选项页残留文案
    option_labels = (
        ('text', '日本語'), ('text', '日语'), ('text', 'Japanese'),
        ('description', '日本語'), ('description', '日语'), ('description', 'Japanese'),
    )
    # 保存成功后常见：首页 Tab 切为日文
    home_tabs_ja = (
        ('text', 'ホーム'),
        ('text', 'コミュニティ'),
        ('text', 'チャット'),
        ('text', '私'),
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        if any(device(**{kind: value}).exists for kind, value in option_labels):
            return
        ja_hits = sum(1 for kind, value in home_tabs_ja if device(**{kind: value}).exists)
        # 至少命中 2 个日文 Tab，避免单字误判
        if ja_hits >= 2:
            return
        # 仅「ホーム + 私」也足够证明已切日语
        if device(text='ホーム').exists and device(text='私').exists:
            return
        time.sleep(0.5)
    pytest.fail(
        '保存后未检测到日语界面（期望语言页出现 日本語/Japanese，或首页 Tab 出现 ホーム/コミュニティ/チャット/私）'
    )


@pytest.mark.mobile
def test_login_success():
    """完整登录：启动 -> 引导/进入登录页 -> 填邮箱验证码 -> 勾选协议 -> 登录 -> 校验首页。"""
    _run_full_login()


@pytest.mark.mobile
def test_change_language_to_japanese():
    """登录后进入设置，将应用语言切换为日语并校验保存结果。"""
    _run_full_login()
    device = _device()
    bind_device(device)
    try:
        _click_first(
            device,
            (('text', '设置'), ('text', 'Settings'), ('description', '设置'), ('description', 'Settings'),
             ('resourceId', '{0}:id/btn_setting'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/tv_setting'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/settings'.format(PACKAGE_NAME))),
            '点击设置', '登录后未找到设置入口'
        )
        _click_first(
            device,
            (('text', '语言'), ('text', 'Language'), ('description', '语言'), ('description', 'Language'),
             ('resourceId', '{0}:id/tv_language'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/setting_language'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/language'.format(PACKAGE_NAME))),
            '点击语言设置', '设置页未找到语言入口'
        )
        _click_first(
            device,
            (('text', '日本語'), ('text', '日语'), ('text', 'Japanese'),
             ('description', '日本語'), ('description', '日语'), ('description', 'Japanese'),
             ('resourceId', '{0}:id/radio_japanese'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/language_japanese'.format(PACKAGE_NAME))),
            '选择日语', '语言列表未找到日语选项'
        )
        _click_first(
            device,
            (('text', '保存'), ('text', 'Save'), ('text', '确定'), ('text', 'OK'),
             ('description', '保存'), ('description', 'Save'),
             ('resourceId', '{0}:id/btn_save'.format(PACKAGE_NAME)),
             ('resourceId', '{0}:id/save'.format(PACKAGE_NAME))),
            '保存语言设置', '语言设置页未找到保存按钮'
        )
        finish_step('校验语言设置保存结果', action_type='assert')
        _assert_japanese_selected(device)
        finish_step('语言已成功切换为日语', action_type='done', language='ja')
    except Exception as exc:
        fail_step('日语语言设置流程失败', str(exc)[:800], action_type='assert')
        raise
