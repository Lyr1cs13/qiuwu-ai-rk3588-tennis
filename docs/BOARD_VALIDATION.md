# RK3588 board validation

This guide validates the published product layer, camera path, result contracts,
and NPU observability. It does not expose private model assets or production
tuning parameters.

## 1. Public software checks

```bash
python3 qiuwu.py check
python3 qiuwu.py demo --mode match
python3 qiuwu.py demo --mode side
```

Both demo commands validate sanitized fixtures and write contract-compatible
reports to `outputs/public_demo/`. They prove result parsing and task artifacts;
they do not claim to run model inference.

## 2. Camera path

```bash
v4l2-ctl -d /dev/video11 --all
python3 qiuwu.py camera --device /dev/video11 --width 1920 --height 1080 --fps 60
```

`--fps 60` is a requested camera rate. The achieved frame rate must be measured
from V4L2/ISP output on the target board, because it depends on sensor mode,
kernel driver, device tree, ISP configuration, and cable hardware.

## 3. NPU observation

During a private deployment that uses the tracking worker plan, observe the three
RK3588 NPU cores with:

```bash
sudo watch -n 0.3 cat /sys/kernel/debug/rknpu/load
```

The published benchmark was sampled during a three-runtime TrackNet inference
stage: Core0 82%, Core1 82%, Core2 83%. This is an inference-stage sample, not a
promise for every input video or end-to-end pipeline.

## 4. Result contract

Production runtime implementations should emit a JSON document compatible with
`contracts/task-result.schema.json`, plus artifact paths such as trajectory,
events, judgement, action segments, and rendered video. The public GUI and cloud
adapters consume these stable artifacts rather than a model-specific API.
