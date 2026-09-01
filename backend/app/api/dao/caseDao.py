# encoding: UTF-8
from sqlalchemy import func
import re


from ..model.caseModel import CaseReview, CaseSnapshot, Module, TestCase
from logger import logger


class CaseDao(object):
    """用例域通用 DAO，复用模块、用例、快照、评审的基础操作。"""

    @staticmethod
    def create(session, model_cls, add_info):
        """创建记录并提交事务。"""
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__}新增失败！{err}')
            return 0, f'新增失败！{err}'
        return obj.id, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info)
        err = session.done(close=False)
        if err:
            logger.error(f'{model_cls.__name__}更新失败！id: {obj_id}, err: {err}')
            return 0, f'更新失败！{err}'
        if not update_res:
            return 0, '未查询到对应记录！'
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page=1, limit=20, order_column=None):
        query = session.query(model_cls).filter(*filter_list)
        if hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        total = query.count()
        if order_column is not None:
            query = query.order_by(order_column.desc())
        rets = query.offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        return rets, total

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return CaseDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})

    @staticmethod
    def next_case_key(session, project_id, module_id=None, product_id=None):
        from ..model.productModel import Product
        from ..model.projectModel import Project
        from ..model.caseModel import Module
        
        product_abbr = ''
        if product_id:
            product = session.query(Product).filter(Product.id == int(product_id), Product.is_delete == 0).first()
            if product and product.name:
                product_abbr = CaseDao._generate_abbreviation(product.name)
        
        project_abbr = ''
        project = session.query(Project).filter(Project.id == int(project_id), Project.is_delete == 0).first()
        if project and project.name:
            project_abbr = CaseDao._generate_abbreviation(project.name)
        
        module_abbr = ''
        if module_id:
            module = session.query(Module).filter(Module.id == int(module_id), Module.is_delete == 0).first()
            if module and module.name:
                module_abbr = CaseDao._generate_abbreviation(module.name)
        
        parts = ['TC']
        if product_abbr:
            parts.append(product_abbr)
        if project_abbr:
            parts.append(project_abbr)
        if module_abbr:
            parts.append(module_abbr)
        
        prefix = '-'.join(parts)
        
        existing_keys = session.query(TestCase.case_key).filter(
            TestCase.project_id == int(project_id),
            TestCase.is_delete == 0,
            TestCase.case_key.like(f'{prefix}-%')
        ).all()

        max_num = 0
        key_pattern = re.compile(r'^{}-(\d+)$'.format(re.escape(prefix)))
        for row in existing_keys:
            case_key = row[0] if isinstance(row, tuple) else getattr(row, 'case_key', '')
            match = key_pattern.match(case_key or '')
            if match:
                max_num = max(max_num, int(match.group(1)))
        
        return '{}-{:03d}'.format(prefix, max_num + 1)

    
    @staticmethod
    def _generate_abbreviation(name):
        import re
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        english_pattern = re.compile(r'[a-zA-Z]+')
        
        chinese_chars = chinese_pattern.findall(name)
        if chinese_chars:
            full_chinese = ''.join(chinese_chars)
            abbr = ''.join([CaseDao._get_pinyin_first_char(c) for c in full_chinese[:4]])
            abbr = abbr.lower()
            if len(abbr) < 2:
                abbr = abbr.ljust(2, 'n')
            return abbr
        
        english_words = english_pattern.findall(name)
        if english_words:
            abbr = english_words[0].lower()[:4]
            if len(abbr) < 2:
                abbr = abbr.ljust(2, 'x')
            return abbr
        
        abbr = name.lower()[:4]
        if len(abbr) < 2:
            abbr = abbr.ljust(2, 'x')
        return abbr
    
    @staticmethod
    def _get_pinyin_first_char(char):
        pinyin_map = {
            '智': 'Z', '慧': 'H', '运': 'Y', '营': 'Y',
            '报': 'B', '关': 'G', '工': 'G', '作': 'Z', '台': 'T',
            '测': 'C', '试': 'S', '用': 'Y', '例': 'L',
            '产': 'C', '品': 'P', '项': 'X', '目': 'M',
            '模': 'M', '块': 'K', '管': 'G', '理': 'L',
            '系': 'X', '统': 'T', '功': 'G', '能': 'N',
            '页': 'Y', '面': 'M', '查': 'C', '询': 'X',
            '添': 'T', '加': 'J', '编': 'B', '辑': 'J',
            '删': 'S', '除': 'C', '导': 'D', '入': 'R',
            '导': 'D', '出': 'C', '批': 'P', '量': 'L',
            '设': 'S', '置': 'Z', '配': 'P', '置': 'Z',
            '权': 'Q', '限': 'X', '角': 'J', '色': 'S',
            '用': 'Y', '户': 'H', '组': 'Z', '织': 'Z',
            '计': 'J', '划': 'H', '执': 'Z', '行': 'X',
            '报': 'B', '告': 'G', '统': 'T', '计': 'J',
            '首': 'S', '页': 'Y', '仪': 'Y', '表': 'B',
            '烟': 'Y', '冒': 'M', '回': 'H', '归': 'G',
            '集': 'J', '成': 'C', '接': 'J', '口': 'K',
            '安': 'A', '全': 'Q', '日': 'R', '志': 'Z',
            '监': 'J', '控': 'K', '优': 'Y', '化': 'H',
            '性': 'X', '能': 'N', '首': 'S', '尾': 'W',
            '开': 'K', '发': 'F', '测': 'C', '运': 'Y',
            '维': 'W', '设': 'S', '计': 'J', '研': 'Y',
            '发': 'F', '部': 'B', '组': 'Z', '个': 'G',
            '人': 'R', '公': 'G', '司': 'S', '有': 'Y',
            '限': 'X', '责': 'Z', '任': 'R', '股': 'G',
            '份': 'F', '集': 'J', '团': 'T', '科': 'K',
            '技': 'J', '网': 'W', '络': 'L', '信': 'X',
            '息': 'X', '软': 'R', '件': 'J', '系': 'X',
            '统': 'T', '解': 'J', '决': 'J', '方': 'F',
            '案': 'A', '服': 'F', '务': 'W', '支': 'Z',
            '持': 'C', '培': 'P', '训': 'X', '咨': 'Z',
            '询': 'X', '销': 'X', '售': 'S', '市': 'S',
            '场': 'C', '运': 'Y', '营': 'Y', '管': 'G',
            '理': 'L', '财': 'C', '务': 'W', '人': 'R',
            '力': 'L', '资': 'Z', '源': 'Y', '行': 'X',
            '政': 'Z', '法': 'F', '律': 'L', '合': 'H',
            '规': 'G', '质': 'Z', '量': 'L', '安': 'A',
            '全': 'Q', '环': 'H', '境': 'J', '职': 'Z',
            '能': 'N', '模': 'M', '块': 'K', '页': 'Y',
            '面': 'M', '窗': 'C', '口': 'K', '表': 'B',
            '单': 'D', '按': 'A', '钮': 'N', '链': 'L',
            '接': 'J', '图': 'T', '标': 'B', '菜': 'C',
            '单': 'D', '导': 'D', '航': 'H', '搜': 'S',
            '索': 'S', '过': 'G', '滤': 'L', '排': 'P',
            '序': 'X', '分': 'F', '页': 'Y', '导': 'D',
            '入': 'R', '导': 'D', '出': 'C', '打': 'D',
            '印': 'Y', '导': 'D', '出': 'C', '删': 'S',
            '除': 'C', '复': 'F', '制': 'Z', '粘': 'N',
            '贴': 'T', '剪': 'J', '切': 'Q', '保': 'B',
            '存': 'C', '取': 'Q', '消': 'X', '确': 'Q',
            '认': 'R', '提': 'T', '交': 'J', '审': 'S',
            '核': 'H', '批': 'P', '准': 'Z', '拒': 'J',
            '绝': 'J', '返': 'F', '回': 'H', '修': 'X',
            '改': 'G', '查': 'C', '看': 'K', '详': 'X',
            '情': 'Q', '列': 'L', '表': 'B', '统': 'T',
            '计': 'J', '图': 'T', '表': 'B', '报': 'B',
            '告': 'G', '日': 'R', '志': 'Z', '备': 'B',
            '注': 'Z', '描': 'M', '述': 'S', '名': 'M',
            '称': 'C', '编': 'B', '号': 'H', '类': 'L',
            '型': 'X', '状': 'Z', '态': 'T', '优': 'Y',
            '先': 'X', '级': 'J', '标': 'B', '签': 'Q',
            '关': 'G', '键': 'J', '词': 'C', '描': 'M',
            '述': 'S', '附': 'F', '件': 'J', '链': 'L',
            '接': 'J', '时': 'S', '间': 'J', '日': 'R',
            '期': 'Q', '数': 'S', '量': 'L', '金': 'J',
            '额': 'E', '价': 'J', '格': 'G', '数': 'S',
            '据': 'J', '库': 'K', '服': 'F', '务': 'W',
            '器': 'Q', '线': 'X', '程': 'C', '进': 'J',
            '度': 'D', '速': 'S', '度': 'D', '效': 'X',
            '率': 'L', '性': 'X', '能': 'N', '稳': 'W',
            '定': 'D', '可': 'K', '靠': 'K', '安': 'A',
            '全': 'Q', '兼': 'J', '容': 'R', '扩': 'K',
            '展': 'Z', '升': 'S', '级': 'J', '更': 'G',
            '新': 'X', '修': 'X', '补': 'B', '修': 'X',
            '复': 'F', '优': 'Y', '化': 'H', '重': 'Z',
            '构': 'G', '改': 'G', '造': 'Z', '移': 'Y',
            '植': 'Z', '集': 'J', '成': 'C', '接': 'J',
            '口': 'K', '调': 'T', '试': 'S', '测': 'C',
            '试': 'S', '验': 'Y', '证': 'Z', '确': 'Q',
            '认': 'R', '回': 'H', '归': 'G', '演': 'Y',
            '示': 'S', '培': 'P', '训': 'X', '指': 'Z',
            '导': 'D', '支': 'Z', '持': 'C', '帮': 'B',
            '助': 'Z', '反': 'F', '馈': 'K', '投': 'T',
            '诉': 'S', '建': 'J', '议': 'Y', '评': 'P',
            '独': 'D', '立': 'L', '站': 'Z', '采': 'C',
            '购': 'G', '供': 'G', '应': 'Y', '商': 'S',
            '价': 'J', '满': 'M', '意': 'Y', '度': 'D'
        }
        return pinyin_map.get(char, 'N')

    @staticmethod
    def next_snapshot_version(session, case_id):
        """生成用例快照版本号。"""
        max_version = session.query(func.max(CaseSnapshot.version)).filter(CaseSnapshot.case_id == int(case_id)).scalar() or 0
        return int(max_version) + 1

    @staticmethod
    def module_model():
        return Module

    @staticmethod
    def case_model():
        return TestCase

    @staticmethod
    def snapshot_model():
        return CaseSnapshot

    @staticmethod
    def review_model():
        return CaseReview

    @staticmethod
    def get_module_name_map(session, module_ids):
        if not module_ids:
            return {}
        module_items = session.query(Module).filter(Module.id.in_(module_ids), Module.is_delete == 0).all()
        return {module.id: module.name for module in module_items}

    @staticmethod
    def copy_case(session, source_case_id, user_id=None):
        """复制用例：读取源用例，生成新编号，创建副本。返回 (new_id, error_msg)。"""
        source = session.query(TestCase).filter(
            TestCase.id == int(source_case_id), TestCase.is_delete == 0
        ).first()
        if not source:
            return 0, '源用例不存在'

        project_id = source.project_id
        module_id = source.module_id

        # 生成新编号（基于同一项目+模块）
        from ..model.productModel import Product
        from ..model.projectModel import Project

        product_id = None
        project = session.query(Project).filter(Project.id == project_id, Project.is_delete == 0).first()
        if project:
            product_id = project.product_id

        new_case_key = CaseDao.next_case_key(session, project_id, module_id, product_id)

        # 复制所有字段，重置 id、case_key、is_ai_generated，更新创建人
        add_info = {
            'project_id': project_id,
            'module_id': module_id,
            'case_key': new_case_key,
            'title': source.title,
            'preconditions': source.preconditions,
            'steps': source.steps,
            'expected_results': source.expected_results,
            'priority': source.priority,
            'case_type': source.case_type,
            'tags': list(source.tags) if source.tags else [],
            'status': 1,  # 复制后默认为正常状态
            'is_auto': source.is_auto,
            'is_ai_generated': 0,  # 复制后不再标记为 AI 生成
            'created_by': user_id or source.created_by,
            'is_delete': 0,
        }

        new_case = TestCase(**add_info)
        session.add(new_case)
        err = session.done(close=False)
        if err:
            logger.warning(f'用例复制失败！{err}')
            return 0, f'复制失败！{err}'
        return new_case.id, ''
