"""
AutoSkill - automatic skill definition generator
Generates skill.yaml + scoring.py from expert videos or descriptions
"""
import os, yaml, json
from typing import Optional


class AutoSkillGenerator:
    """Auto-generate skill definitions with optional LLM enhancement"""

    SKILL_PROMPT = """You are a medical exam expert. Generate a skill.yaml from this description:

{description}

Key point data from expert video: {keypoint_data}

Output ONLY valid YAML with these fields:
name, display_name, category, exam_station, difficulty, model, landmarks, features, metrics, feedback"""

    SCORING_PROMPT = """Generate a scoring.py plugin for this skill:

{skill_yaml}

Output ONLY valid Python code with class SkillScorer implementing:
extract_features(landmarks, frame_idx, fps) -> dict
compute_metrics(feature_history) -> dict
get_feedback(metrics) -> list

Use numpy only. No external deps."""

    def __init__(self, llm_tutor=None):
        self.llm = llm_tutor

    def from_description(self, name, display_name, description,
                         category="clinical", station=3, difficulty="intermediate",
                         keypoint_hints=None):
        if not self.llm or not self.llm.is_enabled():
            return self._make_fallback(name, display_name)

        kp_str = json.dumps(keypoint_hints, ensure_ascii=False) if keypoint_hints else "not available"

        prompt_yaml = self.SKILL_PROMPT.format(description=description, keypoint_data=kp_str)
        skill_yaml = self._call_llm(prompt_yaml) or self._fallback_yaml(name, display_name)

        prompt_score = self.SCORING_PROMPT.format(skill_yaml=skill_yaml)
        scoring_py = self._call_llm(prompt_score) or self._fallback_scoring(name)

        return {"skill_yaml": skill_yaml, "scoring_py": scoring_py}

    def from_video(self, video_path, skill_name, description=""):
        kp = self._extract_keypoints(video_path)
        features = self._analyze_trajectory(kp)
        return self.from_description(name=skill_name, display_name=skill_name,
                                     description=description, keypoint_hints=features)

    def _extract_keypoints(self, video_path):
        return {"frames_analyzed": 0, "detected_motions": ["periodic"], "active_landmarks": ["wrists", "shoulders"]}

    def _analyze_trajectory(self, kp):
        return {"motion_type": kp.get("detected_motions", ["unknown"])[0],
                "suggested_features": ["wrist_y_normalized"],
                "suggested_metrics": ["rate", "consistency"]}

    def _call_llm(self, prompt):
        if not self.llm: return None
        try:
            return self.llm.backend.chat(prompt, max_tokens=2000)
        except Exception as e:
            print(f"  [AutoSkill] LLM error: {e}")
            return None

    def _make_fallback(self, name, display_name):
        return {"skill_yaml": self._fallback_yaml(name, display_name),
                "scoring_py": self._fallback_scoring(name), "_source": "template"}

    def _fallback_yaml(self, name, display_name):
        return (f"name: {name}\n"
                f'display_name: "{display_name}"\n'
                f"category: clinical\nexam_station: 3\ndifficulty: intermediate\nversion: 1.0.0-auto\n\n"
                f"model:\n  type: mediapipe_pose\n  num_poses: 1\n\n"
                f"landmarks:\n"
                f"  - {{id: 15, name: left_wrist, type: wrist, required: true}}\n"
                f"  - {{id: 16, name: right_wrist, type: wrist, required: true}}\n"
                f"  - {{id: 11, name: left_shoulder, type: shoulder, required: true}}\n"
                f"  - {{id: 12, name: right_shoulder, type: shoulder, required: true}}\n\n"
                f"features:\n"
                f"  - name: primary_motion\n    signal_type: periodic\n    window_seconds: 10\n\n"
                f"metrics:\n"
                f"  - name: quality_score\n    display_name: Quality\n"
                f"    unit: '%'\n    target: 100\n    acceptable_range: [60, 100]\n    weight: 1.0\n\n"
                f"feedback:\n  rules:\n"
                f"    - {{condition: quality_score < 60, severity: warning, message: Needs improvement}}\n"
                f"    - {{condition: quality_score >= 80, severity: success, message: Good technique}}\n")

    def _fallback_scoring(self, name):
        return (
            f'"""{name} skill scoring plugin (auto-generated)\n'
            'TODO: implement actual scoring logic\n"""\n'
            'import numpy as np\n\n\n'
            'class SkillScorer:\n'
            '    def __init__(self, config):\n'
            '        self.config = config\n'
            '        self.fps = 30\n\n'
            '    def extract_features(self, landmarks, frame_idx, fps):\n'
            '        self.fps = fps\n'
            '        return {"primary_motion": 0.0}\n\n'
            '    def compute_metrics(self, feature_history):\n'
            '        return {"quality_score": {"value": 75, "unit": "%", "score": 0.75}}\n\n'
            '    def get_feedback(self, metrics):\n'
            '        score = metrics.get("quality_score", {}).get("value", 0)\n'
            '        if score >= 80:\n'
            '            return [{"severity": "success", "message": "Good technique"}]\n'
            '        return [{"severity": "warning", "message": "Needs improvement"}]\n'
        )


def generate_skill(name, description, **kwargs):
    gen = AutoSkillGenerator()
    return gen.from_description(name, name, description, **kwargs)
