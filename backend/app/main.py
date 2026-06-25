"""城市空间分析平台 — FastAPI 主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routers import poi, od_matrix


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title='城市空间分析平台',
    description='POI 附近查询 · 异步 OD 矩阵计算 · Leaflet 可视化',
    version='1.0.0',
    lifespan=lifespan,
)

app.include_router(poi.router)
app.include_router(od_matrix.router)
app.mount('/static', StaticFiles(directory='app/static'), name='static')


@app.get('/')
async def index():
    return FileResponse('app/static/index.html')
