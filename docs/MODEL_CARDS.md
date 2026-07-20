# Edge model cards

The deployed product uses four independently versioned model roles. The cards
below document purpose, input/output semantics, and edge integration boundaries;
they intentionally omit weights, datasets, calibration samples, preprocessing,
decode logic, and production runtime parameters.

| Model role | Product mode | Public input/output contract | RK3588 integration |
|---|---|---|---|
| Competition-view TrackNet | Match judgement | Consecutive frames -> per-frame ball coordinate and confidence | Three independent RKNN runtime workers may be scheduled on cores 0/1/2 |
| Side-view TrackNet | Personal training | Consecutive frames -> per-frame ball coordinate and confidence | Reuses the product tracking contract with a view-specific model asset |
| Tennis court keypoint detector | Match judgement | Frame -> court lock state, public keypoints, quality metadata | Called until a credible court state is locked, then geometry is reused |
| Pose + MS-TCN++ action stack | Personal training and event context | Frame/pose sequence -> public pose availability and action segments | CPU-side pose context and NPU-side action model are coordinated by the training pipeline |

## Model lifecycle

```text
Training data and evaluation
        -> protected model assets
        -> ONNX export
        -> RKNN build and board verification
        -> private runtime deployment
        -> public TrackPoint / CourtState / ActionSegment / EventRecord contracts
        -> GUI, local evidence and optional cloud artifacts
```

This separation lets the UI, device integration, result schema, and cloud adapters
remain stable while model versions evolve under controlled deployment.
