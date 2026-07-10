#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera Recorder — tkinter live preview + OpenCV MP4 recording.

Stack (proven on RK3588):
  UI:            tkinter
  Video display: PIL.ImageTk.PhotoImage (real-time refresh)
  Camera:        cv2.VideoCapture + V4L2 (/dev/video11, MJPG)
  Recording:     cv2.VideoWriter (mp4v codec → .mp4)
  Concurrency:   threading.Thread (UI main + camera capture)
  Timing:        time.perf_counter() + root.after(200, ...)
  File naming:   recording_1.mp4, recording_2.mp4, ...

Usage:
    python3 camera_recorder.py              # preview only
    python3 camera_recorder.py --headless   # recording only, no preview window
"""

import argparse
import os
import sys
import threading
import time

import cv2
from PIL import Image, ImageTk

# ── Camera defaults ──────────────────────────────────────────────
DEFAULT_DEVICE = "/dev/video11"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = 600
OUTPUT_DIR = os.path.expanduser("~/rk3588_tennis_system/outputs/recordings")

# ── Filename generator ───────────────────────────────────────────

def next_filename():
    """Generate incremental filename: recording_1.mp4, recording_2.mp4, ..."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    i = 1
    while True:
        path = os.path.join(OUTPUT_DIR, "recording_{}.mp4".format(i))
        if not os.path.exists(path):
            return path
        i += 1


# ── Camera recorder class ────────────────────────────────────────

