KNOWLEDGE_BASE = {
    "eu_battery": {
        "title": "欧盟《电池与废电池法规》",
        "code": "EU 2023/1542",
        "summary": "用于判断出口欧盟电池产品的法规适用范围、碳足迹披露、电池护照和后续合规要求。",
        "keywords": ["欧盟", "法规", "适用", "披露", "电池护照", "认证"],
    },
    "jrc_storage": {
        "title": "JRC 固定式储能工业电池碳足迹规则",
        "code": "JRC Storage Battery Method",
        "summary": "用于匹配固定式储能工业电池的功能单位、生命周期边界、活动数据与报告结构。",
        "keywords": ["JRC", "储能", "生命周期", "功能单位", "核算边界"],
    },
    "iso_14067": {
        "title": "ISO 14067 产品碳足迹标准",
        "code": "ISO 14067",
        "summary": "用于规范产品碳足迹的量化、表达、数据质量说明和报告逻辑。",
        "keywords": ["ISO", "14067", "产品碳足迹", "报告", "数据质量"],
    },
    "data_quality": {
        "title": "碳迹可循数据可信度分级规则",
        "code": "A-E Data Quality",
        "summary": "A 为第三方核验数据，B 为企业实测数据，C 为单据推算数据，D 为公开数据库或行业平均数据，E 为样板模拟数据。",
        "keywords": ["可信度", "等级", "A", "B", "C", "D", "E", "数据质量"],
    },
}

def search_knowledge(query: str):
    """通过关键词检索演示知识库。"""
    normalized = query.lower()
    matches = []

    for item in KNOWLEDGE_BASE.values():
        haystack = " ".join(
            [item["title"], item["code"], item["summary"], *item["keywords"]]
        ).lower()
        if any(word.lower() in normalized for word in item["keywords"]):
            matches.append(item)
        elif any(token in haystack for token in normalized.split() if len(token) >= 2):
            matches.append(item)

    if not matches:
        matches = [
            KNOWLEDGE_BASE["eu_battery"],
            KNOWLEDGE_BASE["jrc_storage"],
            KNOWLEDGE_BASE["iso_14067"],
        ]

    return matches[:3]
