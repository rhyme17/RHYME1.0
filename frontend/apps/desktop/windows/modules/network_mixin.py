from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel

try:
    from frontend.apps.desktop.windows.modules.online_workers import NetworkCheckWorker
except ModuleNotFoundError:
    from apps.desktop.windows.modules.online_workers import NetworkCheckWorker


class NetworkMixin:
    def init_network_monitor(self):
        if hasattr(self, "statusBar") and self.statusBar() is not None:
            self.statusBar().showMessage("就绪")
            self.statusBar().setVisible(True)

        self._network_check_timer = QTimer(self)
        self._network_check_timer.timeout.connect(self._check_network_status)
        self._network_check_timer.start(30000)
        self._network_check_worker = None
        self.init_network_status_bar()
        self._check_network_status()

    def init_network_status_bar(self):
        if not hasattr(self, "statusBar"):
            return

        status_bar = self.statusBar()
        self._network_status_label = QLabel("⏳ 网络检测中...", status_bar)
        self._network_status_label.setStyleSheet("color: #888; padding: 2px 8px; cursor: pointer;")
        self._network_status_label.mousePressEvent = self._on_network_status_clicked
        status_bar.addPermanentWidget(self._network_status_label)

    def _on_network_status_clicked(self, event):
        self.open_network_check_dialog()

    def check_network_status(self):
        if not hasattr(self, "_network_status_label"):
            return
        self._network_status_label.setText("⏳ 检查中...")
        self._network_status_label.setStyleSheet("color: #FFA500; padding: 2px 8px;")
        self._check_network_status()

    def _check_network_status(self):
        if self._network_check_worker and self._network_check_worker.isRunning():
            return
        self._network_check_worker = NetworkCheckWorker(
            self.online_music_service, parent=self
        )
        self._network_check_worker.finished_with_result.connect(self._on_network_checked)
        self._network_check_worker.start()

    def _on_network_checked(self, available):
        was_available = self.online_music_service.is_network_available
        self.online_music_service._network_available = available

        if not available:
            self._set_network_status_disconnected()
        else:
            self._set_network_status_connected()

    def _set_network_status_disconnected(self):
        if hasattr(self, "_network_status_label"):
            self._network_status_label.setText("🔴 离线 - 点击查看")
            self._network_status_label.setStyleSheet(
                "color: #FC5C5C; padding: 2px 8px; font-weight: bold; cursor: pointer;"
            )
        self._update_online_buttons_state(False)
        self.show_nonblocking_error("网络连接已断开，在线功能不可用")

    def _set_network_status_connected(self):
        if hasattr(self, "_network_status_label"):
            self._network_status_label.setText("🟢 在线 - 点击查看")
            self._network_status_label.setStyleSheet(
                "color: #5CFC9A; padding: 2px 8px; font-weight: bold; cursor: pointer;"
            )
        self._update_online_buttons_state(True)

    def _update_online_buttons_state(self, enabled):
        if hasattr(self, "online_search_btn"):
            self.online_search_btn.setEnabled(enabled)

    def open_network_check_dialog(self):
        try:
            from frontend.apps.desktop.windows.modules.network_check_dialog import NetworkCheckDialog
        except ModuleNotFoundError:
            from apps.desktop.windows.modules.network_check_dialog import NetworkCheckDialog

        dialog = NetworkCheckDialog(self.online_music_service, parent=self)
        dialog.exec_()
