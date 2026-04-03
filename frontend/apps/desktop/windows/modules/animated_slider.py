import math

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class AnimatedProgressSlider(QSlider):
    """在标准进度条上叠加轻量流光效果。"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._flow_enabled = True
        self._pulse_enabled = True
        self._wave_enabled = True
        self._accent_enabled = True
        self._playback_active = False
        self._flow_phase = 0.0
        self._pulse_phase = 0.0
        self._wave_phase = 0.0
        self._audio_intensity = 0.0
        self._audio_accent = 0.0
        self._flow_timer = QTimer(self)
        self._flow_timer.timeout.connect(self._tick_flow)
        self._flow_timer.setInterval(33)

    def set_flow_enabled(self, enabled):
        self._flow_enabled = bool(enabled)
        self._refresh_flow_timer()
        self.update()

    def set_playback_active(self, active):
        self._playback_active = bool(active)
        self._refresh_flow_timer()
        self.update()

    def set_pulse_enabled(self, enabled):
        self._pulse_enabled = bool(enabled)
        self._refresh_flow_timer()
        self.update()

    def set_wave_enabled(self, enabled):
        self._wave_enabled = bool(enabled)
        self._refresh_flow_timer()
        self.update()

    def set_accent_enabled(self, enabled):
        self._accent_enabled = bool(enabled)
        self._refresh_flow_timer()
        self.update()

    def set_audio_intensity(self, intensity):
        value = max(0.0, min(1.0, float(intensity or 0.0)))
        self._audio_intensity = value
        if self._playback_active and self._wave_enabled:
            self.update()

    def set_audio_accent(self, accent):
        value = max(0.0, min(1.0, float(accent or 0.0)))
        self._audio_accent = value
        if self._playback_active and self._wave_enabled and self._accent_enabled:
            self.update()

    def _refresh_flow_timer(self):
        has_dynamic_effect = self._flow_enabled or self._pulse_enabled or self._wave_enabled or self._accent_enabled
        should_run = has_dynamic_effect and self._playback_active and not self.isSliderDown()
        if should_run:
            if not self._flow_timer.isActive():
                self._flow_timer.start()
        elif self._flow_timer.isActive():
            self._flow_timer.stop()

    def _tick_flow(self):
        if self._flow_enabled:
            self._flow_phase = (self._flow_phase + 0.035) % 1.0
        if self._pulse_enabled:
            self._pulse_phase = (self._pulse_phase + 0.02) % 1.0
        if self._wave_enabled:
            self._wave_phase = (self._wave_phase + 0.03) % 1.0
        if self._accent_enabled:
            self._audio_accent *= 0.90
        self.update()

    def sliderPressEvent(self, event):
        super().sliderPressEvent(event)
        self._refresh_flow_timer()

    def sliderReleaseEvent(self, event):
        super().sliderReleaseEvent(event)
        self._refresh_flow_timer()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._playback_active:
            return

        option = QStyleOptionSlider()
        self.initStyleOption(option)

        groove = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self)
        handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
        if groove.isNull() or handle.isNull() or groove.width() <= 4:
            return

        if self.maximum() <= self.minimum():
            return

        left = groove.left()
        full_width = max(1, groove.width())
        span = max(1, groove.width() - 1)
        position = QStyle.sliderPositionFromValue(
            self.minimum(),
            self.maximum(),
            self.sliderPosition(),
            span,
            option.upsideDown,
        )
        right = min(groove.right(), left + position)
        width = max(0, right - left + 1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if width > 2:
            band_half = max(12.0, width * 0.15)
            shimmer_center = left + (width * self._flow_phase)
            pulse_factor = 1.0
            if self._pulse_enabled:
                # 轻脉冲：仅调制亮度，不改变进度几何尺寸。
                pulse_factor = 0.78 + (0.22 * (0.5 + 0.5 * math.sin(2.0 * math.pi * self._pulse_phase)))
            g = QLinearGradient(shimmer_center - band_half, 0, shimmer_center + band_half, 0)
            edge_alpha = int(35 * pulse_factor)
            peak_alpha = int(90 * pulse_factor)
            g.setColorAt(0.0, QColor(255, 255, 255, 0))
            g.setColorAt(0.45, QColor(255, 255, 255, edge_alpha))
            g.setColorAt(0.5, QColor(255, 255, 255, peak_alpha))
            g.setColorAt(0.55, QColor(255, 255, 255, edge_alpha))
            g.setColorAt(1.0, QColor(255, 255, 255, 0))

            overlay_rect = groove.adjusted(0, 1, 0, -1)
            overlay_rect.setLeft(left)
            overlay_rect.setRight(right)
            painter.setPen(Qt.NoPen)
            painter.setBrush(g)
            painter.drawRoundedRect(overlay_rect, 3, 3)

        if self._wave_enabled and self._audio_intensity > 0.01:
            accent_boost = self._audio_accent if self._accent_enabled else 0.0
            amplitude = 1.5 + (self._audio_intensity * 5.5) + (accent_boost * 4.0)
            baseline = max(2, groove.top() - 4)
            points = max(36, min(96, int(full_width / 3)))
            step = full_width / float(points - 1)
            phase = self._wave_phase * 2.0 * math.pi
            shake = accent_boost * 8.0

            wave_pen = QPen(QColor(59, 130, 246, 185), 1.3)
            painter.setPen(wave_pen)
            for i in range(points - 1):
                x1 = left + (i * step)
                x2 = left + ((i + 1) * step)
                jitter1 = math.sin(phase * 7.0 + i * 2.35) * shake
                jitter2 = math.sin(phase * 7.0 + (i + 1) * 2.35) * shake
                y1 = baseline - (math.sin(phase + i * 0.42) * amplitude) + jitter1
                y2 = baseline - (math.sin(phase + (i + 1) * 0.42) * amplitude) + jitter2
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))







