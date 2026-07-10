"""RK3588公开运行计划描述。

这里公开三核独立Runtime的工程组织方式，不包含生产调度策略、队列深度、
内存复用、线程亲和性或模型调优参数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class NpuWorkerSpec:
    worker_id: int
    core_id: int
    role: str


@dataclass(frozen=True)
class RuntimePlan:
    workers: Sequence[NpuWorkerSpec]
    preserve_frame_order: bool = True

    def validate(self) -> None:
        worker_ids = [item.worker_id for item in self.workers]
        core_ids = [item.core_id for item in self.workers]
        if len(worker_ids) != len(set(worker_ids)):
            raise ValueError("worker_id必须唯一")
        if len(core_ids) != len(set(core_ids)):
            raise ValueError("每个公开Worker应绑定独立NPU核心")
        if any(core not in (0, 1, 2) for core in core_ids):
            raise ValueError("RK3588公开运行计划仅接受NPU Core 0/1/2")


TRACKING_PLAN = RuntimePlan(
    workers=(
        NpuWorkerSpec(worker_id=0, core_id=0, role="tracking"),
        NpuWorkerSpec(worker_id=1, core_id=1, role="tracking"),
        NpuWorkerSpec(worker_id=2, core_id=2, role="tracking"),
    )
)
