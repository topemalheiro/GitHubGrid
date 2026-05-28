import sys
import random

from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QImage, QPainter, QColor, QPixmap, QCursor
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .grid_window import ContributionGridWindow
from .github_service import GitHubServiceError, get_username, fetch_contributions
from .models import ContributionData


# GitHub dark colors for tray icon
TRAY_COLORS = [
    QColor(14, 68, 41),
    QColor(0, 109, 50),
    QColor(38, 166, 65),
    QColor(57, 211, 83),
]


def create_tray_icon() -> QIcon:
    size = 64
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    rng = random.Random(42)
    cell = 14
    gap = 2
    margin = (size - (4 * cell + 3 * gap)) // 2

    for row in range(4):
        for col in range(4):
            color = TRAY_COLORS[rng.randint(0, len(TRAY_COLORS) - 1)]
            painter.setBrush(color)
            x = margin + col * (cell + gap)
            y = margin + row * (cell + gap)
            painter.drawRoundedRect(x, y, cell, cell, 3, 3)

    painter.end()
    return QIcon(QPixmap.fromImage(img))


class FetchWorker(QThread):
    finished = pyqtSignal(object, object)  # result, error

    def __init__(self, username: str = ""):
        super().__init__()
        self._username = username

    def run(self):
        try:
            if not self._username:
                self.finished.emit(get_username(), None)
            else:
                self.finished.emit(fetch_contributions(self._username), None)
        except Exception as e:
            self.finished.emit(None, str(e))


class GitHubGridApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("GitHubGrid")
        self.app.setApplicationDisplayName("GitHubGrid")

        self._username = ""
        self._data: ContributionData | None = None
        self._current_worker: FetchWorker | None = None

        self._window = ContributionGridWindow()
        self._window.refresh_btn.clicked.connect(self._on_refresh)

        self._tray_icon = QSystemTrayIcon(create_tray_icon(), self.app)
        self._tray_icon.setToolTip("GitHubGrid")
        self._tray_icon.activated.connect(self._on_tray_activated)

        self._menu = QMenu()
        self._refresh_action = QAction("Refresh", self._menu)
        self._refresh_action.triggered.connect(self._on_refresh)
        self._menu.addAction(self._refresh_action)
        self._menu.addSeparator()
        self._exit_action = QAction("Exit", self._menu)
        self._exit_action.triggered.connect(self._quit)
        self._menu.addAction(self._exit_action)

        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.show()

        self._auto_refresh_timer = QTimer()
        self._auto_refresh_timer.setInterval(20 * 60 * 1000)  # 20 minutes
        self._auto_refresh_timer.timeout.connect(self._on_refresh)

        # Defer initialization so tray icon is ready
        QTimer.singleShot(500, self._initialize)

    def _initialize(self):
        self._window.set_status("Loading...")
        # Don't show window on startup; stay in tray only
        self._start_worker("")

    def _start_worker(self, username: str):
        if self._current_worker is not None and self._current_worker.isRunning():
            return
        self._current_worker = FetchWorker(username)
        if not username:
            self._current_worker.finished.connect(self._on_username_ready)
        else:
            self._current_worker.finished.connect(self._on_refresh_ready)
        self._current_worker.start()

    def _on_username_ready(self, result, error):
        if error:
            self._window.set_status(f"Failed to connect. {error}")
            self._tray_icon.showMessage(
                "GitHubGrid",
                f"Failed to load: {error}",
                QSystemTrayIcon.MessageIcon.Critical,
            )
            return

        self._username = result
        self._on_refresh()
        self._auto_refresh_timer.start()

    def _on_refresh(self):
        if not self._username:
            return

        self._window.set_status("Refreshing...")
        self._start_worker(self._username)

    def _on_refresh_ready(self, result, error):
        if error:
            self._window.set_status(f"Failed to refresh. {error}")
            self._tray_icon.showMessage(
                "GitHubGrid",
                f"Refresh failed: {error}",
                QSystemTrayIcon.MessageIcon.Warning,
            )
            return

        self._data = result
        self._window.set_data(self._data)
        if self._window.isVisible():
            self._position_window()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._window.isVisible():
                self._window.hide()
            else:
                self._position_window()
                self._window.show()
                self._window.raise_()
                self._window.activateWindow()
                self._on_refresh()

    def _position_window(self):
        tray_geo = self._tray_icon.geometry()
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
        else:
            sg = None

        if tray_geo.isValid() and not tray_geo.isEmpty():
            # Position above the tray icon
            x = tray_geo.center().x() - self._window.width() // 2
            y = tray_geo.top() - self._window.height() - 8
        elif sg:
            # Fallback: bottom-right of primary screen
            x = sg.right() - self._window.width() - 16
            y = sg.bottom() - self._window.height() - 16
        else:
            # Last resort: near cursor
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() - self._window.width() // 2
            y = cursor_pos.y() - self._window.height() - 8
            screen = QApplication.screenAt(cursor_pos)
            if screen:
                sg = screen.availableGeometry()

        if sg:
            x = max(sg.left(), min(x, sg.right() - self._window.width()))
            y = max(sg.top(), min(y, sg.bottom() - self._window.height()))

        # Use setGeometry instead of move — some Wayland compositors respect it better
        self._window.setGeometry(x, y, self._window.width(), self._window.height())

    def _quit(self):
        self._tray_icon.hide()
        self.app.quit()

    def run(self):
        return self.app.exec()


def main():
    app = GitHubGridApp()
    sys.exit(app.run())
