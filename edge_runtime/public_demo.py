"""Public, deterministic task-result replay for the open edge reference.

The public repository intentionally does not ship trained weights or production
inference code.  This module is still executable: it validates and replays
sanitized result fixtures through the same task-result contract used by the
product layer.  A private runtime can replace the fixture source without
changing GUI, cloud adapters, or result consumers.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .contracts import ActionSegment, EventRecord, JudgementState, TrackPoint


class PublicDemoError(RuntimeError):
    """Raised when a public demo fixture does not match the exposed contract."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicDemoError(f"Cannot read JSON fixture: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublicDemoError(f"Fixture must be a JSON object: {path}")
    return payload


def _read_trajectory(path: Path) -> list[TrackPoint]:
    points: list[TrackPoint] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            points.append(
                TrackPoint(
                    frame_index=int(row["frame_index"]),
                    timestamp_s=float(row["timestamp_s"]),
                    x=float(row["x"]),
                    y=float(row["y"]),
                    confidence=float(row["confidence"]),
                    source=row.get("source") or "fixture",
                )
            )
    if not points:
        raise PublicDemoError(f"Trajectory fixture is empty: {path}")
    return points


def _read_events(path: Path) -> list[EventRecord]:
    events: list[EventRecord] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            position = None
            if row.get("x") and row.get("y"):
                position = (float(row["x"]), float(row["y"]))
            events.append(
                EventRecord(
                    event_type=row["event_type"],
                    frame_index=int(row["frame_index"]),
                    timestamp_s=float(row["timestamp_s"]),
                    position=position,
                    confidence=float(row.get("confidence") or 0.0),
                    evidence={"source": "sanitized_fixture"},
                )
            )
    return events


def _read_actions(path: Path) -> list[ActionSegment]:
    actions: list[ActionSegment] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            actions.append(
                ActionSegment(
                    label=row["label"],
                    start_frame=int(row["start_frame"]),
                    end_frame=int(row["end_frame"]),
                    confidence=float(row["confidence"]),
                )
            )
    return actions


def _check_task_result(payload: dict[str, Any], mode: str) -> None:
    required = {"schema_version", "task_id", "mode", "status", "artifacts"}
    missing = required - set(payload)
    if missing:
        raise PublicDemoError(f"Task result misses fields: {', '.join(sorted(missing))}")
    if payload["schema_version"] != 1 or payload["mode"] != mode or payload["status"] != "done":
        raise PublicDemoError("Task result fixture has an unsupported status, mode, or schema version")
    if not isinstance(payload["artifacts"], list):
        raise PublicDemoError("Task result artifacts must be a list")


def run_public_demo(root: Path, mode: str, output_dir: Path, validate_only: bool = False) -> Path:
    """Replay a sanitized task result and write a verified public summary."""

    fixture_dir = root / "examples" / f"{mode}_demo"
    result = _read_json(fixture_dir / "task_result.json")
    _check_task_result(result, mode)

    points = _read_trajectory(fixture_dir / "trajectory.csv")
    events = _read_events(fixture_dir / "events.csv")
    actions = _read_actions(fixture_dir / "actions.csv") if (fixture_dir / "actions.csv").exists() else []
    score = result.get("summary", {}).get("score", {})
    judgement = JudgementState(
        status="done",
        score_top=int(score.get("top", 0)),
        score_bottom=int(score.get("bottom", 0)),
        reason=str(result.get("summary", {}).get("result_reason", "public fixture")),
    )

    report = {
        "schema_version": 1,
        "source": "sanitized_public_fixture",
        "task_id": result["task_id"],
        "mode": mode,
        "status": "validated" if validate_only else "replayed",
        "counts": {"track_points": len(points), "events": len(events), "actions": len(actions)},
        "judgement": asdict(judgement),
        "first_track_point": asdict(points[0]),
        "last_track_point": asdict(points[-1]),
        "events": [asdict(item) for item in events],
        "actions": [asdict(item) for item in actions],
        "artifacts": result["artifacts"],
        "notice": "This is a deterministic public replay. Production inference is supplied by a separately deployed runtime.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{mode}_public_demo_result.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(f"[PUBLIC DEMO] mode={mode} task={result['task_id']}")
    print(f"[PUBLIC DEMO] track_points={len(points)} events={len(events)} actions={len(actions)}")
    print(f"[PUBLIC DEMO] verified_result={output_path}")
    return output_path
