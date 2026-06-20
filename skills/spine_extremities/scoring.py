"""
spine_extremities Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "spine_extremities"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}

        lw=self._lm(landmarks,"left_wrist"); rw=self._lm(landmarks,"right_wrist")
        ls=self._lm(landmarks,"left_shoulder"); rs=self._lm(landmarks,"right_shoulder")
        lh=self._lm(landmarks,"left_hip"); rh=self._lm(landmarks,"right_hip")
        lk=self._lm(landmarks,"left_knee"); rk=self._lm(landmarks,"right_knee")
        f["lw_y"]=lw[1]; f["rw_y"]=rw[1]
        if "lw_y" in self.landmark_history and len(self.landmark_history["lw_y"])>=60:
            yh=self.landmark_history["lw_y"][-60:]
            f["vertical_scope"]=float(max(yh)-min(yh))
        if "lw_y" in self.landmark_history and "rw_y" in self.landmark_history:
            ly=self.landmark_history["lw_y"][-30:]; ry=self.landmark_history["rw_y"][-30:]
            if len(ly)>=10 and len(ry)>=10 and np.std(ly)>1e-6 and np.std(ry)>1e-6:
                f["hand_symmetry"]=float(abs(np.corrcoef(ly,ry)[0,1]))
        # Bending angle: shoulder-hip-knee
        ms=((ls[0]+rs[0])/2,(ls[1]+rs[1])/2,(ls[2]+rs[2])/2)
        mh=((lh[0]+rh[0])/2,(lh[1]+rh[1])/2,(lh[2]+rh[2])/2)
        mk=((lk[0]+rk[0])/2,(lk[1]+rk[1])/2,(lk[2]+rk[2])/2)
        f["bending_angle"]=self._a(ms, mh, mk)
        if "left_wrist" in self.landmark_history:
            lt=self.landmark_history["left_wrist"][-30:]
            if len(lt)>=5:
                f["range_of_motion"]=float(max(p[1] for p in lt)-min(p[1] for p in lt))
    
        for k,v in f.items():
            self.landmark_history.setdefault(k,[]).append(v)
            if len(self.landmark_history[k]) > 300: self.landmark_history[k] = self.landmark_history[k][-300:]
        self.feature_cache = f; return f
    def _lm(self, lm, name):
        if name in lm:
            v = lm[name]
            if isinstance(v, (list, tuple)): return (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0)
        return (0,0,0,0)
    def _d(self, a, b):
        return float(np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2))
    def _a(self, a, b, c):
        ba = (a[0]-b[0], a[1]-b[1], a[2]-b[2]); bc = (c[0]-b[0], c[1]-b[1], c[2]-b[2])
        dot = ba[0]*bc[0]+ba[1]*bc[1]+ba[2]*bc[2]
        mag = np.sqrt(ba[0]**2+ba[1]**2+ba[2]**2)*np.sqrt(bc[0]**2+bc[1]**2+bc[2]**2)
        if mag < 1e-6: return 90
        return np.degrees(np.arccos(np.clip(dot/mag,-1,1)))
    def compute_metrics(self, features):
        m = {}

        vs=features.get("vertical_scope",0.15)
        m["coverage"]=round(85 if vs>0.1 else 65,1)
        m["symmetry"]=round(features.get("hand_symmetry",0.7)*100,1)
        ba=features.get("bending_angle",90)
        m["angle_accuracy"]=round(85 if 60<=ba<=120 else 70,1)
        rm=features.get("range_of_motion",0.1)
        m["technique"]=round(85 if rm>0.05 else 70,1)
    
        return m
    def get_feedback(self, metrics, features):
        fb = [{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]

        if features.get("vertical_scope",0.15)<0.1: fb.append({"type":"info","message":"检查范围应从颈椎到腰椎","severity":"info","metric":"coverage"})
        if features.get("hand_symmetry",0.7)<0.5: fb.append({"type":"warning","message":"左右对称检查不足","severity":"warning","metric":"symmetry"})
    
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history = {}; self.feature_cache = {}
