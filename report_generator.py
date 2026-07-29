from __future__ import annotations

from datetime import datetime
from typing import Dict


def build_markdown_report(
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
) -> str:
    if diagnosis:
        completeness = diagnosis.get("completeness", 0)
        confidence = diagnosis.get("confidence_level", "E")
        missing_items = diagnosis.get("missing_items", [])
    else:
        completeness = 0
        confidence = "E"
        missing_items = ["尚未上传并诊断 BOM"]

    missing_text = "\n".join(f"- {item}" for item in missing_items)

    return f"""# 碳迹可循项目摘要

生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}

## 一、项目基础信息

- PSID：{project["psid"]}
- 企业名称：{project["company_name"]}
- 产品名称：{project["product_name"]}
- 产品类型：{project["battery_type"]}
- 标称电压：{project["voltage"]}
- 名义容量：{project["capacity_kwh"]} kWh
- 目标市场：{project["target_market"]}

## 二、数据诊断

- BOM 完整度：{completeness}%
- 数据可信度：{confidence} 级

### 主要缺失项

{missing_text}

## 三、样板碳足迹预核算

- 生命周期净排放：{carbon_total:.1f} kgCO₂e/pack
- 单位容量排放：{unit_result:.2f} kgCO₂e/kWh

## 四、建议动作

1. 优先补齐高敏感度的材料质量和供应商数据；
2. 保存采购单、规格书、能耗台账与物流单据；
3. 对排放因子来源和生命周期边界进行人工复核；
4. 在正式认证前由具备资质的机构开展核验。

## 五、服务边界

本报告仅用于“碳迹可循”智能体原型展示和认证前准备演示，
不替代第三方认证机构，不承诺正式认证或市场准入结果。
"""
