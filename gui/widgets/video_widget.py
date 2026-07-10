# -*- coding: utf-8 -*-
"""
Video Stream Widget — displays real-time or playback video frames.

Renders video from:
  - A local MP4 file (tracknet_rknn_output.mp4 or body_action_overlay.mp4)
  - RTSP camera stream (future)

The widget auto-refreshes via QTimer and can overlay ball trails,
skeleton overlays, and event flash animations.
"""

import os

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy


class VideoWidget(QWidget):
    """Video display widget with optional overlay painting."""

    signal_frame_changed = pyqtSignal(int)  # current frame number

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("background-color: #000000; border: 1px solid #30363d; border-radius: 6px;")

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignCenter)
        self._video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._video_label.setMinimumSize(320, 180)
        self._video_label.setText("视频画面")
        self._video_label.setStyleSheet("color: #484f58; font-size: 24px; border: none;")
        layout.addWidget(self._video_label)

        # Click-to-play/pause
        self.setMouseTracking(True)
        self._paused = True   # start paused for demo videos
        self._auto_pause = False  # auto-pause on first frame for demo

        # State
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._fps = 0
        self._frame_count = 0
        self._current_frame_num = 0
        self._video_path = None
        self._paused = False
        self._loaded_mode = None  # which mode loaded this video

        # Per-mode video cache: {mode_key: video_path}
        self._mode_videos = {}

        # Overlay data (updated externally)
        self._ball_trail = []
        self._skeleton_points = []
        self._event_flash = None
        self._score_top = 0
        self._score_bottom = 0

        # Placeholder pixmap
        self._placeholder = self._create_placeholder()

    # ── Public API ────────────────────────────────────────────────

    def stop(self):
        """Stop playback and release resources."""
        self._timer.stop()
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._current_frame_num = 0
        self._video_label.setPixmap(self._placeholder)

    def seek_frame(self, frame_num: int):
        """Seek to a specific frame number."""
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            self._current_frame_num = frame_num
            ret, frame = self._cap.read()
            if ret:
                self._display_frame(frame)

    def pause(self):
        self._paused = True
        self._timer.stop()
        self._show_pause_overlay = True
        self.update()

    def resume(self):
        self._paused = False
        self._show_pause_overlay = False
        self._auto_pause = False
        if self._cap is not None:
            self._timer.start(max(1, int(1000.0 / self._fps)))
        self.update()

    def mousePressEvent(self, event):
        """Click to toggle play/pause, or X to close video."""
        if self._cap is None:
            return
        # Check if X button clicked
        xr = getattr(self, '_x_btn_rect', None)
        if xr:
            # Scale click coords to pixmap coords
            scale_x = self._video_label.pixmap().width() / self._video_label.width() if self._video_label.pixmap() and self._video_label.width() else 1
            scale_y = self._video_label.pixmap().height() / self._video_label.height() if self._video_label.pixmap() and self._video_label.height() else 1
            px = event.pos().x() * scale_x
            py = event.pos().y() * scale_y
            if xr[0] <= px <= xr[0] + xr[2] and xr[1] <= py <= xr[1] + xr[3]:
                self.clear_video()
                return
        # Toggle play/pause
        if self._paused:
            self.resume()
        else:
            self.pause()

    def load_video_paused(self, path, mode_key=None):
        """Load video but keep it paused on first frame. Saves per-mode."""
        if mode_key:
            self._loaded_mode = mode_key
            self._mode_videos[mode_key] = path
        self._auto_pause = True
        self.load_video(path)

    def clear_video(self):
        """Close current video, return to placeholder."""
        if self._loaded_mode:
            self._mode_videos.pop(self._loaded_mode, None)
        self._loaded_mode = None
        self.stop()
        self.show_placeholder("")
        self._show_pause_overlay = False

    def set_mode(self, mode_key):
        """Switch to this mode — restore its video if cached."""
        if mode_key in self._mode_videos:
            path = self._mode_videos[mode_key]
            self._loaded_mode = mode_key
            self._auto_pause = True
            self.load_video(path)
        else:
            # No video for this mode — show placeholder
            if self._loaded_mode is not None:
                # Save current before switching away
                if self._video_path:
                    self._mode_videos[self._loaded_mode] = self._video_path
            self._loaded_mode = mode_key
            self.stop()
            self.show_placeholder("")
            self._show_pause_overlay = False

    def load_video(self, path):
        """Load and start playing a video file."""
        if not os.path.exists(path):
            self._video_label.setText("视频文件不存在:\n{}".format(path))
            return

        self.stop()
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self._video_label.setText("无法打开视频:\n{}".format(path))
            self._cap = None
            return

        self._video_path = path
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        # Read first frame to show preview
        ret, frame = self._cap.read()
        if ret:
            self._current_frame_num = 0
            self._display_frame(frame)

        if self._auto_pause:
            self._paused = True
            self._show_pause_overlay = True
            self._auto_pause = False
        else:
            interval_ms = max(1, int(1000.0 / self._fps))
            self._timer.start(interval_ms)
        self.update()
        self._video_label.update()

    def is_playing(self) -> bool:
        return self._cap is not None and self._timer.isActive()

    # ── Live camera preview ──────────────────────────────────────

    signal_frame_captured = pyqtSignal(object)  # raw BGR frame for recording

    signal_frame_captured = pyqtSignal(object)

    def start_camera_preview(self, device="/dev/video11"):
        """Start a generic V4L2 preview without model preprocessing."""
        self.stop()
        self._cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        if not self._cap.isOpened():
            self._cap = None
            self._video_label.setText("摄像头不可用:\n{}".format(device))
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self._cap.set(cv2.CAP_PROP_FPS, 60)
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._paused = False
        self._camera_mode = True
        try:
            self._timer.timeout.disconnect()
        except Exception:
            pass
        self._timer.timeout.connect(self._next_camera_frame)
        self._timer.start(max(1, int(1000.0 / self._fps)))
        return True

    def stop_camera_preview(self):
        """Stop live camera feed."""
        self._camera_mode = False
        self.stop()

    def _next_camera_frame(self):
        if not getattr(self, '_camera_mode', False):
            return
        if self._cap is None:
            return
        ok, frame = self._cap.read()
        if not ok:
            return
        self._current_frame_num += 1
        self.signal_frame_captured.emit(frame)
        self._display_frame(frame)

    def is_playing(self) -> bool:
        return self._cap is not None and self._timer.isActive()

    def heightForWidth(self, width: int) -> int:
        """Lock aspect ratio to 16:9."""
        return int(width * 9 / 16)

    def hasHeightForWidth(self) -> bool:
        return True

    def set_overlay_data(self, ball_trail=None, skeleton=None, event=None, score_top=0, score_bottom=0):
        """Update overlay annotations from external data sources."""
        if ball_trail is not None:
            self._ball_trail = ball_trail
        if skeleton is not None:
            self._skeleton_points = skeleton
        if event is not None:
            self._event_flash = event
        self._score_top = score_top
        self._score_bottom = score_bottom

    # ── Internal ──────────────────────────────────────────────────

    def _next_frame(self):
        if self._cap is None or self._paused:
            return

        ret, frame = self._cap.read()
        if not ret:
            # Loop or stop
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._current_frame_num = 0
            return

        self._current_frame_num = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.signal_frame_changed.emit(self._current_frame_num)
        self._display_frame(frame)

    def _display_frame(self, frame: np.ndarray):
        """Convert OpenCV BGR frame to QPixmap and paint overlays."""
        if frame is None:
            return

        # Resize to fit widget while keeping aspect ratio
        h, w = frame.shape[:2]
        target_w = self._video_label.width()
        target_h = self._video_label.height()

        if target_w < 10 or target_h < 10:
            return

        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)

        if new_w > 0 and new_h > 0:
            frame_resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        else:
            frame_resized = frame

        # Convert BGR → RGB
        rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)

        # Paint overlays
        if self._ball_trail or self._skeleton_points or self._event_flash:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Ball trail
            if self._ball_trail:
                pen = QPen(QColor(255, 255, 0, 180), 2)
                painter.setPen(pen)
                scaled_trail = [(int(x * scale), int(y * scale)) for (x, y) in self._ball_trail]
                for i in range(len(scaled_trail) - 1):
                    painter.drawLine(
                        scaled_trail[i][0], scaled_trail[i][1],
                        scaled_trail[i + 1][0], scaled_trail[i + 1][1],
                    )

            # Skeleton
            if self._skeleton_points:
                pen = QPen(QColor(0, 255, 128, 200), 2)
                painter.setPen(pen)
                for pt in self._skeleton_points:
                    sx, sy = int(pt[0] * scale), int(pt[1] * scale)
                    painter.drawEllipse(sx - 2, sy - 2, 4, 4)

            # Event flash
            if self._event_flash is not None:
                event_type, timestamp = self._event_flash
                elapsed = cv2.getTickCount() / cv2.getTickFrequency() - timestamp
                if elapsed < 2.0:
                    alpha = max(0, int(255 * (1.0 - elapsed / 2.0)))
                    color = QColor(0, 180, 0, alpha) if event_type == "IN" else QColor(233, 69, 96, alpha)
                    painter.fillRect(QRect(0, 0, w, h), color)

            # Score overlay (top-left)
            font = QFont("DejaVu Sans", 18, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 30, "Top {} - {} Bottom".format(self._score_top, self._score_bottom))

            painter.end()

        # Always draw X button on top-right when video is loaded
        if self._video_path:
            x_painter = QPainter(pixmap)
            x_painter.setRenderHint(QPainter.Antialiasing)
            # X button background
            x_btn_x = pixmap.width() - 36
            x_btn_y = 8
            x_painter.setBrush(QColor(0, 0, 0, 160))
            x_painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            x_painter.drawRoundedRect(x_btn_x, x_btn_y, 28, 28, 6, 6)
            # X lines
            x_painter.setPen(QPen(QColor(255, 255, 255, 220), 2.5))
            x_painter.drawLine(x_btn_x + 8, x_btn_y + 8, x_btn_x + 20, x_btn_y + 20)
            x_painter.drawLine(x_btn_x + 20, x_btn_y + 8, x_btn_x + 8, x_btn_y + 20)
            self._x_btn_rect = (x_btn_x, x_btn_y, 28, 28)
            x_painter.end()

        # Pause overlay
        if self._show_pause_overlay:
            p_painter = QPainter(pixmap)
            p_painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 120))
            p_painter.setRenderHint(QPainter.Antialiasing)
            p_painter.setBrush(QColor(255, 255, 255, 200))
            p_painter.setPen(Qt.NoPen)
            cx, cy = pixmap.width() // 2, pixmap.height() // 2
            bar_w, bar_h = 12, 50
            gap = 16
            p_painter.drawRoundedRect(cx - gap - bar_w, cy - bar_h // 2, bar_w, bar_h, 4, 4)
            p_painter.drawRoundedRect(cx + gap, cy - bar_h // 2, bar_w, bar_h, 4, 4)
            font = QFont("DejaVu Sans", 16, QFont.Bold)
            p_painter.setFont(font)
            p_painter.setPen(QColor(255, 255, 255, 220))
            p_painter.drawText(pixmap.rect().adjusted(0, 60, 0, 0),
                               Qt.AlignHCenter | Qt.AlignTop, "点击播放")
            p_painter.end()

        self._video_label.setPixmap(pixmap)

    def show_placeholder(self, mode_text=""):
        """Show an informative placeholder."""
        pixmap = QPixmap(640, 360)
        pixmap.fill(QColor("#0d1117"))
        painter = QPainter(pixmap)
        # Grid lines for monitor feel
        painter.setPen(QPen(QColor("#1a1a2e"), 1))
        for i in range(0, 640, 40):
            painter.drawLine(i, 0, i, 360)
        for i in range(0, 360, 40):
            painter.drawLine(0, i, 640, i)
        # Border
        painter.setPen(QPen(QColor("#30363d"), 2))
        painter.drawRect(2, 2, 636, 356)
        # Text
        painter.setPen(QColor("#484f58"))
        font = QFont("DejaVu Sans", 14)
        painter.setFont(font)
        painter.drawText(QRect(0, 60, 640, 80), Qt.AlignCenter,
                         "● REC STANDBY")
        font2 = QFont("DejaVu Sans", 11)
        painter.setFont(font2)
        painter.setPen(QColor("#30363d"))
        if mode_text:
            painter.drawText(QRect(0, 130, 640, 40), Qt.AlignCenter, mode_text)
        painter.drawText(QRect(0, 180, 640, 40), Qt.AlignCenter,
                         "点击 ▶ RUN 启动推理流水线")
        painter.drawText(QRect(0, 210, 640, 40), Qt.AlignCenter,
                         "结果视频将在此回放")
        # Corner timestamp
        import time
        painter.setPen(QColor("#30363d"))
        font3 = QFont("DejaVu Sans Mono", 9)
        painter.setFont(font3)
        painter.drawText(QRect(10, 330, 200, 20), Qt.AlignLeft,
                         time.strftime("%Y-%m-%d %H:%M:%S"))
        painter.drawText(QRect(430, 330, 200, 20), Qt.AlignRight,
                         "RK3588 NPU")
        painter.end()
        self._placeholder = pixmap
        self._video_label.setPixmap(pixmap)

    def _create_placeholder(self) -> QPixmap:
        """Legacy — use show_placeholder instead."""
        return QPixmap(640, 360)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-display current frame at new size
        if self._cap is not None and hasattr(self, '_current_frame_num'):
            pass  # next frame will auto-resize
