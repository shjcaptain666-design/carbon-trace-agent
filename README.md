# 碳迹可循 AI 碳足迹智能体

这是一个使用 Python + Streamlit 制作的展示型 Web 应用。

## 一、当前功能

- AI 智能体聊天工作台
- 智能体执行轨迹
- 法规与方法知识库匹配
- PSID 项目资料
- Excel/CSV BOM 上传
- BOM 字段和缺失项诊断
- 补齐任务生成与状态编辑
- 生命周期样板预核算图表
- Markdown 报告下载

## 二、本地运行

### 1. 打开项目文件夹

使用 VS Code 打开本项目。

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
```

### 3. 激活虚拟环境

```powershell
.venv\Scripts\activate
```

如果 PowerShell 阻止脚本执行，可以临时执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
```

### 4. 安装依赖

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 启动应用

```powershell
python -m streamlit run streamlit_app.py
```

浏览器通常会自动打开：

```text
http://localhost:8501
```

## 三、推荐演示流程

1. 进入“智能体工作台”；
2. 点击“法规适用性判断”；
3. 进入“数据中心”；
4. 上传 `data/sample_bom.xlsx`；
5. 点击“启动智能诊断”；
6. 生成缺失数据任务；
7. 回到智能体工作台，点击“检查当前 BOM”；
8. 查看碳足迹结果；
9. 在报告中心下载项目摘要。

## 四、部署前文件

部署到 Streamlit Community Cloud 时，至少保留：

- `streamlit_app.py`
- `agent.py`
- `knowledge_base.py`
- `bom_analyzer.py`
- `carbon_calculator.py`
- `report_generator.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `data/sample_bom.xlsx`

不要上传 `.venv` 文件夹。
