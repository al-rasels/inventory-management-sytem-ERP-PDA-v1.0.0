"""
Production‑grade Analytics View – QtAwesome icons, dual export, chart support.
"""
from __future__ import annotations

import csv
import logging
from datetime import date
from typing import Optional, Dict, List, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QDate, QDateTime, QTime
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
    QTableView, QHeaderView, QFrame, QPushButton, QProgressBar,
    QMessageBox, QSplitter, QMenu, QAbstractItemView, QApplication,
    QStyle, QStackedWidget, QTextEdit, QFileDialog
)

# optional chart support
try:
    from PySide6.QtCharts import (
        QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
    )
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QPainter
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False

from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import KPICard

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Background worker
# ------------------------------------------------------------------
class AnalyticsWorker(QThread):
    summary_ready = Signal(dict)
    categories_ready = Signal(list)
    trend_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(
        self,
        report_service,
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        super().__init__()
        self.report_service = report_service
        self.days = days
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            # Convert dates to strings for SQL
            s_date = self.start_date.strftime("%Y-%m-%d") if self.start_date else None
            e_date = self.end_date.strftime("%Y-%m-%d") if self.end_date else None

            # 1. Sales summary
            summary = self.report_service.get_sales_summary(
                days=self.days,
                start_date=s_date,
                end_date=e_date,
            )
            summary = {
                'revenue': float(summary.get('revenue', 0)),
                'profit': float(summary.get('profit', 0)),
                'sales_count': int(summary.get('sales_count', 0)),
            }
            self.summary_ready.emit(summary)

            # 2. Category breakdown
            cat_df = self.report_service.get_profit_by_category(
                days=self.days,
                start_date=s_date,
                end_date=e_date,
            )
            cat_list = []
            if cat_df is not None and not cat_df.empty:
                for _, row in cat_df.iterrows():
                    cat_list.append({
                        'category': str(row['category']),
                        'revenue': float(row['rev']),
                        'profit': float(row['prof']),
                        'margin': float(row.get('margin', 0)),
                    })
            self.categories_ready.emit(cat_list)

            # 3. Daily trend
            trend_df = self.report_service.get_daily_sales_trend(
                days=self.days,
                start_date=s_date,
                end_date=e_date,
            )
            trend_list = []
            if trend_df is not None and not trend_df.empty:
                for _, row in trend_df.iterrows():
                    date_val = row['date']
                    if isinstance(date_val, str):
                        qdate = QDate.fromString(date_val[:10], "yyyy-MM-dd")
                    elif hasattr(date_val, 'toordinal'):
                        qdate = QDate(date_val)
                    else:
                        qdate = QDate.currentDate()
                    trend_list.append({
                        'date': qdate,
                        'revenue': float(row.get('daily_rev', 0)),
                    })
            self.trend_ready.emit(trend_list)

        except Exception as e:
            logger.exception("Analytics worker failed")
            self.error_occurred.emit(str(e))


# ------------------------------------------------------------------
# Main widget
# ------------------------------------------------------------------
class PySideAnalytics(QWidget):
    def __init__(self, report_service, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self._worker: Optional[AnalyticsWorker] = None
        self._current_summary = {}
        self._categories_data = []
        self._trend_data = []

        self._setup_ui()
        self._connect_signals()
        self._start_loading()

    # ----- UI construction -------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        self._build_toolbar(main_layout)
        self._build_kpi_row(main_layout)

        content_wrapper = QVBoxLayout()
        content_wrapper.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_content())    # index 0
        self.stack.addWidget(self._build_loading_widget())  # index 1
        self.stack.addWidget(self._build_error_widget())    # index 2
        content_wrapper.addWidget(self.stack)

        main_layout.addLayout(content_wrapper, stretch=1)

        # Context menu & shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        export_category_action = QAction("Export Category CSV", self)
        export_category_action.setShortcut(QKeySequence("Ctrl+E"))
        export_category_action.triggered.connect(lambda: self.export_csv("category"))
        self.addAction(export_category_action)

        export_trend_action = QAction("Export Trend CSV", self)
        export_trend_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_trend_action.triggered.connect(lambda: self.export_csv("trend"))
        self.addAction(export_trend_action)

        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        self.addAction(refresh_action)

    def _build_toolbar(self, parent_layout):
        frame = QFrame()
        frame.setFixedHeight(56)
        frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        # Icon + Title
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.chart-line', color=Theme.TEXT_PRIMARY).pixmap(20, 20))
        layout.addWidget(title_icon)

        title = QLabel("Business Analytics")
        title.setStyleSheet(Theme.label_title())
        layout.addWidget(title)
        layout.addStretch()

        layout.addWidget(QLabel(
            "Timeframe:",
            styleSheet=f"color: {Theme.TEXT_MUTED}; font-weight: bold; border: none; background: transparent;"
        ))

        self.time_combo = QComboBox()
        self.time_combo.addItems(list(TIME_PRESETS.keys()))
        self.time_combo.setCurrentText("Last 30 Days")
        self.time_combo.setStyleSheet(Theme.combo_style())
        layout.addWidget(self.time_combo)

        # Custom date widgets
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_start.setStyleSheet(Theme.combo_style())
        self.date_start.setVisible(False)
        layout.addWidget(self.date_start)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setStyleSheet(Theme.combo_style())
        self.date_end.setVisible(False)
        layout.addWidget(self.date_end)

        self.btn_apply_custom = QPushButton("Apply")
        self.btn_apply_custom.setVisible(False)
        self.btn_apply_custom.clicked.connect(self.refresh)
        layout.addWidget(self.btn_apply_custom)

        parent_layout.addWidget(frame)

    def _build_kpi_row(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(12)

        self.kpi_rev = KPICard("Revenue", "৳ 0",
                               qta_icon('fa5s.money-bill-wave', color=Theme.ACCENT),
                               Theme.ACCENT)
        self.kpi_prof = KPICard("Profit", "৳ 0",
                                qta_icon('fa5s.chart-line', color=Theme.SUCCESS),
                                Theme.SUCCESS)
        self.kpi_margin = KPICard("Avg Margin", "0%",
                                  qta_icon('fa5s.percent', color=Theme.ORANGE),
                                  Theme.ORANGE)
        self.kpi_orders = KPICard("Total Sales", "0",
                                  qta_icon('fa5s.shopping-cart', color=Theme.PURPLE),
                                  Theme.PURPLE)

        for w in [self.kpi_rev, self.kpi_prof, self.kpi_margin, self.kpi_orders]:
            row.addWidget(w)
        parent_layout.addLayout(row)

    def _build_content(self):
        splitter = QSplitter(Qt.Horizontal)

        # Left: category breakdown
        cat_frame = QFrame()
        cat_frame.setStyleSheet(Theme.card_style())
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(12, 12, 12, 12)
        cat_layout.addWidget(QLabel("Profit by Category", styleSheet=Theme.label_title()))

        self.cat_model = QStandardItemModel(0, 4)
        self.cat_model.setHorizontalHeaderLabels(["Category", "Revenue", "Profit", "Margin"])
        self.cat_table = QTableView()
        self.cat_table.setModel(self.cat_model)
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cat_table.setSortingEnabled(True)
        self.cat_table.setStyleSheet(Theme.tableview_style())
        self.cat_table.setShowGrid(False)
        cat_layout.addWidget(self.cat_table)
        splitter.addWidget(cat_frame)

        # Right: trend table + optional chart
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        if HAS_CHARTS:
            self.chart_view = QChartView()
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            right_layout.addWidget(self.chart_view, stretch=1)

        trend_frame = QFrame()
        trend_frame.setStyleSheet(Theme.card_style())
        trend_layout = QVBoxLayout(trend_frame)
        trend_layout.setContentsMargins(12, 12, 12, 12)
        trend_layout.addWidget(QLabel("Daily Sales Trend", styleSheet=Theme.label_title()))

        self.trend_model = QStandardItemModel(0, 2)
        self.trend_model.setHorizontalHeaderLabels(["Date", "Revenue"])
        self.trend_table = QTableView()
        self.trend_table.setModel(self.trend_model)
        self.trend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.trend_table.setSortingEnabled(True)
        self.trend_table.setStyleSheet(Theme.tableview_style())
        self.trend_table.setShowGrid(False)
        trend_layout.addWidget(self.trend_table)

        right_layout.addWidget(trend_frame, stretch=1)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 600])
        return splitter

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        self.loading_label = QLabel("Loading analytics data...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        layout.addWidget(self.loading_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(300)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)
        return w

    def _build_error_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(f"color: {Theme.DANGER}; font-weight: bold;")
        layout.addWidget(self.error_label)

        self.error_detail = QTextEdit()
        self.error_detail.setReadOnly(True)
        self.error_detail.setMaximumHeight(80)
        self.error_detail.setVisible(False)
        layout.addWidget(self.error_detail)

        retry_btn = QPushButton("Retry")
        retry_btn.clicked.connect(self.refresh)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)

        return w

    # ----- Signal wiring ---------------------------------------------------
    def _connect_signals(self):
        self.time_combo.currentTextChanged.connect(self._on_timeframe_changed)
        self.date_start.dateChanged.connect(self._clear_custom_apply_highlight)
        self.date_end.dateChanged.connect(self._clear_custom_apply_highlight)

    def _on_timeframe_changed(self, text):
        show_custom = (text == "Custom Range...")
        self.date_start.setVisible(show_custom)
        self.date_end.setVisible(show_custom)
        self.btn_apply_custom.setVisible(show_custom)

        if not show_custom:
            self._start_loading()

    def _clear_custom_apply_highlight(self):
        pass

    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        selected = self.time_combo.currentText()
        days = TIME_PRESETS.get(selected)
        start = end = None
        if selected == "Custom Range...":
            start = self.date_start.date().toPython()
            end = self.date_end.date().toPython()
            if start > end:
                start, end = end, start
            days = None

        self.stack.setCurrentIndex(1)

        self._worker = AnalyticsWorker(
            self.report_service,
            days=days,
            start_date=start,
            end_date=end,
        )
        self._worker.summary_ready.connect(self._on_summary_ready)
        self._worker.categories_ready.connect(self._on_categories_ready)
        self._worker.trend_ready.connect(self._on_trend_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(dict)
    def _on_summary_ready(self, summary):
        self._current_summary = summary

    @Slot(list)
    def _on_categories_ready(self, data):
        self._categories_data = data
        self._populate_category_table()

    @Slot(list)
    def _on_trend_ready(self, data):
        self._trend_data = data
        self._populate_trend_table()
        if HAS_CHARTS:
            self._update_chart()
        self.stack.setCurrentIndex(0)

    @Slot(str)
    def _on_error(self, msg):
        logger.error(f"Analytics error: {msg}")
        self.error_label.setText("Failed to load analytics data.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    def _populate_category_table(self):
        self.cat_model.removeRows(0, self.cat_model.rowCount())
        for cat in self._categories_data:
            cat_item = QStandardItem(cat['category'])
            rev_item = QStandardItem(f"৳ {cat['revenue']:,.0f}")
            prof_item = QStandardItem(f"৳ {cat['profit']:,.0f}")
            margin = cat.get('margin', 0)
            margin_item = QStandardItem(f"{margin:.1f}%")

            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            prof_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            margin_item.setTextAlignment(Qt.AlignCenter)

            if cat['profit'] > 0:
                prof_item.setForeground(QColor(Theme.SUCCESS))
            elif cat['profit'] < 0:
                prof_item.setForeground(QColor(Theme.DANGER))

            self.cat_model.appendRow([cat_item, rev_item, prof_item, margin_item])

        s = self._current_summary
        rev = s.get('revenue', 0) or 0
        prof = s.get('profit', 0) or 0
        orders = s.get('sales_count', 0) or 0
        margin = (prof / rev * 100) if rev != 0 else None

        self.kpi_rev.set_value(f"৳ {rev:,.0f}")
        self.kpi_prof.set_value(f"৳ {prof:,.0f}")
        self.kpi_margin.set_value(f"{margin:.1f}%" if margin is not None else "—")
        self.kpi_orders.set_value(str(orders))

    def _populate_trend_table(self):
        self.trend_model.removeRows(0, self.trend_model.rowCount())
        for t in self._trend_data:
            date_item = QStandardItem(t['date'].toString("yyyy-MM-dd"))
            rev_item = QStandardItem(f"৳ {t['revenue']:,.0f}")
            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.trend_model.appendRow([date_item, rev_item])

    def _update_chart(self):
        if not self._trend_data:
            return

        series = QLineSeries()
        series.setName("Revenue")
        for t in self._trend_data:
            dt = QDateTime(t['date'], QTime(0, 0))
            series.append(dt.toMSecsSinceEpoch(), t['revenue'])

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Daily Revenue")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM dd")
        axis_x.setTitleText("Date")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Revenue (৳)")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        self.chart_view.setChart(chart)

    def export_csv(self, data_type="category"):
        if data_type == "category":
            path, _ = QFileDialog.getSaveFileName(self, "Export Category Data", "categories.csv", "CSV Files (*.csv)")
            if not path: return
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Category", "Revenue", "Profit", "Margin"])
                    for cat in self._categories_data:
                        writer.writerow([cat['category'], f"{cat['revenue']:.2f}", f"{cat['profit']:.2f}", f"{cat['margin']:.1f}"])
                QMessageBox.information(self, "Export", f"Data exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
        else:  # trend
            path, _ = QFileDialog.getSaveFileName(self, "Export Trend Data", "daily_sales.csv", "CSV Files (*.csv)")
            if not path: return
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Revenue"])
                    for t in self._trend_data:
                        writer.writerow([t['date'].toString("yyyy-MM-dd"), f"{t['revenue']:.2f}"])
                QMessageBox.information(self, "Export", f"Data exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px; }} QMenu::item {{ padding: 8px 20px; }} QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}")

        menu.addAction(qta_icon('fa5s.sync-alt', color=Theme.TEXT_PRIMARY), "Refresh", self.refresh, QKeySequence("F5"))
        menu.addSeparator()
        menu.addAction(qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY), "Export Category CSV", lambda: self.export_csv("category"), QKeySequence("Ctrl+E"))
        menu.addAction(qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY), "Export Trend CSV", lambda: self.export_csv("trend"), QKeySequence("Ctrl+Shift+E"))
        menu.exec_(self.mapToGlobal(pos))


# ------------------------------------------------------------------
# Presets
# ------------------------------------------------------------------
TIME_PRESETS = {
    "Today": 1,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "This Year": 365,
    "Custom Range...": None,
    "All Time": None,
}