# Public result fixtures

This directory contains small, sanitized task-result fixtures. They are not model
weights, original videos, calibration data, or production output. Their purpose is
to make the published contracts executable and reviewable without exposing private
AI assets.

Run either mode from the repository root:

```bash
python3 qiuwu.py demo --mode match
python3 qiuwu.py demo --mode side
```

The command validates the fixture, reconstructs public contract objects, and writes
a verified JSON report under `outputs/public_demo/`.
