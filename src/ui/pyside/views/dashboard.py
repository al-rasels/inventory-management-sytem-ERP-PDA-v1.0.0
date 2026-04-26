"""
Dashboard View – Executive overview with QtAwesome icons, background loading, and chart.
"""
from __future__ import annotations

import csv
import logging
from datetime import date
from typing import Optional, List, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableView,
    QHeaderView, QAbstractItemView, QPushButton, QProgressBar,
    QStackedWidget, QTextEdit, QSplitter, QComboBox, QMenu, QMessageBox,
    QApplication, QStyle, QFileDialog
)

try:
    from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QPainter
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False

from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import IconKPICard

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Icon‑based KPICard (unified across views)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# Background worker
# ------------------------------------------------------------------
class DashboardWorker(QThread):
    summary_ready = Signal(dict)          # {revenue, profit}
    stock_count_ready = Signal(int)       # active products
    alerts_ready = Signal(list)           # list of low‑stock dicts
    recent_ready = Signal(list)           # recent activity list
    error_occurred = Signal(str)

    def __init__(
        self,
        inventory_service,
        reporting_service,
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        super().__init__()
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service
        self.days = days
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            # 1. Sales summary
            summary = self.reporting_service.get_sales_summary(
                days=self.days,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            summary_dict = {
                'revenue': float(summary.get('revenue', 0)),
                'profit': float(summary.get('profit', 0)),
            }
            self.summary_ready.emit(summary_dict)

            # 2. Active product count
            stock_df = self.inventory_service.get_stock_status()
            count = len(stock_df) if stock_df is not None else 0
            self.stock_count_ready.emit(count)

            # 3. Low‑stock alerts
            alerts_df = self.reporting_service.get_reorder_alerts()
            alerts_list = []
            if alerts_df is not None and not alerts_df.empty:
                for _, row in alerts_df.iterrows():
                    alerts_list.append({
                        'name': str(row['name']),
                        'stock': int(row['current_stock']),
                    })
            self.alerts_ready.emit(alerts_list)

            # 4. Recent activity
            recent_df = self.reporting_service.get_recent_activity(limit=20)
            recent_list = []
            if recent_df is not None and not recent_df.empty:
                for _, row in recent_df.iterrows():
                    d = row['date']
                    date_str = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)[:10]
                    recent_list.append({
                        'type': str(row['type']),
                        'name': str(row['name']),
                        'amount': float(row['amt']),
                        'date': date_str,
                    })
            self.recent_ready.emit(recent_list)

        except Exception as e:
            logger.exception("Dashboard worker failed")
            self.error_occurred.emit(str(e))


# ------------------------------------------------------------------
# Main Dashboard Widget
# ------------------------------------------------------------------
class PySideDashboard(QWidget):
    def __init__(self, inventory_service, reporting_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service
        self._worker: Optional[DashboardWorker] = None

        self._current_summary = {}
        self._alerts_list = []
        self._recent_list = []

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

        # Content stack (normal / loading / error)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_content())          # index 0
        self.stack.addWidget(self._build_loading_widget())   # index 1
        self.stack.addWidget(self._build_error_widget())     # index 2
        main_layout.addWidget(self.stack, stretch=1)

        # Shortcuts & context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        self.addAction(refresh_action)

        export_action = QAction("Export Alerts CSV", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_csv)
        self.addAction(export_action)

    def _build_toolbar(self, parent_layout):
        toolbar = QFrame()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 0, 16, 0)

        # Icon + title
        icon_label = QLabel()
        icon_label.setPixmap(qta_icon('fa5s.home', color=Theme.TEXT_PRIMARY).pixmap(20, 20))
        layout.addWidget(icon_label)

        title = QLabel("Executive Dashboard")
        title.setStyleSheet(Theme.label_title())
        layout.addWidget(title)
        layout.addStretch()

        # Timeframe
        layout.addWidget(QLabel(
            "Timeframe:",
            styleSheet=f"color: {Theme.TEXT_MUTED}; font-weight: bold; border: none; background: transparent;"
        ))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Today", "Last 7 Days", "Last 30 Days", "This Year", "All Time"])
        self.time_combo.setCurrentText("Last 30 Days")
        self.time_combo.setStyleSheet(Theme.combo_style())
        layout.addWidget(self.time_combo)

        # Refresh button
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(qta_icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.setText(" Refresh")
        self.refresh_btn.setStyleSheet(Theme.btn_primary())
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

        parent_layout.addWidget(toolbar)

    def _build_kpi_row(self, parent_layout):
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.kpi_revenue = IconKPICard(
            "Revenue", "৳ 0",
            qta_icon('fa5s.money-bill-wave', color=Theme.ACCENT), Theme.ACCENT
        )
        self.kpi_profit = IconKPICard(
            "Net Profit", "৳ 0",
            qta_icon('fa5s.coins', color=Theme.SUCCESS), Theme.SUCCESS
        )
        self.kpi_products = IconKPICard(
            "Active Products", "0",
            qta_icon('fa5s.box', color=Theme.PURPLE), Theme.PURPLE
        )
        self.kpi_alerts = IconKPICard(
            "Low Stock Alerts", "0",
            qta_icon('fa5s.exclamation-triangle', color=Theme.SUCCESS), Theme.SUCCESS
        )

        for w in [self.kpi_revenue, self.kpi_profit, self.kpi_products, self.kpi_alerts]:
            kpi_layout.addWidget(w)
        parent_layout.addLayout(kpi_layout)

    def _build_content(self):
        splitter = QSplitter(Qt.Horizontal)

        # Left panel – Recent Activity
        recent_frame = QFrame()
        recent_frame.setStyleSheet(Theme.card_style())
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(12, 12, 12, 12)

        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.clock', color=Theme.TEXT_PRIMARY).pixmap(18, 18))
        title_row.addWidget(title_icon)
        recent_title = QLabel("Recent Activity")
        recent_title.setStyleSheet(Theme.label_title())
        title_row.addWidget(recent_title)
        title_row.addStretch()
        recent_layout.addLayout(title_row)

        self.recent_model = QStandardItemModel(0, 4)
        self.recent_model.setHorizontalHeaderLabels(["Type", "Product", "Amount", "Date"])
        self.recent_table = QTableView()
        self.recent_table.setModel(self.recent_model)
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent_table.setSortingEnabled(True)
        self.recent_table.setStyleSheet(Theme.tableview_style())
        self.recent_table.setShowGrid(False)
        recent_layout.addWidget(self.recent_table)
        splitter.addWidget(recent_frame)

        # Right panel – Low Stock + optional chart
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        alert_frame = QFrame()
        alert_frame.setStyleSheet(Theme.card_style())
        alert_layout = QVBoxLayout(alert_frame)
        alert_layout.setContentsMargins(12, 12, 12, 12)

        alert_title_row = QHBoxLayout()
        alert_icon = QLabel()
        alert_icon.setPixmap(qta_icon('fa5s.exclamation-triangle', color=Theme.TEXT_PRIMARY).pixmap(18, 18))
        alert_title_row.addWidget(alert_icon)
        alert_title = QLabel("Low Stock Alerts")
        alert_title.setStyleSheet(Theme.label_title())
        alert_title_row.addWidget(alert_title)
        alert_title_row.addStretch()
        alert_layout.addLayout(alert_title_row)

        self.alert_model = QStandardItemModel(0, 2)
        self.alert_model.setHorizontalHeaderLabels(["Product", "Stock"])
        self.alert_table = QTableView()
        self.alert_table.setModel(self.alert_model)
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alert_table.verticalHeader().setVisible(False)
        self.alert_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.alert_table.setSortingEnabled(True)
        self.alert_table.setStyleSheet(Theme.tableview_style())
        self.alert_table.setShowGrid(False)
        alert_layout.addWidget(self.alert_table)
        right_layout.addWidget(alert_frame, stretch=1)

        if HAS_CHARTS:
            self.chart_view = QChartView()
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            right_layout.addWidget(self.chart_view, stretch=1)

        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        return splitter

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Loading dashboard data...")
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        layout.addWidget(lbl)
        prog = QProgressBar()
        prog.setRange(0, 0)
        prog.setFixedWidth(300)
        layout.addWidget(prog, alignment=Qt.AlignCenter)
        return w

    def _build_error_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32))
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
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
        self.time_combo.currentTextChanged.connect(self._start_loading)

    # ----- Data loading ----------------------------------------------------
    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        sel = self.time_combo.currentText()
        days_map = {"Today": 1, "Last 7 Days": 7, "Last 30 Days": 30, "This Year": 365, "All Time": None}
        days = days_map.get(sel, 30)

        self.stack.setCurrentIndex(1)

        self._worker = DashboardWorker(
            self.inventory_service,
            self.reporting_service,
            days=days,
        )
        self._worker.summary_ready.connect(self._on_summary)
        self._worker.stock_count_ready.connect(self._on_stock_count)
        self._worker.alerts_ready.connect(self._on_alerts)
        self._worker.recent_ready.connect(self._on_recent)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(dict)
    def _on_summary(self, s: dict):
        self._current_summary = s

    @Slot(int)
    def _on_stock_count(self, count: int):
        self.kpi_products.set_value(str(count))

    @Slot(list)
    def _on_alerts(self, alerts: list):
        self._alerts_list = alerts
        self.kpi_alerts.set_value(str(len(alerts)))
        alert_color = Theme.DANGER if len(alerts) > 0 else Theme.SUCCESS
        self.kpi_alerts.set_color(alert_color)

        self.alert_model.removeRows(0, self.alert_model.rowCount())
        if not alerts:
            placeholder = QStandardItem("All stock levels are healthy")
            placeholder.setSelectable(False)
            self.alert_model.appendRow([placeholder])
            return

        for a in alerts:
            name_item = QStandardItem(a['name'])
            stock_item = QStandardItem(str(a['stock']))
            stock_item.setForeground(QColor(Theme.DANGER))
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.alert_model.appendRow([name_item, stock_item])

    @Slot(list)
    def _on_recent(self, recent: list):
        self._recent_list = recent
        self.recent_model.removeRows(0, self.recent_model.rowCount())
        if not recent:
            placeholder = QStandardItem("No recent activity")
            placeholder.setSelectable(False)
            self.recent_model.appendRow([placeholder])
            self._finalise_ui_updates()
            return

        for r in recent:
            type_text = "Sale" if r['type'] == 'SALE' else "Purchase"
            color = Theme.SUCCESS if r['type'] == 'SALE' else Theme.ORANGE
            type_item = QStandardItem(type_text)
            type_item.setForeground(QColor(color))
            name_item = QStandardItem(r['name'])
            amt_item = QStandardItem(f"৳ {r['amount']:,.0f}")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            date_item = QStandardItem(r['date'])
            self.recent_model.appendRow([type_item, name_item, amt_item, date_item])

        self._finalise_ui_updates()

    def _finalise_ui_updates(self):
        rev = self._current_summary.get('revenue', 0) or 0
        prof = self._current_summary.get('profit', 0) or 0
        self.kpi_revenue.set_value(f"৳ {rev:,.0f}")
        self.kpi_profit.set_value(f"৳ {prof:,.0f}")

        if HAS_CHARTS and self._recent_list:
            self._update_chart()

        self.stack.setCurrentIndex(0)

    def _update_chart(self):
        sales_total = sum(r['amount'] for r in self._recent_list if r['type'] == 'SALE')
        purchases_total = sum(r['amount'] for r in self._recent_list if r['type'] != 'SALE')

        set_sales = QBarSet("Sales")
        set_purchases = QBarSet("Purchases")
        set_sales.append(sales_total)
        set_purchases.append(purchases_total)

        series = QBarSeries()
        series.append(set_sales)
        series.append(set_purchases)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Recent Activity Summary")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_y = QValueAxis()
        axis_y.setTitleText("Amount (৳)")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        self.chart_view.setChart(chart)

    @Slot(str)
    def _on_error(self, msg: str):
        logger.error(f"Dashboard error: {msg}")
        self.error_label.setText("Failed to load dashboard data.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    # ----- Public actions --------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Low Stock Alerts", "low_stock.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Product", "Stock"])
                for a in self._alerts_list:
                    writer.writerow([a['name'], a['stock']])
            QMessageBox.information(self, "Export", f"Alerts exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; "
            f"border: 1px solid {Theme.BORDER}; padding: 4px; }} "
            f"QMenu::item {{ padding: 8px 20px; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}"
        )
        menu.addAction(qta_icon('fa5s.sync-alt', color=Theme.TEXT_PRIMARY), "Refresh", self.refresh, QKeySequence("F5"))
        menu.addAction(qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY), "Export Alerts CSV", self.export_csv, QKeySequence("Ctrl+E"))
        menu.exec_(self.mapToGlobal(pos))