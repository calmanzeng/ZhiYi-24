"""
catheterization: 导尿术 Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "catheterization"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}
        lw = self._lm(landmarks, "left_wrist"); rw = self._lm(landmarks, "right_wrist")
        le = self._lm(landmarks, "left_elbow"); re = self._lm(landmarks, "right_elbow")
        rs = self._lm(landmarks, "right_shoulder"); ls = self._lm(landmarks, "left_shoulder")
        f["hand_distance"] = float(np.sqrt((lw[0]-rw[0])**2+(lw[1]-rw[1])**2))
        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt = self.landmark_history["left_wrist"][-20:]; rt = self.landmark_history["right_wrist"][-20:]
            if len(lt)>=5 and len(rt)>=5:
                ly=[p[1] for p in lt]; ry=[p[1] for p in rt]
                if np.std(ly)>1e-6 and np.std(ry)>1e-6:
                    f["hand_symmetry"]=float(abs(np.corrcoef(ly,ry)[0,1]))
        if "left_wrist" in self.landmark_history:
            lwt=self.landmark_history["left_wrist"][-15:]
            if len(lwt)>=5:
                dp=[np.sqrt((lwt[i][0]-lwt[i-1][0])**2+(lwt[i][1]-lwt[i-1][1])**2) for i in range(1,len(lwt))]
                f["wrist_motion"]=float(1.0/(1.0+np.var(dp)*10)) if dp else 0.8
        if "left_wrist" in self.landmark_history:
            lwt=self.landmark_history["left_wrist"][-20:]
            if len(lwt)>=5:
                f["steadiness"]=float(np.var([p[0] for p in lwt])+np.var([p[1] for p in lwt]))
        f["approach_angle"] = self._a(rs, re, rw)
        for k,v in f.items():
            self.landmark_history.setdefault(k,[]).append(v)
            if len(self.landmark_history[k]) > 300: self.landmark_history[k] = self.landmark_history[k][-300:]
        self.feature_cache=f; return f
    def _lm(self, lm, name):
        if name in lm:
            v=lm[name]
            if isinstance(v,(list,tuple)): return (v[0],v[1],v[2],v[3] if len(v)>3 else 1.0)
        return (0,0,0,0)
    def _a(self, a,b,c):
        ba=(a[0]-b[0],a[1]-b[1],a[2]-b[2]); bc=(c[0]-b[0],c[1]-b[1],c[2]-b[2])
        dot=ba[0]*bc[0]+ba[1]*bc[1]+ba[2]*bc[2]
        mag=np.sqrt(ba[0]**2+ba[1]**2+ba[2]**2)*np.sqrt(bc[0]**2+bc[1]**2+bc[2]**2)
        if mag<1e-6: return 90
        return np.degrees(np.arccos(np.clip(dot/mag,-1,1)))
    def compute_metrics(self, features):
        m={}
        hd=features.get("hand_distance",0.3)
        m["sterile_technique"]=round(90 if 0.15<=hd<=0.5 else (70 if hd>0.5 else 85),1)
        m["smoothness"]=round(min(100,features.get("wrist_motion",0.8)*100),1)
        dev=abs(features.get("approach_angle",120)-120)
        m["angle_score"]=round(max(60,100-dev*0.5),1)
        m["confidence"]=round(max(50,100-features.get("steadiness",0)*50),1)
        return m
    def get_feedback(self, metrics, features):
        fb=[{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]
        if features.get("wrist_motion",0.8) < 0.5:
            fb.append({"type":"warning","message":"操作生硬，应轻柔推进","severity":"warning","metric":"smoothness"})
        if features.get("hand_symmetry",0.8) < 0.4:
            fb.append({"type":"info","message":"双手配合不佳","severity":"info","metric":"confidence"})
        if features.get("steadiness",0) > 1.8:
            fb.append({"type":"warning","message":"手部不稳定","severity":"warning","metric":"confidence"})
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history={}; self.feature_cache={}
