from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Dict, List

import streamlit as st

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


def _get_ai_config() -> tuple[str | None, str, str]:
    """读取 Streamlit Secrets 中的大模型配置。"""
    try:
        api_key = str(st.secrets["AI_API_KEY"]).strip()
        base_url = str(st.secrets.get("AI_BASE_URL", "https://api.groq.com/openai/v1")).strip().rstrip("/")
        model = str(st.secrets.get("AI_MODEL", "openai/gpt-oss-120b")).strip()
        return api_key, base_url, model
    except Exception as exc:
        st.error(f"AI 配置读取失败：{type(exc).__name__}: {exc}")
        return None, "https://api.groq.com/openai/v1", "openai/gpt-oss-120b"

def _build_system_prompt(
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
    sources: List[dict],
) -> str:
    diagnosis_text = "尚未进行 BOM 诊断"
    if diagnosis:
        diagnosis_text = (
            f"完整度 {diagnosis.get('completeness', 0)}%；"
            f"可信度 {diagnosis.get('confidence_level', 'E')} 级；"
            f"缺失项：{', '.join(diagnosis.get('missing_items', [])) or '无'}"
        )

    kb_text = "\n".join(
        f"- {item.get('title', '')}（{item.get('code', '')}）：{item.get('summary', '')}"
        for item in sources
    ) or "- 当前没有检索到直接匹配的本地知识条目。"

    return f"""
你是“碳迹可循”平台的 AI 碳足迹智能体“小碳”。
你的目标是帮助企业用户快速理解产品碳足迹、欧盟电池法规、BOM 数据完整性、生命周期排放核算和报告准备。

【回答风格】
1. 使用中文，专业但易懂，避免堆砌术语。
2. 优先结合当前项目上下文回答，不要假装已经拿到系统中不存在的数据。
3. 对法规、认证和正式核算结论保持谨慎；演示系统中的计算结果必须明确属于“预核算/演示结果”。
4. 回答尽量控制在 250~500 字，适合网页演示；重要数字使用 Markdown 加粗。
5. 能给出下一步行动时，结尾给 2~3 条简洁建议。
6. 不要声称你访问了互联网。你只能使用下面给出的项目上下文和本地知识库摘要。

【当前项目】
- PSID：{project.get('psid', '未设置')}
- 企业：{project.get('company_name', '未设置')}
- 产品：{project.get('product_name', '未设置')}
- 电池类型：{project.get('battery_type', '未设置')}
- 标称电压：{project.get('voltage', '未设置')}
- 容量：{project.get('capacity_kwh', 0)} kWh
- 目标市场：{project.get('target_market', '未设置')}

【当前 BOM 诊断】
{diagnosis_text}

【当前预核算结果】
- 生命周期净排放：{carbon_total:.1f} kgCO2e/pack
- 单位容量排放：{unit_result:.2f} kgCO2e/kWh
- 结果性质：展示型预核算结果，不用于正式认证

【本次检索到的本地知识库】
{kb_text}
""".strip()


def _call_llm(
    prompt: str,
    history: List[dict],
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
    sources: List[dict],
) -> str | None:
    api_key, base_url, model = _get_ai_config()
    if not api_key:
        st.error("未读取到 AI_API_KEY。请检查 Streamlit Cloud -> App settings -> Secrets。")
        return None

    # 只带最近几轮，既保留连续对话，又避免演示时上下文越来越长。
    recent_history = []
    for message in history[-8:]:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and content:
            recent_history.append({"role": role, "content": content})

    messages = [
        {
            "role": "system",
            "content": _build_system_prompt(
                project=project,
                diagnosis=diagnosis,
                carbon_total=carbon_total,
                unit_result=unit_result,
                sources=sources,
            ),
        },
        *recent_history,
        {"role": "user", "content": prompt},
    ]

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.35,
            "max_completion_tokens": 700,
            "reasoning_effort": "low",
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "carbon-trace-agent/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = "无法读取错误响应体"
        st.error(f"AI API HTTP 错误：{exc.code} {exc.reason}")
        st.code(detail[:3000])
        return None
    except urllib.error.URLError as exc:
        st.error(f"AI API 网络连接失败：{exc.reason}")
        return None
    except TimeoutError:
        st.error("AI API 请求超时，请稍后重试。")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        st.error(f"AI API 返回格式异常：{type(exc).__name__}: {exc}")
        return None
    except Exception as exc:
        st.error(f"AI API 未知错误：{type(exc).__name__}: {exc}")
        return None


def _fallback_answer(
    intent: str,
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
    sources: List[dict],
) -> tuple[str, List[str], List[str]]:
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

当前项目还没有可用的 BOM 诊断结果。请先进入“数据上传与补齐”，上传 Excel 或 CSV 格式的 BOM。

#### 本次匹配的知识库

{_format_sources(sources)}
"""
            actions = ["进入数据上传与补齐"]
        else:
            missing = diagnosis.get("missing_items", [])
            missing_text = "\n".join(
                f"{index + 1}. {item}" for index, item in enumerate(missing)
            ) or "暂无明显缺失项。"
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

你也可以直接问我更开放的问题，例如“为什么供应商 PCF 数据会影响核算可信度？”
"""
        actions = ["法规适用性判断", "检查当前 BOM", "生成预核算摘要"]

    return answer.strip(), trace, actions


def run_agent(
    prompt: str,
    project: Dict,
    diagnosis: Dict | None,
    carbon_total: float,
    unit_result: float,
    history: List[dict] | None = None,
) -> Dict:
    intent = detect_intent(prompt)
    sources = search_knowledge(prompt)
    history = history or []

    ai_answer = _call_llm(
        prompt=prompt,
        history=history,
        project=project,
        diagnosis=diagnosis,
        carbon_total=carbon_total,
        unit_result=unit_result,
        sources=sources,
    )

    if ai_answer:
        trace = [
            "读取当前 PSID 项目上下文",
            "识别用户问题与任务意图",
            "检索本地法规与方法知识库",
            "调用大模型进行上下文推理",
            "生成面向企业用户的回答",
        ]
        actions = ["继续追问", "查看项目数据", "进入报告中心"]
        answer = ai_answer
        ai_enabled = True
    else:
        answer, trace, actions = _fallback_answer(
            intent=intent,
            project=project,
            diagnosis=diagnosis,
            carbon_total=carbon_total,
            unit_result=unit_result,
            sources=sources,
        )
        ai_enabled = False

    return {
        "intent": intent,
        "answer": answer,
        "trace": trace,
        "actions": actions,
        "sources": sources,
        "ai_enabled": ai_enabled,
    }
