from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from agent import run_agent
from bom_analyzer import analyze_bom
from carbon_calculator import calculate_demo_results
from knowledge_base import KNOWLEDGE_BASE
from report_generator import build_markdown_report
import secrets
from datetime import datetime


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
    --brand-dark: #0f4a35;
    --brand-soft: #eaf5f0;
    --brand-softer: #f6fbf8;
    --text-main: #22342c;
    --text-muted: #6b7d74;
    --border: #dfe9e4;
    --warning-bg: #fff8e6;
    --danger-bg: #fff1f0;
    --card-shadow: 0 10px 28px rgba(23, 107, 77, 0.08);
}

/* 页面整体 */
.block-container {
    padding-top: 1.3rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f4fbf7 0%, #ffffff 100%);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1 {
    color: var(--brand-dark);
    font-size: 1.45rem;
    font-weight: 800;
}

[data-testid="stSidebar"] .stCaption {
    color: var(--text-muted);
}

/* 主标题卡片 */
.agent-title {
    position: relative;
    padding: 1.4rem 1.6rem;
    border: 1px solid var(--border);
    border-radius: 22px;
    background:
        radial-gradient(circle at top right, rgba(23,107,77,0.16), transparent 32%),
        linear-gradient(135deg, #f8fdfb 0%, #edf8f3 100%);
    box-shadow: var(--card-shadow);
    margin-bottom: 1.2rem;
    overflow: hidden;
}

.agent-title::after {
    content: "";
    position: absolute;
    width: 160px;
    height: 160px;
    right: -50px;
    bottom: -70px;
    border-radius: 50%;
    background: rgba(23, 107, 77, 0.08);
}

.agent-title h1 {
    margin: 0;
    color: var(--brand-dark);
    font-size: 2.05rem;
    font-weight: 850;
    letter-spacing: -0.02em;
}

.agent-title p {
    margin: .45rem 0 0;
    color: var(--text-muted);
    font-size: 1rem;
}

/* 通用卡片 */
.status-card {
    padding: 1rem 1.1rem;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(20, 70, 50, 0.05);
}

/* 小字说明 */
.small-muted {
    color: var(--text-muted);
    font-size: .88rem;
}

/* Streamlit 指标卡片 */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1rem;
    box-shadow: 0 6px 18px rgba(20, 70, 50, 0.045);
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted);
}

[data-testid="stMetricValue"] {
    color: var(--brand-dark);
    font-weight: 800;
}

/* 按钮 */
.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(23, 107, 77, 0.28);
    background: #ffffff;
    color: var(--brand-dark);
    font-weight: 650;
    transition: all 0.15s ease-in-out;
}

.stButton > button:hover {
    border-color: var(--brand);
    background: var(--brand-soft);
    color: var(--brand-dark);
    transform: translateY(-1px);
}

/* 主按钮 */
.stDownloadButton > button {
    border-radius: 12px;
    font-weight: 700;
}

/* 提示框圆角 */
[data-testid="stAlert"] {
    border-radius: 14px;
}

/* 表格和编辑器 */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 16px;
    overflow: hidden;
}

/* 聊天气泡区域 */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: .35rem .35rem;
}

/* 分割线 */
hr {
    margin: 1.2rem 0;
    border-color: var(--border);
}