class CameraRecorder:
    """tkinter-based camera preview + MP4 recording."""

    def __init__(self, device=DEFAULT_DEVICE, width=DEFAULT_WIDTH,
                 height=DEFAULT_HEIGHT, fps=30.0, headless=False):
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.headless = headless

        # State
        self.cap = None
        self.writer = None
        self.recording = False
        self.recording_start = 0.0
        self.frame_count = 0
        self.output_path = None
        self.running = False

        # tkinter
        self.root = None
        self.panel = None
        self.btn_record = None
        self.lbl_status = None

    # ── Camera ───────────────────────────────────────────────────

    def open_camera(self):
        """Open V4L2 camera with MJPG format."""
        cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        return cap

    # ── Recording ────────────────────────────────────────────────

    def start_recording(self):
        """Start MP4 recording via cv2.VideoWriter."""
        self.output_path = next_filename()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(
            self.output_path, fourcc, self.fps,
            (self.width, self.height),
        )
        if not self.writer.isOpened():
            self._log("ERROR: Cannot create video writer")
            return False
        self.recording = True
        self.recording_start = time.perf_counter()
        self._log("REC START: {}".format(os.path.basename(self.output_path)))
        return True

    def stop_recording(self):
        """Stop recording and finalize file."""
        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None
        if self.output_path and os.path.exists(self.output_path):
            dur = time.perf_counter() - self.recording_start
            sz = os.path.getsize(self.output_path)
            self._log("REC SAVED: {} ({:.1f} MB, {:.0f}s)".format(
                os.path.basename(self.output_path),
                sz / (1024 * 1024), dur,
            ))
        self.output_path = None

    # ── Helpers ──────────────────────────────────────────────────

    def _log(self, msg):
        print("[{}] {}".format(
            time.strftime("%H:%M:%S"), msg))
        sys.stdout.flush()

    def _format_duration(self, seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return "{}:{:02d}:{:02d}".format(h, m, s)
        return "{}:{:02d}".format(m, s)

    # ── UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        """Build tkinter preview window."""
        import tkinter as tk

        self.root = tk.Tk()
        self.root.title("Camera Recorder — OV13855")
        self.root.configure(bg="#1a1a2e")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Preview panel
        self.panel = tk.Label(self.root, bg="#0d1117")
        self.panel.pack(padx=4, pady=(4, 0))

        # Bottom bar
        bar = tk.Frame(self.root, bg="#1a1a2e")
        bar.pack(fill=tk.X, padx=8, pady=4)

        self.btn_record = tk.Button(
            bar, text="● 开始录制", bg="#1a7f37", fg="white",
            font=("", 11, "bold"), relief=tk.FLAT,
            activebackground="#2ea043", activeforeground="white",
            command=self._toggle_recording,
        )
        self.btn_record.pack(side=tk.LEFT, padx=2)

        btn_quit = tk.Button(
            bar, text="✕ 退出", bg="#da3633", fg="white",
            font=("", 10), relief=tk.FLAT,
            activebackground="#f85149", activeforeground="white",
            command=self._on_close,
        )
        btn_quit.pack(side=tk.RIGHT, padx=2)

        self.lbl_status = tk.Label(
            bar, text="就绪 | 0帧",
            bg="#1a1a2e", fg="#8b949e", font=("", 9),
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=8)

        # Key bindings
        self.root.bind('<space>', lambda e: self._toggle_recording())
        self.root.bind('<Escape>', lambda e: self._on_close())
        self.root.bind('q', lambda e: self._on_close())

        self.root.geometry("{}x{}".format(
            PREVIEW_WIDTH + 16, PREVIEW_HEIGHT + 60))

    def _toggle_recording(self):
        """Start or stop recording."""
        if self.recording:
            self.stop_recording()
            self.btn_record.configure(
                text="● 开始录制", bg="#1a7f37")
        else:
            if self.start_recording():
                self.btn_record.configure(
                    text="■ 停止录制", bg="#da3633")

    def _on_close(self):
        """Graceful shutdown."""
        self.running = False
        if self.recording:
            self.stop_recording()
        if self.root:
            self.root.quit()
            self.root.destroy()

    # ── Main loop (camera thread) ────────────────────────────────

    def _camera_loop(self):
        """Camera capture thread — reads frames and queues for UI."""
        start_time = time.perf_counter()
        fps_update_interval = 0.5
        last_fps_update = start_time
        fps_frame_count = 0
        fps_display = 0.0

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.005)
                continue

            self.frame_count += 1
            fps_frame_count += 1

            now = time.perf_counter()
            if now - last_fps_update >= fps_update_interval:
                fps_display = fps_frame_count / (now - last_fps_update)
                fps_frame_count = 0
                last_fps_update = now

            # Write to recording
            if self.recording and self.writer:
                self.writer.write(frame)

            # Convert to RGB for tkinter
            if not self.headless:
                preview = cv2.resize(frame, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
                rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

                # Overlay text
                lines = [
                    "{}x{} | {:.1f} fps | {}帧".format(
                        self.width, self.height, fps_display,
                        self.frame_count),
                ]
                if self.recording:
                    dur = time.perf_counter() - self.recording_start
                    lines.append("● REC {}".format(
                        self._format_duration(dur)))
                else:
                    lines.append("预览模式 (空格开始/停止, Q退出)")

                y = 18
                for line in lines:
                    cv2.putText(rgb, line, (6, y),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 255, 0), 1)
                    y += 18

                # The frame will be picked up by UI refresh timer
                self._current_frame = rgb

    def _ui_refresh(self):
        """Called by tkinter timer (~50ms) to refresh the preview image."""
        if not self.running or self.headless:
            return
        frame = getattr(self, '_current_frame', None)
        if frame is not None:
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.panel.imgtk = imgtk
            self.panel.configure(image=imgtk)

        # Update status label
        parts = []
        if self.recording:
            dur = time.perf_counter() - self.recording_start
            parts.append("● REC {}".format(self._format_duration(dur)))
        parts.append("{}帧".format(self.frame_count))
        if self.output_path and self.recording:
            sz = os.path.getsize(self.output_path) if os.path.exists(
                self.output_path) else 0
            parts.append("{:.1f}MB".format(sz / (1024 * 1024)))
        self.lbl_status.configure(text=" | ".join(parts))

        self.root.after(50, self._ui_refresh)

    # ── Run ──────────────────────────────────────────────────────

    def run(self):
        """Start the camera recorder."""
        self._log("Camera Recorder starting...")
        self._log("Device: {}  |  {}x{}  |  MJPG".format(
            self.device, self.width, self.height))

        # Open camera
        self.cap = self.open_camera()
        if self.cap is None:
            self._log("ERROR: Cannot open camera {}".format(self.device))
            return 1

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = actual_w
        self.height = actual_h
        self._log("Camera opened: {}x{}".format(actual_w, actual_h))

        self.running = True

        if self.headless:
            self._log("Headless mode — auto-recording")
            self.start_recording()
            self._camera_loop()
        else:
            # Build UI
            self._build_ui()

            # Start camera thread
            cam_thread = threading.Thread(
                target=self._camera_loop, daemon=True)
            cam_thread.start()

            # Start UI refresh
            self.root.after(100, self._ui_refresh)

            # Run tkinter main loop
            self.root.mainloop()

        # Cleanup
        self.running = False
        if self.recording:
            self.stop_recording()
        if self.cap:
            self.cap.release()
        self._log("Camera Recorder stopped. {} frames total.".format(
            self.frame_count))
        return 0


# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="tkinter Camera Recorder — OV13855"
    )
    parser.add_argument("--headless", action="store_true",
                        help="Recording only, no preview window")
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    recorder = CameraRecorder(
        device=args.device,
        width=args.width,
        height=args.height,
        fps=args.fps,
        headless=args.headless,
    )
    return recorder.run()


if __name__ == "__main__":
    sys.exit(main())
