"""个人训练模式主体流水线。

公开视频输入、侧视追踪、姿态感知、动作时序分析、训练事件组织、可视化
和结果发布的完整协同关系；模型与特征算法由受保护组件实现。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from edge_runtime.component_api import (
    ActionRecognizer,
    BallTracker,
    EventInterpreter,
    PoseProvider,
    ResultPublisher,
    ResultRenderer,
    VideoSource,
)
from edge_runtime.contracts import TaskArtifacts


@dataclass
class TrainingComponents:
    source: VideoSource
    tracker: BallTracker
    pose_provider: PoseProvider
    action_recognizer: ActionRecognizer
    event_interpreter: EventInterpreter
    renderer: ResultRenderer
    publisher: Optional[ResultPublisher] = None


class TrainingPipeline:
    """组合个人训练模式全部公开阶段。"""

    def __init__(self, components: TrainingComponents):
        self.components = components

    def run(self) -> TaskArtifacts:
        c = self.components
        try:
            for frame in c.source.frames():
                # 私有侧视Tracker保留模型适配、轨迹修复和坐标校正。
                point = c.tracker.update(frame)

                # PoseProvider输出公开姿态上下文，不暴露特征构造细节。
                pose = c.pose_provider.update(frame)

                # 私有ActionRecognizer完成连续动作分割和类别识别。
                actions = c.action_recognizer.update(pose)

                # 训练事件层组织球路、出界和动作之间的时间关系。
                events = c.event_interpreter.update(
                    frame=frame,
                    point=point,
                    court=None,
                    pose=pose,
                )

                c.renderer.write_frame(
                    frame=frame,
                    point=point,
                    court=None,
                    pose=pose,
                    actions=actions,
                    events=events,
                    judgement=None,
                )
        finally:
            c.source.close()

        c.tracker.finalize()
        c.action_recognizer.finalize()
        artifacts = c.renderer.finalize()
        if c.publisher is not None:
            c.publisher.publish(artifacts)
        return artifacts
