"""双人对打模式主体流水线。

该文件公开真实业务编排：视频输入、球场锁定、球路追踪、人体上下文、
事件理解、规则判罚、可视化与结果发布。模型推理、几何求解、事件评分和
规则状态机由注入组件提供，属于受保护实现边界。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from edge_runtime.component_api import (
    BallTracker,
    CourtLocator,
    EventInterpreter,
    PoseProvider,
    ResultPublisher,
    ResultRenderer,
    RuleEngine,
    VideoSource,
)
from edge_runtime.contracts import CourtState, JudgementState, TaskArtifacts


@dataclass
class MatchComponents:
    source: VideoSource
    tracker: BallTracker
    court_locator: CourtLocator
    pose_provider: PoseProvider
    event_interpreter: EventInterpreter
    rule_engine: RuleEngine
    renderer: ResultRenderer
    publisher: Optional[ResultPublisher] = None


class MatchPipeline:
    """组合比赛模式全部公开阶段，不依赖具体模型实现。"""

    def __init__(self, components: MatchComponents):
        self.components = components
        self.court: Optional[CourtState] = None
        self.judgement: Optional[JudgementState] = None

    def run(self) -> TaskArtifacts:
        c = self.components
        try:
            for frame in c.source.frames():
                # 私有CourtLocator负责检出质量、映射稳定和锁定条件。
                if self.court is None or not self.court.locked:
                    candidate = c.court_locator.observe(frame)
                    if candidate is not None and candidate.locked:
                        self.court = candidate

                # 私有Tracker负责模型前后处理、轨迹恢复和异常点抑制。
                point = c.tracker.update(frame)

                # 姿态上下文用于区分击球、发球过程与真实落地事件。
                pose = c.pose_provider.update(frame)

                # 私有事件解释器融合球路、球场和运动员上下文。
                events = c.event_interpreter.update(
                    frame=frame,
                    point=point,
                    court=self.court,
                    pose=pose,
                )

                # 私有规则引擎维护回合状态、得分归属和异常锁定。
                if events:
                    self.judgement = c.rule_engine.update(events)

                c.renderer.write_frame(
                    frame=frame,
                    point=point,
                    court=self.court,
                    pose=pose,
                    actions=(),
                    events=events,
                    judgement=self.judgement,
                )
        finally:
            c.source.close()

        c.tracker.finalize()
        artifacts = c.renderer.finalize()
        if c.publisher is not None:
            c.publisher.publish(artifacts)
        return artifacts
