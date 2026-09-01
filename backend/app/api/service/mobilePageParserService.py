# encoding: UTF-8
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from app.core.config import MOBILE_AUTOMATION_ADB_PATH
from app.api.service.mobileArtifactService import MobileArtifactService

_BOUNDS_PATTERN = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]')


class MobilePageParserService(object):
    @staticmethod
    def _run_adb(args, timeout=20, binary=False):
        return subprocess.run(
            [MOBILE_AUTOMATION_ADB_PATH] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )

    @staticmethod
    def _parse_bounds(value):
        matched = _BOUNDS_PATTERN.fullmatch(value or '')
        if not matched:
            return [0, 0, 0, 0]
        return [int(item) for item in matched.groups()]

    @staticmethod
    def parse_xml(xml_text):
        elements = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            return {'elements': [], 'dom_quality': 'invalid', 'error': str(exc)}
        for index, node in enumerate(root.iter('node'), start=1):
            attrs = node.attrib
            bounds = MobilePageParserService._parse_bounds(attrs.get('bounds'))
            elements.append({
                'id': 'dom_{0}'.format(index),
                'class_name': attrs.get('class', ''),
                'text': attrs.get('text', ''),
                'content_desc': attrs.get('content-desc', ''),
                'resource_id': attrs.get('resource-id', ''),
                'bounds': bounds,
                'clickable': attrs.get('clickable') == 'true',
                'enabled': attrs.get('enabled') == 'true',
                'checked': attrs.get('checked') == 'true',
                'selected': attrs.get('selected') == 'true',
            })
        quality = 'good' if len(elements) >= 5 else 'insufficient'
        return {'elements': elements, 'dom_quality': quality}

    @staticmethod
    def capture(session, execution_id, execution_no, serial_no, execution_case_id=None, capture_label=None):
        root = MobileArtifactService.execution_root(execution_no) / 'snapshots'
        root.mkdir(parents=True, exist_ok=True)
        if execution_case_id:
            prefix = 'case_{0}_{1}_'.format(execution_case_id, capture_label or 'snapshot')
        else:
            prefix = 'manual_{0}_'.format(capture_label or 'snapshot')
        xml_result = MobilePageParserService._run_adb(['-s', serial_no, 'exec-out', 'uiautomator', 'dump', '/dev/tty'])
        xml_text = xml_result.stdout.decode('utf-8', errors='replace')
        if not xml_text.strip().startswith('<?xml'):
            dump_result = MobilePageParserService._run_adb(['-s', serial_no, 'shell', 'uiautomator', 'dump', '/sdcard/window.xml'])
            if dump_result.returncode == 0:
                read_result = MobilePageParserService._run_adb(['-s', serial_no, 'exec-out', 'cat', '/sdcard/window.xml'])
                xml_text = read_result.stdout.decode('utf-8', errors='replace')
        screenshot_result = MobilePageParserService._run_adb(['-s', serial_no, 'exec-out', 'screencap', '-p'])
        xml_path = root / (prefix + 'page.xml')
        image_path = root / (prefix + 'page.png')
        json_path = root / (prefix + 'page.json')
        xml_path.write_text(xml_text, encoding='utf-8')
        image_path.write_bytes(screenshot_result.stdout)
        snapshot = MobilePageParserService.parse_xml(xml_text)
        snapshot['serial_no'] = serial_no
        snapshot['xml_capture_error'] = xml_result.stderr.decode('utf-8', errors='replace')[:500]
        snapshot['screenshot_capture_error'] = screenshot_result.stderr.decode('utf-8', errors='replace')[:500]
        json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
        xml_artifact = MobileArtifactService.register_file(session, execution_id, xml_path, 'ui_xml', execution_case_id)
        screenshot_artifact = MobileArtifactService.register_file(session, execution_id, image_path, 'screenshot', execution_case_id)
        json_artifact = MobileArtifactService.register_file(session, execution_id, json_path, 'page_json', execution_case_id)
        return {
            'snapshot': snapshot,
            'xml_artifact_id': xml_artifact.id if xml_artifact else None,
            'screenshot_artifact_id': screenshot_artifact.id if screenshot_artifact else None,
            'page_json_artifact_id': json_artifact.id if json_artifact else None,
        }
