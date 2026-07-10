"""AI组件能力接口。

公开层定义组件职责和协同关系；具体模型、参数、前后处理与判罚实现由
设备侧受保护运行时实现。接口采用Protocol，方便模型升级和场景替换。
"""

from __future__ import annotations

from typing import Iterable, Optional, Protocol, Sequence

from .contracts import (
    ActionSegment,
    CourtState,
    EventRecord,
    FramePacket,
    JudgementState,
    PoseContext,
    TaskArtifacts,
    TrackPoint,
)


class VideoSource(Protocol):
    def frames(self) -> Iterable[FramePacket]: ...
    def close(self) -> None: ...


class BallTracker(Protocol):
    def update(self, frame: FramePacket) -> Optional[TrackPoint]: ...
    def finalize(self) -> Sequence[TrackPoint]: ...


class CourtLocator(Protocol):
    def observe(self, frame: FramePacket) -> Optional[CourtState]: ...


class PoseProvider(Protocol):
    def update(self, frame: FramePacket) -> PoseContext: ...


class ActionRecognizer(Protocol):
    def update(self, pose: PoseContext) -> Sequence[ActionSegment]: ...
    def finalize(self) -> Sequence[ActionSegment]: ...


class EventInterpreter(Protocol):
    def update(
        self,
        frame: FramePacket,
        point: Optional[TrackPoint],
        court: Optional[CourtState],
        pose: Optional[PoseContext],
    ) -> Sequence[EventRecord]: ...


class RuleEngine(Protocol):
    def update(self, events: Sequence[EventRecord]) -> JudgementState: ...


class ResultRenderer(Protocol):
    def write_frame(
        self,
        frame: FramePacket,
        point: Optional[TrackPoint],
        court: Optional[CourtState],
        pose: Optional[PoseContext],
        actions: Sequence[ActionSegment],
        events: Sequence[EventRecord],
        judgement: Optional[JudgementState],
    ) -> None: ...

    def finalize(self) -> TaskArtifacts: ...


class ResultPublisher(Protocol):
    def publish(self, artifacts: TaskArtifacts) -> None: ...
