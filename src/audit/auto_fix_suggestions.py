from __future__ import annotations


def build_auto_fix_suggestions(issues: list[dict]) -> list[dict]:
    suggestions = []
    for issue in issues:
        title = issue.get("title", "")
        if "技术控件" in title:
            suggestions.append({"target": "dashboard", "suggestion_zh": "将 API Base、Provider、路径输入放入高级设置抽屉。"})
        elif "禁止正向按钮" in title:
            suggestions.append({"target": "copy", "suggestion_zh": "使用“观察”“风险解释”“纸面模拟”替代交易动作词。"})
        elif "今日观察" in title:
            suggestions.append({"target": "home", "suggestion_zh": "首页默认调用 next-available 并展示 Top 观察信号。"})
        else:
            suggestions.append({"target": "general", "suggestion_zh": issue.get("suggestion_zh", "请查看对应页面。")})
    return suggestions
