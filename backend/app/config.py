"""城市空间分析平台 - 配置模块"""
import os

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://spatial_user:spatial_pass@localhost:5432/urban_spatial'
)
SYNC_DATABASE_URL = DATABASE_URL.replace('+asyncpg', '+psycopg2')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
