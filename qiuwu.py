#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""球悟AI公开工程统一入口。

公开仓库负责触控交互、摄像头采集、任务编排和云端适配。模型推理、
事件分析与判罚算法由独立私有运行时通过稳定命令契约接入。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from runtime_bridge import PrivateRuntime, RuntimeConfigurationError


ROOT = Path(__file__).resolve().parent


def run_gui(args: argparse.Namespace) -> int:
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "wayland")
    env.setdefault("QT_SCALE_FACTOR", "1")
    env.setdefault("QT_PLUGIN_PATH", "/usr/lib/aarch64-linux-gnu/qt5/plugins")
    cmd = [sys.executable, str(ROOT / "gui" / "tennis_gui.py")]
    if args.compact:
        cmd.append("--compact")
    return subprocess.run(cmd, cwd=str(ROOT), env=env, check=False).returncode


def run_camera(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(ROOT / "camera_recorder.py"),
        "--device", args.device,
        "--width", str(args.width),
        "--height", str(args.height),
        "--fps", str(args.fps),
    ]
    if args.headless:
        cmd.append("--headless")
    return subprocess.run(cmd, cwd=str(ROOT), check=False).returncode


def run_pipeline(args: argparse.Namespace) -> int:
    runtime = PrivateRuntime(ROOT)
    modes = ("match", "side") if args.mode == "all" else (args.mode,)
    for mode in modes:
        video = args.video
        if args.mode == "all":
            video = args.match_video if mode == "match" else args.side_video
        if not video:
            video = str(ROOT / ("match_judgement" if mode == "match" else "side_training") / "input.mp4")
        rc = runtime.run(
            mode=mode,
            video=Path(video),
            cloud=args.cloud,
            calibrate_only=args.calibrate_only,
        )
        if rc != 0:
            return rc
    return 0


def check_environment(_: argparse.Namespace) -> int:
    print("球悟AI公开工程检查")
    ok = True
    for module, label in (("cv2", "OpenCV"), ("numpy", "NumPy"), ("PyQt5", "PyQt5")):
        try:
            __import__(module)
            print(f"[OK] {label}")
        except Exception as exc:
            ok = False
            print(f"[MISS] {label}: {exc}")

    runtime = PrivateRuntime(ROOT, required=False)
    if runtime.available:
        print("[OK] 私有AI运行时已接入")
        for mode in ("match", "side"):
            print(f"[{'OK' if runtime.has_mode(mode) else 'MISS'}] {mode}运行模式")
    else:
        print("[PUBLIC] 未安装私有AI运行时；GUI、摄像头和公开接口仍可使用")
        print("         复制runtime.private.example.json为runtime.private.json并配置内部运行器")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="球悟AI：RK3588网球智练智判系统")
    sub = parser.add_subparsers(dest="command")

    gui = sub.add_parser("gui", help="启动PyQt触控界面")
    gui.add_argument("--compact", action="store_true", help="适配小尺寸触控屏")
    gui.set_defaults(func=run_gui)

    run = sub.add_parser("run", help="通过私有运行时执行端侧分析")
    run.add_argument("--mode", choices=["match", "side", "all"], default="match")
    run.add_argument("--video", help="单模式输入视频")
    run.add_argument("--match-video", help="all模式的比赛视角视频")
    run.add_argument("--side-video", help="all模式的侧视训练视频")
    run.add_argument("--cloud", action="store_true", help="允许私有运行时提交标准化上云任务")
    run.add_argument("--calibrate-only", action="store_true", help="仅请求场地标定")
    run.set_defaults(func=run_pipeline)

    camera = sub.add_parser("camera", help="OV13855摄像头预览与录制")
    camera.add_argument("--device", default="/dev/video11")
    camera.add_argument("--width", type=int, default=1920)
    camera.add_argument("--height", type=int, default=1080)
    camera.add_argument("--fps", type=float, default=60.0)
    camera.add_argument("--headless", action="store_true")
    camera.set_defaults(func=run_camera)

    check = sub.add_parser("check", help="检查公开工程与私有运行时接入状态")
    check.set_defaults(func=check_environment)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["gui"])
    try:
        return args.func(args)
    except (RuntimeConfigurationError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
