# -*- coding: utf-8 -*-
"""
Right Data Panel — compact score, events table, action frequency, cloud.
"""

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QStackedWidget,
)

from gui.modes import MODE_A, MODE_B
from gui.widgets.score_box import ScoreBox
from gui.widgets.event_table import EventTable
from gui.widgets.cloud_indicator import CloudIndicator


class RightDataPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Cloud indicator at TOP so bottom console doesn't block it
        self.cloud_indicator = CloudIndicator()
        layout.addWidget(self.cloud_indicator)

        # Header
        self._header = QLabel("比赛判罚看板")
        self._header.setAlignment(Qt.AlignCenter)
        self._header.setStyleSheet(
            "color:#ccff00;font-weight:bold;font-size:12px;border:none;")
        layout.addWidget(self._header)

        # Stacked panels
        self._stack = QStackedWidget()
        self._match_panel = self._build_match_panel()
        self._stack.addWidget(self._match_panel)
        self._training_panel = self._build_training_panel()
        self._stack.addWidget(self._training_panel)
        layout.addWidget(self._stack, 1)

    # ── Match panel ──────────────────────────────────────────────

    def _build_match_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(3)

        self.score_box = ScoreBox()
        l.addWidget(self.score_box)

        self.event_table = EventTable()
        l.addWidget(self.event_table, 1)
        return w

    # ── Training panel ───────────────────────────────────────────

    def _build_training_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)

        lbl = QLabel("当前动作")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "color:#58a6ff;font-weight:bold;font-size:12px;border:none;")
        l.addWidget(lbl)

        self._action_label = QLabel("等待数据...")
        self._action_label.setAlignment(Qt.AlignCenter)
        self._action_label.setMinimumHeight(32)
        self._action_label.setStyleSheet(
            "background:#161b22;color:#8b949e;font-size:18px;font-weight:bold;"
            "border:1px solid #30363d;border-radius:6px;padding:6px;")
        l.addWidget(self._action_label)

        lbl2 = QLabel("动作频率统计")
        lbl2.setAlignment(Qt.AlignCenter)
        lbl2.setStyleSheet(
            "color:#58a6ff;font-weight:bold;font-size:11px;border:none;")
        l.addWidget(lbl2)

        # Frequency bars — store references for updates
        self._freq_bars = {}
        for key, label, color in [
            ("forehand", "正手", "#f0a050"),
            ("backhand", "反手", "#3fb950"),
            ("serve", "发球", "#58a6ff"),
            ("background", "背景", "#484f58"),
        ]:
            fw, flabel, fbar = self._make_freq_bar(label, color)
            self._freq_bars[key] = fbar
            l.addWidget(fw)

        l.addStretch()
        return w

    def _make_freq_bar(self, label, color):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 1, 0, 1)
        l.setSpacing(4)
        name = QLabel(label)
        name.setStyleSheet(
            "color:#8b949e;font-size:10px;border:none;min-width:70px;")
        l.addWidget(name)
        bar = QLabel("0%")
        bar.setAlignment(Qt.AlignCenter)
        bar.setStyleSheet(
            "background:{};color:#fff;font-size:9px;font-weight:bold;"
            "border-radius:3px;padding:2px 4px;min-width:45px;".format(color))
        l.addWidget(bar, 1)
        return w, bar, bar

    def update_frequencies(self, predictions: list):
        if not predictions:
            return
        total = len(predictions)
        counts = {"forehand": 0, "backhand": 0, "serve": 0, "background": 0}
        for p in predictions:
            if p in counts:
                counts[p] += 1
        for key, bar in self._freq_bars.items():
            cnt = counts.get(key, 0)
            pct = cnt / total * 100 if total > 0 else 0
            bar.setText("{:.1f}%".format(pct))
        self._action_label.setText("数据分析成功")
        self._action_label.setStyleSheet(
            "background:#1a7f37;color:#fff;font-size:16px;font-weight:bold;"
            "border:1px solid #30363d;border-radius:6px;padding:6px;")
        self._header.setText("个人智练看板 ✓")

    # ── Mode switching ───────────────────────────────────────────

    def set_mode(self, mode_key):
        if mode_key == MODE_A:
            self._stack.setCurrentIndex(0)
            self._header.setText("比赛判罚看板")
        elif mode_key == MODE_B:
            self._stack.setCurrentIndex(1)
            self._header.setText("个人智练看板")

    # ── Public slots ─────────────────────────────────────────────

    @pyqtSlot(object)
    def update_judgement(self, data: dict):
        self.score_box.update_judgement(data)
        self._header.setText("比赛判罚看板 ✓")

    @pyqtSlot(object)
    def update_bounce_events(self, events: list):
        self.event_table.update_bounce_events(events)

    def set_action(self, action: str):
        colors = {"serve": "#58a6ff", "forehand": "#f0a050",
                  "backhand": "#3fb950", "background": "#8b949e"}
        labels = {"serve": "发球 SERVE", "forehand": "正手 FOREHAND",
                  "backhand": "反手 BACKHAND", "background": "背景"}
        color = colors.get(action, "#8b949e")
        label = labels.get(action, action)
        self._action_label.setText(label)
        self._action_label.setStyleSheet(
            "background:#161b22;color:{};font-size:18px;font-weight:bold;"
            "border:1px solid #30363d;border-radius:6px;padding:6px;".format(color))
