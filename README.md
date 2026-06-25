# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# 城市空间分析平台 — 完整技术文档
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

---

## 1. 项目概览

本平台是一个基于 **Docker 容器化** 部署的线上城市空间分析系统，提供两大核心能力：

| 能力 | 说明 |
|------|------|
| **POI 附近查询** | 给定经纬度中心点和半径，快速检索范围内兴趣点（6大类别） |
| **异步 OD 矩阵** | 提交多组起点-终点坐标，后台 Celery 异步计算球面距离矩阵 |

技术栈：FastAPI + PostGIS + Celery + Redis + Leaflet + Docker Compose

---

## 2. 项目目录结构

`
urban-spatial-platform/
├── docker-compose.yml              # Docker 四服务编排（核心入口）
├── backend/
│   ├── Dockerfile                  # 后端镜像构建文件
│   ├── requirements.txt            # Python 依赖清单
│   ├── init_db/
│   │   └── init.sql                # PostgreSQL 初始化（建表 + 33条示例POI）
│   └── app/
│       ├── main.py                 # FastAPI 入口 + 生命周期管理
│       ├── config.py               # 环境变量 → 配置常量
│       ├── database.py             # SQLAlchemy 异步引擎 + 会话工厂
│       ├── models.py               # ORM 模型（POI表 + OD任务表）
│       ├── schemas.py              # Pydantic 请求/响应校验模型
│       ├── routers/
│       │   ├── poi.py              # POI 附近查询路由
│       │   └── od_matrix.py        # OD 矩阵路由
│       ├── tasks/
│       │   └── od_tasks.py         # Celery Worker（Haversine 距离计算）
│       └── static/
│           └── index.html          # Leaflet 交互式地图前端
`

---

## 3. 四大容器服务详解

### 3.1 Redis（消息中间件）
- 镜像：redis:7-alpine (~30MB)
- 端口：6379
- 角色：Celery 的 **Broker（消息队列）** 和 **Result Backend（结果存储）**
- 流程：FastAPI → 投递任务到 Redis 队列 → Celery Worker 拉取执行 → 结果写回 Redis

### 3.2 PostGIS（空间数据库）
- 镜像：postgis/postgis:16-3.4
- 端口：5432
- 数据库：urban_spatial / 用户：spatial_user / 密码：spatial_pass
- 数据持久化：pgdata 卷挂载到 /var/lib/postgresql/data
- 自动初始化：首次启动执行 init_db/init.sql（建表 + 插入示例数据）
- 健康检查：pg_isready 命令每 5 秒检测，确保依赖服务在数据库就绪后才启动

### 3.3 Celery Worker（异步任务处理器）
- 构建：同 backend/Dockerfile
- 命令：celery -A app.tasks.od_tasks worker --loglevel=info --concurrency=2
- 并发：同时处理最多 2 个任务
- 依赖：等待 PostGIS healthy + Redis started
- 作用：独立进程执行 CPU 密集型 OD 矩阵计算，不阻塞 Web 请求

### 3.4 FastAPI（Web 服务器）
- 构建：同 backend/Dockerfile
- 命令：uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
- 端口映射：8000:8000
- --reload：开发模式代码热重载（生产应去掉）

---

## 4. 启动流程（完整顺序）

### Docker Compose 启动链
`
docker compose up -d
    │
    ├─ Step 1: Redis 启动（无依赖）
    ├─ Step 2: PostGIS 启动
    │     └─ 首次启动 → 自动执行 init.sql
    │          ├─ CREATE EXTENSION postgis
    │          ├─ CREATE TABLE pois + 空间索引
    │          ├─ CREATE TABLE od_matrix_tasks + 索引
    │          └─ INSERT 33 条上海示例 POI
    │     └─ pg_isready 检测通过 → 标记 healthy
    │
    ├─ Step 3: Celery Worker 启动（等待 PostGIS healthy + Redis）
    └─ Step 4: FastAPI 启动（等待 PostGIS healthy + Redis）
          │
          └─ lifespan() 启动回调：
               ├─ engine.begin() → Base.metadata.create_all（幂等建表）
               ├─ 注册路由：/api/poi/*  + /api/od-matrix/*
               ├─ 挂载静态文件：/static → app/static/
               ├─ 注册首页：GET / → index.html
               └─ yield → 应用就绪
`

### 访问地址
| 服务 | 地址 |
|------|------|
| 地图前端 | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 5. POI 附近查询 — 完整调用链

### API
GET /api/poi/nearby?lat=31.2324&lng=121.4753&radius=3000&limit=50&category=餐饮

### 后端处理流程（routers/poi.py）
`
用户请求
  │
  ▼
FastAPI Query 参数校验：lat(-90~90)  lng(-180~180)  radius>=0  limit(1~500)
  │
  ▼
执行原生 SQL：
  SELECT id, name, category, address,
         ST_X(geom::geometry) AS lng,
         ST_Y(geom::geometry) AS lat,
         ST_Distance(geom::geography,
           ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
         ) AS distance_m
  FROM pois
  WHERE ST_DWithin(geom::geography,
          ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
    AND (:category IS NULL OR category = :category)
  ORDER BY distance_m
  LIMIT :limit
  │
  ▼
PostGIS 内部执行：
  1. ST_MakePoint(lng, lat)        → 创建几何点
  2. ST_SetSRID(..., 4326)         → 标记 WGS84 坐标系
  3. ::geography 转换               → 切换到球面坐标系（精确米制距离）
  4. ST_DWithin(...)               → 利用 GiST 空间索引快速筛选
  5. ST_Distance(...)              → 精确计算球面距离（米）
  6. ORDER BY + LIMIT              → 排序截断
  │
  ▼
返回 JSON → 前端渲染 Marker + 结果列表
`

