"""
lumbar_puncture: 腰椎穿刺术 Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "lumbar_puncture"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}
        ls = self._lm(landmarks, "left_shoulder"); rs = self._lm(landmarks, "right_shoulder")
        lh = self._lm(landmarks, "left_hip"); rh = self._lm(landmarks, "right_hip")
        lk = self._lm(landmarks, "left_knee"); rk = self._lm(landmarks, "right_knee")
        rw = self._lm(landmarks, "right_wrist")
        msh = ((ls[0]+rs[0])/2, (ls[1]+rs[1])/2, (ls[2]+rs[2])/2)
        mhp = ((lh[0]+rh[0])/2, (lh[1]+rh[1])/2, (lh[2]+rh[2])/2)
        mkn = ((lk[0]+rk[0])/2, (lk[1]+rk[1])/2, (lk[2]+rk[2])/2)
        f["patient_curling"] = self._a(msh, mhp, mkn)
        f["insertion_angle"] = 85
        f["dom_x"] = rw[0]; f["dom_y"] = rw[1]
        if "dom_x" in self.landmark_history and len(self.landmark_history["dom_x"]) >= 10:
            xh = self.landmark_history["dom_x"][-15:]; yh = self.landmark_history["dom_y"][-15:]
            f["hand_stability"] = float(np.sqrt(np.var(xh)+np.var(yh)))
        if "dom_y" in self.landmark_history and len(self.landmark_history["dom_y"]) >= 5:
            f["depth_control"] = abs(self.landmark_history["dom_y"][-1]-self.landmark_history["dom_y"][-5])
        for k,v in f.items():
            self.landmark_history.setdefault(k,[]).append(v)
            if len(self.landmark_history[k]) > 300: self.landmark_history[k] = self.landmark_history[k][-300:]
        self.feature_cache = f; return f
    def _lm(self, lm, name):
        if name in lm:
            v = lm[name]
            if isinstance(v, (list, tuple)): return (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0)
        return (0,0,0,0)
    def _a(self, a, b, c):
        ba = (a[0]-b[0], a[1]-b[1], a[2]-b[2]); bc = (c[0]-b[0], c[1]-b[1], c[2]-b[2])
        dot = ba[0]*bc[0]+ba[1]*bc[1]+ba[2]*bc[2]
        mag = np.sqrt(ba[0]**2+ba[1]**2+ba[2]**2)*np.sqrt(bc[0]**2+bc[1]**2+bc[2]**2)
        if mag < 1e-6: return 90
        return np.degrees(np.arccos(np.clip(dot/mag,-1,1)))
    def compute_metrics(self, features):
        m = {}
        c = features.get("patient_curling", 60)
        if 40 <= c <= 70: m["positioning"] = 95
        elif c < 40: m["positioning"] = round(60 + c*0.8, 1)
        else: m["positioning"] = round(max(40, 100-(c-70)*1.2), 1)
        dev = abs(features.get("insertion_angle", 90)-90)
        m["angle_score"] = round(max(0,100-dev*1.2), 1)
        m["stability"] = round(max(40,100-features.get("hand_stability",0)*30), 1)
        dc = features.get("depth_control", 0.02)
        m["depth_accuracy"] = round(90 if dc < 0.02 else (80 if dc < 0.04 else max(50,100-dc*150)), 1)
        return m
    def get_feedback(self, metrics, features):
        fb = [{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]
        if features.get("patient_curling",60) > 70:
            fb.append({"type":"warning","message":"体位屈曲不足，建议加大屈曲","severity":"warning","metric":"positioning"})
        ia = features.get("insertion_angle", 85)
        if ia < 70 or ia > 110:
            fb.append({"type":"critical","message":"穿刺角度应在80-90","severity":"critical","metric":"angle_score"})
        if features.get("hand_stability",0) > 2.0:
            fb.append({"type":"critical","message":"手部抖动明显","severity":"critical","metric":"stability"})
        return fb if len(fb) > 1 else fb + [{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history = {}; self.feature_cache = {}
