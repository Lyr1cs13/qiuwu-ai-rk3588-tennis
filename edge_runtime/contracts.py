"""跨模型、跨业务模式共享的公开数据契约。

这些结构描述模块之间交换什么，不描述模型如何得到结果。私有组件只要
遵守这些契约，就可以替换模型版本而不修改GUI、云端或业务编排代码。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class FramePacket:
    index: int
    timestamp_s: float
    image: Any
    source_size: tuple[int, int]


@dataclass(frozen=True)
class TrackPoint:
    frame_index: int
    timestamp_s: float
    x: float
    y: float
    confidence: float
    source: str = "model"


@dataclass(frozen=True)
class CourtState:
    locked: bool
    image_points: Sequence[tuple[float, float]] = field(default_factory=tuple)
    quality: float = 0.0
    public_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PoseContext:
    frame_index: int
    available: bool
    public_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionSegment:
    label: str
    start_frame: int
    end_frame: int
    confidence: float


@dataclass(frozen=True)
class EventRecord:
    event_type: str
    frame_index: int
    timestamp_s: float
    position: Optional[tuple[float, float]] = None
    confidence: float = 0.0
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JudgementState:
    status: str
    score_top: int = 0
    score_bottom: int = 0
    reason: str = ""
    public_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskArtifacts:
    task_id: str
    mode: str
    video_path: Optional[Path] = None
    trajectory_path: Optional[Path] = None
    event_path: Optional[Path] = None
    summary_path: Optional[Path] = None
    extra_paths: Sequence[Path] = field(default_factory=tuple)
