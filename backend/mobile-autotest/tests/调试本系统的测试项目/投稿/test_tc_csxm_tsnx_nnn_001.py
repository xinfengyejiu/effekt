# -*- coding: utf-8 -*-
"""Joyhub 投稿完整流程测试。

流程：登录 → My Posts → Post → 上传图片 → 填标题/内容 → 添加标签 → 选 Channel → 提交 → 在 Under review 查看结果。
"""
import sys
import os
import time
import pytest

# ── 将 mobile-autotest 根目录加入路径 ──
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tests.调试本系统的测试项目.common import (
    init_device,
    clear_data_and_launch,
    login_joyhub,
    dismiss_permission_dialogs,
    agree_community_guidelines,
    finish_step,
    PACKAGE_NAME,
)

# ── 常用控件 ID ──
POSTER_ENTRY_ID = '{0}:id/cl_poster'.format(PACKAGE_NAME)
POST_BTN_ID = '{0}:id/button'.format(PACKAGE_NAME)
IV_PIC_ID = '{0}:id/iv_pic'.format(PACKAGE_NAME)
BTN_CHECK_ID = '{0}:id/btnCheck'.format(PACKAGE_NAME)
COMPLETE_SELECT_ID = '{0}:id/ps_complete_select'.format(PACKAGE_NAME)
ET_TITLE_ID = '{0}:id/et_title'.format(PACKAGE_NAME)
ET_CONTENT_ID = '{0}:id/et_content'.format(PACKAGE_NAME)
BTN_ADD_TAG_ID = '{0}:id/btn_add_tag'.format(PACKAGE_NAME)
TV_TOY_ID = '{0}:id/tv_toy'.format(PACKAGE_NAME)
TV_COMMUNITY_CHANNEL_ID = '{0}:id/tv_communityChannel'.format(PACKAGE_NAME)
TV_TITLE_POST_ID = '{0}:id/tv_title'.format(PACKAGE_NAME)


@pytest.fixture(scope='module')
def device():
    """初始化设备、清数据、启动、登录。"""
    dev = init_device()
    clear_data_and_launch(dev)
    login_joyhub(dev)
    yield dev


def _safe_click(selector, step_name, timeout=10):
    """等待控件出现并点击，超时则 fail。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if selector.exists:
            selector.click()
            return
        time.sleep(0.4)
    pytest.fail('{0}: 等待控件超时'.format(step_name))


def _wait_exists(selector, step_name, timeout=10):
    """等待控件出现，超时则 fail。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if selector.exists:
            return selector
        time.sleep(0.4)
    pytest.fail('{0}: 等待控件超时'.format(step_name))


