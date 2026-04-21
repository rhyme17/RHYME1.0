import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QWidget


class AudioVisualizerWidget(QWidget):
    DEFAULT_BAR_COUNT = 64
    DEFAULT_REFRESH_RATE = 60
    DEFAULT_BAR_WIDTH_RATIO = 0.7
    DEFAULT_BAR_GAP_RATIO = 0.3
    DEFAULT_MIN_BAR_HEIGHT = 2
    DEFAULT_MAX_BAR_HEIGHT_RATIO = 0.9

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar_count = self.DEFAULT_BAR_COUNT
        self._refresh_rate = self.DEFAULT_REFRESH_RATE
        self._bar_width_ratio = self.DEFAULT_BAR_WIDTH_RATIO
        self._bar_gap_ratio = self.DEFAULT_BAR_GAP_RATIO
        self._min_bar_height = self.DEFAULT_MIN_BAR_HEIGHT
        self._max_bar_height_ratio = self.DEFAULT_MAX_BAR_HEIGHT_RATIO

        self._spectrum_data = np.zeros(self._bar_count)
        self._smoothed_spectrum = np.zeros(self._bar_count)
        self._smoothing_factor = 0.3

        self._is_active = False
        self._visible = True

        self._background_color = QColor(30, 30, 30)
        self._bar_color = QColor(100, 180, 255)
        self._bar_color_gradient_start = QColor(80, 160, 255)
        self._bar_color_gradient_end = QColor(120, 200, 255)

        self.setMinimumHeight(80)
        self.setMaximumHeight(150)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Fixed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._timer.setInterval(int(1000 / self._refresh_rate))

    def set_bar_count(self, count):
        count = max(8, min(256, int(count)))
        if count != self._bar_count:
            self._bar_count = count
            self._spectrum_data = np.zeros(self._bar_count)
            self._smoothed_spectrum = np.zeros(self._bar_count)
            self.update()

    def set_refresh_rate(self, fps):
        fps = max(10, min(120, int(fps)))
        if fps != self._refresh_rate:
            self._refresh_rate = fps
            self._timer.setInterval(int(1000 / self._refresh_rate))

    def set_bar_color(self, color):
        if isinstance(color, QColor):
            self._bar_color = color
            self.update()
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            self._bar_color = QColor(*color[:3])
            self.update()

    def set_background_color(self, color):
        if isinstance(color, QColor):
            self._background_color = color
            self.update()
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            self._background_color = QColor(*color[:3])
            self.update()

    def set_smoothing_factor(self, factor):
        self._smoothing_factor = max(0.0, min(1.0, float(factor)))

    def set_active(self, active):
        self._is_active = bool(active)
        if self._is_active and self._visible:
            if not self._timer.isActive():
                self._timer.start()
        else:
            if self._timer.isActive():
                self._timer.stop()
            self._spectrum_data = np.zeros(self._bar_count)
            self._smoothed_spectrum = np.zeros(self._bar_count)
            self.update()

    def set_visualizer_visible(self, visible):
        self._visible = bool(visible)
        if self._visible:
            self.show()
            if self._is_active:
                if not self._timer.isActive():
                    self._timer.start()
        else:
            self.hide()
            if self._timer.isActive():
                self._timer.stop()

    def update_spectrum(self, spectrum_data):
        if spectrum_data is None:
            self._spectrum_data = np.zeros(self._bar_count)
        elif len(spectrum_data) == self._bar_count:
            self._spectrum_data = np.array(spectrum_data, dtype=np.float32)
        else:
            self._spectrum_data = np.interp(
                np.linspace(0, len(spectrum_data) - 1, self._bar_count),
                np.arange(len(spectrum_data)),
                spectrum_data
            )

    def _on_timer(self):
        if not self._is_active:
            return
        self._smooth_spectrum()
        self.update()

    def _smooth_spectrum(self):
        self._smoothed_spectrum = (
            self._smoothing_factor * self._spectrum_data +
            (1.0 - self._smoothing_factor) * self._smoothed_spectrum
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), self._background_color)

        if not self._is_active or not self._visible:
            return

        width = self.width()
        height = self.height()

        total_gap_width = width * self._bar_gap_ratio
        total_bar_width = width * self._bar_width_ratio

        gap_width = total_gap_width / (self._bar_count + 1)
        bar_width = total_bar_width / self._bar_count

        max_bar_height = height * self._max_bar_height_ratio

        for i in range(self._bar_count):
            x = gap_width + i * (bar_width + gap_width)
            bar_height = max(
                self._min_bar_height,
                self._smoothed_spectrum[i] * max_bar_height
            )

            y = (height - bar_height) / 2

            gradient_ratio = self._smoothed_spectrum[i]
            r = int(self._bar_color_gradient_start.red() * (1 - gradient_ratio) +
                   self._bar_color_gradient_end.red() * gradient_ratio)
            g = int(self._bar_color_gradient_start.green() * (1 - gradient_ratio) +
                   self._bar_color_gradient_end.green() * gradient_ratio)
            b = int(self._bar_color_gradient_start.blue() * (1 - gradient_ratio) +
                   self._bar_color_gradient_end.blue() * gradient_ratio)

            color = QColor(r, g, b)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 2, 2)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSizeHint(self):
        return self.minimumSize()

    def clear(self):
        self._spectrum_data = np.zeros(self._bar_count)
        self._smoothed_spectrum = np.zeros(self._bar_count)
        self.update()
