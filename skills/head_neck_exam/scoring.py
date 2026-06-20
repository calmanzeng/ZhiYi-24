"""
head_neck_exam Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "head_neck_exam"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}

        nose=self._lm(landmarks,"nose"); rw=self._lm(landmarks,"right_wrist")
        lw=self._lm(landmarks,"left_wrist")
        f["hand_face_distance"]=float(np.sqrt((rw[0]-nose[0])**2+(rw[1]-nose[1])**2 +
            (rw[2]-nose[2])**2))
        f["dom_x"]=rw[0]; f["dom_y"]=rw[1]
        if "dom_x" in self.landmark_history and len(self.landmark_history["dom_x"])>=10:
            xh=self.landmark_history["dom_x"][-15:]; yh=self.landmark_history["dom_y"][-15:]
            f["hand_stability"]=float(np.sqrt(np.var(xh)+np.var(yh)))
        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt=self.landmark_history["left_wrist"][-20:]; rt=self.landmark_history["right_wrist"][-20:]
            if len(lt)>=10 and len(rt)>=10:
                ly=[p[1] for p in lt]; ry=[p[1] for p in rt]
                if np.std(ly)>1e-6 and np.std(ry)>1e-6:
                    f["bilateral_coordination"]=float(abs(np.corrcoef(ly,ry)[0,1]))
        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt=self.landmark_history["left_wrist"][-60:]; rt=self.landmark_history["right_wrist"][-60:]
            if len(lt)>=10 and len(rt)>=10:
                ax=[p[0] for p in lt]+[p[0] for p in rt]; ay=[p[1] for p in lt]+[p[1] for p in rt]
                f["movement_scope"]=float((max(ax)-min(ax))*(max(ay)-min(ay)))
    
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

        hfd=features.get("hand_face_distance",0.3)
        m["precision"]=round(90 if 0.1<=hfd<=0.35 else (75 if hfd<0.1 else 65),1)
        m["stability"]=round(max(40,100-features.get("hand_stability",0)*30),1)
        m["coordination"]=round(features.get("bilateral_coordination",0.7)*100,1)
        ms=features.get("movement_scope",0.15)
        m["thoroughness"]=round(85 if 0.05<=ms<=0.4 else 65,1)
    
        return m
    def get_feedback(self, metrics, features):
        fb = [{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]

        hfd=features.get("hand_face_distance",0.3)
        if hfd>0.5: fb.append({"type":"info","message":"手离患者面部太远","severity":"info","metric":"precision"})
        if features.get("hand_stability",0)>1.5: fb.append({"type":"warning","message":"近面部操作手部不够稳","severity":"warning","metric":"stability"})
    
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history = {}; self.feature_cache = {}
