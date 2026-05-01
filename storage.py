"""
数据存储层 - 负责JSON文件的读写管理
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from models import DayPlan, Task


def _get_base_dir() -> Path:
    """获取程序运行目录（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：使用 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：使用脚本所在目录
        return Path(__file__).parent


class Storage:
    """本地JSON文件存储管理器"""

    DATA_DIR = _get_base_dir() / "data"

    def __init__(self):
        self.DATA_DIR.mkdir(exist_ok=True)

    def _file_path(self, date_str: str) -> Path:
        return self.DATA_DIR / f"{date_str}.json"

    def load_day(self, date_str: str) -> DayPlan:
        """加载某一天的计划，如果不存在则返回空计划"""
        path = self._file_path(date_str)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DayPlan.from_dict(data)
        return DayPlan(date=date_str)

    def save_day(self, day_plan: DayPlan):
        """保存某一天的计划到JSON文件"""
        path = self._file_path(day_plan.date)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(day_plan.to_dict(), f, ensure_ascii=False, indent=2)

    def delete_day_file(self, date_str: str):
        """删除某一天的数据文件"""
        path = self._file_path(date_str)
        if path.exists():
            path.unlink()

    def list_available_dates(self, days: int = 30) -> List[str]:
        """列出最近N天有数据的日期"""
        dates = []
        today = datetime.now().date()
        for i in range(days):
            d = (today - timedelta(days=i)).isoformat()
            if self._file_path(d).exists():
                dates.append(d)
        return dates

    def load_range(self, start_date: str, end_date: str) -> List[DayPlan]:
        """加载一个日期范围内的所有计划"""
        results = []
        s = datetime.fromisoformat(start_date).date()
        e = datetime.fromisoformat(end_date).date()
        current = s
        while current <= e:
            date_str = current.isoformat()
            results.append(self.load_day(date_str))
            current += timedelta(days=1)
        return results

    def get_all_dates(self) -> List[str]:
        """获取所有存在数据文件的日期"""
        dates = []
        for f in sorted(self.DATA_DIR.glob("*.json")):
            dates.append(f.stem)
        return dates
