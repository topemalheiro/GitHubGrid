from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt, QPoint, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from .models import ContributionData, ContributionDay, ContributionLevel

# GitHub dark theme colors
BG_COLOR = QColor(13, 17, 23)
SURFACE_COLOR = QColor(22, 27, 34)
TEXT_COLOR = QColor(230, 237, 243)
SECONDARY_TEXT_COLOR = QColor(139, 148, 158)
BORDER_COLOR = QColor(48, 54, 61)
ACCENT_COLOR = QColor(35, 134, 54)

LEVEL_COLORS = {
    ContributionLevel.NONE: QColor(22, 27, 34),
    ContributionLevel.FIRST_QUARTILE: QColor(14, 68, 41),
    ContributionLevel.SECOND_QUARTILE: QColor(0, 109, 50),
    ContributionLevel.THIRD_QUARTILE: QColor(38, 166, 65),
    ContributionLevel.FOURTH_QUARTILE: QColor(57, 211, 83),
}

CELL_SIZE = 13
CELL_GAP = 3
CELL_STRIDE = CELL_SIZE + CELL_GAP


def _day_suffix(day: int) -> str:
    if day in (1, 21, 31):
        return "st"
    if day in (2, 22):
        return "nd"
    if day in (3, 23):
        return "rd"
    return "th"


def _format_tooltip(day: ContributionDay) -> str:
    count = day.contribution_count
    count_str = (
        "No contributions"
        if count == 0
        else f"{count} contribution{'s' if count != 1 else ''}"
    )
    return f"{count_str} on {day.date.strftime('%B %d')}{_day_suffix(day.date.day)}."


class ContributionCell(QWidget):
    def __init__(self, day: ContributionDay, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.day = day
        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        self.setToolTip(_format_tooltip(day))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(LEVEL_COLORS[self.day.level])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 2, 2)
        painter.end()


class GridWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data: Optional[ContributionData] = None
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        # Default size for ~1 year of data
        self._default_width = 53 * CELL_STRIDE - CELL_GAP
        self._default_height = 7 * CELL_STRIDE - CELL_GAP
        self.setMinimumSize(self._default_width, self._default_height)

    def set_data(self, data: Optional[ContributionData]):
        self._data = data
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        if self._data is None:
            return QSize(self._default_width, self._default_height)
        width = len(self._data.weeks) * CELL_STRIDE - CELL_GAP
        height = 7 * CELL_STRIDE - CELL_GAP
        return QSize(max(width, self._default_width), max(height, self._default_height))

    @staticmethod
    def _row_for_day(d: date) -> int:
        """Sunday=0 like C# DayOfWeek, not Python's Monday=0 weekday()."""
        return (d.weekday() + 1) % 7

    def _day_at(self, pos: QPoint) -> Optional[ContributionDay]:
        if self._data is None:
            return None
        week_idx = pos.x() // CELL_STRIDE
        day_idx = pos.y() // CELL_STRIDE
        if 0 <= week_idx < len(self._data.weeks):
            week = self._data.weeks[week_idx]
            for day in week.days:
                if self._row_for_day(day.date) == day_idx:
                    return day
        return None

    def mouseMoveEvent(self, event):
        day = self._day_at(event.pos())
        if day:
            self.setToolTip(_format_tooltip(day))
        else:
            self.setToolTip("")
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        if self._data is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        for week_idx, week in enumerate(self._data.weeks):
            for day in week.days:
                row_idx = self._row_for_day(day.date)
                x = week_idx * CELL_STRIDE
                y = row_idx * CELL_STRIDE
                painter.setBrush(LEVEL_COLORS[day.level])
                painter.drawRoundedRect(QRectF(x, y, CELL_SIZE, CELL_SIZE), 2, 2)

        painter.end()


class MonthLabelsWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data: Optional[ContributionData] = None
        self.setFixedHeight(16)
        self._default_width = 53 * CELL_STRIDE - CELL_GAP
        self.setMinimumWidth(self._default_width)

    def set_data(self, data: Optional[ContributionData]):
        self._data = data
        if data:
            self.setFixedWidth(max(len(data.weeks) * CELL_STRIDE - CELL_GAP, self._default_width))
        else:
            self.setFixedWidth(self._default_width)
        self.update()

    def paintEvent(self, event):
        if self._data is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("sans-serif", 9)
        painter.setFont(font)
        painter.setPen(SECONDARY_TEXT_COLOR)

        last_month = -1
        for week_idx, week in enumerate(self._data.weeks):
            if not week.days:
                continue
            month = week.days[0].date.month
            if month != last_month:
                last_month = month
                name = week.days[0].date.strftime("%b")
                painter.drawText(week_idx * CELL_STRIDE, 12, name)

        painter.end()


class DayLabelsWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedWidth(30)
        self.setFixedHeight(7 * CELL_STRIDE - CELL_GAP)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("sans-serif", 9)
        painter.setFont(font)
        painter.setPen(SECONDARY_TEXT_COLOR)

        labels = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
        for row, name in labels:
            painter.drawText(0, row * CELL_STRIDE + 10, name)

        painter.end()


class LegendWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(74, 13)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        levels = [
            ContributionLevel.NONE,
            ContributionLevel.FIRST_QUARTILE,
            ContributionLevel.SECOND_QUARTILE,
            ContributionLevel.THIRD_QUARTILE,
            ContributionLevel.FOURTH_QUARTILE,
        ]
        for i, level in enumerate(levels):
            painter.setBrush(LEVEL_COLORS[level])
            painter.drawRoundedRect(QRectF(i * 15, 0, 11, 11), 2, 2)

        painter.end()


class ContributionGridWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._data: Optional[ContributionData] = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        # Main container with rounded border
        self.container = QWidget(self)
        self.container.setObjectName("container")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        # Header: status + refresh button
        header = QHBoxLayout()
        header.setSpacing(10)

        self.status_label = QLabel("Loading...")
        self.status_label.setFont(QFont("sans-serif", 13, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {TEXT_COLOR.name()};")
        header.addWidget(self.status_label)

        header.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setObjectName("refreshBtn")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setFixedHeight(28)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)
        layout.addSpacing(12)

        # Month labels
        self.month_labels = MonthLabelsWidget()
        month_layout = QHBoxLayout()
        month_layout.addSpacing(30)
        month_layout.addWidget(self.month_labels)
        layout.addLayout(month_layout)
        layout.addSpacing(2)

        # Day labels + grid
        grid_row = QHBoxLayout()
        grid_row.setSpacing(0)
        self.day_labels = DayLabelsWidget()
        grid_row.addWidget(self.day_labels)
        self.grid_widget = GridWidget()
        grid_row.addWidget(self.grid_widget)
        layout.addLayout(grid_row)
        layout.addSpacing(10)

        # Footer: today + legend
        footer = QHBoxLayout()
        footer.setSpacing(10)

        self.today_label = QLabel("")
        self.today_label.setFont(QFont("sans-serif", 10))
        self.today_label.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR.name()};")
        footer.addWidget(self.today_label)

        footer.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        legend_label_less = QLabel("Less")
        legend_label_less.setFont(QFont("sans-serif", 9))
        legend_label_less.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR.name()};")
        footer.addWidget(legend_label_less)
        footer.addWidget(LegendWidget())
        legend_label_more = QLabel("More")
        legend_label_more.setFont(QFont("sans-serif", 9))
        legend_label_more.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR.name()};")
        footer.addWidget(legend_label_more)

        layout.addLayout(footer)

        # Main window layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

    def _apply_styles(self):
        self.container.setStyleSheet(f"""
            QWidget#container {{
                background-color: {BG_COLOR.name()};
                border: 1px solid {BORDER_COLOR.name()};
                border-radius: 12px;
            }}
            QPushButton#refreshBtn {{
                background-color: {SURFACE_COLOR.name()};
                color: #C9D1D9;
                border: 1px solid {BORDER_COLOR.name()};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton#refreshBtn:hover {{
                background-color: {BORDER_COLOR.name()};
            }}
            QPushButton#refreshBtn:pressed {{
                background-color: #3B434B;
            }}
            QToolTip {{
                background-color: #1B1F23;
                color: #E6EDF3;
                border: 1px solid {BORDER_COLOR.name()};
                padding: 5px 8px;
                font-size: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(20)
        shadow.setOffset(4, 4)
        shadow.setColor(QColor(0, 0, 0, 153))
        self.container.setGraphicsEffect(shadow)

    def set_data(self, data: Optional[ContributionData]):
        self._data = data
        self.grid_widget.set_data(data)
        self.month_labels.set_data(data)

        if data:
            self.status_label.setText(f"{data.total_contributions} contributions in the last year")
            self._update_today()
        else:
            self.status_label.setText("Failed to connect. Check gh CLI authentication.")
            self.today_label.setText("")

        self.adjustSize()

    def _update_today(self):
        if self._data is None:
            self.today_label.setText("")
            return

        today = date.today()
        today_day = None
        for week in self._data.weeks:
            for day in week.days:
                if day.date == today:
                    today_day = day
                    break
            if today_day:
                break

        if today_day:
            count = today_day.contribution_count
            text = (
                "No contributions today"
                if count == 0
                else f"{count} contribution{'s' if count != 1 else ''} today"
            )
            self.today_label.setText(text)
        else:
            self.today_label.setText("")

    def set_status(self, text: str):
        self.status_label.setText(text)

    def position_near_tray(self):
        # On X11 we can position; on Wayland the compositor handles it.
        # Try to place near bottom-right of screen as a best-effort.
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.right() - self.width() - 16,
            geo.bottom() - self.height() - 16,
        )

    def leaveEvent(self, event):
        # Optional: hide on leave if desired
        pass

    def changeEvent(self, event):
        # Hide when window is deactivated
        if event.type() == event.Type.WindowDeactivate:
            self.hide()
        super().changeEvent(event)
