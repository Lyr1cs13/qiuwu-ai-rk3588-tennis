# -*- coding: utf-8 -*-
"""
Score Box Widget — displays IN/OUT verdict and real-time score.

Reads from judgement.json to show:
  - Latest verdict (IN green / OUT red)
  - Top vs Bottom scores
  - Point summary
"""

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy,
)


class ScoreBox(QWidget):
    """Score and verdict display widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)

        # Verdict (compact, bold)
        self._verdict_label = QLabel(" 等待判罚...")
        self._verdict_label.setAlignment(Qt.AlignCenter)
        self._verdict_label.setMinimumHeight(30)
        self._verdict_label.setStyleSheet(
            "background:#11161f;color:#8b949e;font-size:13px;"
            "font-weight:bold;border:1px solid #2a3040;"
            "border-radius:6px;padding:6px;"
        )
        layout.addWidget(self._verdict_label)

        # Score row
        score_frame = QFrame()
        score_frame.setStyleSheet(
            "background:#111820;border:1px solid #2a3040;border-radius:6px;")
        score_layout = QHBoxLayout(score_frame)
        score_layout.setContentsMargins(8, 3, 8, 3)

        self._score_top = QLabel("0")
        self._score_top.setAlignment(Qt.AlignCenter)
        self._score_top.setStyleSheet("color:#58a6ff;font-size:26px;font-weight:bold;border:none;")
        self._score_bottom = QLabel("0")
        self._score_bottom.setAlignment(Qt.AlignCenter)
        self._score_bottom.setStyleSheet("color:#f0a050;font-size:26px;font-weight:bold;border:none;")
        vs = QLabel(":")
        vs.setAlignment(Qt.AlignCenter)
        vs.setStyleSheet("color:#484f58;font-size:20px;border:none;")

        score_layout.addWidget(QLabel("TOP"))
        score_layout.addWidget(self._score_top)
        score_layout.addWidget(vs)
        score_layout.addWidget(self._score_bottom)
        score_layout.addWidget(QLabel("BOT"))
        for lbl in score_frame.findChildren(QLabel):
            if lbl.text() in ("TOP", "BOT"):
                lbl.setStyleSheet("color:#8b949e;font-size:8px;border:none;")
                lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(score_frame)

        # Reason
        self._reason_label = QLabel("")
        self._reason_label.setAlignment(Qt.AlignCenter)
        self._reason_label.setWordWrap(True)
        self._reason_label.setStyleSheet("color:#8b949e;font-size:9px;border:none;padding:2px;")
        layout.addWidget(self._reason_label)

    # ── Public slot ───────────────────────────────────────────────

    @pyqtSlot(object)
    def update_judgement(self, data: dict):
        if not data:
            return

        # Find the latest point_awarded judgement for final score
        judgements = data.get("judgements", [])
        top_pts = 0
        bot_pts = 0
        last_verdict = ""
        last_winner = ""
        last_reason = ""
        last_frame = 0

        for j in judgements:
            if j.get("score_changed") or j.get("point_awarded"):
                sa = j.get("score_after", {})
                top_pts = sa.get("top", top_pts)
                bot_pts = sa.get("bottom", bot_pts)
            last_verdict = j.get("status", "")
            last_winner = j.get("winner", "")
            last_reason = j.get("reason", "")
            last_frame = j.get("frame", last_frame)

        self._score_top.setText(str(top_pts))
        self._score_bottom.setText(str(bot_pts))

        # Status text mapping
        status_map = {
            "OUT_POINT": ("● OUT 出界", "#da3633"),
            "OWN_SIDE_POINT_LOST": ("● 落己方场地", "#da3633"),
            "IN_CONTINUE": ("● IN 继续", "#1a7f37"),
        }
        text, color = status_map.get(last_verdict,
                                     ("● 得分方: {}".format(last_winner or "?"), "#1a7f37"))
        self._verdict_label.setText(text)
        self._verdict_label.setStyleSheet(
            "background:{};color:#fff;font-size:13px;"
            "font-weight:bold;border-radius:6px;padding:4px;".format(color))

        self._reason_label.setText(
            "frame={} | {}\nTop {} : Bottom {}".format(
                last_frame, last_reason.replace("_", " "), top_pts, bot_pts))