# ═══════════════════════════════════════════════
# 测试主流程
# ═══════════════════════════════════════════════
def test_tc_csxm_tsnx_nnn_001(device):
    """Joyhub 投稿完整流程测试。"""
    d = device

    # ─ 步骤 1：进入 My Posts ──
    dismiss_permission_dialogs(d)

    # login_joyhub 已自动进入 Me 页，直接点击 My Posts 入口
    # 优先使用 cl_poster 资源 ID（更稳定），回退到 My Posts 文字
    poster = d(resourceId=POSTER_ENTRY_ID)
    if poster.exists:
        poster.click()
    else:
        my_posts = d(text='My Posts')
        if my_posts.exists:
            my_posts.click()
        else:
            pytest.fail('未找到 My Posts 入口')
    time.sleep(2)

    # 处理可能弹出的社区协议
    agree_community_guidelines(d)

    # 等待进入 My Posts 页面
    _wait_exists(d(text='Displaying'), 'My Posts 页面 - Displaying Tab', timeout=10)
    finish_step('进入 My Posts', action_type='ui')

    # ── 步骤 2：点击 Post 进入发帖编辑页 ──
    # 关闭可能弹出的每日限额弹窗（仅 btnCancel，不用 btn_back 以免退出页面）
    cancel_btn = d(resourceId='{0}:id/btnCancel'.format(PACKAGE_NAME))
    if cancel_btn.exists:
        cancel_btn.click()
        time.sleep(1)

    # 确认仍在 My Posts 页面，如果不在则返回
    displaying = d(text='Displaying')
    if not displaying.exists:
        # 可能被弹窗带到了其他页面，尝试按返回
        d.press('back')
        time.sleep(1)
        _wait_exists(d(text='Displaying'), 'My Posts 页面 - Displaying Tab', timeout=5)

    # 滚动查找 Post 按钮（Post 按钮在 "No posts yet" 区域下方）
    post_btn = d(resourceId=POST_BTN_ID, text='Post')
    if not post_btn.exists:
        for _ in range(8):
            d.swipe_ext('up', scale=0.7)
            time.sleep(1)
            if post_btn.exists:
                break
    _safe_click(post_btn, 'Post 按钮', timeout=10)
    time.sleep(3)

    # 处理可能的草稿确认弹窗
    confirm = d(resourceId='{0}:id/btnSure'.format(PACKAGE_NAME))
    if confirm.exists:
        confirm.click()
        time.sleep(1)

    _wait_exists(d(resourceId=ET_TITLE_ID), '发帖编辑页 - 标题输入框', timeout=10)
    finish_step('点击 Post 进入编辑页', action_type='ui')

    # ── 步骤 3：上传图片 ──
    _safe_click(d(resourceId=IV_PIC_ID), '图片上传按钮', timeout=8)
    time.sleep(2)

    # 在图片选择器中选中第一张照片
    btn_check = d(resourceId=BTN_CHECK_ID)
    _wait_exists(btn_check, '图片选择器 - 选中按钮', timeout=8)
    btn_check[0].click()
    time.sleep(1)

    # 点击完成
    _safe_click(d(resourceId=COMPLETE_SELECT_ID), '图片选择 - 完成按钮', timeout=5)
    time.sleep(2)

    # 验证回到编辑页
    _wait_exists(d(resourceId=ET_TITLE_ID), '选择图片后回到编辑页', timeout=10)
    finish_step('上传图片', action_type='ui')

    # ── 步骤 4：输入标题 ──
    title_input = d(resourceId=ET_TITLE_ID)
    title_input.click()
    time.sleep(0.3)
    title_input.set_text('Test Post')
    time.sleep(0.5)
    finish_step('输入标题 Test Post', action_type='ui')

    # ── 步骤 5：输入内容 ──
    content_input = d(resourceId=ET_CONTENT_ID)
    content_input.click()
    time.sleep(0.3)
    content_input.set_text('This is a test post for automation.')
    time.sleep(0.5)
    finish_step('输入内容', action_type='ui')

    # ── 步骤 6：添加标签 ─
    # 点击 Add tag 会在内容末尾追加 #
    _safe_click(d(resourceId=BTN_ADD_TAG_ID), 'Add tag 按钮', timeout=8)
    time.sleep(1)

    # 在 # 后面输入标签名
    d.send_keys('AutoTest')
    time.sleep(1)

    # 收起键盘
    try:
        d.hide_keyboard()
    except Exception:
        pass
    time.sleep(0.5)
    finish_step('添加标签 AutoTest', action_type='ui')

    # ── 步骤 7：选择 Channel ──
    toy_channel = d(resourceId=TV_TOY_ID)
    _safe_click(toy_channel, 'Toy Channel', timeout=8)
    time.sleep(1)
    finish_step('选择 Channel: Toy', action_type='ui')

    # ── 步骤 8：提交帖子 ──
    publish_btn = d(resourceId='{0}:id/btn_publish'.format(PACKAGE_NAME))
    _safe_click(publish_btn, '发布按钮', timeout=8)
    time.sleep(5)

    # 验证提交后返回 My Posts 页面
    _wait_exists(d(text='Displaying'), '提交后返回 My Posts 页面', timeout=15)
    finish_step('提交帖子', action_type='ui')

    # ── 步骤 9：在 Under review 中查看结果 ──
    # 点击 Under review tab
    under_review = d(text='Under review')
    _safe_click(under_review, 'Under review Tab', timeout=8)
    time.sleep(2)

    # 验证能看到刚提交的帖子标题
    post_title = d(resourceId=TV_TITLE_POST_ID, text='Test Post')
    _wait_exists(post_title, 'Under review 中看到 Test Post', timeout=10)
    finish_step('在 Under review 中确认帖子 Test Post', action_type='ui')