/* 页面小标题 */
h2, h3 {
    color: var(--text-main);
    letter-spacing: -0.01em;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .agent-title {
        padding: 1.1rem 1.2rem;
        border-radius: 18px;
    }

    .agent-title h1 {
        font-size: 1.45rem;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
/* 页面底部工作人员入口 */
.staff-contact-fixed {
    position: fixed;
    bottom: 10px;
    left: calc(50% + 8rem);
    transform: translateX(-50%);
    z-index: 999;
    font-size: 12px;
    color: #8a9891;
}

.staff-contact-fixed a {
    color: #8a9891;
    text-decoration: none;
}

.staff-contact-fixed a:hover {
    color: #176b4d;
    text-decoration: underline;
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
        "projects": {},
        "queried_project": None,
        "last_created_key": None,
        "active_psid_key": None,
        "report_query_key": None,
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "你好，我是“碳迹可循”AI 碳足迹智能体“小碳”。"
                    "您有什么相关问题或者疑惑可以咨询我哦。"
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

#这个函数是为了演示数据数据上传与补齐模块而增加的演示数据
def add_demo_missing_requests(project):

    if project.get("missing_requests"):
        return

    project["missing_requests"] = [
        {
            "title": "补充电芯供应商信息",
            "module": "原材料",
            "priority": "高",
            "reason": (
                "当前 BOM 中部分电芯材料"
                "未提供供应商来源信息。"
            ),
            "requirement": (
                "请提供电芯供应商名称、"
                "采购规格书或采购证明。"
            ),
            "status": "待补充",
        },
        {
            "title": "补充生产线用电数据",
            "module": "生产制造",
            "priority": "高",
            "reason": (
                "当前资料无法确定产品生产阶段"
                "实际电力消耗。"
            ),
            "requirement": (
                "请提供对应生产周期的"
                "电力台账或电费记录。"
            ),
            "status": "待补充",
        },
        {
            "title": "补充运输距离信息",
            "module": "运输分销",
            "priority": "中",
            "reason": (
                "现有物流资料中缺少"
                "欧盟境内运输距离。"
            ),
            "requirement": (
                "请提供运输路线、"
                "运输方式及距离说明。"
            ),
            "status": "待补充",
        },
    ]
def go_to(page: str):
    st.session_state.current_page = page

def render_staff_contact():
    """在页面底部显示统一的工作人员咨询入口。"""

    # 给页面主体和底部入口之间预留空间
    st.markdown(
        "<div style='height:70px;'></div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="staff-contact-fixed">
            <a href="?page=contact">
                咨询工作人员
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_psid_project(
    project_name,
    product_name,
    product_model,
    battery_chemistry,
    voltage,
    capacity_kwh,
):
    # 生成类似 API Key 的唯一 PSID 密钥
    psid_key = "psid_live_" + secrets.token_hex(8)

    project_data = {
        "psid_key": psid_key,
        "project_name": project_name,
        "product_name": product_name,
        "product_model": product_model,
        "battery_chemistry": battery_chemistry,
        "voltage": voltage,
        "capacity_kwh": capacity_kwh,

        # 项目状态
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "progress": 0,
        "report_version": "尚未生成",
        "status": "项目已创建",

        # 企业上传资料
        "enterprise_files": [],

        # 工作人员审核状态
        "review_status": "尚未提交测算",

        # 工作人员返回的缺失数据
        "missing_requests": [],

        # 已完成的补齐数量
        "completed_missing": 0,
    }

    # 保存到当前 Streamlit 会话中
    st.session_state.projects[psid_key] = project_data

    # 记录最后创建的密钥
    st.session_state.last_created_key = psid_key

    return psid_key

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

    st.markdown(
        f"""
<div class="agent-title">
    <h1>🌿 碳迹可循 AI 碳足迹智能体</h1>

""",
        unsafe_allow_html=True,
    )
initialize_state()
requested_page = st.query_params.get("page")

if requested_page == "contact":
    st.session_state.current_page = "联系工作人员"

elif requested_page == "agent":
    st.session_state.current_page = "智能体工作台"

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
        "数据上传与补齐",
        "报告中心",
        "知识库查询",
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
    st.subheader('咨询智能体“小碳”')

    # 固定显示小碳欢迎语
    with st.chat_message("assistant"):
        st.markdown(
            "您好，我是“碳迹可循”AI碳足迹智能体“小碳”，"
            "您有什么相关问题或者疑惑可以咨询我哦"
        )

    # -----------------------------
    # 咨询输入框
    # -----------------------------
    input_col, send_col = st.columns([8, 1])

    with input_col:
        typed_prompt = st.text_input(
            "咨询问题",
            placeholder="请输入您想咨询的问题……",
            label_visibility="collapsed",
            key="agent_question"
        )

    with send_col:
        send_clicked = st.button(
            "发送",
            use_container_width=True,
            type="primary"
        )

    # -----------------------------
    # 三个快捷咨询按钮
    # -----------------------------
    st.caption("快捷咨询")

    prompt_cols = st.columns(3)

    if prompt_cols[0].button(
        "法规适用性判断",
        use_container_width=True
    ):
        st.session_state.pending_prompt = (
            "请判断当前产品是否适用欧盟电池碳足迹要求。"
        )

    if prompt_cols[1].button(
        "检查当前 BOM",
        use_container_width=True
    ):
        st.session_state.pending_prompt = (
            "请检查当前 BOM 的数据完整性。"
        )

    if prompt_cols[2].button(
        "生成预核算摘要",
        use_container_width=True
    ):
        st.session_state.pending_prompt = (
            "请生成当前项目的碳足迹预核算摘要。"
        )

    # -----------------------------
    # 历史咨询记录
    # 第一条欢迎语不重复显示
    # -----------------------------
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 判断本次需要发送的问题
    prompt = st.session_state.pop(
        "pending_prompt",
        None,
    )

    if send_clicked and typed_prompt.strip():
        prompt = typed_prompt.strip()

    # -----------------------------
    # 智能体处理问题
    # -----------------------------
    if prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("小碳正在结合项目数据与知识库分析……"):
            agent_result = run_agent(
                prompt=prompt,
                project=project,
                diagnosis=st.session_state.diagnosis,
                carbon_total=carbon_total,
                unit_result=unit_result,
                history=st.session_state.messages[:-1],
            )

        st.session_state.last_trace = agent_result["trace"]
        st.session_state.last_sources = agent_result["sources"]

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": agent_result["answer"],
            }
        )

        with st.chat_message("assistant"):
            st.markdown(agent_result["answer"])
            if agent_result.get("ai_enabled"):
                st.caption("AI 实时推理 · 已结合当前项目上下文与本地知识库")

        if (
            agent_result["intent"] == "diagnosis"
            and st.session_state.diagnosis
        ):
            if st.button(
                "将诊断结果生成补齐任务",
                type="primary",
            ):
                add_tasks_from_diagnosis()

    # 给底部联系入口留一点空间
    st.markdown("<div style='height:70px;'></div>",
                unsafe_allow_html=True)
    st.markdown(
        """
        <div class="staff-contact-fixed">
            <a href="?page=contact">
                咨询工作人员
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

elif page == "项目中心":
    st.subheader("PSID 项目中心")

    st.caption(
        "创建独立的产品碳足迹项目，并通过专属 PSID Key "
        "查询项目进度、任务和报告。"
    )

    st.write("")

    # =====================================================
    # 第一部分：PSID 项目创建
    # =====================================================

    st.markdown("### ① PSID 项目创建")

    st.caption(
        "填写产品基本信息后，系统将自动生成唯一的 PSID Key。"
        "请妥善保存该密钥。"
    )

    with st.form("create_psid_form"):

        project_name = st.text_input(
            "项目名称",
            placeholder="例如：德国户储 5.12kWh 电池碳足迹项目"
        )

        product_name = st.text_input(
            "产品名称",
            placeholder="例如：低压 LFP 储能电池模块"
        )

        col1, col2 = st.columns(2)

        with col1:
            product_model = st.text_input(
                "产品型号",
                placeholder="例如：CT-5120-LFP"
            )

        with col2:
            battery_chemistry = st.selectbox(
                "电池体系",
                [
                    "磷酸铁锂（LFP）",
                    "三元锂（NCM）",
                    "钠离子电池",
                    "其他"
                ]
            )

        col3, col4 = st.columns(2)

        with col3:
            voltage = st.text_input(
                "标称电压",
                placeholder="例如：51.2V"
            )

        with col4:
            capacity_kwh = st.number_input(
                "名义容量（kWh）",
                min_value=0.1,
                value=5.12,
                step=0.1
            )

        create_project = st.form_submit_button(
            "创建 PSID 项目",
            type="primary",
            use_container_width=True
        )

    # -----------------------------------------------------
    # 创建项目
    # -----------------------------------------------------

    if create_project:

        if not project_name.strip():
            st.warning("请输入项目名称。")

        elif not product_name.strip():
            st.warning("请输入产品名称。")

        elif not product_model.strip():
            st.warning("请输入产品型号。")

        elif not voltage.strip():
            st.warning("请输入标称电压。")

        else:

            new_key = create_psid_project(
                project_name=project_name.strip(),
                product_name=product_name.strip(),
                product_model=product_model.strip(),
                battery_chemistry=battery_chemistry,
                voltage=voltage.strip(),
                capacity_kwh=capacity_kwh,
            )

            st.success("PSID 项目创建成功")

            st.markdown("##### 您的 PSID Key")

            st.code(
                new_key,
                language=None
            )

            st.warning(
                "请妥善保存此 PSID Key。"
                "后续查询项目状态时需要使用该密钥。"
            )

    st.divider()

    # =====================================================
    # 第二部分：PSID 项目信息查询
    # =====================================================

    st.markdown("### ② PSID 项目信息查询")

    st.caption(
        "输入创建项目时获得的 PSID Key，"
        "即可查询对应项目。"
    )

    query_col, button_col = st.columns([5, 1])

    with query_col:

        query_key = st.text_input(
            "PSID Key",
            placeholder="psid_live_xxxxxxxxxxxxxxxx",
            label_visibility="collapsed",
            key="psid_query_input"
        )

    with button_col:

        query_clicked = st.button(
            "查询项目",
            type="primary",
            use_container_width=True
        )

    # -----------------------------------------------------
    # 查询项目
    # -----------------------------------------------------

    if query_clicked:

        if not query_key.strip():

            st.warning("请输入 PSID Key。")

        elif query_key.strip() not in st.session_state.projects:

            st.error(
                "没有找到对应项目，请检查 PSID Key 是否正确。"
            )

            st.session_state.queried_project = None

        else:

            st.session_state.queried_project = (
                st.session_state.projects[
                    query_key.strip()
                ]
            )

    # -----------------------------------------------------
    # 显示查询结果
    # -----------------------------------------------------

    if st.session_state.queried_project:

        found_project = st.session_state.queried_project

        st.write("")

        st.success("项目查询成功")

        st.markdown(
            f"""
                **项目名称：** {found_project["project_name"]}

                **产品名称：** {found_project["product_name"]}

                **产品型号：** {found_project["product_model"]}

                **电池体系：** {found_project["battery_chemistry"]}

                **标称电压：** {found_project["voltage"]}

                **名义容量：** {found_project["capacity_kwh"]:.2f} kWh

                **创建时间：** {found_project["created_at"]}
                """
        )

        st.write("")

        # ===============================================
        # 项目状态入口
        # ===============================================

        progress_col, task_col, report_col = st.columns(3)

        # 完成进度
        with progress_col:

            st.metric(
                "项目完成进度",
                f'{found_project["progress"]}%'
            )

            if st.button(
                    "查看项目数据",
                    use_container_width=True,
                    key="project_progress_button"
            ):
                go_to("数据中心")
                st.rerun()

        # 待完成任务
        with task_col:

            st.metric(
                "待完成任务",
                f'{found_project["pending_tasks"]} 项'
            )

            if st.button(
                    "查看待完成任务",
                    use_container_width=True,
                    key="project_task_button"
            ):
                go_to("缺失任务")
                st.rerun()

        # 报告版本
        with report_col:

            st.metric(
                "报告版本",
                found_project["report_version"]
            )

            if st.button(
                    "查看项目报告",
                    use_container_width=True,
                    key="project_report_button"
            ):
                go_to("报告中心")
                st.rerun()
    render_staff_contact()

elif page == "数据上传与补齐":

    st.subheader("数据上传与补齐")

    st.caption(
        "通过 PSID Key 进入对应项目，完成企业基础数据提交及后续缺失数据补充。"
    )

    st.write("")

    # =====================================================
    # 第一步：进入 PSID 项目
    # =====================================================

    if st.session_state.active_psid_key is None:

        st.markdown("### 进入项目")

        st.caption(
            "请输入创建项目时获得的 PSID Key。"
        )

        key_col, enter_col = st.columns([5, 1])

        with key_col:
            access_key = st.text_input(
                "PSID Key",
                placeholder="psid_live_xxxxxxxxxxxxxxxx",
                label_visibility="collapsed",
                key="data_access_key"
            )

        with enter_col:
            enter_project = st.button(
                "进入项目",
                type="primary",
                use_container_width=True
            )

        if enter_project:

            clean_key = access_key.strip()

            if not clean_key:

                st.warning("请输入 PSID Key。")

            elif clean_key not in st.session_state.projects:

                st.error(
                    "未找到对应项目，请检查 PSID Key 是否正确。"
                )

            else:

                st.session_state.active_psid_key = clean_key
                st.success("项目验证成功。")
                st.rerun()

    # =====================================================
    # 已进入项目
    # =====================================================

    else:

        active_key = st.session_state.active_psid_key
        active_project = st.session_state.projects[active_key]
        add_demo_missing_requests(active_project)

        # 兼容之前创建的旧项目
        active_project.setdefault(
            "enterprise_files",
            []
        )

        active_project.setdefault(
            "review_status",
            "尚未提交测算"
        )

        active_project.setdefault(
            "missing_requests",
            []
        )

        active_project.setdefault(
            "completed_missing",
            0
        )

        # -------------------------------------------------
        # 当前项目信息
        # -------------------------------------------------

        info_col, exit_col = st.columns([5, 1])

        with info_col:

            st.markdown(
                f"""
                **当前项目：{active_project["project_name"]}**

                产品：{active_project["product_name"]} ·
                {active_project["product_model"]}
                """
            )

            st.caption(
                f"PSID：{active_key}"
            )

        with exit_col:

            if st.button(
                "退出项目",
                use_container_width=True
            ):

                st.session_state.active_psid_key = None
                st.rerun()

        st.divider()

        # =================================================
        # 两个业务模块
        # =================================================

        upload_tab, missing_tab = st.tabs(
            [
                "企业数据上传",
                "缺失数据补齐"
            ]
        )

        # =================================================
        # 企业数据上传
        # =================================================

        with upload_tab:

            st.markdown("### 企业基础数据提交")

            st.caption(
                "请上传开展产品碳足迹预核算所需的企业基础资料。"
                "工作人员将在收到资料后进行数据检查和测算。"
            )

            st.write("")

            upload_type = st.selectbox(
                "资料类型",
                [
                    "产品 BOM",
                    "产品规格书",
                    "生产能耗数据",
                    "物流运输数据",
                    "供应商资料",
                    "回收与处置数据",
                    "其他证明材料"
                ],
                key="enterprise_upload_type"
            )

            enterprise_upload = st.file_uploader(
                "选择需要上传的文件",
                type=[
                    "xlsx",
                    "xls",
                    "csv",
                    "pdf",
                    "docx",
                    "png",
                    "jpg",
                    "jpeg"
                ],
                accept_multiple_files=True,
                key="enterprise_project_upload"
            )

            data_note = st.text_area(
                "资料说明（选填）",
                placeholder=(
                    "例如：该文件为 2025 年生产线月度用电台账，"
                    "对应本项目产品生产环节。"
                ),
                key="enterprise_data_note"
            )

            if st.button(
                "保存上传资料",
                type="primary",
                key="save_enterprise_files"
            ):

                if not enterprise_upload:

                    st.warning(
                        "请至少选择一个文件。"
                    )

                else:

                    for uploaded_file in enterprise_upload:

                        file_record = {
                            "file_name": uploaded_file.name,
                            "file_type": upload_type,
                            "note": data_note,
                            "status": "已上传",
                            "uploaded_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        }

                        active_project[
                            "enterprise_files"
                        ].append(file_record)

                    st.success(
                        f"已保存 {len(enterprise_upload)} 个文件。"
                    )

            # ---------------------------------------------
            # 已上传资料
            # ---------------------------------------------

            st.write("")
            st.markdown("#### 已上传资料")

            if not active_project["enterprise_files"]:

                st.info(
                    "当前项目尚未上传企业资料。"
                )

            else:

                uploaded_df = pd.DataFrame(
                    active_project["enterprise_files"]
                )

                st.dataframe(
                    uploaded_df,
                    use_container_width=True,
                    hide_index=True
                )

            st.write("")

            # ---------------------------------------------
            # 提交工作人员
            # ---------------------------------------------

            st.markdown("#### 提交测算")

            st.caption(
                "资料准备完成后，可提交工作人员进行数据检查和碳足迹测算。"
            )

            if st.button(
                "提交工作人员测算",
                type="primary",
                key="submit_for_review"
            ):

                if not active_project[
                    "enterprise_files"
                ]:

                    st.warning(
                        "请先上传至少一份企业资料。"
                    )

                else:

                    active_project[
                        "review_status"
                    ] = "工作人员审核中"

                    st.success(
                        "资料已提交。工作人员将进行数据检查与测算。"
                    )

            st.info(
                "当前状态："
                + active_project["review_status"]
            )

        # =================================================
        # 缺失数据补齐
        # =================================================

        with missing_tab:

            st.markdown("### 缺失数据补齐")

            st.caption(
                "工作人员完成企业数据检查后，"
                "如发现关键数据或证明材料缺失，"
                "将在此处返回需要补充的任务。"
            )

            st.write("")

            missing_requests = active_project[
                "missing_requests"
            ]

            # ---------------------------------------------
            # 当前没有缺失任务
            # ---------------------------------------------

            if not missing_requests:

                if (
                    active_project["review_status"]
                    == "工作人员审核中"
                ):

                    st.info(
                        "工作人员正在检查您提交的数据，"
                        "当前暂无需要补充的资料。"
                    )

                else:

                    st.info(
                        "当前项目暂无缺失数据补齐任务。"
                    )

            # ---------------------------------------------
            # 有缺失任务
            # ---------------------------------------------

            else:

                unfinished = [
                    item
                    for item in missing_requests
                    if item["status"] != "已完成"
                ]

                complete_count = (
                    len(missing_requests)
                    - len(unfinished)
                )

                progress = (
                    complete_count
                    / len(missing_requests)
                )

                st.progress(
                    progress,
                    text=(
                        f"补齐进度："
                        f"{complete_count}/"
                        f"{len(missing_requests)}"
                    )
                )

                for index, task in enumerate(
                    missing_requests
                ):

                    with st.expander(
                        f'{index + 1}. '
                        f'{task["title"]} · '
                        f'{task["status"]}'
                    ):

                        st.write(
                            f'**所属模块：** '
                            f'{task["module"]}'
                        )

                        st.write(
                            f'**优先级：** '
                            f'{task["priority"]}'
                        )

                        st.write(
                            f'**缺失原因：** '
                            f'{task["reason"]}'
                        )

                        st.write(
                            f'**需要补充：** '
                            f'{task["requirement"]}'
                        )

                        if task["status"] != "已完成":

                            supplement_file = (
                                st.file_uploader(
                                    "上传补充材料",
                                    type=[
                                        "xlsx",
                                        "xls",
                                        "csv",
                                        "pdf",
                                        "docx",
                                        "png",
                                        "jpg",
                                        "jpeg"
                                    ],
                                    key=(
                                        f"missing_file_"
                                        f"{index}"
                                    )
                                )
                            )

                            supplement_note = (
                                st.text_area(
                                    "补充说明（选填）",
                                    key=(
                                        f"missing_note_"
                                        f"{index}"
                                    )
                                )
                            )

                            if st.button(
                                "提交本项补充资料",
                                key=(
                                    f"submit_missing_"
                                    f"{index}"
                                ),
                                type="primary"
                            ):

                                if supplement_file is None:

                                    st.warning(
                                        "请上传对应补充材料。"
                                    )

                                else:

                                    task["status"] = (
                                        "已提交待复核"
                                    )

                                    task[
                                        "supplement_file"
                                    ] = (
                                        supplement_file.name
                                    )

                                    task[
                                        "supplement_note"
                                    ] = (
                                        supplement_note
                                    )

                                    st.success(
                                        "补充资料已提交，"
                                        "等待工作人员复核。"
                                    )

                                    st.rerun()
    render_staff_contact()


elif page == "报告中心":

    st.subheader("报告中心")

    st.caption(
        "通过 PSID Key 查询对应项目的碳足迹报告及报告状态。"
    )

    st.write("")

    # =====================================================
    # 左右布局
    # =====================================================

    report_main, report_showcase = st.columns(
        [4, 1],
        gap="large"
    )

    # =====================================================
    # 左侧：项目报告查询
    # =====================================================

    with report_main:

        st.markdown("### PSID 项目报告查询")

        st.caption(
            "请输入项目创建时获得的 PSID Key，"
            "查看对应项目的报告状态与报告版本。"
        )

        st.write("")

        key_col, query_col = st.columns([5, 1])

        with key_col:

            report_key = st.text_input(
                "PSID Key",
                placeholder="psid_live_xxxxxxxxxxxxxxxx",
                label_visibility="collapsed",
                key="report_psid_input"
            )

        with query_col:

            report_query_clicked = st.button(
                "查询",
                type="primary",
                use_container_width=True,
                key="report_query_button"
            )

        # -------------------------------------------------
        # 查询 PSID
        # -------------------------------------------------

        if report_query_clicked:

            clean_key = report_key.strip()

            if not clean_key:

                st.warning("请输入 PSID Key。")

            elif clean_key not in st.session_state.projects:

                st.error(
                    "未找到对应项目，请检查 PSID Key 是否正确。"
                )

                st.session_state.report_query_key = None

            else:

                st.session_state.report_query_key = clean_key

        # -------------------------------------------------
        # 查询成功
        # -------------------------------------------------

        if st.session_state.report_query_key:

            current_key = st.session_state.report_query_key

            if current_key in st.session_state.projects:

                report_project = st.session_state.projects[
                    current_key
                ]

                # 兼容之前创建的项目
                report_project.setdefault(
                    "report_version",
                    "尚未生成"
                )

                report_project.setdefault(
                    "status",
                    "项目已创建"
                )

                st.write("")

                st.success("项目查询成功")

                # -----------------------------------------
                # 项目信息
                # -----------------------------------------

                with st.container(border=True):

                    st.markdown(
                        f"""
                        #### {report_project["project_name"]}

                        **产品名称：**
                        {report_project["product_name"]}

                        **产品型号：**
                        {report_project["product_model"]}

                        **PSID：**
                        `{current_key}`
                        """
                    )

                st.write("")

                # -----------------------------------------
                # 报告状态
                # -----------------------------------------

                status_col, version_col = st.columns(2)

                with status_col:

                    st.metric(
                        "报告状态",
                        (
                            "待生成"
                            if report_project["report_version"]
                            == "尚未生成"
                            else "已生成"
                        )
                    )

                with version_col:

                    st.metric(
                        "当前版本",
                        report_project["report_version"]
                    )

                st.write("")

                # -----------------------------------------
                # 当前没有报告
                # -----------------------------------------

                if (
                    report_project["report_version"]
                    == "尚未生成"
                ):

                    st.info(
                        "当前项目尚未生成正式报告。"
                        "完成数据提交、缺失数据补齐及工作人员复核后，"
                        "报告将在此处发布。"
                    )

                # -----------------------------------------
                # 已有报告
                # -----------------------------------------

                else:

                    st.markdown("#### 项目报告")

                    st.write(
                        "报告已经生成，您可以在线查看"
                        "或下载当前版本。"
                    )

                    button_col1, button_col2 = st.columns(2)

                    with button_col1:

                        st.button(
                            "在线查看报告",
                            use_container_width=True,
                            type="primary",
                            key="view_project_report"
                        )

                    with button_col2:

                        st.button(
                            "下载当前报告",
                            use_container_width=True,
                            key="download_project_report"
                        )

    # =====================================================
    # 右侧：优秀报告展示
    # =====================================================

    with report_showcase:

        st.markdown("### 优秀报告展示")

        st.caption(
            "查看其他项目的完整碳足迹报告案例。"
        )

        st.write("")

        # -------------------------------------------------
        # 暂无正式案例，先保留展示位置
        # -------------------------------------------------

        with st.container(border=True):

            st.markdown(
                """
                #### 某储能科技有限公司
                """
            )

            st.caption(
                "电池碳足迹报告"
            )

            st.write("")

            st.markdown(
                """
                <div style="
                    font-size: 12px;
                    color: #8a9891;
                    padding: 6px 0;
                ">
                    完整案例正在整理中
                </div>
                """,
                unsafe_allow_html=True
            )

            st.button(
                "查看完整报告",
                disabled=True,
                use_container_width=True,
                key="excellent_report_demo"
            )

    render_staff_contact()


elif page == "知识库查询":

    st.subheader("知识库查询")

    st.caption(
        "碳迹可循的碳足迹预核算与合规判断基于欧盟官方法规、"
        "JRC 技术方法及 Product Environmental Footprint（PEF）方法体系。"
    )

    st.info(
        "以下文件均链接至欧盟官方机构网站。"
        "点击对应按钮可直接前往官方页面查阅原文。"
    )

    st.write("")

    # =====================================================
    # 核心测算依据
    # =====================================================

    st.markdown("### 核心测算依据")

    st.caption(
        "以下文件构成当前工业储能电池碳足迹预核算的主要法规与方法依据。"
    )

    st.write("")

    # -----------------------------------------------------
    # 文件 1：EU Batteries Regulation
    # -----------------------------------------------------

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:

            st.markdown(
                """
                #### Regulation (EU) 2023/1542

                **欧盟《电池与废电池法规》**
                """
            )

            st.caption(
                "法律依据 · European Union / EUR-Lex"
            )

            st.write(
                "规定欧盟市场电池产品的可持续性、碳足迹、"
                "信息披露、回收及合规要求。"
                "其中 Article 7 对相关电池产品的碳足迹要求作出规定。"
            )

        with col2:

            st.write("")

            st.link_button(
                "查看官方原文 ↗",
                "https://eur-lex.europa.eu/legal-content/EN/TXT/"
                "?uri=CELEX%3A02023R1542-20250731",
                use_container_width=True
            )

    # -----------------------------------------------------
    # 文件 2：JRC CFB-IND
    # -----------------------------------------------------

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:

            st.markdown(
                """
                #### Rules for the calculation of the Carbon Footprint of Industrial Batteries without external storage (CFB-IND)

                **工业电池碳足迹计算规则（CFB-IND）**
                """
            )

            st.caption(
                "核心技术方法 · European Commission Joint Research Centre"
            )

            st.write(
                "JRC 发布的工业电池碳足迹计算与核验技术方法，"
                "针对无外部储能且容量超过 2 kWh 的工业电池，"
                "是本项目生命周期边界、功能单位和计算方法的重要技术依据。"
            )

        with col2:

            st.write("")

            st.link_button(
                "查看官方文件 ↗",
                "https://publications.jrc.ec.europa.eu/"
                "repository/handle/JRC141282",
                use_container_width=True
            )

    # -----------------------------------------------------
    # 文件 3：PEF
    # -----------------------------------------------------

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:

            st.markdown(
                """
                #### Commission Recommendation (EU) 2021/2279

                **Product Environmental Footprint（PEF）方法**
                """
            )

            st.caption(
                "生命周期评价方法基础 · European Commission / EUR-Lex"
            )

            st.write(
                "欧盟产品环境足迹方法体系。"
                "工业电池碳足迹方法在生命周期评价、"
                "环境影响计算及数据处理方面以 PEF 方法为重要基础。"
            )

        with col2:

            st.write("")

            st.link_button(
                "查看官方原文 ↗",
                "https://eur-lex.europa.eu/legal-content/EN/TXT/"
                "?uri=CELEX%3A32021H2279",
                use_container_width=True
            )

    st.write("")
    st.divider()

    # =====================================================
    # 你可能还想知道
    # =====================================================

    st.markdown("### 你可能还想知道")

    st.caption(
        "以下内容用于进一步了解欧盟电池法规及工业电池碳足迹政策背景。"
    )

    st.write("")

    related_col1, related_col2 = st.columns(2)

    with related_col1:

        with st.container(border=True):

            st.markdown(
                "#### 欧盟 Batteries 官方专题"
            )

            st.caption(
                "European Commission · Environment"
            )

            st.write(
                "了解欧盟电池法规的政策目标、"
                "实施安排及相关官方动态。"
            )

            st.link_button(
                "前往官方页面 ↗",
                "https://environment.ec.europa.eu/"
                "topics/waste-and-recycling/batteries_en",
                use_container_width=True
            )

    with related_col2:

        with st.container(border=True):

            st.markdown(
                "#### JRC 工业电池碳足迹方法说明"
            )

            st.caption(
                "European Commission · Joint Research Centre"
            )

            st.write(
                "JRC 对 CFB-IND 方法适用范围、"
                "生命周期阶段和政策背景的官方说明。"
            )

            st.link_button(
                "查看方法说明 ↗",
                "https://joint-research-centre.ec.europa.eu/"
                "jrc-news-and-updates/"
                "calculating-carbon-footprint-industrial-batteries-"
                "methodological-support-2025-05-28_en",
                use_container_width=True
            )

    st.write("")

    # =====================================================
    # 持续维护提示
    # =====================================================

    st.markdown(
        """
        <div style="
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: #9aa6a0;
        ">
            法规知识库持续更新中
        </div>
        """,
        unsafe_allow_html=True
    )