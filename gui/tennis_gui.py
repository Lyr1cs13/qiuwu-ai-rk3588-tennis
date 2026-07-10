#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QiuWu AI | 球悟AI — Mode-driven tennis analysis GUI.

Two scenes → one unified RUN button:
  Scene A: 俯视·比赛智判 (match judgement)
  Scene B: 侧视·个人智练 (side training)
"""

import os, sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStatusBar, QLabel, QMessageBox, QDockWidget, QPushButton,
    QApplication, QDesktopWidget, QFrame, QScroller,
    QPlainTextEdit, QScrollArea, QTableWidget,
)
from PyQt5.QtGui import QFont

from gui.app import create_application
from gui.modes import MODE_A, MODE_B, get_mode_info, get_script
from gui.panels.left_panel import LeftModePanel
from gui.panels.center_panel import CenterVisualPanel
from gui.panels.right_panel import RightDataPanel
from gui.panels.top_bar import TopStatusBar
from gui.panels.bottom_console import BottomConsole
from gui.backend.process_manager import ProcessManager
from gui.backend.file_watcher import FileWatcher
from gui.backend.data_parser import DataParser


COMPACT_QSS = """
* { font-size: 11px; }
QGroupBox { font-size: 11px; padding: 6px 4px 4px 4px; margin-top: 8px; }
QGroupBox::title { font-size: 10px; padding: 0 4px; }
QPushButton { padding: 4px 8px; font-size: 11px; min-height: 24px; }
QPushButton#btnRun { font-size: 14px; min-height: 36px; }
QPushButton#btnStop { font-size: 14px; min-height: 36px; }
QLabel#sceneTitle { font-size: 13px; }
QTableWidget { font-size: 10px; }
QPlainTextEdit { font-size: 9px; }
"""


class TennisGUI(QMainWindow):

    signal_log = pyqtSignal(str)

    def __init__(self, compact=False):
        super().__init__()
        self._compact = compact

        self.process_mgr = ProcessManager()
        self.data_parser = DataParser(project_root=_PROJECT_ROOT)
        self.file_watcher = FileWatcher(project_root=_PROJECT_ROOT)

        self._active_mode = MODE_A
        self._cloud_enabled = False
        self._running = False
        self._mode_state = {}

        self.setWindowTitle("QiuWu AI | 球悟AI 网球智练智判系统")
        if compact:
            self.setMinimumSize(800, 480)
            self.setWindowFlags(Qt.FramelessWindowHint)
        else:
            self.setMinimumSize(1280, 800)
            self.resize(1920, 1080)

        self._build_top_bar()
        self._build_central()
        self._build_bottom()
        self._wire_signals()

        if compact:
            self.showFullScreen()
        self._enable_touch_scroll()

        self._log("[系统] QiuWu AI 球悟AI 已启动 — {}".format(
            "紧凑模式" if compact else "标准模式"))
        self._log("[系统] 项目根: {}".format(_PROJECT_ROOT))

        info = get_mode_info(MODE_A)
        self.center_panel.video_widget.show_placeholder(info["name"])

    # ── Build ────────────────────────────────────────────────────

    def _build_top_bar(self):
        self.top_bar = TopStatusBar()
        self.top_bar.setMovable(False)

        if self._compact:
            for name, icon in [("_btn_menu", "☰"), ("_btn_data", "📊"),
                               ("_btn_log", "📜"), ("_btn_exit", "✕")]:
                btn = QPushButton(icon)
                btn.setFixedSize(32, 28)
                btn.setStyleSheet(
                    "QPushButton{background:#21262d;border:1px solid #30363d;"
                    "border-radius:4px;color:#c9d1d9;font-size:14px}"
                    "QPushButton:hover{background:#30363d}")
                if icon == "✕":
                    btn.setStyleSheet(btn.styleSheet().replace(
                        "#21262d", "#da3633").replace("#30363d", "#f85149"))
                    btn.clicked.connect(self.close)
                setattr(self, name, btn)
            self.top_bar.insertWidget(None, self._btn_menu)
            self.top_bar.addWidget(self._btn_log)
            self.top_bar.addWidget(self._btn_data)
            self.top_bar.addWidget(self._btn_exit)

        self.addToolBar(Qt.TopToolBarArea, self.top_bar)
        self.top_bar.set_batch_upload_callback(self.run_batch_upload)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        if self._compact:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.center_panel = CenterVisualPanel(_PROJECT_ROOT, compact=True)
            layout.addWidget(self.center_panel)
            container = QWidget()
            container.setLayout(layout)
            root_layout.addWidget(container)

            self.left_panel = LeftModePanel(self)
            self.right_panel = RightDataPanel()

            self._dock_left = QDockWidget("场景模式")
            self._dock_left.setWidget(self.left_panel)
            self._dock_left.setMaximumWidth(360)
            self._dock_left.setMinimumWidth(260)
            self._dock_left.close()
            self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_left)

            self._dock_right = QDockWidget("数据面板")
            self._dock_right.setWidget(self.right_panel)
            self._dock_right.setMaximumWidth(380)
            self._dock_right.setMinimumWidth(260)
            self._dock_right.close()
            self.addDockWidget(Qt.RightDockWidgetArea, self._dock_right)

            self._dock_log = QDockWidget("日志")
            self._dock_log.setWidget(BottomConsole())
            self._dock_log.setMaximumHeight(180)
            self._dock_log.close()
            self.addDockWidget(Qt.BottomDockWidgetArea, self._dock_log)
            self.bottom_console = self._dock_log.widget()

            self._btn_menu.clicked.connect(
                lambda: self._dock_left.show() if self._dock_left.isHidden()
                else self._dock_left.close())
            self._btn_data.clicked.connect(
                lambda: self._dock_right.show() if self._dock_right.isHidden()
                else self._dock_right.close())
            self._btn_log.clicked.connect(
                lambda: self._dock_log.show() if self._dock_log.isHidden()
                else self._dock_log.close())
        else:
            splitter = QSplitter(Qt.Horizontal)
            splitter.setHandleWidth(1)
            self.left_panel = LeftModePanel(self)
            self.left_panel.setMinimumWidth(260)
            self.left_panel.setMaximumWidth(320)
            splitter.addWidget(self.left_panel)
            self.center_panel = CenterVisualPanel(_PROJECT_ROOT)
            splitter.addWidget(self.center_panel)
            self.right_panel = RightDataPanel()
            self.right_panel.setMinimumWidth(280)
            splitter.addWidget(self.right_panel)
            splitter.setStretchFactor(0, 2)
            splitter.setStretchFactor(1, 5)
            splitter.setStretchFactor(2, 3)
            splitter.setSizes([260, 700, 380])
            root_layout.addWidget(splitter)
            self.bottom_console = BottomConsole()

    def _build_bottom(self):
        if self._compact:
            return
        dock = QDockWidget("终端日志")
        dock.setWidget(self.bottom_console)
        dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    # ── Signals ──────────────────────────────────────────────────

    def _wire_signals(self):
        self.process_mgr.signal_stdout.connect(self._on_stdout)
        self.process_mgr.signal_stderr.connect(self._on_stderr)
        self.process_mgr.signal_process_started.connect(self._on_started)
        self.process_mgr.signal_process_finished.connect(self._on_finished)

        self.file_watcher.signal_judgement_updated.connect(
            self.right_panel.update_judgement)
        self.file_watcher.signal_bounce_events_updated.connect(
            self.right_panel.update_bounce_events)
        self.file_watcher.signal_trajectory_updated.connect(
            self.top_bar.on_trajectory_data)
        self.file_watcher.signal_action_prediction_updated.connect(
            self.center_panel.action_timeline.load_actions)
        self.file_watcher.signal_action_prediction_updated.connect(
            self.right_panel.update_frequencies)

        self.center_panel.video_widget.signal_frame_captured.connect(
            self.left_panel._on_frame_captured)
        self.signal_log.connect(self.bottom_console.append_line)

    # ── Mode switching ───────────────────────────────────────────

    def set_mode(self, mode_key):
        old_mode = getattr(self, '_active_mode', None)
        if old_mode and old_mode != mode_key:
            self._mode_state[old_mode] = {
                'cloud': self._cloud_enabled,
                'file_path': self.left_panel._src_path.text(),
                'cam_checked': self.left_panel._src_cam.isChecked(),
            }

        self._active_mode = mode_key
        info = get_mode_info(mode_key)

        if mode_key in self._mode_state:
            st = self._mode_state[mode_key]
            self._cloud_enabled = st['cloud']
            self.left_panel._cloud_check.setChecked(st['cloud'])
            self.left_panel._src_path.setText(st['file_path'])
            if st['cam_checked']:
                self.left_panel._src_cam.setChecked(True)
            else:
                self.left_panel._src_file.setChecked(True)
        else:
            self._cloud_enabled = False
            self.left_panel._cloud_check.setChecked(False)
            self.right_panel.cloud_indicator.set_mqtt_status(False)
            self.top_bar.set_cloud_status("disabled")

        self._log("[模式] 切换 → {}".format(info["name"]))
        self.center_panel.set_mode(mode_key)
        self.center_panel.video_widget.set_mode(mode_key)
        self.right_panel.set_mode(mode_key)
        self.top_bar.set_mode_label(info["name"])

    def set_cloud(self, enabled):
        self._cloud_enabled = enabled
        name = get_mode_info(self._active_mode)["name"]
        if enabled:
            self._log("[{}] 自动上云 ON — 点击 RUN 后连接".format(name))
            self.right_panel.cloud_indicator.set_mqtt_status(False, "待启动")
            self.top_bar.set_cloud_status("disabled")
        else:
            self._log("[{}] 本地模式".format(name))
            self.right_panel.cloud_indicator.set_mqtt_status(False, "未连接")
            self.top_bar.set_cloud_status("disabled")

    # ── Pipeline ─────────────────────────────────────────────────

    def run_pipeline(self):
        info = get_mode_info(self._active_mode)
        if self._cloud_enabled:
            self._log("[云端] MQTT+OSS 自动上传已启用")

        if self.left_panel._src_cam.isChecked():
            self._log("[相机] 启动实时预览 + 录制")
            self.center_panel.video_widget.start_camera_preview()
            self.left_panel._start_camera_recording()
            return

        # Validate file is selected
        video_path = self.left_panel._src_path.text().strip()
        if not video_path or not os.path.exists(video_path):
            self._msgbox("未选择文件",
                        "请先选择视频文件再启动运行。\n\n"
                        "步骤：选择 ○ 本地文件 → 点击 📂 浏览文件")
            self._log("[错误] 未选择有效的视频文件")
            return

        self._log("[启动] {}".format(info["name"]))
        self._log("[输入] 本地文件: {}".format(video_path))
        cli_mode = get_script(self._active_mode, self._cloud_enabled)
        cmd = [sys.executable, os.path.join(_PROJECT_ROOT, "qiuwu.py"),
               "run", "--mode", cli_mode, "--video", video_path]
        if self._cloud_enabled:
            cmd.append("--cloud")
        task_name = info["task_name"]

        # Start progress bar
        self.center_panel.progress_bar.start_running(cloud=self._cloud_enabled)

        self.process_mgr.start_script(task_name, cmd, cwd=_PROJECT_ROOT)
        self.file_watcher.start_watching(task_name)
        self._running = True

    def stop_pipeline(self):
        info = get_mode_info(self._active_mode)
        self.center_panel.progress_bar.stop_running()
        if self.left_panel._src_cam.isChecked():
            self.left_panel._on_stop_recording()
            self.center_panel.video_widget.stop_camera_preview()
            self._log("[相机] 录制停止, 开始处理...")
            rec_path = getattr(self.left_panel, '_rec_path', None)
            if rec_path and os.path.exists(rec_path):
                cli_mode = get_script(self._active_mode, self._cloud_enabled)
                cmd = [sys.executable, os.path.join(_PROJECT_ROOT, "qiuwu.py"),
                       "run", "--mode", cli_mode, "--video", rec_path]
                if self._cloud_enabled:
                    cmd.append("--cloud")
                self._log("[输入] 录制文件: {}".format(rec_path))
                self.center_panel.progress_bar.start_running(
                    cloud=self._cloud_enabled)
                self.process_mgr.start_script(
                    info["task_name"], cmd, cwd=_PROJECT_ROOT)
                self.file_watcher.start_watching(info["task_name"])
        else:
            self.process_mgr.stop_process(info["task_name"])
        self._running = False
        self._log("[停止] {} 已终止".format(info["name"]))

    def run_camera_preview(self):
        if self.center_panel.video_widget.start_camera_preview():
            self._log("[相机] 实时预览已启动")
        else:
            self._log("[相机] 预览启动失败")

    def stop_camera_preview(self):
        self.center_panel.video_widget.stop_camera_preview()
        self._log("[相机] 预览已停止")

    def run_batch_upload(self):
        self.process_mgr.start_script(
            "batch_upload",
            [sys.executable, os.path.join(_PROJECT_ROOT, "qiuwu.py"),
             "run", "--mode", "all", "--cloud"],
            cwd=_PROJECT_ROOT)
        self._log("[云端] 批量上传已启动")

    # ── Slots ────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_stdout(self, text):
        self.bottom_console.append_stdout(text)

    @pyqtSlot(str)
    def _on_stderr(self, text):
        self.bottom_console.append_stderr(text)

    @pyqtSlot(str)
    def _on_started(self, name):
        self.bottom_console.append_system("[OK] {} 已启动".format(name))

    @pyqtSlot(str, int)
    def _on_finished(self, name, rc):
        status = "完成" if rc == 0 else "失败 (code={})".format(rc)
        self.bottom_console.append_system("[{}] {} {}".format(
            "OK" if rc == 0 else "ERR", name, status))
        self._running = False
        self.center_panel.progress_bar.stop_running()
        # Animate cloud progress if cloud was enabled
        if self._cloud_enabled and rc == 0:
            for i in range(5):
                QTimer.singleShot(i * 400, lambda p=(i+1)*20:
                    self.center_panel.progress_bar.set_cloud_progress(p))
            QTimer.singleShot(2200, lambda:
                self.center_panel.progress_bar.set_cloud_progress(100))
        if rc == 0:
            info = get_mode_info(self._active_mode)
            video_rel = info.get("output_video", "")
            if video_rel:
                video_path = os.path.join(_PROJECT_ROOT, video_rel)
                if os.path.exists(video_path):
                    self._log("[视频] 加载结果: {}".format(video_rel))
                    self.center_panel.video_widget.load_video(video_path)

    # ── Touch ────────────────────────────────────────────────────

    def _enable_touch_scroll(self):
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPlainTextEdit, QScrollArea, QTableWidget)):
                QScroller.grabGesture(widget.viewport(), QScroller.TouchGesture)

    def _log(self, msg):
        self.bottom_console.append_system(msg)

    # ── Close ────────────────────────────────────────────────────

    def _msgbox(self, title, text, icon=QMessageBox.Warning,
                buttons=QMessageBox.Ok):
        """Create a centered, readable message box."""
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)
        box.setStandardButtons(buttons)
        box.setStyleSheet(
            "QMessageBox{background:#161b22;font-size:14px;}"
            "QLabel{color:#e0e0e0;font-size:14px;min-width:300px;}"
            "QPushButton{background:#21262d;color:#c9d1d9;"
            "border:1px solid #30363d;border-radius:4px;"
            "padding:8px 20px;font-size:13px;min-width:80px;}"
            "QPushButton:hover{background:#30363d;}")
        return box.exec()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "退出确认",
            "确定要退出球悟AI系统吗？\n所有正在运行的任务将被终止。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.process_mgr.stop_all()
            self.file_watcher.stop_watching()
            event.accept()
        else:
            event.ignore()


# ── Entry ────────────────────────────────────────────────────────

def _is_small_screen():
    try:
        return QDesktopWidget().screenGeometry().width() < 1200
    except Exception:
        return False


def main():
    app = create_application(sys.argv)
    compact = "--compact" in sys.argv or _is_small_screen()
    if compact:
        app.setStyleSheet(app.styleSheet() + COMPACT_QSS)
    window = TennisGUI(compact=compact)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
