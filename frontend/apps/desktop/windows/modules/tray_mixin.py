from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QAction, QApplication, QCheckBox, QMenu, QMessageBox, QStyle, QSystemTrayIcon


class TrayMixin:
    def _is_tray_supported(self):
        return bool(getattr(self, "tray_enabled", True)) and QSystemTrayIcon.isSystemTrayAvailable()

    def _resolve_tray_icon(self):
        # 某些打包场景下 windowIcon 可能为空，需提供稳定回退。
        icon = self.windowIcon()
        if not icon.isNull():
            return icon
        app = QApplication.instance()
        if app is not None:
            app_icon = app.windowIcon()
            if not app_icon.isNull():
                return app_icon
            style = app.style()
            if style is not None:
                fallback = style.standardIcon(QStyle.SP_ComputerIcon)
                if not fallback.isNull():
                    return fallback
        style = self.style() if hasattr(self, "style") else None
        if style is not None:
            return style.standardIcon(QStyle.SP_ComputerIcon)
        return icon

    def _disable_tray_entry(self, reason):
        self.tray_enabled = False
        if hasattr(self, "show_status_hint"):
            self.show_status_hint(reason, timeout_ms=2800)

    def init_system_tray(self):
        if getattr(self, "_tray_icon", None) is not None:
            return
        if not self._is_tray_supported():
            self._disable_tray_entry("当前系统环境不支持系统托盘")
            return

        tray = QSystemTrayIcon(self)
        tray.setToolTip(self.windowTitle() or "RHYME")
        tray.setIcon(self._resolve_tray_icon())
        if tray.icon().isNull():
            self._disable_tray_entry("托盘图标初始化失败，已禁用隐藏到托盘")
            tray.deleteLater()
            return

        menu = QMenu(self)
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.restore_from_tray)
        menu.addAction(show_action)

        play_pause_action = QAction("播放/暂停", self)
        play_pause_action.triggered.connect(self.toggle_play)
        menu.addAction(play_pause_action)

        next_action = QAction("下一首", self)
        next_action.triggered.connect(self.play_next)
        menu.addAction(next_action)

        menu.addSeparator()
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.request_quit_from_tray)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.setVisible(True)
        if not tray.isVisible():
            self._disable_tray_entry("系统未接受托盘图标，已禁用隐藏到托盘")
            tray.deleteLater()
            return

        self._tray_icon = tray
        self._tray_menu = menu

    def teardown_system_tray(self):
        tray = getattr(self, "_tray_icon", None)
        if tray is not None:
            tray.hide()
            tray.deleteLater()
        self._tray_icon = None
        self._tray_menu = None

    def hide_to_tray(self):
        if not self._is_tray_supported():
            return
        self.showMinimized()
        self.hide()
        if not getattr(self, "_tray_hint_shown", False):
            tray = getattr(self, "_tray_icon", None)
            if tray is not None:
                tray.showMessage("RHYME", "程序已隐藏到系统托盘，可双击托盘图标恢复。", QSystemTrayIcon.Information, 2000)
            self._tray_hint_shown = True

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def request_quit_from_tray(self):
        self._quit_requested = True
        self.close()

    def should_hide_to_tray_on_close(self):
        if bool(getattr(self, "_quit_requested", False)):
            return False
        if bool(getattr(self, "close_behavior_configured", False)):
            return self._is_tray_supported() and bool(getattr(self, "close_to_tray_enabled", False))
        return self._resolve_first_close_behavior()

    def _prompt_first_close_action(self):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setWindowTitle("关闭程序")
        dialog.setText("首次关闭时请选择操作")
        dialog.setInformativeText("可以隐藏到托盘继续后台运行，或直接关闭程序。")

        hide_button = dialog.addButton("隐藏到托盘", QMessageBox.AcceptRole)
        close_button = dialog.addButton("关闭程序", QMessageBox.DestructiveRole)
        dialog.setDefaultButton(close_button)

        remember_checkbox = QCheckBox("记住我的选择")
        remember_checkbox.setChecked(True)
        dialog.setCheckBox(remember_checkbox)

        dialog.exec_()
        clicked = dialog.clickedButton()
        should_hide = clicked == hide_button
        remember = bool(dialog.checkBox() and dialog.checkBox().isChecked())
        if clicked is None:
            should_hide = False
            remember = False
        return should_hide, remember

    def _resolve_first_close_behavior(self):
        if not bool(getattr(self, "tray_enabled", True)):
            self.close_to_tray_enabled = False
            self.close_behavior_configured = True
            if hasattr(self, "schedule_save_app_settings"):
                self.schedule_save_app_settings()
            return False

        if not self._is_tray_supported():
            self.close_to_tray_enabled = False
            self.close_behavior_configured = True
            if hasattr(self, "schedule_save_app_settings"):
                self.schedule_save_app_settings()
            return False

        should_hide, remember = self._prompt_first_close_action()
        self.close_to_tray_enabled = bool(should_hide)
        if remember:
            self.close_behavior_configured = True
            if hasattr(self, "schedule_save_app_settings"):
                self.schedule_save_app_settings()
        return bool(should_hide)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_from_tray()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            pass
        super().changeEvent(event)

