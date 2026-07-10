# -*- coding: utf-8 -*-
"""
NPU Monitor Widget — displays RK3588 NPU core utilization and FPS.

Shows three NPU core indicators and current inference frame rate.
Data is updated via the top status bar refresh timer.
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


class NPUMonitor(QWidget):
    """RK3588 NPU three-core status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # NPU label
        lbl = QLabel("NPU:")
        lbl.setStyleSheet("color: #8b949e; font-size: 11px; border: none;")
        layout.addWidget(lbl)

        # Core indicators
        self._core_labels = []
        for i in range(3):
            core_lbl = QLabel("C{}".format(i))
            core_lbl.setStyleSheet(
                "background-color: #21262d; color: #484f58; font-size: 10px; "
                "border-radius: 3px; padding: 2px 6px; border: none;"
            )
            layout.addWidget(core_lbl)
            self._core_labels.append(core_lbl)

        # FPS
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("color: #c9d1d9; font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(self._fps_label)

    # ── Public ────────────────────────────────────────────────────

    def set_core_active(self, core_idx: int, active: bool):
        """Highlight a core as active/inactive."""
        if 0 <= core_idx < 3:
            if active:
                self._core_labels[core_idx].setStyleSheet(
                    "background-color: #1a7f37; color: #ffffff; font-size: 10px; "
                    "border-radius: 3px; padding: 2px 6px; border: none;"
                )
            else:
                self._core_labels[core_idx].setStyleSheet(
                    "background-color: #21262d; color: #484f58; font-size: 10px; "
                    "border-radius: 3px; padding: 2px 6px; border: none;"
                )

    def set_fps(self, fps: float):
        """Update FPS display."""
        self._fps_label.setText("FPS: {:.1f}".format(fps))

    def set_all_active(self):
        """Light all three cores as active (default during inference)."""
        for i in range(3):
            self.set_core_active(i, True)

    def set_all_idle(self):
        """Dim all cores (idle state)."""
        for i in range(3):
            self.set_core_active(i, False)
