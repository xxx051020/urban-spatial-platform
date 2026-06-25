"""POI 附近查询路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import NearbyPOIResponse, POIResponse

router = APIRouter(prefix="/api/poi", tags=["POI 查询"])


@router.get("/nearby", response_model=NearbyPOIResponse)
async def nearby_poi(
    lat: float = Query(..., ge=-90, le=90, description="中心纬度"),
    lng: float = Query(..., ge=-180, le=180, description="中心经度"),
    radius: float = Query(500, ge=0, description="搜索半径（米）"),
    limit: int = Query(50, ge=1, le=500, description="返回数量上限"),
    category: Optional[str] = Query(None, description="按类别筛选"),
    db: AsyncSession = Depends(get_db),
):
    """查询中心点附近指定半径内的 POI 兴趣点"""
    if category:
        sql = text("""
            SELECT id, name, category, address,
                   ST_X(geom::geometry) AS lng,
                   ST_Y(geom::geometry) AS lat,
                   ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance_m
            FROM pois
            WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
              AND category = :category
            ORDER BY distance_m
            LIMIT :limit
        """)
        params = {'lng': lng, 'lat': lat, 'radius': radius, 'category': category, 'limit': limit}
    else:
        sql = text("""
            SELECT id, name, category, address,
                   ST_X(geom::geometry) AS lng,
                   ST_Y(geom::geometry) AS lat,
                   ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance_m
            FROM pois
            WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
            ORDER BY distance_m
            LIMIT :limit
        """)
        params = {'lng': lng, 'lat': lat, 'radius': radius, 'limit': limit}

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    pois = [
        POIResponse(
            id=r['id'], name=r['name'], category=r['category'],
            address=r['address'], lng=r['lng'], lat=r['lat'],
            distance_m=round(r['distance_m'], 2)
        )
        for r in rows
    ]

    return NearbyPOIResponse(center=[lng, lat], radius_m=radius, count=len(pois), results=pois)


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取所有 POI 类别"""
    result = await db.execute(text('SELECT DISTINCT category FROM pois ORDER BY category'))
    return {'categories': [r[0] for r in result]}
