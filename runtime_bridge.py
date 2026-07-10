#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公开工程与私有AI运行时之间的稳定进程契约。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class RuntimeConfigurationError(RuntimeError):
    pass


class PrivateRuntime:
    """从本地私有清单加载比赛/训练运行器，不暴露其内部实现。"""

    def __init__(self, root: Path, required: bool = True):
        self.root = Path(root).resolve()
        self.config_path = self.root / "runtime.private.json"
        self.config = None
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as handle:
                self.config = json.load(handle)
            self._validate()
        elif required:
            raise RuntimeConfigurationError(
                "未安装私有AI运行时。公开仓库仅提供产品外壳与接口；"
                "内部部署时请提供runtime.private.json。"
            )

    @property
    def available(self) -> bool:
        return self.config is not None

    def has_mode(self, mode: str) -> bool:
        return bool(self.config and mode in self.config.get("modes", {}))

    def _validate(self) -> None:
        if self.config.get("schema_version") != 1:
            raise RuntimeConfigurationError("runtime.private.json版本不受支持")
        modes = self.config.get("modes")
        if not isinstance(modes, dict):
            raise RuntimeConfigurationError("runtime.private.json缺少modes对象")
        for name, item in modes.items():
            command = item.get("command") if isinstance(item, dict) else None
            if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
                raise RuntimeConfigurationError(f"运行模式{name}的command必须是非空字符串数组")

    def run(self, mode: str, video: Path, cloud: bool, calibrate_only: bool = False) -> int:
        if not self.has_mode(mode):
            raise RuntimeConfigurationError(f"私有运行时未提供{mode}模式")
        video = Path(video).expanduser().resolve()
        if not video.exists():
            raise FileNotFoundError(f"输入视频不存在: {video}")

        item = self.config["modes"][mode]
        command = list(item["command"])
        command.extend(["--video", str(video)])
        if cloud:
            command.append("--cloud")
        if calibrate_only:
            command.append("--calibrate-only")

        env = os.environ.copy()
        env.update(
            {
                "QIUWU_PROJECT_ROOT": str(self.root),
                "QIUWU_TASK_MODE": mode,
                "QIUWU_RESULT_SCHEMA": str(self.root / "contracts" / "task-result.schema.json"),
            }
        )
        cwd = Path(item.get("cwd", self.root))
        if not cwd.is_absolute():
            cwd = self.root / cwd
        return subprocess.run(command, cwd=str(cwd), env=env, check=False).returncode
