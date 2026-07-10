# -*- coding: utf-8 -*-
"""Scene mode definitions for the QiuWu AI touch UI."""

MODE_A = "match"
MODE_B = "side"
MODE_C = "all"

MODES = {
    MODE_A: {
        "name": "双人对打智判",
        "subtitle": "比赛视角追踪 / 球场标定 / 落地判罚 / 比分记录",
        "icon": "🎾",
        "color": "#ccff00",
        "cli_mode": "match",
        "output_video": "match_judgement/tracknet_rknn_output.mp4",
        "output_csv": "match_judgement/tracknet_rknn_output.csv",
        "output_events": "match_judgement/bounce_events.csv",
        "output_judgement": "match_judgement/judgement.json",
        "mini_court_visible": True,
        "timeline_visible": False,
        "court_calib_enabled": True,
        "roi_enabled": True,
        "right_panel": "judgement",
        "task_name": "match_judgement",
    },
    MODE_B: {
        "name": "个人训练智练",
        "subtitle": "侧视球路追踪 / 出界统计 / 人体动作分析",
        "icon": "🏃",
        "color": "#58a6ff",
        "cli_mode": "side",
        "output_video": "side_training/side_training_output.mp4",
        "output_csv": "side_training/side_tracknet_output.csv",
        "output_prediction": "side_training/body_action_prediction.txt",
        "mini_court_visible": False,
        "timeline_visible": True,
        "court_calib_enabled": False,
        "roi_enabled": False,
        "right_panel": "training",
        "task_name": "side_training",
    },
    MODE_C: {
        "name": "双模式全流程",
        "subtitle": "双人对打 + 个人训练 / 端侧分析 / 可选上云",
        "icon": "⚡",
        "color": "#f0a050",
        "cli_mode": "all",
        "output_video": "match_judgement/tracknet_rknn_output.mp4",
        "output_csv": "match_judgement/tracknet_rknn_output.csv",
        "output_events": "match_judgement/bounce_events.csv",
        "output_judgement": "match_judgement/judgement.json",
        "output_prediction": "side_training/body_action_prediction.txt",
        "mini_court_visible": True,
        "timeline_visible": True,
        "court_calib_enabled": True,
        "roi_enabled": True,
        "right_panel": "combined",
        "task_name": "dual_pipeline",
    },
}


def get_mode_info(mode_key):
    """Return mode metadata dict for the given key."""
    return MODES.get(mode_key, MODES[MODE_A])


def get_script(mode_key, cloud=False):
    """Compatibility helper used by the GUI: return the unified CLI mode."""
    info = MODES.get(mode_key, MODES[MODE_A])
    return info["cli_mode"]
