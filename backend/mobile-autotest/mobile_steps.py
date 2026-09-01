# encoding: UTF-8
"""移动自动化运行时步骤上报：写入 MOBILE_ARTIFACT_DIR 下 jsonl，供平台同步到执行过程。"""
import json
import os
import threading
import time
from pathlib import Path

_lock = threading.Lock()
_step_no = 0
_device = None


def _steps_file_path():
    artifact_dir = os.environ.get('MOBILE_ARTIFACT_DIR')
    if not artifact_dir:
        return None
    relative = (os.environ.get('MOBILE_RUNTIME_STEPS_FILE') or 'runtime_steps.jsonl').strip().replace('\\', '/')
    if not relative or '..' in relative or relative.startswith('/'):
        relative = 'runtime_steps.jsonl'
    return Path(artifact_dir) / relative


def reset_steps():
    global _step_no, _device
    with _lock:
        _step_no = 0
        _device = None
        path = _steps_file_path()
        if path and path.exists():
            path.unlink()


def bind_device(device):
    """绑定 uiautomator2 设备，供步骤截图使用。"""
    global _device
    _device = device


def _capture_step_screenshot(step_no):
    artifact_dir = os.environ.get('MOBILE_ARTIFACT_DIR')
    if not artifact_dir or _device is None:
        return ''
    shot_dir = Path(artifact_dir) / 'step_screenshots'
    shot_dir.mkdir(parents=True, exist_ok=True)
    case_token = str(os.environ.get('MOBILE_EXECUTION_CASE_ID') or '0')
    filename = 'case_{0}_step_{1:03d}.png'.format(case_token, step_no)
    path = shot_dir / filename
    try:
        _device.screenshot(str(path))
        if path.is_file() and path.stat().st_size > 0:
            return 'step_screenshots/{0}'.format(filename)
    except Exception as exc:
        print('[MOBILE_STEP] screenshot failed: {0}'.format(exc), flush=True)
    return ''


def report_step(instruction, action_type='ui', status='running', error_message='', screenshot=True, **payload):
    """上报一个可见执行步骤，并尽量附带当前画面截图。"""
    global _step_no
    with _lock:
        _step_no += 1
        current_no = _step_no
        screenshot_rel = ''
        if screenshot:
            screenshot_rel = _capture_step_screenshot(current_no)
        record = {
            'step_no': current_no,
            'instruction': instruction,
            'action_type': action_type,
            'status': status,
            'error_message': error_message or '',
            'action_payload': payload or {},
            'screenshot_rel': screenshot_rel,
            'ts': time.time(),
        }
        line = json.dumps(record, ensure_ascii=False)
        path = _steps_file_path()
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8') as fp:
                fp.write(line + '\n')
                fp.flush()
        print('[MOBILE_STEP] {0} | {1} | {2} | shot={3}'.format(
            current_no, status, instruction, bool(screenshot_rel)
        ), flush=True)
        return current_no


def finish_step(instruction, action_type='ui', status='success', error_message='', **payload):
    return report_step(
        instruction,
        action_type=action_type,
        status=status,
        error_message=error_message,
        **payload
    )


def fail_step(instruction, error_message, action_type='assert', **payload):
    return report_step(
        instruction,
        action_type=action_type,
        status='failed',
        error_message=error_message,
        **payload
    )
