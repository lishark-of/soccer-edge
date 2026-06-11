from __future__ import annotations

FORBIDDEN_CONTROL_WORDS = ["下注", "投注", "购买", "下单", "支付", "代购", "跟单", "自动投注", "追号", "倍投", "回血", "必中", "稳赢", "稳赚", "杀庄", "保本"]


def find_static_app_issues(html: str, js: str = "") -> list[dict]:
    combined = html + "\n" + js
    issues = []
    if "今日观察" not in html:
        issues.append(_issue("error", "首页缺少今日观察", "用户打开 App 后不知道先看哪里。", "把今日观察作为默认首屏。"))
    if "API Base" in html or "操作面板" in html:
        issues.append(_issue("warning", "技术控件暴露", "普通用户会被 API Base / Provider / 路径输入干扰。", "把技术控件放入默认关闭的高级设置。"))
    if "<details id=\"advancedSettings\" open" in html:
        issues.append(_issue("warning", "高级设置默认展开", "普通用户会先看到技术配置。", "高级设置默认关闭。"))
    for word in FORBIDDEN_CONTROL_WORDS:
        if f">{word}<" in combined or f">{word} " in combined:
            issues.append(_issue("error", f"存在禁止正向按钮：{word}", "可能被理解为真实交易入口。", "删除该按钮或改为观察/风险解释语言。"))
    return issues


def _issue(severity: str, title: str, impact: str, suggestion: str) -> dict:
    return {"severity": severity, "title": title, "impact_zh": impact, "suggestion_zh": suggestion}
