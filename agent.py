from __future__ import annotations

from typing import Dict, List

from knowledge_base import search_knowledge


def detect_intent(prompt: str) -> str:
    text = prompt.strip().lower()

    if any(word in text for word in ["bom", "缺失", "检查", "完整", "诊断", "数据"]):
        return "diagnosis"
    if any(word in text for word in ["碳足迹", "核算", "排放", "结果", "计算"]):
        return "calculation"
    if any(word in text for word in ["报告", "材料", "摘要", "下载"]):
        return "report"
    if any(word in text for word in ["法规", "欧盟", "适用", "认证", "护照"]):
        return "regulation"
    return "help"


def _format_sources(sources: List[dict]) -> str:
    lines = []
    for source in sources:
        lines.append(f"- **{source['title']}（{source['code']}）**：{source['summary']}")
    return "\n".join(lines)


def run_agent(
    prompt: str,
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
) -> Dict:
    intent = detect_intent(prompt)
    sources = search_knowledge(prompt)

    trace = [
        "读取当前 PSID 项目上下文",
        "识别用户任务意图",
        "检索法规与方法知识库",
    ]

    if intent == "regulation":
        trace.extend(["匹配产品容量与目标市场", "形成适用性初步判断"])
        capacity = float(project.get("capacity_kwh", 0))
        target_market = project.get("target_market", "欧盟")
        applicable = capacity > 2 and target_market == "欧盟"

        if applicable:
            conclusion = (
                f"当前项目产品容量为 **{capacity:.2f} kWh**，目标市场为 **{target_market}**。"
                "按本演示规则，它属于需要重点开展欧盟电池碳足迹合规准备的项目。"
            )
        else:
            conclusion = (
                "根据当前项目数据，暂不能直接判断为重点适用项目。"
                "请进一步确认容量、产品类型、用途和出口目的地。"
            )

        answer = f"""
### 适用性初步判断

{conclusion}

**建议下一步**

1. 上传产品规格书和 BOM；
2. 完成生产能耗、物流与供应商资料检查；
3. 由人工人员复核正式法规口径。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
        actions = ["进入资料上传", "开始数据诊断"]

    elif intent == "diagnosis":
        trace.extend(["读取当前 BOM 诊断结果", "汇总缺失项", "生成补齐建议"])

        if diagnosis is None:
            answer = f"""
### 数据诊断尚未开始

当前项目还没有可用的 BOM 诊断结果。请先进入“数据中心”，上传 Excel 或 CSV 格式的 BOM。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
            actions = ["进入数据中心"]
        else:
            missing = diagnosis.get("missing_items", [])
            missing_text = "\n".join(
                f"{index + 1}. {item}" for index, item in enumerate(missing)
            )
            answer = f"""
### 数据完整性诊断

- 当前完整度：**{diagnosis.get('completeness', 0)}%**
- 数据可信度：**{diagnosis.get('confidence_level', 'E')} 级**
- 已识别标准字段：{", ".join(diagnosis.get("recognized_columns", [])) or "暂无"}

**主要问题**

{missing_text}

**智能体建议**

优先补齐质量、材料类型和供应商信息；同时保留采购单、规格书、PCF/EPD 或企业台账作为数据证明。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
            actions = ["生成补齐任务", "查看缺失任务"]

    elif intent == "calculation":
        trace.extend(["读取生命周期样板参数", "汇总四阶段结果", "计算单位容量结果"])
        answer = f"""
### 碳足迹预核算摘要

- 生命周期净排放：**{carbon_total:.1f} kgCO₂e/pack**
- 单位容量排放：**{unit_result:.2f} kgCO₂e/kWh**
- 结果性质：**样板演示结果**

当前结果用于展示原材料、生产制造、运输分销和回收处置四个模块的计算流程，不用于正式认证。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
        actions = ["查看碳足迹结果", "生成报告摘要"]

    elif intent == "report":
        trace.extend(["读取项目状态", "整理诊断与测算摘要", "准备报告内容"])
        answer = f"""
### 报告生成准备完成

智能体已经整理：

- 当前 PSID 和产品基础信息；
- BOM 数据完整度与缺失项；
- 生命周期样板预核算结果；
- 服务边界和人工复核提示。

请进入“报告中心”预览并下载项目摘要。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
        actions = ["进入报告中心"]

    else:
        trace.append("返回可执行能力清单")
        answer = """
### 我可以协助完成以下任务

- 判断产品是否需要开展欧盟碳足迹合规准备；
- 检查 BOM 数据完整性；
- 生成缺失数据补齐任务；
- 展示生命周期预核算结果；
- 整理项目报告摘要。

你可以输入：

> 请判断当前产品是否适用欧盟电池碳足迹要求。

或者：

> 请检查我上传的 BOM 是否完整。
"""
        actions = ["法规适用性判断", "检查当前 BOM", "生成预核算摘要"]

    return {
        "intent": intent,
        "answer": answer.strip(),
        "trace": trace,
        "actions": actions,
        "sources": sources,
    }
