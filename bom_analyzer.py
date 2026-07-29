from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


COLUMN_ALIASES = {
    "部件名称": ["部件名称", "物料名称", "材料名称", "零部件名称", "item", "name"],
    "质量(kg)": ["质量(kg)", "质量", "重量(kg)", "重量", "mass", "weight"],
    "材料类型": ["材料类型", "材质", "类别", "material type", "category"],
    "供应商": ["供应商", "供应商名称", "supplier", "vendor"],
}


@dataclass
class DiagnosisResult:
    normalized_df: pd.DataFrame
    missing_items: List[str]
    recognized_columns: List[str]
    completeness: int
    confidence_level: str


def _find_column(columns, aliases):
    normalized = {str(column).strip().lower(): column for column in columns}
    for alias in aliases:
        key = alias.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def analyze_bom(df: pd.DataFrame) -> DiagnosisResult:
    if df.empty:
        return DiagnosisResult(
            normalized_df=df,
            missing_items=["BOM 文件没有数据行"],
            recognized_columns=[],
            completeness=0,
            confidence_level="E",
        )

    output = pd.DataFrame()
    recognized = []
    missing = []

    for standard_name, aliases in COLUMN_ALIASES.items():
        source = _find_column(df.columns, aliases)
        if source is None:
            output[standard_name] = pd.NA
            missing.append(f"缺少必要字段：{standard_name}")
        else:
            output[standard_name] = df[source]
            recognized.append(standard_name)

    if "部件名称" in output:
        empty = output["部件名称"].isna() | (output["部件名称"].astype(str).str.strip() == "")
        if empty.any():
            missing.append(f"有 {int(empty.sum())} 行缺少部件名称")

    if "质量(kg)" in output:
        numeric_mass = pd.to_numeric(output["质量(kg)"], errors="coerce")
        invalid = numeric_mass.isna()
        output["质量(kg)"] = numeric_mass
        if invalid.any():
            missing.append(f"有 {int(invalid.sum())} 行缺少有效质量数据")

    if "材料类型" in output:
        empty = output["材料类型"].isna() | (output["材料类型"].astype(str).str.strip() == "")
        if empty.any():
            missing.append(f"有 {int(empty.sum())} 行缺少材料类型")

    if "供应商" in output:
        empty = output["供应商"].isna() | (output["供应商"].astype(str).str.strip() == "")
        if empty.any():
            missing.append(f"有 {int(empty.sum())} 行缺少供应商信息")

    required_checks = 4
    field_score = len(recognized) / required_checks

    cell_total = max(len(output) * required_checks, 1)
    cell_present = int(output.notna().sum().sum())
    cell_score = cell_present / cell_total

    completeness = round((field_score * 0.6 + cell_score * 0.4) * 100)
    completeness = max(0, min(100, completeness))

    if completeness >= 90:
        confidence = "B"
    elif completeness >= 70:
        confidence = "C"
    elif completeness >= 40:
        confidence = "D"
    else:
        confidence = "E"

    if not missing:
        missing.append("当前演示字段未发现明显缺失，仍需人工复核排放因子来源和证明材料")

    return DiagnosisResult(
        normalized_df=output,
        missing_items=missing,
        recognized_columns=recognized,
        completeness=completeness,
        confidence_level=confidence,
    )
