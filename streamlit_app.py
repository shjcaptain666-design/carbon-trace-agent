from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from agent import run_agent
from bom_analyzer import analyze_bom
from carbon_calculator import calculate_demo_results
from knowledge_base import KNOWLEDGE_BASE
from report_generator import build_markdown_report


st.set_page_config(
    page_title="碳迹可循 AI 智能体",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


CUSTOM_CSS = """
<style>
:root {
    --brand: #176b4d;
    --brand-light: #eaf5f0;
    --border: #dfe9e4;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    border-right: 1px solid var(--border);
}

.agent-title {
    padding: 1.1rem 1.2rem;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: linear-gradient(135deg, #f7fcf9, #edf8f3);
    margin-bottom: 1rem;
}

.agent-title h1 {
    margin: 0;
    color: var(--brand);
    font-size: 2rem;
}

.agent-title p {
    margin: .35rem 0 0;
    color: #52645c;
}

.status-card {
    padding: .8rem 1rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: white;
}

.small-muted {
    color: #6f7e77;
    font-size: .88rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


DEFAULT_PROJECT = {
    "psid": "PSID-DEMO-0001",
    "company_name": "某低压储能电池企业",
    "product_name": "5.12kWh 低压 LFP 储能电池",
    "battery_type": "固定式低压 LFP 储能电池",
    "voltage": "51.2V",
    "capacity_kwh": 5.12,
    "target_market": "欧盟",
}

DEFAULT_TASKS = pd.DataFrame(
    [
        {
            "模块": "原材料",
            "缺失数据": "电芯供应商名称",
            "责任方": "企业采购部门",
            "优先级": "高",
            "状态": "待补充",
        },
        {
            "模块": "原材料",
            "缺失数据": "供应商 PCF/EPD 文件",
            "责任方": "供应商",
            "优先级": "高",
            "状态": "待补充",
        },
        {
            "模块": "生产制造",
            "缺失数据": "产线用电量",
            "责任方": "企业生产部门",
            "优先级": "高",
            "状态": "待补充",
        },
    ]
)


def initialize_state():
    defaults = {
        "project": DEFAULT_PROJECT.copy(),
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "你好，我是“碳迹可循”AI 碳足迹智能体。"
                    "我可以协助法规适用性判断、BOM 数据诊断、预核算展示和报告整理。"
                ),
            }
        ],
        "diagnosis": None,
        "bom_df": None,
        "tasks": DEFAULT_TASKS.copy(),
        "last_trace": [],
        "last_sources": [],
        "current_page": "智能体工作台",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(page: str):
    st.session_state.current_page = page


def progress_from_tasks(tasks: pd.DataFrame) -> int:
    if tasks.empty:
        return 0
    completed = int((tasks["状态"] == "已完成").sum())
    return round(completed / len(tasks) * 100)


def add_tasks_from_diagnosis():
    diagnosis = st.session_state.diagnosis
    if not diagnosis:
        st.warning("请先上传并诊断 BOM。")
        return

    existing = set(st.session_state.tasks["缺失数据"].astype(str).tolist())
    new_rows = []

    for item in diagnosis["missing_items"]:
        if item not in existing:
            new_rows.append(
                {
                    "模块": "BOM 数据",
                    "缺失数据": item,
                    "责任方": "企业或供应商",
                    "优先级": "高" if "质量" in item or "字段" in item else "中",
                    "状态": "待补充",
                }
            )

    if new_rows:
        st.session_state.tasks = pd.concat(
            [st.session_state.tasks, pd.DataFrame(new_rows)],
            ignore_index=True,
        )
        st.success(f"已新增 {len(new_rows)} 项补齐任务。")
    else:
        st.info("相同任务已经存在，无需重复生成。")


def render_project_banner():
    project = st.session_state.project
    task_progress = progress_from_tasks(st.session_state.tasks)
    data_complete = (
        st.session_state.diagnosis["completeness"]
        if st.session_state.diagnosis
        else 0
    )

    st.markdown(
        f"""
<div class="agent-title">
    <h1>🌿 碳迹可循 AI 碳足迹智能体</h1>
    <p>当前项目：{project["psid"]} · {project["product_name"]}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("目标市场", project["target_market"])
    c2.metric("名义容量", f'{project["capacity_kwh"]:.2f} kWh')
    c3.metric("BOM 完整度", f"{data_complete}%")
    c4.metric("任务完成度", f"{task_progress}%")


initialize_state()

with st.sidebar:
    st.title("碳迹可循")
    st.caption("基于知识库的 AI 碳足迹建模智能体")

    role = st.selectbox(
        "演示角色",
        ["企业客户", "供应商", "认证协同方", "平台后台"],
    )

    pages = [
        "智能体工作台",
        "项目中心",
        "数据中心",
        "缺失任务",
        "碳足迹结果",
        "报告中心",
        "知识库",
    ]

    selected_page = st.radio(
        "功能导航",
        pages,
        index=pages.index(st.session_state.current_page),
    )
    st.session_state.current_page = selected_page

    st.divider()
    st.caption(f"当前角色：{role}")
    st.caption(f'当前项目：{st.session_state.project["psid"]}')
    st.warning("本系统为展示型原型，所有数据均为模拟数据。")

render_project_banner()
page = st.session_state.current_page
project = st.session_state.project
results, carbon_total, unit_result = calculate_demo_results(project["capacity_kwh"])


if page == "智能体工作台":
    left, right = st.columns([2.1, 1], gap="large")

    with left:
        st.subheader("AI 对话与任务执行")

        prompt_cols = st.columns(3)
        if prompt_cols[0].button("法规适用性判断", use_container_width=True):
            st.session_state.pending_prompt = "请判断当前产品是否适用欧盟电池碳足迹要求。"
        if prompt_cols[1].button("检查当前 BOM", use_container_width=True):
            st.session_state.pending_prompt = "请检查当前 BOM 的数据完整性。"
        if prompt_cols[2].button("生成预核算摘要", use_container_width=True):
            st.session_state.pending_prompt = "请生成当前项目的碳足迹预核算摘要。"

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        typed_prompt = st.chat_input("请输入你希望智能体完成的任务")
        prompt = typed_prompt or st.session_state.pop("pending_prompt", None)

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            agent_result = run_agent(
                prompt=prompt,
                project=project,
                diagnosis=st.session_state.diagnosis,
                carbon_total=carbon_total,
                unit_result=unit_result,
            )

            st.session_state.last_trace = agent_result["trace"]
            st.session_state.last_sources = agent_result["sources"]
            st.session_state.messages.append(
                {"role": "assistant", "content": agent_result["answer"]}
            )

            with st.chat_message("assistant"):
                st.markdown(agent_result["answer"])

            if agent_result["intent"] == "diagnosis" and st.session_state.diagnosis:
                if st.button("将诊断结果生成补齐任务", type="primary"):
                    add_tasks_from_diagnosis()

    with right:
        st.subheader("智能体执行轨迹")
        if st.session_state.last_trace:
            with st.status("最近一次任务已完成", state="complete", expanded=True):
                for index, step in enumerate(st.session_state.last_trace, start=1):
                    st.write(f"{index}. {step}")
        else:
            st.info("发送任务后，这里会显示知识库检索和数据处理过程。")

        st.subheader("本次知识库依据")
        if st.session_state.last_sources:
            for source in st.session_state.last_sources:
                with st.expander(source["title"]):
                    st.caption(source["code"])
                    st.write(source["summary"])
        else:
            st.caption("尚未执行知识库检索。")

        st.subheader("当前项目动作")
        if st.button("进入数据中心", use_container_width=True):
            go_to("数据中心")
            st.rerun()
        if st.button("查看缺失任务", use_container_width=True):
            go_to("缺失任务")
            st.rerun()
        if st.button("查看预核算结果", use_container_width=True):
            go_to("碳足迹结果")
            st.rerun()


elif page == "项目中心":
    st.subheader("PSID 项目资料")

    with st.form("project_form"):
        company_name = st.text_input("企业名称", project["company_name"])
        product_name = st.text_input("产品名称", project["product_name"])

        c1, c2 = st.columns(2)
        battery_type = c1.text_input("产品类型", project["battery_type"])
        voltage = c2.text_input("标称电压", project["voltage"])

        c3, c4 = st.columns(2)
        capacity = c3.number_input(
            "名义容量（kWh）",
            min_value=0.1,
            value=float(project["capacity_kwh"]),
            step=0.1,
        )
        target_market = c4.selectbox(
            "目标市场",
            ["欧盟", "英国", "北美", "其他"],
            index=["欧盟", "英国", "北美", "其他"].index(project["target_market"]),
        )

        if st.form_submit_button("保存项目资料", type="primary"):
            project.update(
                {
                    "company_name": company_name,
                    "product_name": product_name,
                    "battery_type": battery_type,
                    "voltage": voltage,
                    "capacity_kwh": capacity,
                    "target_market": target_market,
                }
            )
            st.success("项目资料已保存。")

    st.info(
        "第一版使用固定 PSID 进行演示。正式系统中，可由后端为每个产品项目生成唯一 PSID。"
    )


elif page == "数据中心":
    st.subheader("BOM 上传与智能诊断")
    st.write(
        "上传 Excel 或 CSV。推荐先使用项目 data 文件夹中的 sample_bom.xlsx 进行测试。"
    )

    uploaded = st.file_uploader(
        "选择 BOM 文件",
        type=["xlsx", "csv"],
        accept_multiple_files=False,
    )

    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            st.session_state.bom_df = df
            st.success(f"文件读取成功：{len(df)} 行，{len(df.columns)} 列。")
            st.dataframe(df.head(30), use_container_width=True, hide_index=True)

            if st.button("启动智能诊断", type="primary"):
                diagnosis_result = analyze_bom(df)
                st.session_state.diagnosis = {
                    "missing_items": diagnosis_result.missing_items,
                    "recognized_columns": diagnosis_result.recognized_columns,
                    "completeness": diagnosis_result.completeness,
                    "confidence_level": diagnosis_result.confidence_level,
                }

                project_dir = UPLOAD_DIR / project["psid"]
                project_dir.mkdir(parents=True, exist_ok=True)
                safe_name = Path(uploaded.name).name
                (project_dir / safe_name).write_bytes(uploaded.getbuffer())

                st.success("诊断完成，文件已保存到当前项目目录。")
                st.rerun()

        except Exception as exc:
            st.error(f"文件读取失败：{exc}")

    if st.session_state.diagnosis:
        diagnosis = st.session_state.diagnosis
        st.divider()
        st.subheader("诊断结果")

        c1, c2 = st.columns(2)
        c1.metric("BOM 完整度", f'{diagnosis["completeness"]}%')
        c2.metric("数据可信度", f'{diagnosis["confidence_level"]} 级')

        st.write("**已识别字段**")
        st.write("、".join(diagnosis["recognized_columns"]) or "暂无")

        st.write("**主要缺失项**")
        for item in diagnosis["missing_items"]:
            st.write(f"- {item}")

        if st.button("生成补齐任务", type="primary"):
            add_tasks_from_diagnosis()


elif page == "缺失任务":
    st.subheader("缺失数据补齐任务")

    edited_tasks = st.data_editor(
        st.session_state.tasks,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "状态": st.column_config.SelectboxColumn(
                "状态",
                options=["待补充", "审核中", "已完成"],
            ),
            "优先级": st.column_config.SelectboxColumn(
                "优先级",
                options=["高", "中", "低"],
            ),
        },
        key="task_editor",
    )

    if st.button("保存任务状态", type="primary"):
        st.session_state.tasks = edited_tasks
        st.success("任务状态已保存。")

    progress = progress_from_tasks(edited_tasks)
    st.progress(progress / 100, text=f"任务完成度：{progress}%")


