# -*- coding: utf-8 -*-
"""
Center Visual Panel — video display + progress bar / action timeline.

Widgets show/hide based on active scene mode.
"""

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QStackedWidget,
)

from gui.modes import MODE_A, MODE_B
from gui.widgets.video_widget import VideoWidget
from gui.widgets.progress_bar import ProgressBarWidget
from gui.widgets.action_timeline import ActionTimelineWidget


class CenterVisualPanel(QWidget):

    def __init__(self, project_root: str, compact: bool = False, parent=None):
        super().__init__(parent)
        self._project_root = project_root
        self._compact = compact

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Video widget ──
        self.video_widget = VideoWidget()
        self.video_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.video_widget, 10)

        # ── Bottom bar: stacked between progress & timeline ──
        bottom = QWidget()
        bottom.setObjectName("bottomBar")
        bottom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if compact:
            bottom.setMinimumHeight(120)
            bottom.setMaximumHeight(160)
        else:
            bottom.setMinimumHeight(100)
            bottom.setMaximumHeight(180)
        bottom.setStyleSheet(
            "#bottomBar{background:#0d1117;border-top:2px solid #ccff00;}")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(6, 4, 6, 4)
        bottom_layout.setSpacing(4)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Page 0: Progress bar (default / pipeline running)
        self.progress_bar = ProgressBarWidget()
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.addWidget(self.progress_bar)

        # Page 1: Action timeline (side mode)
        self.action_timeline = ActionTimelineWidget()
        self.action_timeline.setMinimumHeight(70)
        self.action_timeline.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.addWidget(self.action_timeline)

        bottom_layout.addWidget(self._stack, 1)
        layout.addWidget(bottom, 1)

        # Internal signals
        self.video_widget.signal_frame_changed.connect(
            self.action_timeline.on_frame_changed)

    # ── Mode switching ───────────────────────────────────────────

    def set_mode(self, mode_key):
        if mode_key == MODE_A:
            self._stack.setCurrentIndex(0)  # progress bar
        elif mode_key == MODE_B:
            self._stack.setCurrentIndex(0)  # progress bar (no timeline)

    def show_progress(self):
        self._stack.setCurrentIndex(0)

    def show_timeline(self):
        self._stack.setCurrentIndex(1)

    def reset_progress(self):
        self.progress_bar.reset()

    # ── Public slots ─────────────────────────────────────────────

    @pyqtSlot(str, str)
    def on_video_source_changed(self, source_type: str, path: str):
        if source_type == "file" and path:
            self.video_widget.load_video(path)

    def load_action_data(self, actions: list):
        self.action_timeline.load_actions(actions)
