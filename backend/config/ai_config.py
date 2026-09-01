# encoding: UTF-8
"""
AI大模型配置文件
支持多种模型提供商：OpenAI、自定义API等
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

# 加载项目根目录.env，避免进程工作目录不同导致读取到其他配置
ENV_PATH = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(ENV_PATH, override=True)

class AIConfig:
    """AI配置类"""
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4096'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # Routin/Meteor API配置（兼容OpenAI格式的API）
    METEOR_API_KEY = os.getenv('METEOR_API_KEY', '')
    ROUTIN_API_KEY = os.getenv('ROUTIN_API_KEY', '')
    CUSTOM_API_KEY = os.getenv('CUSTOM_API_KEY', '')
    CUSTOM_API_BASE = os.getenv('CUSTOM_API_BASE', 'https://api.routin.ai/v1')
    CUSTOM_MODEL = os.getenv('CUSTOM_MODEL', 'gpt-4o')
    
    # 模型提供商：openai, custom
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'openai')
    
    # 超时配置（秒）
    CONNECT_TIMEOUT = int(os.getenv('AI_CONNECT_TIMEOUT', '60'))
    READ_TIMEOUT = int(os.getenv('AI_READ_TIMEOUT', '180'))
    
    # 重试配置
    MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('AI_RETRY_DELAY', '2.0'))
    GATEWAY_RETRY_DELAY = float(os.getenv('AI_GATEWAY_RETRY_DELAY', '30.0'))
    GATEWAY_MAX_RETRIES = int(os.getenv('AI_GATEWAY_MAX_RETRIES', '3'))
    CASE_GENERATION_AGENT_CONCURRENCY = int(os.getenv('AI_CASE_GENERATION_AGENT_CONCURRENCY', '0'))
    CASE_GENERATION_AGENT_MAX_WORKERS = int(os.getenv('AI_CASE_GENERATION_AGENT_MAX_WORKERS', '64'))
    CASE_GENERATION_AGENT_TIMEOUT = int(os.getenv('AI_CASE_GENERATION_AGENT_TIMEOUT', '600'))
    CASE_GENERATION_AGENT_IDLE_TIMEOUT = int(os.getenv('AI_CASE_GENERATION_AGENT_IDLE_TIMEOUT', '90'))
    REVIEW_AGENT_CONCURRENCY = int(os.getenv('AI_REVIEW_AGENT_CONCURRENCY', '3'))
    REVIEW_AGENT_CHUNK_SIZE = int(os.getenv('AI_REVIEW_AGENT_CHUNK_SIZE', '6000'))
    REQUEST_CONCURRENCY = int(os.getenv('AI_REQUEST_CONCURRENCY', '2'))
    REQUEST_MIN_INTERVAL = float(os.getenv('AI_REQUEST_MIN_INTERVAL', '5.0'))
    
    @staticmethod
    def get_api_key():
        """获取API密钥"""
        if AIConfig.MODEL_PROVIDER == 'openai':
            return AIConfig.OPENAI_API_KEY
        return AIConfig.METEOR_API_KEY or AIConfig.ROUTIN_API_KEY or AIConfig.CUSTOM_API_KEY
    
    @staticmethod
    def get_api_key_source():
        """获取当前API密钥来源，用于排查配置加载问题"""
        if AIConfig.MODEL_PROVIDER == 'openai':
            return 'OPENAI_API_KEY'
        if AIConfig.METEOR_API_KEY:
            return 'METEOR_API_KEY'
        if AIConfig.ROUTIN_API_KEY:
            return 'ROUTIN_API_KEY'
        if AIConfig.CUSTOM_API_KEY:
            return 'CUSTOM_API_KEY'
        return 'EMPTY'
    
    @staticmethod
    def get_api_base():
        """获取API基础URL"""
        if AIConfig.MODEL_PROVIDER == 'openai':
            return AIConfig.OPENAI_API_BASE
        return AIConfig.CUSTOM_API_BASE
    
    @staticmethod
    def get_model():
        """获取模型名称"""
        if AIConfig.MODEL_PROVIDER == 'openai':
            return AIConfig.OPENAI_MODEL
        return AIConfig.CUSTOM_MODEL