elif page == "碳足迹结果":
    st.subheader("生命周期样板预核算")

    c1, c2, c3 = st.columns(3)
    c1.metric("生命周期净排放", f"{carbon_total:.1f} kgCO₂e/pack")
    c2.metric("单位容量排放", f"{unit_result:.2f} kgCO₂e/kWh")
    c3.metric("结果可信度", "C 级（演示）")

    chart_data = results.set_index("生命周期模块")[["kgCO2e/pack"]]
    st.bar_chart(chart_data, use_container_width=True)
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.warning(
        "当前为计划书样板值。正式产品需建立排放因子库、计算规则和人工复核机制。"
    )


elif page == "报告中心":
    st.subheader("报告预览与下载")

    report = build_markdown_report(
        project=project,
        diagnosis=st.session_state.diagnosis,
        carbon_total=carbon_total,
        unit_result=unit_result,
    )

    st.markdown(report)
    st.download_button(
        "下载 Markdown 项目摘要",
        data=report.encode("utf-8"),
        file_name=f'{project["psid"]}_项目摘要.md',
        mime="text/markdown",
        type="primary",
    )


elif page == "知识库":
    st.subheader("演示知识库")
    st.write(
        "第一版使用结构化 Python 字典模拟知识库，展示智能体检索依据。后期可升级为法规文档检索与向量知识库。"
    )

    for item in KNOWLEDGE_BASE.values():
        with st.expander(f'{item["title"]} · {item["code"]}'):
            st.write(item["summary"])
            st.caption("关键词：" + "、".join(item["keywords"]))
