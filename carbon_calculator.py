from __future__ import annotations

import pandas as pd


DEFAULT_RESULTS = pd.DataFrame(
    [
        {"生命周期模块": "原材料获取", "kgCO2e/pack": 260.2, "说明": "样板 BOM 与材料因子"},
        {"生命周期模块": "生产制造", "kgCO2e/pack": 133.1, "说明": "中国制造基准情景"},
        {"生命周期模块": "运输分销", "kgCO2e/pack": 12.3, "说明": "中国至欧盟模拟路径"},
        {"生命周期模块": "回收处置", "kgCO2e/pack": -34.3, "说明": "回收信用模拟值"},
    ]
)


def calculate_demo_results(capacity_kwh: float):
    capacity = max(float(capacity_kwh), 0.1)
    results = DEFAULT_RESULTS.copy()
    total = float(results["kgCO2e/pack"].sum())
    unit_result = total / capacity
    return results, total, unit_result
