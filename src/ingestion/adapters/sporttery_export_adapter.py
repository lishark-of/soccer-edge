from __future__ import annotations

from src.ingestion.adapters.generic_csv_adapter import GenericCsvAdapter


SPORTTERY_HEADERS = {
    "日期",
    "比赛日期",
    "开赛日期",
    "赛事",
    "联赛",
    "主队",
    "主队名称",
    "客队",
    "客队名称",
    "比分",
    "全场比分",
    "半场比分",
    "胜赔",
    "主胜",
    "胜",
    "平赔",
    "平",
    "负赔",
    "客胜",
    "负",
    "让球",
    "让胜",
    "让平",
    "让负",
}


class SportteryExportAdapter(GenericCsvAdapter):
    name = "sporttery_export"

    def can_handle(self, path: str) -> bool:
        if not super().can_handle(path):
            return False
        columns = set(self._columns(path))
        return len(columns.intersection(SPORTTERY_HEADERS)) >= 4
