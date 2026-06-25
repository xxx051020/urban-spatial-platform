""""ORM 模型定义 — POI 兴趣点表、OD 矩阵结果表"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base


class POI(Base):
    __tablename__ = 'pois'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment='POI 名称')
    category = Column(String(100), nullable=False, comment='类别：餐饮/交通/商业/教育')
    address = Column(String(500), comment='地址')
    geom = Column(Geometry('POINT', srid=4326), nullable=False)


class ODMatrixTask(Base):
    __tablename__ = 'od_matrix_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(20), default='pending', comment='pending|running|completed|failed')
    result = Column(String, comment='JSON 结果')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
