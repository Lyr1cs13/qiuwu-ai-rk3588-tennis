# OV13855摄像头接入与验证

本项目的感知入口采用OV13855 MIPI摄像头。公开工程提供从设备发现、V4L2采集、PyQt预览到任务调度的通用接入路径，便于在RK3588平台复现实机交互与验证流程。

```text
OV13855 MIPI Sensor
        ↓
RKISP / RKAIQ
        ↓
V4L2 Video Node
        ↓
Latest-frame Camera Adapter
        ↓
PyQt Preview / Edge Task Scheduler
```

## 验证步骤

1. 使用`v4l2-ctl --list-devices`确认ISP视频节点与镜头子设备。
2. 以目标分辨率和像素格式启动V4L2流，并测量实际帧率。
3. 在触控界面确认预览稳定、构图和曝光满足使用场景。
4. 将同一最新帧输入实时可视化组件或端侧任务入口；实时预览不应积压历史帧。

公开参考命令：

```bash
python3 qiuwu.py camera --device /dev/video11 --width 1920 --height 1080 --fps 60
```

`--fps`表示请求帧率，实际输出需以板端V4L2测量结果为准。摄像头模组、镜头、ISP IQ文件和现场光照条件会影响最终画面质量与可达帧率。

## 工程边界

本仓库公开设备接入、预览、任务协同和验证方法。具体镜头标定、ISP调优、驱动补丁、量产参数、模型运行时及训练资产属于受控交付内容，不随公开仓库发布。
