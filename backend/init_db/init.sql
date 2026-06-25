-- ============================================================
-- 城市空间分析平台 — 数据库初始化脚本
-- 上海人民广场—陆家嘴区域 示例 POI 数据
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------------------------------------
-- POI 兴趣点表
-- ---------------------------------------
CREATE TABLE IF NOT EXISTS pois (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    category    VARCHAR(100) NOT NULL,
    address     VARCHAR(500),
    geom        GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pois_geom ON pois USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_pois_category ON pois (category);

-- ---------------------------------------
-- OD 矩阵任务表
-- ---------------------------------------
CREATE TABLE IF NOT EXISTS od_matrix_tasks (
    id          SERIAL PRIMARY KEY,
    task_id     VARCHAR(64) UNIQUE NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    result      TEXT,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_od_task_id ON od_matrix_tasks (task_id);

-- ---------------------------------------
-- 示例 POI 数据：上海核心区域
-- ---------------------------------------
INSERT INTO pois (name, category, address, geom) VALUES
-- 交通枢纽
('人民广场地铁站', '交通', '上海市黄浦区人民广场', ST_SetSRID(ST_MakePoint(121.4753, 31.2324), 4326)),
('陆家嘴地铁站',   '交通', '上海市浦东新区陆家嘴', ST_SetSRID(ST_MakePoint(121.5026, 31.2362), 4326)),
('南京东路地铁站', '交通', '上海市黄浦区南京东路', ST_SetSRID(ST_MakePoint(121.4847, 31.2370), 4326)),
('静安寺地铁站',   '交通', '上海市静安区静安寺', ST_SetSRID(ST_MakePoint(121.4453, 31.2246), 4326)),
('虹桥火车站',     '交通', '上海市闵行区虹桥枢纽', ST_SetSRID(ST_MakePoint(121.3200, 31.1942), 4326)),
('上海火车站',     '交通', '上海市静安区秣陵路303号', ST_SetSRID(ST_MakePoint(121.4557, 31.2498), 4326)),

-- 商业购物
('来福士广场',     '商业', '上海市黄浦区西藏中路268号', ST_SetSRID(ST_MakePoint(121.4771, 31.2338), 4326)),
('正大广场',       '商业', '上海市浦东新区陆家嘴西路168号', ST_SetSRID(ST_MakePoint(121.5005, 31.2373), 4326)),
('上海国金中心',   '商业', '上海市浦东新区世纪大道8号', ST_SetSRID(ST_MakePoint(121.5037, 31.2378), 4326)),
('新世界城',       '商业', '上海市黄浦区南京西路2-88号', ST_SetSRID(ST_MakePoint(121.4733, 31.2350), 4326)),
('恒隆广场',       '商业', '上海市静安区南京西路1266号', ST_SetSRID(ST_MakePoint(121.4513, 31.2279), 4326)),
('环贸iapm',       '商业', '上海市徐汇区淮海中路999号', ST_SetSRID(ST_MakePoint(121.4579, 31.2162), 4326)),

-- 餐饮美食
('南翔馒头店',     '餐饮', '上海市黄浦区豫园路85号', ST_SetSRID(ST_MakePoint(121.4911, 31.2283), 4326)),
('老正兴菜馆',     '餐饮', '上海市黄浦区福州路556号', ST_SetSRID(ST_MakePoint(121.4808, 31.2333), 4326)),
('绿波廊',         '餐饮', '上海市黄浦区豫园路115号', ST_SetSRID(ST_MakePoint(121.4915, 31.2280), 4326)),
('鼎泰丰(国金店)', '餐饮', '上海市浦东新区世纪大道8号', ST_SetSRID(ST_MakePoint(121.5037, 31.2378), 4326)),
('大董烤鸭店',     '餐饮', '上海市黄浦区淮海中路999号', ST_SetSRID(ST_MakePoint(121.4710, 31.2190), 4326)),

-- 教育文化
('上海博物馆',     '教育', '上海市黄浦区人民大道201号', ST_SetSRID(ST_MakePoint(121.4739, 31.2314), 4326)),
('上海图书馆',     '教育', '上海市徐汇区淮海中路1555号', ST_SetSRID(ST_MakePoint(121.4489, 31.2110), 4326)),
('上海大剧院',     '教育', '上海市黄浦区人民大道300号', ST_SetSRID(ST_MakePoint(121.4720, 31.2328), 4326)),
('东方艺术中心',   '教育', '上海市浦东新区丁香路425号', ST_SetSRID(ST_MakePoint(121.5358, 31.2235), 4326)),
('上海科技馆',     '教育', '上海市浦东新区世纪大道2000号', ST_SetSRID(ST_MakePoint(121.5423, 31.2194), 4326)),
('复旦大学(邯郸校区)', '教育', '上海市杨浦区邯郸路220号', ST_SetSRID(ST_MakePoint(121.5023, 31.2968), 4326)),
('上海交通大学(徐汇校区)', '教育', '上海市徐汇区华山路1954号', ST_SetSRID(ST_MakePoint(121.4355, 31.2011), 4326)),

-- 医院
('瑞金医院',       '医疗', '上海市黄浦区瑞金二路197号', ST_SetSRID(ST_MakePoint(121.4648, 31.2137), 4326)),
('华山医院',       '医疗', '上海市静安区乌鲁木齐中路12号', ST_SetSRID(ST_MakePoint(121.4435, 31.2192), 4326)),
('中山医院',       '医疗', '上海市徐汇区枫林路180号', ST_SetSRID(ST_MakePoint(121.4546, 31.1978), 4326)),
('仁济医院(东院)', '医疗', '上海市浦东新区浦建路160号', ST_SetSRID(ST_MakePoint(121.5215, 31.2080), 4326)),

-- 公园景点
('外滩',           '景点', '上海市黄浦区中山东一路', ST_SetSRID(ST_MakePoint(121.4905, 31.2397), 4326)),
('豫园',           '景点', '上海市黄浦区安仁街218号', ST_SetSRID(ST_MakePoint(121.4919, 31.2286), 4326)),
('东方明珠',       '景点', '上海市浦东新区世纪大道1号', ST_SetSRID(ST_MakePoint(121.4998, 31.2397), 4326)),
('上海中心大厦',   '景点', '上海市浦东新区陆家嘴银城中路501号', ST_SetSRID(ST_MakePoint(121.5056, 31.2355), 4326)),
('世纪公园',       '景点', '上海市浦东新区锦绣路1001号', ST_SetSRID(ST_MakePoint(121.5444, 31.2132), 4326)),
('人民公园',       '景点', '上海市黄浦区南京西路231号', ST_SetSRID(ST_MakePoint(121.4714, 31.2330), 4326));