### 涉及的空间概念
| 概念 | 说明 |
|------|------|
| SRID 4326 | WGS 1984 坐标系（GPS标准） |
| Geometry vs Geography | 平面几何(度) vs 球面几何(米) |
| ST_DWithin | 空间距离筛选，利用 GiST 索引 |
| GiST 索引 | PostgreSQL 通用搜索树，空间查询加速 |

---

## 6. OD 矩阵计算 — 完整调用链

### API
POST /api/od-matrix/
Body: { "origins": [[lng,lat],...], "destinations": [[lng,lat],...] }

### 异步处理流程
`
POST 请求
  │
  ▼
routers/od_matrix.py → create_od_matrix_task()
  │
  │  compute_od_matrix.delay(origins, destinations)
  │  → 任务投递到 Redis 队列
  │  → 立即返回 { task_id, status: "pending" }
  │
  ▼
Celery Worker 从 Redis 拉取任务
  │
  ▼
tasks/od_tasks.py → compute_od_matrix()
  │
  │  for o in origins:
  │    for d in destinations:
  │      _haversine(o.lng, o.lat, d.lng, d.lat)
  │
  ▼
_haversine 公式：
  a = sin^2(Delta_phi/2) + cos(phi1)*cos(phi2)*sin^2(Delta_lambda/2)
  c = 2 * atan2(sqrt(a), sqrt(1-a))
  d = 6371000 * c     （地球半径 6371km x 弧度）
  │
  ▼
结果写入 Redis → 前端轮询获取
`

### 前端轮询（index.html）
`
每隔 1.5 秒 GET /api/od-matrix/{task_id}
  ├─ status=running → 继续等待
  ├─ status=completed → 展示矩阵表格 + 彩色OD连线
  └─ 60次超时 → 提示刷新
`

---

## 7. 数据库初始化脚本（init.sql）

### 执行时机
PostGIS 容器首次创建时，Docker 自动将 init_db/ 目录映射到容器的 /docker-entrypoint-initdb.d/，PostgreSQL 启动后按文件名顺序执行。

### 脚本步骤
1. **CREATE EXTENSION postgis** — 启用 PostGIS 扩展
2. **建 POI 表** — id, name, category, address, geom (POINT, 4326)
3. **建空间索引** — GiST 索引加速 ST_DWithin
4. **建 OD 任务表** — task_id, status, result, created_at, updated_at
5. **插入示例数据** — 上海核心区 33 个 POI

### 示例 POI 覆盖
| 类别 | 数量 | 示例 |
|------|------|------|
| 交通 | 6 | 人民广场站、陆家嘴站、虹桥火车站... |
| 商业 | 6 | 来福士、正大广场、国金中心、恒隆... |
| 餐饮 | 5 | 南翔馒头店、绿波廊、鼎泰丰... |
| 教育 | 7 | 上海博物馆、复旦、交大... |
| 医疗 | 4 | 瑞金医院、华山医院、中山医院... |
| 景点 | 5 | 外滩、豫园、东方明珠、上海中心... |

---

## 8. 前端页面（index.html）

### 技术选型
- Leaflet.js 1.9.4（从 CDN 加载，零构建）
- OpenStreetMap 免费底图
- 纯单文件 HTML/CSS/JS

### 页面布局
`
┌────────────────────────────────────────────────────┐
│ 平台标题                    [API文档]               │
├──────────────────────┬─────────────────────────────┤
│                      │  POI 查询面板                │
│    Leaflet 地图       │  - 经纬度输入(点击地图填充)   │
│    (OSM 底图)         │  - 半径/类别/数量设置        │
│                      │  - 搜索结果列表              │
│  蓝色标记=搜索中心     ├─────────────────────────────┤
│  Marker=POI结果       │  OD 矩阵面板                │
│  绿点=OD起点          │  - 添加起终点(点击地图)      │
│  红点=OD终点          │  - 提交计算 → 轮询结果       │
│  彩色虚线=OD连线       │  - 矩阵表格 + 距离着色连线   │
└──────────────────────┴─────────────────────────────┘
`

### 交互逻辑
- **POI 查询**：点击地图 → 自动填经纬度 → 搜索 → 列表+标记展示 → 点击列表项缩放定位
- **OD 矩阵**：按钮切换模式 → 点击地图添加 → 提交 → 轮询 → 表格+着色连线
- **连线颜色**：<2km 绿色 / 2-5km 橙色 / >5km 红色

---

## 9. 配置项说明

所有配置通过 docker-compose.yml 的 environment 注入，各模块用 os.getenv() 读取：

| 环境变量 | 默认值 | 使用者 |
|----------|--------|--------|
| DATABASE_URL | postgresql+asyncpg://spatial_user:spatial_pass@postgis:5432/urban_spatial | FastAPI, Celery |
| CELERY_BROKER_URL | redis://redis:6379/0 | Celery |
| CELERY_RESULT_BACKEND | redis://redis:6379/0 | Celery |

---

## 10. 运维命令速查

`ash
# 启动
docker compose up -d

# 重新构建并启动（修改代码后）
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f fastapi
docker compose logs -f celery_worker

# 重启某服务
docker compose restart fastapi

# 停止
docker compose down

# 完全重置（清空数据库）
docker compose down -v && docker compose up -d
`

---

> 版本 1.0 | 2026-06-05
