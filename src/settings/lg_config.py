from pydantic_settings import BaseSettings
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class ServiceType(str, Enum):
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    # LangSmith settings
    LANGSMITH_PROJECT: str = ""
    LANGSMITH_API_KEY: str = ""
    
    # 应用基础设置 (新增)
    APP_ENV: str = "development"
    DEBUG: Union[bool, str] = True
    APP_TITLE: str = "CustomerService"
    PROJECT_NAME: str = "CustomerService"
    APP_DESCRIPTION: str = "E-CustomerService"
    
    # Swagger UI 认证 (新增)
    SWAGGER_UI_USERNAME: str = "admin"
    SWAGGER_UI_PASSWORD: str = "your-swagger-password"
    
    # CORS 设置 (新增)
    CORS_ORIGINS: Union[List[str], str] = []
    
    # JWT Token 设置 (新增，注意字段名差异)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Union[int, str] = 240
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: Union[int, str] = 7

    # Deepseek settings
    DEEPSEEK_API_KEY: str = ""  # 可选默认空字符串，实际使用前需校验
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Vision Model settings (独立配置)
    VISION_API_KEY: str = ""
    VISION_BASE_URL: str = "https://api.example.com/vision"
    VISION_MODEL: str = "vision-model-name"

    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3"
    OLLAMA_REASON_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_AGENT_MODEL: str = "llama3"

    # Service selection
    CHAT_SERVICE: ServiceType = ServiceType.DEEPSEEK
    REASON_SERVICE: ServiceType = ServiceType.OLLAMA
    AGENT_SERVICE: ServiceType = ServiceType.DEEPSEEK

    # Search settings
    SERPAPI_KEY: str = ""
    SEARCH_RESULT_COUNT: int = 3

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "customer_service_db"

    # Neo4j settings
    NEO4J_URL: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"

    # JWT settings (保留原始字段)
    SECRET_KEY: str = "your-secret-key"  # 生产环境请更换为强密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_EXPIRE: int = 3600
    REDIS_CACHE_THRESHOLD: float = 0.8

    # Embedding settings 
    EMBEDDING_TYPE: str = "ollama"  # ollama 或 sentence_transformer
    EMBEDDING_MODEL: str = "bge-m3"  # ollama embedding模型
    EMBEDDING_THRESHOLD: float = 0.90  # 语义相似度阈值

    # GraphRAG settings
    GRAPHRAG_PROJECT_DIR: str = r"D:\python_code\CustomerService\customerservice\src\graphrag"  # GraphRAG项目目录
    GRAPHRAG_DATA_DIR: str = "data"  # 数据目录名称
    GRAPHRAG_QUERY_TYPE: str = "local"  # 查询类型
    GRAPHRAG_RESPONSE_TYPE: str = "text"  # 响应类型
    GRAPHRAG_COMMUNITY_LEVEL: int = 3  # 社区级别
    GRAPHRAG_DYNAMIC_COMMUNITY: bool = False  # 是否动态选择社区

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def REDIS_URL(self) -> str:
        """构建Redis URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def NEO4J_CONN_URL(self) -> str:
        """构建Neo4j连接URL"""
        return f"{self.NEO4J_URL}"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # 分割逗号分隔的字符串并去除空白字符
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', mode='before')
    @classmethod
    def parse_jwt_access_token_expire_minutes(cls, v):
        if isinstance(v, str):
            return int(v)
        return v
    
    @field_validator('JWT_REFRESH_TOKEN_EXPIRE_DAYS', mode='before')
    @classmethod
    def parse_jwt_refresh_token_expire_days(cls, v):
        if isinstance(v, str):
            return int(v)
        return v
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug_flag(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v

    class Config:
        env_file = str(ENV_FILE)  # 使用绝对路径
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
