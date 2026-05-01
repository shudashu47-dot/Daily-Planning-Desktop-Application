"""
PySide6 主界面 - 现代化每日计划程序
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QScrollArea, QFrame,
    QProgressBar, QTextEdit, QGraphicsDropShadowEffect, QMessageBox,
    QFileDialog, QDialog, QGridLayout, QSizePolicy, QCheckBox, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QIcon, QPalette, QFontDatabase

from models import Task, DayPlan
from storage import Storage


# ============ 配色方案 ============
COLORS = {
    "primary": "#6366f1",
    "primary_dark": "#4f46e5",
    "primary_light": "#818cf8",
    "bg": "#f1f5f9",
    "card": "#ffffff",
    "text": "#0f172a",
    "text_secondary": "#64748b",
    "border": "#e2e8f0",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "high": "#ef4444",
    "medium": "#f59e0b",
    "low": "#3b82f6",
    "sidebar": "#ffffff",
}

PRIORITY_MAP = {
    "high": ("高", COLORS["high"]),
    "medium": ("中", COLORS["medium"]),
    "low": ("低", COLORS["low"]),
}

CATEGORY_MAP = {
    "工作": ("#dbeafe", "#1e40af"),
    "学习": ("#f3e8ff", "#6b21a8"),
    "生活": ("#dcfce7", "#166534"),
    "其他": ("#f1f5f9", "#475569"),
}

CATEGORY_LABELS = ["工作", "学习", "生活", "其他"]


# ============ 全局 QSS ============
GLOBAL_STYLE = """
QMainWindow {
    background-color: #f1f5f9;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QComboBox {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 10px;
    background: white;
    color: #0f172a;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #6366f1;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: white;
    selection-background-color: #e0e7ff;
    selection-color: #0f172a;
    padding: 4px;
}
QLineEdit {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    background: white;
    color: #0f172a;
    font-size: 14px;
}
QLineEdit:focus {
    border: 2px solid #6366f1;
}
QTextEdit {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px;
    background: #f8fafc;
    color: #0f172a;
    font-size: 13px;
}
QTextEdit:focus {
    border: 2px solid #6366f1;
}
QProgressBar {
    border: none;
    border-radius: 5px;
    background-color: #e2e8f0;
    height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 5px;
    background-color: #6366f1;
}
"""


# ============ 任务卡片组件 ============
class TaskCard(QFrame):
    def __init__(self, task: Task, on_toggle, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.task = task
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.setObjectName("taskCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMaximumWidth(800)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧优先级色条
        self.priority_bar = QFrame()
        self.priority_bar.setFixedWidth(4)
        layout.addWidget(self.priority_bar)

        # 内容区
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(8)

        # 第一行：复选框 + 内容 + 操作
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.setCursor(Qt.PointingHandCursor)
        self.checkbox.stateChanged.connect(self._on_toggle)
        row1.addWidget(self.checkbox)

        self.lbl_content = QLabel(self.task.content)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setMinimumHeight(22)
        row1.addWidget(self.lbl_content, 1)

        self.btn_edit = QPushButton("✏")
        self.btn_edit.setFixedSize(28, 28)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.clicked.connect(self._on_edit)
        row1.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("✕")
        self.btn_delete.setFixedSize(28, 28)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.clicked.connect(self._on_delete)
        row1.addWidget(self.btn_delete)

        content_layout.addLayout(row1)

        # 第二行：标签
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        prio_text, prio_color = PRIORITY_MAP.get(self.task.priority, ("中", COLORS["medium"]))
        self.lbl_priority = QLabel(prio_text)
        self.lbl_priority.setAlignment(Qt.AlignCenter)
        self.lbl_priority.setFixedSize(28, 20)
        row2.addWidget(self.lbl_priority)

        cat_bg, cat_fg = CATEGORY_MAP.get(self.task.category, ("#f1f5f9", "#475569"))
        self.lbl_category = QLabel(self.task.category)
        self.lbl_category.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.lbl_category)

        if self.task.tomato_count > 0:
            self.lbl_tomato = QLabel(f"🍅 {self.task.tomato_count}")
            row2.addWidget(self.lbl_tomato)

        row2.addStretch()

        if self.task.completed and self.task.completed_at:
            time_str = self.task.completed_at[11:16]
            self.lbl_time = QLabel(f"✓ {time_str}")
            row2.addWidget(self.lbl_time)

        content_layout.addLayout(row2)
        layout.addWidget(content, 1)

    def _apply_style(self):
        # 圆角 + 背景
        self.setStyleSheet("""
            #taskCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            #taskCard:hover {
                border-color: #cbd5e1;
            }
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # 优先级色条
        _, prio_color = PRIORITY_MAP.get(self.task.priority, ("中", COLORS["medium"]))
        self.priority_bar.setStyleSheet(f"background-color: {prio_color}; border-radius: 2px;")

        # 复选框样式
        self.checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid {'#cbd5e1' if self.task.completed else prio_color};
                background: {'{prio_color}' if self.task.completed else 'white'};
            }}
            QCheckBox::indicator:checked {{
                background-color: {prio_color};
                border-color: {prio_color};
            }}
        """)

        # 内容文字
        if self.task.completed:
            self.lbl_content.setStyleSheet("""
                color: #94a3b8;
                font-size: 15px;
                font-family: "Microsoft YaHei";
                text-decoration: line-through;
            """)
        else:
            self.lbl_content.setStyleSheet("""
                color: #0f172a;
                font-size: 15px;
                font-family: "Microsoft YaHei";
                font-weight: 500;
            """)

        # 优先级标签
        self.lbl_priority.setStyleSheet(f"""
            background-color: {prio_color};
            color: white;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            font-family: "Microsoft YaHei";
        """)

        # 分类标签
        cat_bg, cat_fg = CATEGORY_MAP.get(self.task.category, ("#f1f5f9", "#475569"))
        self.lbl_category.setStyleSheet(f"""
            background-color: {cat_bg};
            color: {cat_fg};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-family: "Microsoft YaHei";
        """)

        # 按钮样式
        btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #6366f1;
            }
        """
        self.btn_edit.setStyleSheet(btn_style)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background-color: #fef2f2;
                color: #ef4444;
            }
        """)

        # 番茄/时间标签
        small_style = "color: #94a3b8; font-size: 12px; font-family: \"Microsoft YaHei\";"
        if hasattr(self, 'lbl_tomato'):
            self.lbl_tomato.setStyleSheet(small_style)
        if hasattr(self, 'lbl_time'):
            self.lbl_time.setStyleSheet(small_style)

    def _on_toggle(self, state):
        self.on_toggle(self.task, bool(state))

    def _on_edit(self):
        self.on_edit(self.task)

    def _on_delete(self):
        self.on_delete(self.task)

    def enterEvent(self, event):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        super().enterEvent(event)

    def leaveEvent(self, event):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        super().leaveEvent(event)


# ============ 编辑任务弹窗 ============
class EditTaskDialog(QDialog):
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("编辑任务")
        self.setFixedSize(420, 260)
        self.setStyleSheet(f"background-color: {COLORS['bg']}; border-radius: 16px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("✏ 编辑任务")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        layout.addWidget(title)

        self.entry = QLineEdit(task.content)
        self.entry.setPlaceholderText("任务内容...")
        layout.addWidget(self.entry)

        row = QHBoxLayout()
        self.prio_combo = QComboBox()
        self.prio_combo.addItems(["高", "中", "低"])
        prio_label = {"high": "高", "medium": "中", "low": "低"}.get(task.priority, "中")
        self.prio_combo.setCurrentText(prio_label)
        row.addWidget(self.prio_combo)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(CATEGORY_LABELS)
        self.cat_combo.setCurrentText(task.category)
        row.addWidget(self.cat_combo)
        row.addStretch()
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("取消")
        cancel.setFixedSize(80, 36)
        cancel.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #64748b;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cbd5e1;
            }
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        save = QPushButton("保存")
        save.setFixedSize(80, 36)
        save.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        save.clicked.connect(self.accept)
        save.setDefault(True)
        btn_row.addWidget(save)

        layout.addLayout(btn_row)
        self.entry.setFocus()
        self.entry.selectAll()

    def get_result(self):
        priority_map = {"高": "high", "中": "medium", "低": "low"}
        return (
            self.entry.text().strip(),
            priority_map.get(self.prio_combo.currentText(), "medium"),
            self.cat_combo.currentText()
        )


# ============ 统计弹窗 ============
class StatsDialog(QDialog):
    def __init__(self, storage: Storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("统计分析")
        self.setFixedSize(700, 520)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📊 统计概览")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        layout.addWidget(title)

        # 概览卡片
        end = datetime.now().date()
        start = end - timedelta(days=6)
        plans = self.storage.load_range(start.isoformat(), end.isoformat())

        total_tasks = sum(p.total_count for p in plans)
        done_tasks = sum(p.completed_count for p in plans)
        rate = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
        total_tomato = sum(t.tomato_count for p in plans for t in p.tasks)

        cards = QHBoxLayout()
        cards.addWidget(self._create_card("总任务", str(total_tasks), COLORS["primary"]))
        cards.addWidget(self._create_card("已完成", str(done_tasks), COLORS["success"]))
        cards.addWidget(self._create_card("总完成率", f"{rate}%", COLORS["warning"]))
        cards.addWidget(self._create_card("总番茄", str(total_tomato), COLORS["danger"]))
        layout.addLayout(cards)

        # 趋势图区域
        trend_widget = QFrame()
        trend_widget.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        trend_layout = QVBoxLayout(trend_widget)
        trend_layout.setContentsMargins(16, 16, 16, 16)

        trend_title = QLabel("近7天完成率趋势")
        trend_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        trend_layout.addWidget(trend_title)

        self.trend_canvas = QFrame()
        self.trend_canvas.setMinimumHeight(200)
        trend_layout.addWidget(self.trend_canvas)
        layout.addWidget(trend_widget)

        self._draw_trend(plans)

    def _create_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; color: #64748b; font-family: 'Microsoft YaHei';")
        layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color}; font-family: 'Microsoft YaHei';")
        layout.addWidget(lbl_value)

        return card

    def _draw_trend(self, plans):
        # 简化的趋势展示 - 用 QLabel 显示数据
        layout = QHBoxLayout(self.trend_canvas)
        layout.setSpacing(12)

        for p in plans:
            bar_widget = QFrame()
            bar_widget.setFixedWidth(60)
            bar_layout = QVBoxLayout(bar_widget)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(4)

            # 柱状
            bar = QFrame()
            h = max(int(p.completion_rate * 1.5), 10)
            bar.setFixedHeight(h)
            bar.setStyleSheet(f"background-color: {COLORS['primary']}; border-radius: 4px;")
            bar_layout.addWidget(bar, alignment=Qt.AlignBottom)

            # 日期
            date_lbl = QLabel(p.date[5:])
            date_lbl.setAlignment(Qt.AlignCenter)
            date_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
            bar_layout.addWidget(date_lbl)

            # 百分比
            pct_lbl = QLabel(f"{p.completion_rate}%")
            pct_lbl.setAlignment(Qt.AlignCenter)
            pct_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
            bar_layout.addWidget(pct_lbl)

            layout.addWidget(bar_widget)

        layout.addStretch()


# ============ 导出弹窗 ============
class ExportDialog(QDialog):
    def __init__(self, storage: Storage, current_date: str, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.current_date = current_date
        self.setWindowTitle("导出数据")
        self.setFixedSize(360, 240)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📤 导出选项")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        layout.addWidget(title)

        self.export_type = QComboBox()
        self.export_type.addItems(["导出今日 - Markdown", "导出本周 - CSV", "导出全部 - JSON备份"])
        layout.addWidget(self.export_type)

        btn = QPushButton("选择保存位置并导出")
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        btn.clicked.connect(self._do_export)
        layout.addWidget(btn)
        layout.addStretch()

    def _do_export(self):
        etype = self.export_type.currentIndex()

        if etype == 0:
            path, _ = QFileDialog.getSaveFileName(self, "导出今日", f"plan-{self.current_date}.md", "Markdown (*.md)")
            if path:
                self._export_md(path)
        elif etype == 1:
            path, _ = QFileDialog.getSaveFileName(self, "导出本周", f"plan-week-{self.current_date}.csv", "CSV (*.csv)")
            if path:
                self._export_csv(path)
        else:
            path, _ = QFileDialog.getSaveFileName(self, "导出全部", f"plan-backup-{self.current_date}.json", "JSON (*.json)")
            if path:
                self._export_json(path)

        self.accept()

    def _export_md(self, path):
        plan = self.storage.load_day(self.current_date)
        lines = [f"# 每日计划 - {plan.date}", "", f"**完成率**: {plan.completion_rate}% ({plan.completed_count}/{plan.total_count})", "", "## 任务清单", ""]
        for t in plan.tasks:
            status = "[x]" if t.completed else "[ ]"
            prio = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t.priority, "")
            lines.append(f"- {status} {prio} {t.content} 「{t.category}」")
            if t.tomato_count > 0:
                lines.append(f"  - 🍅 番茄数: {t.tomato_count}")
        lines.extend(["", "## 备注", "", plan.daily_note if plan.daily_note else "无"])
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self, "导出成功", f"已保存到:\n{path}")

    def _export_csv(self, path):
        end = datetime.fromisoformat(self.current_date).date()
        start = end - timedelta(days=6)
        plans = self.storage.load_range(start.isoformat(), end.isoformat())
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["日期", "任务内容", "优先级", "分类", "完成状态", "番茄数"])
            for p in plans:
                for t in p.tasks:
                    writer.writerow([p.date, t.content, t.priority, t.category, "已完成" if t.completed else "未完成", t.tomato_count])
        QMessageBox.information(self, "导出成功", f"已保存到:\n{path}")

    def _export_json(self, path):
        dates = self.storage.get_all_dates()
        all_data = [self.storage.load_day(d).to_dict() for d in dates]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "导出成功", f"已备份 {len(all_data)} 天的数据")


# ============ 番茄钟组件 ============
class TomatoTimerWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 25 * 60
        self.remaining = self.total_seconds
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("🍅 番茄钟")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        header.addWidget(title)

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["15", "25", "45", "60"])
        self.duration_combo.setCurrentText("25")
        self.duration_combo.currentTextChanged.connect(self._change_duration)
        header.addWidget(self.duration_combo)
        layout.addLayout(header)

        self.lbl_time = QLabel("25:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setStyleSheet("font-size: 36px; font-weight: bold; color: #6366f1; font-family: 'Microsoft YaHei';")
        layout.addWidget(self.lbl_time)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e2e8f0;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background-color: #6366f1;
            }
        """)
        layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶ 开始")
        self.btn_start.setFixedHeight(36)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        self.btn_start.clicked.connect(self.start)
        btn_row.addWidget(self.btn_start)

        self.btn_pause = QPushButton("⏸ 暂停")
        self.btn_pause.setFixedHeight(36)
        self.btn_pause.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        self.btn_pause.clicked.connect(self.pause)
        btn_row.addWidget(self.btn_pause)

        self.btn_reset = QPushButton("↺")
        self.btn_reset.setFixedSize(36, 36)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #64748b;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cbd5e1;
            }
        """)
        self.btn_reset.clicked.connect(self.reset)
        btn_row.addWidget(self.btn_reset)

        layout.addLayout(btn_row)

    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _change_duration(self, text):
        if not self.is_running:
            mins = int(text)
            self.total_seconds = mins * 60
            self.remaining = self.total_seconds
            self.lbl_time.setText(self._format_time(self.remaining))
            self.progress.setValue(100)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.timer.start(1000)

    def pause(self):
        self.is_running = False
        self.timer.stop()

    def reset(self):
        self.pause()
        mins = int(self.duration_combo.currentText())
        self.total_seconds = mins * 60
        self.remaining = self.total_seconds
        self.lbl_time.setText(self._format_time(self.remaining))
        self.progress.setValue(100)

    def _tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            self.lbl_time.setText(self._format_time(self.remaining))
            pct = int(self.remaining / self.total_seconds * 100)
            self.progress.setValue(pct)
            # 颜色变化
            if pct < 30:
                self.progress.setStyleSheet("""
                    QProgressBar { border: none; border-radius: 3px; background-color: #e2e8f0; }
                    QProgressBar::chunk { border-radius: 3px; background-color: #ef4444; }
                """)
            elif pct < 60:
                self.progress.setStyleSheet("""
                    QProgressBar { border: none; border-radius: 3px; background-color: #e2e8f0; }
                    QProgressBar::chunk { border-radius: 3px; background-color: #f59e0b; }
                """)
            else:
                self.progress.setStyleSheet("""
                    QProgressBar { border: none; border-radius: 3px; background-color: #e2e8f0; }
                    QProgressBar::chunk { border-radius: 3px; background-color: #6366f1; }
                """)
        else:
            self._finish()

    def _finish(self):
        self.pause()
        self.progress.setValue(0)
        QMessageBox.information(self, "番茄钟完成", "专注时间结束，休息一下吧！")
        self.reset()


# ============ 主窗口 ============
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("每日计划")
        self.setMinimumSize(1000, 750)
        self.resize(1100, 800)

        self.storage = Storage()
        self.current_date = datetime.now().date().isoformat()
        self.day_plan = None

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- 左侧边栏 ----------
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: white; border-right: 1px solid #e2e8f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(16)

        # Logo
        logo = QLabel("📋 每日计划")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        sidebar_layout.addWidget(logo)

        sidebar_layout.addSpacing(20)

        # 日期导航
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: #f8fafc; border-radius: 12px;")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 8, 12, 8)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(32, 32)
        self.btn_prev.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #64748b;")
        self.btn_prev.clicked.connect(self._prev_day)
        nav_layout.addWidget(self.btn_prev)

        self.lbl_date = QLabel()
        self.lbl_date.setAlignment(Qt.AlignCenter)
        self.lbl_date.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        nav_layout.addWidget(self.lbl_date, 1)

        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(32, 32)
        self.btn_next.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #64748b;")
        self.btn_next.clicked.connect(self._next_day)
        nav_layout.addWidget(self.btn_next)

        sidebar_layout.addWidget(nav_frame)

        self.btn_today = QPushButton("📅 回到今天")
        self.btn_today.setFixedHeight(40)
        self.btn_today.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        self.btn_today.clicked.connect(self._go_today)
        sidebar_layout.addWidget(self.btn_today)

        sidebar_layout.addSpacing(20)

        # 功能按钮
        self.btn_stats = QPushButton("📊 统计")
        self.btn_stats.setFixedHeight(40)
        self.btn_stats.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border-radius: 10px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
        """)
        self.btn_stats.clicked.connect(self._open_stats)
        sidebar_layout.addWidget(self.btn_stats)

        self.btn_export = QPushButton("📤 导出")
        self.btn_export.setFixedHeight(40)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border-radius: 10px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
        """)
        self.btn_export.clicked.connect(self._open_export)
        sidebar_layout.addWidget(self.btn_export)

        sidebar_layout.addStretch()

        # 底部版权
        copyright = QLabel("v1.0 | 每日计划")
        copyright.setStyleSheet("font-size: 11px; color: #94a3b8;")
        copyright.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(copyright)

        main_layout.addWidget(sidebar)

        # ---------- 右侧内容区 ----------
        content = QFrame()
        content.setStyleSheet(f"background-color: {COLORS['bg']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(20)

        # 顶部标题 + 进度
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: white; border-radius: 16px; border: 1px solid #e2e8f0;")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(24, 20, 24, 20)

        top_row = QHBoxLayout()
        self.lbl_task_title = QLabel("今日任务")
        self.lbl_task_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        top_row.addWidget(self.lbl_task_title)

        self.lbl_task_count = QLabel("(0)")
        self.lbl_task_count.setStyleSheet("font-size: 16px; color: #94a3b8; font-family: 'Microsoft YaHei';")
        top_row.addWidget(self.lbl_task_count)
        top_row.addStretch()

        self.lbl_progress_percent = QLabel("0%")
        self.lbl_progress_percent.setStyleSheet("font-size: 18px; font-weight: bold; color: #6366f1; font-family: 'Microsoft YaHei';")
        top_row.addWidget(self.lbl_progress_percent)

        top_layout.addLayout(top_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        top_layout.addWidget(self.progress_bar)

        content_layout.addWidget(top_frame)

        # 中间：任务列表 + 添加栏
        middle_frame = QFrame()
        middle_frame.setStyleSheet("background-color: white; border-radius: 16px; border: 1px solid #e2e8f0;")
        middle_layout = QVBoxLayout(middle_frame)
        middle_layout.setContentsMargins(20, 20, 20, 20)
        middle_layout.setSpacing(12)

        # 筛选排序
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "未完成", "已完成", "高优先级", "工作", "学习", "生活", "其他"])
        self.filter_combo.currentTextChanged.connect(self._refresh_tasks)
        filter_row.addWidget(self.filter_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["优先级", "添加时间", "分类"])
        self.sort_combo.currentTextChanged.connect(self._refresh_tasks)
        filter_row.addWidget(self.sort_combo)

        filter_row.addStretch()
        middle_layout.addLayout(filter_row)

        # 任务列表滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.tasks_container = QFrame()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 8, 0)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.tasks_container)
        middle_layout.addWidget(scroll, 1)

        # 添加任务栏
        add_frame = QFrame()
        add_frame.setStyleSheet("background-color: #f8fafc; border-radius: 12px; border: 2px solid #6366f1;")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 12, 12, 12)
        add_layout.setSpacing(12)

        self.add_entry = QLineEdit()
        self.add_entry.setPlaceholderText("✏ 添加今日任务...")
        self.add_entry.returnPressed.connect(self._add_task)
        add_layout.addWidget(self.add_entry, 1)

        self.add_prio = QComboBox()
        self.add_prio.addItems(["高", "中", "低"])
        self.add_prio.setCurrentText("中")
        add_layout.addWidget(self.add_prio)

        self.add_cat = QComboBox()
        self.add_cat.addItems(CATEGORY_LABELS)
        self.add_cat.setCurrentText("其他")
        add_layout.addWidget(self.add_cat)

        self.btn_add = QPushButton("＋")
        self.btn_add.setFixedSize(40, 40)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        self.btn_add.clicked.connect(self._add_task)
        add_layout.addWidget(self.btn_add)

        middle_layout.addWidget(add_frame)
        content_layout.addWidget(middle_frame, 1)

        # 右侧底部：番茄钟 + 备注（两列）
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # 番茄钟
        self.tomato = TomatoTimerWidget()
        bottom_row.addWidget(self.tomato)

        # 备注
        note_frame = QFrame()
        note_frame.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        note_layout = QVBoxLayout(note_frame)
        note_layout.setContentsMargins(18, 18, 18, 18)

        note_title = QLabel("📝 每日备注")
        note_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; font-family: 'Microsoft YaHei';")
        note_layout.addWidget(note_title)

        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText("记录今天的想法、反思或重要事项...")
        self.note_text.textChanged.connect(self._save_note_debounced)
        note_layout.addWidget(self.note_text)

        bottom_row.addWidget(note_frame, 1)
        content_layout.addLayout(bottom_row)

        main_layout.addWidget(content, 1)

        # 备注保存防抖
        self._note_timer = QTimer()
        self._note_timer.setSingleShot(True)
        self._note_timer.timeout.connect(self._save_note)

        self.load_date(self.current_date)

    def _format_date(self, date_str):
        d = datetime.fromisoformat(date_str)
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return f"{d.month}月{d.day}日 {weekdays[d.weekday()]}"

    def load_date(self, date_str):
        self.current_date = date_str
        self.lbl_date.setText(self._format_date(date_str))
        self.day_plan = self.storage.load_day(date_str)
        self.note_text.blockSignals(True)
        self.note_text.setPlainText(self.day_plan.daily_note)
        self.note_text.blockSignals(False)
        self._update_overview()
        self._refresh_tasks()

    def _save(self):
        if self.day_plan:
            self.storage.save_day(self.day_plan)
            self._update_overview()

    def _update_overview(self):
        if not self.day_plan:
            return
        self.lbl_task_count.setText(f"({self.day_plan.total_count})")
        self.lbl_progress_percent.setText(f"{self.day_plan.completion_rate}%")
        self.progress_bar.setValue(int(self.day_plan.completion_rate))

        # 进度条颜色
        rate = self.day_plan.completion_rate
        if rate >= 80:
            color = "#22c55e"
        elif rate >= 50:
            color = "#6366f1"
        else:
            color = "#f59e0b"
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 4px; background-color: #e2e8f0; height: 8px; }}
            QProgressBar::chunk {{ border-radius: 4px; background-color: {color}; }}
        """)

    def _refresh_tasks(self):
        # 清空现有任务卡片（保留stretch）
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = list(self.day_plan.tasks)

        # 筛选
        f = self.filter_combo.currentText()
        if f == "未完成":
            tasks = [t for t in tasks if not t.completed]
        elif f == "已完成":
            tasks = [t for t in tasks if t.completed]
        elif f == "高优先级":
            tasks = [t for t in tasks if t.priority == "high"]
        elif f in CATEGORY_LABELS:
            tasks = [t for t in tasks if t.category == f]

        # 排序
        s = self.sort_combo.currentText()
        if s == "优先级":
            tasks.sort(key=lambda t: (-t.priority_value, t.created_at))
        elif s == "添加时间":
            tasks.sort(key=lambda t: t.created_at)
        elif s == "分类":
            tasks.sort(key=lambda t: t.category)

        if not tasks:
            empty = QLabel("📝\n还没有任务\n在下方添加今天的计划吧")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #cbd5e1; font-size: 16px; font-family: 'Microsoft YaHei'; padding: 40px;")
            self.tasks_layout.insertWidget(0, empty)
        else:
            for task in tasks:
                card = TaskCard(task, self._toggle_task, self._edit_task, self._delete_task)
                self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)

    def _prev_day(self):
        d = datetime.fromisoformat(self.current_date).date() - timedelta(days=1)
        self.load_date(d.isoformat())

    def _next_day(self):
        d = datetime.fromisoformat(self.current_date).date() + timedelta(days=1)
        self.load_date(d.isoformat())

    def _go_today(self):
        self.load_date(datetime.now().date().isoformat())

    def _add_task(self):
        content = self.add_entry.text().strip()
        if not content:
            return

        priority_map = {"高": "high", "中": "medium", "低": "low"}
        priority = priority_map.get(self.add_prio.currentText(), "medium")
        category = self.add_cat.currentText()

        task = Task(content=content, priority=priority, category=category)
        self.day_plan.tasks.append(task)
        self._save()
        self._refresh_tasks()
        self.add_entry.clear()
        self.add_entry.setFocus()

    def _toggle_task(self, task, completed):
        was_completed = task.completed
        task.mark_completed(completed)
        self._save()
        self._refresh_tasks()

        if completed and not was_completed:
            QTimer.singleShot(300, lambda: self._ask_tomato(task))

    def _ask_tomato(self, task):
        reply = QMessageBox.question(
            self, "任务完成 🎉",
            f"「{task.content}」已完成！\n\n是否为此任务记录一个番茄？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            task.tomato_count += 1
            self._save()
            self._refresh_tasks()

    def _edit_task(self, task):
        dialog = EditTaskDialog(task, self)
        if dialog.exec() == QDialog.Accepted:
            content, priority, category = dialog.get_result()
            task.content = content
            task.priority = priority
            task.category = category
            self._save()
            self._refresh_tasks()

    def _delete_task(self, task):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务「{task.content}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.day_plan.tasks.remove(task)
            self._save()
            self._refresh_tasks()

    def _save_note_debounced(self):
        self._note_timer.stop()
        self._note_timer.start(500)

    def _save_note(self):
        if self.day_plan:
            self.day_plan.daily_note = self.note_text.toPlainText().strip()
            self._save()

    def _open_stats(self):
        StatsDialog(self.storage, self).exec()

    def _open_export(self):
        ExportDialog(self.storage, self.current_date, self).exec()
