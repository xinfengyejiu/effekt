# encoding: UTF-8
from ..model.aiTaskModel import AiTestTask, AiTestTaskStep
from .aiBaseDao import AiBaseDao


class AiTaskDao(AiBaseDao):
    @staticmethod
    def batch_create_steps(session, rows):
        if not rows:
            return [], ''
        objs = [AiTestTaskStep(**row) for row in rows]
        session.add_all(objs)
        err = session.done(close=False)
        if err:
            return [], f'批量新增失败！{err}'
        return objs, ''
