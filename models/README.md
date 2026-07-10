# 模型资产清单

完整设备版本按场景调度以下模型。公开仓库保留模型职责、输入输出语义和接入位置，不发布模型文件、训练数据或转换参数。

| 模型角色 | 公开能力说明 | 私有资产占位 |
|---|---|---|
| 比赛视角TrackNet | 比赛机位高速网球时序热图追踪 | `models/private/match_tracknet.rknn` |
| 侧视TrackNet | 个人训练机位球路追踪与量化 | `models/private/side_tracknet.rknn` |
| 球场关键点模型 | 场地语义关键位置与几何映射 | `models/private/court_keypoints.rknn` |
| MS-TCN++动作模型 | 人体姿态序列的动作分割与识别 | `models/private/action_temporal.rknn` |

MediaPipe Pose作为人体姿态前端，在CPU侧生成骨架上下文。其输出由私有动作特征适配层交给MS-TCN++，具体特征构造和时间维处理不在公开仓库中。

`models/private/`已被Git忽略。内部设备部署包应在安装阶段写入模型并生成版本清单，公开代码不包含下载地址或替代权重。
