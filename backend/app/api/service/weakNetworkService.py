# encoding: UTF-8
import hashlib
import io
import json
import zipfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from logger import logger
from ..dao.weakNetworkDao import WeakNetworkDao
from ..model.weakNetworkModel import WeakNetworkProfile, WeakNetworkSession

PACK_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / 'resources' / 'weaknet-pack'
PACK_FILES = (
    'weaknet.ps1',
    'weaknet.sh',
    'weaknet_proxy.py',
    'README.txt',
    'TOOLS.md',
)


class WeakNetworkService(object):

    @staticmethod
    def list_profiles(session, req_data):
        items, total = WeakNetworkDao.list_profiles(session, req_data)
        return {
            'list': [WeakNetworkService._profile_dict(x) for x in items],
            'total': total,
        }, ''

    @staticmethod
    def create_profile(session, req_data, user_id=None):
        name = (WeakNetworkService._get(req_data, 'name') or '').strip()
        if not name:
            return {}, 'name 为必传参数'
        preset = (WeakNetworkService._get(req_data, 'presetCode', 'preset_code') or 'custom').strip() or 'custom'
        add_info = {
            'product_id': WeakNetworkService._to_int_or_none(
                WeakNetworkService._get(req_data, 'productId', 'product_id')
            ),
            'product_name': WeakNetworkService._get(req_data, 'productName', 'product_name') or '',
            'project_id': WeakNetworkService._to_int_or_none(
                WeakNetworkService._get(req_data, 'projectId', 'project_id')
            ),
            'project_name': WeakNetworkService._get(req_data, 'projectName', 'project_name') or '',
            'name': name[:128],
            'preset_code': preset[:64],
            'latency_ms': int(WeakNetworkService._get(req_data, 'latencyMs', 'latency_ms') or 0),
            'bandwidth_kbps': int(WeakNetworkService._get(req_data, 'bandwidthKbps', 'bandwidth_kbps') or 0),
            'loss_percent': float(WeakNetworkService._get(req_data, 'lossPercent', 'loss_percent') or 0),
            'disconnect_rules': WeakNetworkService._as_dict(
                WeakNetworkService._get(req_data, 'disconnectRules', 'disconnect_rules')
            ),
            'remark': WeakNetworkService._get(req_data, 'remark') or '',
            'enabled': int(WeakNetworkService._get(req_data, 'enabled') if WeakNetworkService._get(req_data, 'enabled') is not None else 1),
            'is_system': 0,
            'created_by': user_id,
            'is_delete': 0,
        }
        obj, err = WeakNetworkDao.create(session, WeakNetworkProfile, add_info)
        if err:
            return {}, err
        return WeakNetworkService._profile_dict(obj), ''

    @staticmethod
    def update_profile(session, req_data, user_id=None):
        profile_id = WeakNetworkService._get(req_data, 'profileId', 'profile_id', 'id')
        if not profile_id:
            return {}, 'profileId 为必传参数'
        obj = WeakNetworkDao.get_by_id(session, WeakNetworkProfile, profile_id)
        if not obj:
            return {}, '未查询到画像'
        if int(obj.is_system or 0) == 1:
            # allow parameter tweak on system presets but keep preset_code
            pass
        update_info = {}
        mapping = [
            ('name', 'name'),
            ('latencyMs', 'latency_ms'),
            ('latency_ms', 'latency_ms'),
            ('bandwidthKbps', 'bandwidth_kbps'),
            ('bandwidth_kbps', 'bandwidth_kbps'),
            ('lossPercent', 'loss_percent'),
            ('loss_percent', 'loss_percent'),
            ('remark', 'remark'),
            ('enabled', 'enabled'),
            ('productName', 'product_name'),
            ('projectName', 'project_name'),
        ]
        for src, dst in mapping:
            if src in (req_data or {}):
                val = req_data.get(src)
                if dst in ('latency_ms', 'bandwidth_kbps', 'enabled') and val is not None:
                    update_info[dst] = int(val)
                elif dst == 'loss_percent' and val is not None:
                    update_info[dst] = float(val)
                elif val is not None:
                    update_info[dst] = val
        if 'disconnectRules' in (req_data or {}) or 'disconnect_rules' in (req_data or {}):
            update_info['disconnect_rules'] = WeakNetworkService._as_dict(
                WeakNetworkService._get(req_data, 'disconnectRules', 'disconnect_rules')
            )
        if 'presetCode' in (req_data or {}) or 'preset_code' in (req_data or {}):
            if int(obj.is_system or 0) != 1:
                update_info['preset_code'] = (
                    WeakNetworkService._get(req_data, 'presetCode', 'preset_code') or 'custom'
                )[:64]
        if not update_info:
            return WeakNetworkService._profile_dict(obj), ''
        _, err = WeakNetworkDao.update_by_id(session, WeakNetworkProfile, profile_id, update_info)
        if err:
            return {}, err
        obj = WeakNetworkDao.get_by_id(session, WeakNetworkProfile, profile_id)
        return WeakNetworkService._profile_dict(obj), ''

    @staticmethod
    def delete_profile(session, req_data, user_id=None):
        profile_id = WeakNetworkService._get(req_data, 'profileId', 'profile_id', 'id')
        if not profile_id:
            return {}, 'profileId 为必传参数'
        obj = WeakNetworkDao.get_by_id(session, WeakNetworkProfile, profile_id)
        if not obj:
            return {}, '未查询到画像'
        if int(obj.is_system or 0) == 1:
            return {}, '系统预设画像不可删除，可停用'
        _, err = WeakNetworkDao.update_by_id(session, WeakNetworkProfile, profile_id, {'is_delete': 1, 'enabled': 0})
        if err:
            return {}, err
        return {'profileId': int(profile_id)}, ''

    @staticmethod
    def create_session(session, req_data, user_id=None):
        profile_id = WeakNetworkService._get(req_data, 'profileId', 'profile_id')
        if not profile_id:
            return {}, 'profileId 为必传参数'
        profile = WeakNetworkDao.get_by_id(session, WeakNetworkProfile, profile_id)
        if not profile:
            return {}, '未查询到画像'
        if int(profile.enabled or 0) != 1:
            return {}, '画像已停用'
        snapshot = WeakNetworkService._profile_snapshot(profile)
        session_no = WeakNetworkService._next_session_no(session)
        proxy_port = int(WeakNetworkService._get(req_data, 'proxyPort', 'proxy_port') or 18888)
        device_serial = (WeakNetworkService._get(req_data, 'deviceSerial', 'device_serial') or '').strip() or None
        expires_at = datetime.now() + timedelta(days=7)
        add_info = {
            'session_no': session_no,
            'profile_id': int(profile.id),
            'profile_snapshot': snapshot,
            'product_id': WeakNetworkService._to_int_or_none(
                WeakNetworkService._get(req_data, 'productId', 'product_id')
            ) or profile.product_id,
            'project_id': WeakNetworkService._to_int_or_none(
                WeakNetworkService._get(req_data, 'projectId', 'project_id')
            ) or profile.project_id,
            'device_serial': device_serial,
            'proxy_port': proxy_port,
            'status': 'created',
            'expires_at': expires_at,
            'created_by': user_id,
            'remark': WeakNetworkService._get(req_data, 'remark') or '',
            'is_delete': 0,
        }
        obj, err = WeakNetworkDao.create(session, WeakNetworkSession, add_info)
        if err:
            return {}, err
        return WeakNetworkService._session_dict(obj), ''

    @staticmethod
    def list_sessions(session, req_data):
        items, total = WeakNetworkDao.list_sessions(session, req_data)
        return {
            'list': [WeakNetworkService._session_dict(x) for x in items],
            'total': total,
        }, ''

    @staticmethod
    def build_pack_bytes(session, session_id):
        obj = WeakNetworkDao.get_by_id(session, WeakNetworkSession, session_id)
        if not obj:
            return None, None, '未查询到会话'
        if not PACK_TEMPLATE_DIR.exists():
            return None, None, '弱网包模板目录不存在：resources/weaknet-pack'
        snapshot = obj.profile_snapshot or {}
        profile_json = {
            'name': snapshot.get('name'),
            'preset_code': snapshot.get('presetCode') or snapshot.get('preset_code'),
            'latency_ms': int(snapshot.get('latencyMs') or snapshot.get('latency_ms') or 0),
            'bandwidth_kbps': int(snapshot.get('bandwidthKbps') or snapshot.get('bandwidth_kbps') or 0),
            'loss_percent': float(snapshot.get('lossPercent') or snapshot.get('loss_percent') or 0),
            'disconnect_rules': snapshot.get('disconnectRules') or snapshot.get('disconnect_rules') or {},
            'remark': snapshot.get('remark') or '',
        }
        session_json = {
            'session_id': obj.id,
            'session_no': obj.session_no,
            'device_serial': obj.device_serial or '',
            'proxy_port': int(obj.proxy_port or 18888),
            'profile_id': obj.profile_id,
            'created_time': obj.created_time.isoformat(sep=' ', timespec='seconds') if obj.created_time else '',
        }
        buf = io.BytesIO()
        hasher = hashlib.sha256()
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for name in PACK_FILES:
                path = PACK_TEMPLATE_DIR / name
                if not path.exists():
                    continue
                data = path.read_bytes()
                zf.writestr(name, data)
                hasher.update(data)
            profile_bytes = json.dumps(profile_json, ensure_ascii=False, indent=2).encode('utf-8')
            session_bytes = json.dumps(session_json, ensure_ascii=False, indent=2).encode('utf-8')
            zf.writestr('profile.json', profile_bytes)
            zf.writestr('session.json', session_bytes)
            hasher.update(profile_bytes)
            hasher.update(session_bytes)
        pack_hash = hasher.hexdigest()
        WeakNetworkDao.update_by_id(session, WeakNetworkSession, obj.id, {
            'pack_hash': pack_hash,
            'status': 'downloaded',
        })
        filename = 'weaknet-{}-{}.zip'.format(
            (profile_json.get('preset_code') or 'custom'),
            obj.session_no,
        )
        return buf.getvalue(), filename, ''

    @staticmethod
    def _profile_snapshot(profile):
        return {
            'profileId': profile.id,
            'name': profile.name,
            'presetCode': profile.preset_code,
            'latencyMs': int(profile.latency_ms or 0),
            'bandwidthKbps': int(profile.bandwidth_kbps or 0),
            'lossPercent': float(profile.loss_percent or 0),
            'disconnectRules': profile.disconnect_rules or {},
            'remark': profile.remark or '',
        }

    @staticmethod
    def _profile_dict(obj):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        return {
            'profileId': obj.id,
            'productId': obj.product_id,
            'productName': obj.product_name,
            'projectId': obj.project_id,
            'projectName': obj.project_name,
            'name': obj.name,
            'presetCode': obj.preset_code,
            'latencyMs': int(obj.latency_ms or 0),
            'bandwidthKbps': int(obj.bandwidth_kbps or 0),
            'lossPercent': float(obj.loss_percent or 0) if obj.loss_percent is not None else 0,
            'disconnectRules': obj.disconnect_rules or {},
            'remark': obj.remark,
            'enabled': int(obj.enabled or 0),
            'isSystem': int(obj.is_system or 0),
            'createdBy': obj.created_by,
            'createdTime': data.get('created_time') or data.get('createdTime'),
            'updatedTime': data.get('updated_time') or data.get('updatedTime'),
        }

    @staticmethod
    def _session_dict(obj):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        return {
            'sessionId': obj.id,
            'sessionNo': obj.session_no,
            'profileId': obj.profile_id,
            'profileSnapshot': obj.profile_snapshot or {},
            'productId': obj.product_id,
            'projectId': obj.project_id,
            'deviceSerial': obj.device_serial,
            'proxyPort': obj.proxy_port,
            'packHash': obj.pack_hash,
            'status': obj.status,
            'expiresAt': data.get('expires_at') or data.get('expiresAt'),
            'createdBy': obj.created_by,
            'createdTime': data.get('created_time') or data.get('createdTime'),
        }

    @staticmethod
    def _next_session_no(session):
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        prefix = 'WN{}'.format(stamp)
        # uniqueness via DB unique; append random-ish suffix via count
        count = session.query(WeakNetworkSession).filter(
            WeakNetworkSession.session_no.like(prefix + '%')
        ).count()
        return '{}{:02d}'.format(prefix, (count % 100) + 1)

    @staticmethod
    def _as_dict(value):
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    @staticmethod
    def _to_int_or_none(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _get(data, *keys):
        if not data:
            return None
        for k in keys:
            if k in data and data.get(k) is not None:
                return data.get(k)
        return None
