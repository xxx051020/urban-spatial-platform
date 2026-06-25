"""Celery 异步 OD 矩阵计算任务"""
import math
import json
from celery import Celery
from celery.result import AsyncResult
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SYNC_DATABASE_URL

celery_app = Celery(
    'urban_spatial',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算球面距离（米）"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@celery_app.task(bind=True, name='compute_od_matrix')
def compute_od_matrix(self, origins: list, destinations: list):
    """计算 OD 距离矩阵（基于 Haversine 球面距离）"""
    matrix = []
    for o in origins:
        row = []
        for d in destinations:
            row.append(round(_haversine(o[0], o[1], d[0], d[1]), 2))
        matrix.append(row)
    return json.dumps(matrix)
