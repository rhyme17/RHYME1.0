from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QProgressBar,
)


class NetworkCheckDialog(QDialog):
    def __init__(self, online_service, parent=None):
        super().__init__(parent)
        self.online_service = online_service
        self._worker = None

        self.setWindowTitle("网络状态检测")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedSize(320, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.title_label = QLabel("网络连接状态")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.status_label = QLabel("正在检测网络...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 12px;")
        self.result_label.hide()
        layout.addWidget(self.result_label)

        button_layout = QHBoxLayout()
        self.retry_button = QPushButton("重新检测")
        self.retry_button.clicked.connect(self.start_check)
        self.retry_button.hide()
        button_layout.addWidget(self.retry_button)

        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self._apply_theme_styles()
        self.start_check()

    def _apply_theme_styles(self):
        parent = self.parent()
        theme = "light"
        if parent is not None:
            theme = str(getattr(parent, "ui_theme", "light") or "light")
        if theme.strip().lower() == "dark":
            self.setStyleSheet(
                "\n".join([
                    "QDialog { background: #11151d; color: #ffffff; }",
                    "QLabel { color: #ffffff; }",
                    "QPushButton { background: #232b39; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 6px; padding: 6px 12px; }",
                    "QPushButton:hover { background: #2a3445; }",
                    "QProgressBar { background: #20293a; border: 1px solid #4a4a4a; border-radius: 4px; }",
                    "QProgressBar::chunk { background: #2f7bff; border-radius: 3px; }",
                ])
            )

    def start_check(self):
        self.retry_button.hide()
        self.result_label.hide()
        self.progress_bar.show()
        self.status_label.setText("正在检测网络...")
        self.status_label.setStyleSheet("font-size: 14px; color: #666;")

        try:
            from frontend.apps.desktop.windows.modules.online_workers import NetworkCheckWorker
        except ModuleNotFoundError:
            from apps.desktop.windows.modules.online_workers import NetworkCheckWorker

        self._worker = NetworkCheckWorker(self.online_service, parent=self)
        self._worker.finished_with_result.connect(self.on_check_finished)
        self._worker.start()

    def on_check_finished(self, available):
        self.progress_bar.hide()
        self.result_label.show()
        self.retry_button.show()

        if available:
            self.title_label.setText("✅ 网络正常")
            self.status_label.setText("网络连接正常")
            self.status_label.setStyleSheet("font-size: 14px; color: #5CFC9A;")
            self.result_label.setText("可以正常使用在线搜索和下载功能")
            self.result_label.setStyleSheet("font-size: 12px; color: #5CFC9A;")
        else:
            self.title_label.setText("❌ 网络异常")
            self.status_label.setText("网络连接失败")
            self.status_label.setStyleSheet("font-size: 14px; color: #FC5C5C;")
            self.result_label.setText("请检查网络连接后重试")
            self.result_label.setStyleSheet("font-size: 12px; color: #FC5C5C;")
