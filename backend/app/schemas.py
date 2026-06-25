"""Pydantic 请求/响应模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NearbyPOIRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description='中心纬度')
    lng: float = Field(..., ge=-180, le=180, description='中心经度')
    radius: float = Field(500, ge=0, description='搜索半径（米）')
    limit: int = Field(50, ge=1, le=500, description='返回数量上限')
    category: Optional[str] = Field(None, description='按类别筛选')


class POIResponse(BaseModel):
    id: int
    name: str
    category: str
    address: Optional[str]
    lng: float
    lat: float
    distance_m: float

    class Config:
        from_attributes = True


class NearbyPOIResponse(BaseModel):
    center: List[float]
    radius_m: float
    count: int
    results: List[POIResponse]


class ODMatrixRequest(BaseModel):
    origins: List[List[float]] = Field(..., description='起点坐标列表 [[lng, lat], ...]', min_length=1, max_length=100)
    destinations: List[List[float]] = Field(..., description='终点坐标列表 [[lng, lat], ...]', min_length=1, max_length=100)


class ODMatrixTaskResponse(BaseModel):
    task_id: str
    status: str


class ODMatrixResultResponse(BaseModel):
    task_id: str
    status: str
    matrix: Optional[List[List[float]]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
