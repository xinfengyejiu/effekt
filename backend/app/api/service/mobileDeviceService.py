# encoding: UTF-8
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from app.core.config import (
    MOBILE_AUTOMATION_ADB_PATH,
    MOBILE_AUTOMATION_APPIUM_BIN,
    MOBILE_AUTOMATION_APPIUM_URL,
    MOBILE_AUTOMATION_PYTHON,
    MOBILE_AUTOMATION_ROOT,
)
from app.api.dao.mobileAutomationDao import MobileAutomationDao


class MobileDeviceService(object):
    REQUIRED_MODULES = ('pytest', 'uiautomator2', 'allure_pytest')
    _appium_process = None

    @staticmethod
    def _run(args, timeout=15):
        try:
            return subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False
            ), ''
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, str(exc)

    @staticmethod
    def _check_module(name):
        result, error = MobileDeviceService._run([
            MOBILE_AUTOMATION_PYTHON, '-c',
            'import importlib.util; raise SystemExit(0 if importlib.util.find_spec({0!r}) else 1)'.format(name),
        ])
        return bool(result and result.returncode == 0), error or (result.stderr.decode('utf-8', errors='replace') if result else '')

    @staticmethod
    def _appium_status():
        try:
            with urlopen(MOBILE_AUTOMATION_APPIUM_URL + '/status', timeout=2) as response:
                return response.status < 500, ''
        except (URLError, OSError) as exc:
            return False, str(exc)

    @staticmethod
    def _resolve_appium_bin():
        candidates = [
            MOBILE_AUTOMATION_APPIUM_BIN,
            shutil.which(MOBILE_AUTOMATION_APPIUM_BIN),
            shutil.which('appium'),
            os.path.expandvars(r'%APPDATA%\npm\appium.cmd'),
            os.path.expandvars(r'%APPDATA%\npm\appium'),
        ]
        for item in candidates:
            if not item:
                continue
            path = Path(item)
            if path.is_file():
                return str(path)
        return ''

    @staticmethod
    def _appium_listen_args():
        parsed = urlparse(MOBILE_AUTOMATION_APPIUM_URL)
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port or 4723
        return host, port

    @staticmethod
    def environment_check():
        adb_result, adb_error = MobileDeviceService._run([MOBILE_AUTOMATION_ADB_PATH, 'version'])
        modules = {}
        for module in MobileDeviceService.REQUIRED_MODULES:
            installed, error = MobileDeviceService._check_module(module)
            modules[module] = {'installed': installed, 'error': error[:300]}
        appium_ok, appium_error = MobileDeviceService._appium_status()
        modules['appium'] = {'installed': appium_ok, 'error': appium_error[:300]}
        root = Path(MOBILE_AUTOMATION_ROOT)
        return {
            'adb': {
                'available': bool(adb_result and adb_result.returncode == 0),
                'version': adb_result.stdout.decode('utf-8', errors='replace')[:500] if adb_result else '',
                'error': adb_error or (adb_result.stderr.decode('utf-8', errors='replace')[:300] if adb_result else ''),
            },
            'python': {'path': MOBILE_AUTOMATION_PYTHON, 'available': Path(MOBILE_AUTOMATION_PYTHON).is_file()},
            'modules': modules,
            'appium': {'url': MOBILE_AUTOMATION_APPIUM_URL, 'available': appium_ok, 'error': appium_error},
            'script_repository': {
                'path': str(root),
                'available': root.is_dir(),
                'pytest_ini_exists': (root / 'pytest.ini').is_file(),
                'requirements_exists': (root / 'requirements.txt').is_file(),
            },
        }

    @staticmethod
    def start_appium(wait_seconds=25):
        available, error = MobileDeviceService._appium_status()
        if available:
            return {
                'started': False,
                'already_running': True,
                'url': MOBILE_AUTOMATION_APPIUM_URL,
                'message': 'Appium 已在运行',
                'diagnostic': MobileDeviceService.environment_check(),
            }, ''

        appium_bin = MobileDeviceService._resolve_appium_bin()
        if not appium_bin:
            return {}, '未找到 Appium 可执行文件，请先安装 Appium 或配置 MOBILE_AUTOMATION_APPIUM_BIN'

        host, port = MobileDeviceService._appium_listen_args()
        args = [appium_bin, '--address', host, '--port', str(port)]
        popen_kwargs = {
            'stdout': subprocess.DEVNULL,
            'stderr': subprocess.DEVNULL,
            'stdin': subprocess.DEVNULL,
            'cwd': str(Path(MOBILE_AUTOMATION_ROOT)),
        }
        if os.name == 'nt':
            # 独立进程组 + 无窗口，避免随后端退出或弹出控制台
            popen_kwargs['creationflags'] = (
                getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
                | getattr(subprocess, 'DETACHED_PROCESS', 0)
                | getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            # .cmd 需要 shell，否则 CreateProcess 可能失败
            if appium_bin.lower().endswith(('.cmd', '.bat')):
                popen_kwargs['shell'] = True
                args = subprocess.list2cmdline(args)
        else:
            popen_kwargs['start_new_session'] = True

        try:
            MobileDeviceService._appium_process = subprocess.Popen(args, **popen_kwargs)
        except OSError as exc:
            return {}, '启动 Appium 失败：{0}'.format(str(exc)[:300])

        deadline = time.time() + max(5, int(wait_seconds or 25))
        last_error = error
        while time.time() < deadline:
            time.sleep(1)
            available, last_error = MobileDeviceService._appium_status()
            if available:
                return {
                    'started': True,
                    'already_running': False,
                    'url': MOBILE_AUTOMATION_APPIUM_URL,
                    'pid': getattr(MobileDeviceService._appium_process, 'pid', None),
                    'message': 'Appium 已启动',
                    'diagnostic': MobileDeviceService.environment_check(),
                }, ''

        return {}, 'Appium 已尝试启动，但在 {0} 秒内未就绪：{1}'.format(
            wait_seconds, (last_error or 'status 不可用')[:300]
        )

    @staticmethod
    def _device_properties(serial_no):
        def prop(key):
            result, _ = MobileDeviceService._run([MOBILE_AUTOMATION_ADB_PATH, '-s', serial_no, 'shell', 'getprop', key])
            return result.stdout.decode('utf-8', errors='replace').strip() if result and result.returncode == 0 else ''
        size_result, _ = MobileDeviceService._run([MOBILE_AUTOMATION_ADB_PATH, '-s', serial_no, 'shell', 'wm', 'size'])
        density_result, _ = MobileDeviceService._run([MOBILE_AUTOMATION_ADB_PATH, '-s', serial_no, 'shell', 'wm', 'density'])
        size_match = re.search(r'(\d+)x(\d+)', size_result.stdout.decode('utf-8', errors='replace') if size_result else '')
        density_match = re.search(r'(\d+)', density_result.stdout.decode('utf-8', errors='replace') if density_result else '')
        return {
            'brand': prop('ro.product.brand'),
            'model': prop('ro.product.model'),
            'android_version': prop('ro.build.version.release'),
            'sdk_version': prop('ro.build.version.sdk'),
            'screen_width': int(size_match.group(1)) if size_match else None,
            'screen_height': int(size_match.group(2)) if size_match else None,
            'density': density_match.group(1) if density_match else None,
        }

    @staticmethod
    def scan_devices(session):
        result, error = MobileDeviceService._run([MOBILE_AUTOMATION_ADB_PATH, 'devices', '-l'])
        if not result or result.returncode != 0:
            raise RuntimeError(error or (result.stderr.decode('utf-8', errors='replace') if result else 'adb 不可用'))
        now = datetime.now()
        discovered = []
        for raw_line in result.stdout.decode('utf-8', errors='replace').splitlines()[1:]:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            serial_no = parts[0]
            adb_status = parts[1] if len(parts) > 1 else 'unknown'
            values = {'adb_status': adb_status, 'last_seen_time': now}
            if adb_status == 'device':
                values['adb_status'] = 'online'
                values.update(MobileDeviceService._device_properties(serial_no))
            elif adb_status not in ('offline', 'unauthorized'):
                values['adb_status'] = 'unknown'
            device = MobileAutomationDao.upsert_device(session, serial_no, values)
            discovered.append(device)
        session.commit()
        return [item.to_dict() for item in discovered]
