# -*- coding: utf-8 -*-
import json

import requests
from requests.auth import HTTPBasicAuth

from const import JENKINS_BASE_URL, JENKINS_DEFAULT_JOB, JENKINS_TOKEN, JENKINS_USER
from logger import logger


class JenkinsRequest(object):
    def __init__(self, jenkins_url=None, username=None, password=None):
        if jenkins_url:
            self.base_url = jenkins_url.rstrip('/')
            use_username = username or JENKINS_USER or 'jenkins'
            use_password = password or JENKINS_TOKEN or 'jenkins'
            self.auth = HTTPBasicAuth(use_username, use_password)
        else:
            self.base_url = JENKINS_BASE_URL.rstrip('/')
            self.auth = HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN) if JENKINS_USER and JENKINS_TOKEN else None
        self.session = requests.Session()
        self.session.auth = self.auth
        logger.info(f'Jenkins配置: base_url={self.base_url}, username={use_username if jenkins_url else JENKINS_USER}')

    def get_crumb(self):
        if not self.base_url:
            return {}
        
        crumb_url = f'{self.base_url}/crumbIssuer/api/json'
        try:
            response = self.session.get(crumb_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f'获取Jenkins crumb失败：status={response.status_code}')
                return {}
            crumb_data = response.json()
            if crumb_data.get('crumbRequestField') and crumb_data.get('crumb'):
                logger.info(f'成功获取Jenkins crumb: {crumb_data["crumbRequestField"]}')
                return {crumb_data['crumbRequestField']: crumb_data['crumb']}
        except Exception as err:
            logger.warning(f'获取Jenkins crumb失败：{err}')
        return {}

    def build_with_parameters(self, params, job_name=None):
        job_name = job_name or JENKINS_DEFAULT_JOB
        if not self.base_url or not job_name:
            return False, 'Jenkins配置不完整', {}
        
        url = f'{self.base_url}/job/{job_name}/buildWithParameters'
        headers = self.get_crumb()
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        
        logger.info(f'Jenkins构建请求: url={url}, params={json.dumps(params, ensure_ascii=False)}')
        
        try:
            response = self.session.post(url, data=params, headers=headers, timeout=60)
            if response.status_code not in (200, 201, 202):
                logger.error(f'Jenkins触发失败：status={response.status_code}, body={response.text[:500]}')
                
                if response.status_code == 403 and 'crumb' in response.text:
                    logger.info('Crumb失效，尝试重新获取并重试...')
                    headers = self.get_crumb()
                    headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
                    response = self.session.post(url, data=params, headers=headers, timeout=60)
                    
                    if response.status_code not in (200, 201, 202):
                        logger.error(f'Jenkins触发失败(重试后)：status={response.status_code}')
                        return False, f'Jenkins触发失败：{response.status_code}', {}
            
            location = response.headers.get('Location', '')
            queue_id = None
            if '/queue/item/' in location:
                try:
                    queue_id = int(location.rstrip('/').split('/')[-1])
                except Exception:
                    queue_id = None
            
            logger.info(f'Jenkins构建成功：queue_id={queue_id}, location={location}')
            return True, '', {'job_name': job_name, 'queue_id': queue_id, 'location': location}
            
        except Exception as err:
            logger.error(f'Jenkins请求异常：{err}, params={json.dumps(params, ensure_ascii=False)}')
            return False, str(err), {}

    def get_queue_item(self, queue_id):
        if not self.base_url or not queue_id:
            return False, 'Jenkins队列ID为空', {}
        try:
            response = self.session.get(f'{self.base_url}/queue/item/{queue_id}/api/json', timeout=30)
            if response.status_code != 200:
                return False, f'查询Jenkins队列失败：{response.status_code}', {}
            return True, '', response.json()
        except Exception as err:
            logger.error(f'查询Jenkins队列异常：{err}')
            return False, str(err), {}

    def get_build_info(self, job_name, build_number):
        if not self.base_url or not job_name or not build_number:
            return False, 'Jenkins任务或构建号为空', {}
        try:
            url = f'{self.base_url}/job/{job_name}/{build_number}/api/json'
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                return False, f'查询Jenkins构建失败：{response.status_code}', {}
            return True, '', response.json()
        except Exception as err:
            logger.error(f'查询Jenkins构建异常：{err}')
            return False, str(err), {}