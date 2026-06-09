# encoding: UTF-8
import os
import xml.etree.ElementTree as ET


class JacocoCoverageService(object):
    @staticmethod
    def normalize_jacoco_source_path(package_name, sourcefile_name):
        package_path = (package_name or '').replace('.', '/').replace('\\', '/')
        return (package_path + '/' + sourcefile_name).strip('/') if package_path else sourcefile_name

    @staticmethod
    def parse_jacoco_xml(file_path):
        if not os.path.isfile(file_path):
            return {}, 'JaCoCo XML文件不存在'
        try:
            root = ET.parse(file_path).getroot()
            files = {}
            total_covered = 0
            total_missed = 0
            for package in root.findall('.//package'):
                package_name = package.attrib.get('name', '')
                for sourcefile in package.findall('sourcefile'):
                    name = sourcefile.attrib.get('name')
                    normalized = JacocoCoverageService.normalize_jacoco_source_path(package_name, name)
                    covered = []
                    missed = []
                    for line in sourcefile.findall('line'):
                        line_no = int(line.attrib.get('nr', 0))
                        mi = int(line.attrib.get('mi', 0))
                        ci = int(line.attrib.get('ci', 0))
                        if ci > 0:
                            covered.append(line_no)
                            total_covered += 1
                        elif mi > 0:
                            missed.append(line_no)
                            total_missed += 1
                    total = len(covered) + len(missed)
                    files[normalized] = {
                        'coveredLines': covered,
                        'missedLines': missed,
                        'lineRate': round(len(covered) * 100.0 / total, 4) if total else 0
                    }
            total = total_covered + total_missed
            return {'files': files, 'summary': {'lineRate': round(total_covered * 100.0 / total, 4) if total else 0,
                                                'coveredLines': total_covered, 'missedLines': total_missed}}, ''
        except Exception as err:
            return {}, f'JaCoCo XML解析失败：{err}'

    @staticmethod
    def match_file_path(changed_file_path, coverage_files):
        changed = (changed_file_path or '').replace('\\', '/')
        if changed in coverage_files:
            return changed
        candidates = []
        for path in coverage_files.keys():
            normalized = path.replace('\\', '/')
            if changed.endswith(normalized) or normalized.endswith(changed):
                candidates.append(path)
            elif os.path.basename(changed) == os.path.basename(normalized):
                candidates.append(path)
        if not candidates:
            return None
        candidates.sort(key=lambda item: len(item), reverse=True)
        return candidates[0]
