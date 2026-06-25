from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_SHP_DIR = ROOT / "2023_Shp" / "Shp"
PROCESSED_DIR = ROOT / "data" / "processed"
WEB_DATA_DIR = ROOT / "web" / "data"


PYTHON_EXE_NOTE = (
    "Use the bundled Codex Python runtime or any Python 3.11+ environment with "
    "pyshp, h3, pandas, numpy, scipy, scikit-learn, matplotlib, and nbformat."
)


TRACK = {
    "id": "B",
    "name": "Entertainment & Nightlife",
    "question": (
        "Is nightlife truly walkable for residents, or designed for destination "
        "travel? Map the transit-nightlife coverage gap."
    ),
}


SHANGHAI_BOUNDS = {
    # Tightened to the Shanghai municipal POI extent in the supplied 2023 Gaode
    # point data. These bounds keep the demo fast while covering all districts.
    "min_lon": 120.86,
    "min_lat": 30.68,
    "max_lon": 122.24,
    "max_lat": 31.87,
}


GRID_STEP_M = 500
H3_RESOLUTION = 8


MODE_RADII_M = {
    "walk": 1200,
    "bike": 3500,
    "transit": 6000,
    "car": 10000,
}


MODE_WEIGHTING = {
    # Cars are retained for comparison, but not for the baseline score.
    "baseline_modes": ("walk", "bike"),
    "track_modes": ("walk", "bike", "transit"),
}


CATEGORY_RULES = [
    {
        "indicator": "food",
        "label": "Food and restaurants",
        "source_hint": "餐饮服务",
        "keywords": ["餐饮服务", "餐厅", "快餐", "小吃", "咖啡", "茶", "饭店", "饮品", "酒楼"],
    },
    {
        "indicator": "shopping",
        "label": "Daily shopping",
        "source_hint": "购物服务",
        "keywords": ["购物服务", "超市", "便利店", "综合市场", "农副产品", "商场"],
    },
    {
        "indicator": "healthcare",
        "label": "Healthcare",
        "source_hint": "医疗保健服务",
        "keywords": ["医疗保健服务", "医院", "卫生院", "诊所", "药房", "药店"],
    },
    {
        "indicator": "education_culture",
        "label": "Education and culture",
        "source_hint": "科教文化服务/风景名胜",
        "keywords": ["科教文化服务", "学校", "培训", "图书馆", "博物馆", "美术馆", "艺术", "文化"],
    },
    {
        "indicator": "parks_public",
        "label": "Parks and public amenities",
        "source_hint": "风景名胜/公共设施",
        "keywords": ["公园", "广场", "公共设施", "公共厕所", "城市广场", "旅游景点"],
    },
    {
        "indicator": "transit",
        "label": "Transit access",
        "source_hint": "交通设施服务",
        "keywords": ["地铁站", "地铁", "公交站", "公交车站", "轨道交通", "客运站", "火车站", "机场", "交通枢纽"],
    },
    {
        "indicator": "restaurants",
        "label": "Restaurant density",
        "source_hint": "餐饮服务",
        "keywords": ["餐饮服务", "餐厅", "快餐", "小吃", "咖啡", "茶", "饭店", "饮品", "酒楼"],
    },
    {
        "indicator": "bars_night",
        "label": "Bars, KTV, and nightlife",
        "source_hint": "餐饮服务/体育休闲服务",
        "keywords": ["酒吧", "KTV", "卡拉OK", "夜店", "娱乐场所", "剧本杀", "网吧", "夜宵", "烧烤"],
    },
    {
        "indicator": "culture_venues",
        "label": "Cinema, theatre, museum, gallery",
        "source_hint": "科教文化服务/体育休闲服务/风景名胜",
        "keywords": ["电影院", "影院", "剧院", "剧场", "演出", "音乐", "博物馆", "美术馆", "画廊", "艺术馆"],
    },
    {
        "indicator": "convenience_24h",
        "label": "Convenience stores",
        "source_hint": "购物服务",
        "keywords": ["便利店", "罗森", "全家", "7-ELEVEN", "711", "喜士多", "好德", "快客"],
    },
    {
        "indicator": "metro_late_proxy",
        "label": "Late transit proxy",
        "source_hint": "交通设施服务",
        "keywords": ["地铁站", "地铁", "轨道交通", "METRO", "SUBWAY"],
    },
]


BASELINE_INDICATORS = [
    "food",
    "shopping",
    "healthcare",
    "education_culture",
    "parks_public",
    "transit",
]


TRACK_INDICATORS = [
    "restaurants",
    "bars_night",
    "culture_venues",
    "convenience_24h",
    "metro_late_proxy",
]


BASELINE_WEIGHTS = {name: 1 / len(BASELINE_INDICATORS) for name in BASELINE_INDICATORS}

TRACK_WEIGHTS = {
    "restaurants": 0.30,
    "bars_night": 0.25,
    "culture_venues": 0.20,
    "convenience_24h": 0.15,
    "metro_late_proxy": 0.10,
}


DATA_SOURCES = [
    {
        "name": "Gaode/Amap POI shapefiles, Shanghai 2023",
        "file": "2023_Shp/Shp/*.shp",
        "used_for": "POI categories, district names, coordinates, and collection timestamps.",
        "limitations": "Point POI data only; no real network travel time, opening hours, or rating fields.",
    },
    {
        "name": "Derived 500 m analysis grid",
        "file": "data/processed/grid_cells.csv",
        "used_for": "Spatial sampling frame for 15-minute proximity scoring.",
        "limitations": "Grid is generated from POI extent rather than a municipal boundary polygon.",
    },
    {
        "name": "Derived 15-minute mode buffers",
        "file": "data/processed/grid_scores.csv",
        "used_for": "Walk, bike, transit, and car accessibility proxies using mode-specific radii.",
        "limitations": "Euclidean buffers approximate isochrones because no routing API key is included.",
    },
    {
        "name": "Uber H3 indexing",
        "file": "data/processed/shanghai_15mc_h3_track_b.geojson",
        "used_for": "Resolution-8 hex aggregation for the web map.",
        "limitations": "Aggregation uses grid centroids and mean scores within each H3 cell.",
    },
]
