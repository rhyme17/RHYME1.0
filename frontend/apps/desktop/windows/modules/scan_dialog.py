from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class ScanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫描音乐")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(760, 520)
        self.scanned_songs = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("音乐目录："))
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("请选择要扫描的音乐文件夹")
        self.browse_btn = QPushButton("浏览")
        self.scan_btn = QPushButton("开始扫描")
        folder_row.addWidget(self.directory_input, 1)
        folder_row.addWidget(self.browse_btn)
        folder_row.addWidget(self.scan_btn)

        result_label = QLabel("扫描结果（可多选）：")
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QListWidget.ExtendedSelection)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("目标歌单："))
        self.playlist_combo = QComboBox()
        target_row.addWidget(self.playlist_combo, 1)

        create_row = QHBoxLayout()
        create_row.addWidget(QLabel("新歌单名："))
        self.new_playlist_input = QLineEdit()
        self.new_playlist_input.setPlaceholderText("默认使用文件夹名")
        self.save_playlist_btn = QPushButton("保存为歌单")
        create_row.addWidget(self.new_playlist_input, 1)
        create_row.addWidget(self.save_playlist_btn)

        action_row = QHBoxLayout()
        self.add_all_btn = QPushButton("全部加入")
        self.add_selected_btn = QPushButton("选中加入")
        self.close_btn = QPushButton("关闭")
        action_row.addWidget(self.add_all_btn)
        action_row.addWidget(self.add_selected_btn)
        action_row.addStretch()
        action_row.addWidget(self.close_btn)

        self.hint_label = QLabel("请选择目录并扫描")
        self.hint_label.setAlignment(Qt.AlignLeft)

        layout.addLayout(folder_row)
        layout.addWidget(result_label)
        layout.addWidget(self.results_list, 1)
        layout.addLayout(target_row)
        layout.addLayout(create_row)
        layout.addLayout(action_row)
        layout.addWidget(self.hint_label)

        self.browse_btn.clicked.connect(self._browse_directory)
        self.close_btn.clicked.connect(self.reject)
        self.set_scanning_state(False)

    def _browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if directory:
            self.directory_input.setText(directory)

    def set_playlist_names(self, names, selected_name=""):
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        self.playlist_combo.addItems(names)
        if selected_name:
            index = self.playlist_combo.findText(selected_name)
            if index >= 0:
                self.playlist_combo.setCurrentIndex(index)
        self.playlist_combo.blockSignals(False)

    def set_scan_results(self, songs):
        self.scanned_songs = list(songs)
        self.results_list.clear()
        for song in self.scanned_songs:
            text = f"{song.get('title', '')} - {song.get('artist', '')}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, song)
            self.results_list.addItem(item)
        self.hint_label.setText(f"扫描完成，共 {len(self.scanned_songs)} 首")

    def set_scanning_state(self, is_scanning, message=""):
        scanning = bool(is_scanning)
        self.is_scanning = scanning
        self.is_cancelling = False
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("取消扫描" if scanning else "开始扫描")
        self.browse_btn.setEnabled(not scanning)
        self.directory_input.setEnabled(not scanning)
        if message:
            self.hint_label.setText(message)

    def set_cancelling_state(self, message="正在取消扫描..."):
        self.is_cancelling = True
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("取消中...")
        self.browse_btn.setEnabled(False)
        self.directory_input.setEnabled(False)
        if message:
            self.hint_label.setText(message)

    def set_scan_progress(self, scanned_count, total_count):
        if getattr(self, "is_cancelling", False):
            return
        scanned = max(0, int(scanned_count or 0))
        total = max(scanned, int(total_count or 0))
        self.hint_label.setText(f"正在扫描：{scanned}/{total}")

    def selected_songs(self):
        items = self.results_list.selectedItems()
        return [item.data(Qt.UserRole) for item in items if item.data(Qt.UserRole)]

    def selected_playlist_name(self):
        return self.playlist_combo.currentText().strip()

    def suggested_playlist_name(self):
        return self.new_playlist_input.text().strip()

