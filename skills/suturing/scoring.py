"""
suturing: 缝合打结 (Suturing & Knot Tying) Scoring Plugin
"""

import numpy as np
from typing import Dict, List, Any, Optional


class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "suturing"
        self.landmark_history = {}
        self.feature_cache = {}

    def extract_features(self, landmarks):
        f = {}
        ls = self._lm(landmarks, "left_shoulder")
        rs = self._lm(landmarks, "right_shoulder")
        le = self._lm(landmarks, "left_elbow")
        re = self._lm(landmarks, "right_elbow")
        lw = self._lm(landmarks, "left_wrist")
        rw = self._lm(landmarks, "right_wrist")

        if "left_wrist" in self.landmark_history:
            h = self.landmark_history["left_wrist"][-5:]
            if len(h) >= 2:
                sp = [self._d(h[i], h[i-1]) for i in range(1, len(h))]
                f["wrist_speed"] = float(np.mean(sp))
        f["hand_distance"] = self._d(lw, rw)
        f["elbow_angle"] = (self._a(ls, le, lw) + self._a(rs, re, rw)) / 2

        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt = self.landmark_history["left_wrist"][-20:]
            rt = self.landmark_history["right_wrist"][-20:]
            if len(lt) >= 10 and len(rt) >= 10:
                ly = [p[1] for p in lt]; ry = [p[1] for p in rt]
                if np.std(ly) > 1e-6 and np.std(ry) > 1e-6:
                    f["hand_symmetry"] = float(np.corrcoef(ly, ry)[0, 1])
        for k, v in f.items():
            self.landmark_history.setdefault(k, []).append(v)
            if len(self.landmark_history[k]) > 300:
                self.landmark_history[k] = self.landmark_history[k][-300:]
        self.feature_cache = f
        return f

    def _lm(self, lm, name):
        if name in lm:
            v = lm[name]
            if isinstance(v, (list, tuple)):
                return (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0)
        return (0, 0, 0, 0)

    def _d(self, a, b):
        return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

    def _a(self, a, b, c):
        ba = (a[0]-b[0], a[1]-b[1], a[2]-b[2])
        bc = (c[0]-b[0], c[1]-b[1], c[2]-b[2])
        dot = ba[0]*bc[0] + ba[1]*bc[1] + ba[2]*bc[2]
        mag = np.sqrt(ba[0]**2+ba[1]**2+ba[2]**2) * np.sqrt(bc[0]**2+bc[1]**2+bc[2]**2)
        if mag < 1e-6: return 90
        return np.degrees(np.arccos(np.clip(dot/mag, -1, 1)))

    def compute_metrics(self, features):
        m = {}
        p = features.get("hand_symmetry", 0.7) * 100
        if "elbow_angle" in features:
            p = p * 0.7 + max(0, 100 - abs(features["elbow_angle"] - 90) * 1.5) * 0.3
        m["precision"] = round(min(100, p), 1)
        m["coordination"] = round(max(0, min(100, features.get("hand_symmetry", 0.7)*100)), 1)
        s = features.get("wrist_speed", 1.0)
        if s < 0.5: sp = 60 + s*60
        elif s <= 1.2: sp = 90
        else: sp = max(40, 100 - (s-1.2)*20)
        m["speed"] = round(min(100, sp), 1)
        m["stability"] = round(80, 1)
        return m

    def get_feedback(self, metrics, features):
        fb = []
        total = sum(m * w for m, w in zip(metrics.values(), [0.30, 0.25, 0.20, 0.25]))
        fb.append({"type": "overall", "message": f"总分：{min(100,max(0,total)):.0f}/100", "severity": "info"})
        if features.get("hand_symmetry", 1) < 0.6:
            fb.append({"type": "improvement", "message": "双手配合不协调", "severity": "critical", "metric": "coordination"})
        if features.get("wrist_speed", 0) > 2.0:
            fb.append({"type": "improvement", "message": "腕部运动过快", "severity": "warning", "metric": "speed"})
        return fb if fb else [{"type": "info", "message": "操作完成", "severity": "info"}]

    def reset(self):
        self.landmark_history = {}
        self.feature_cache = {}
