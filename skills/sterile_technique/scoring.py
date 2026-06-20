"""
sterile_technique: 无菌术 Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "sterile_technique"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f={}
        ls=self._lm(landmarks,"left_shoulder"); rs=self._lm(landmarks,"right_shoulder")
        le=self._lm(landmarks,"left_elbow"); re=self._lm(landmarks,"right_elbow")
        lw=self._lm(landmarks,"left_wrist"); rw=self._lm(landmarks,"right_wrist")
        f["arm_elevation"]=((lw[1]-ls[1])+(rw[1]-rs[1]))/2
        f["hand_distance"]=float(np.sqrt((lw[0]-rw[0])**2+(lw[1]-rw[1])**2))
        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt=self.landmark_history["left_wrist"][-60:]; rt=self.landmark_history["right_wrist"][-60:]
            if len(lt)>=10 and len(rt)>=10:
                ax=[p[0] for p in lt]+[p[0] for p in rt]
                ay=[p[1] for p in lt]+[p[1] for p in rt]
                f["movement_scope"]=float((max(ax)-min(ax))*(max(ay)-min(ay)))
        f["elbow_angle"]=(self._a(ls,le,lw)+self._a(rs,re,rw))/2
        for k,v in f.items():
            self.landmark_history.setdefault(k,[]).append(v)
            if len(self.landmark_history[k])>300: self.landmark_history[k]=self.landmark_history[k][-300:]
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
        ae=features.get("arm_elevation",0.05)
        p=90 if ae>0 else (75 if ae>-0.05 else 50)
        ea=features.get("elbow_angle",90)
        p=p*0.8+(95 if 60<=ea<=120 else 70)*0.2
        m["posture"]=round(p,1)
        ms=features.get("movement_scope",0.1)
        if ms<0.05: m["range_control"]=95
        elif ms<0.2: m["range_control"]=85
        elif ms<0.5: m["range_control"]=70
        else: m["range_control"]=50
        m["smoothness"]=round(85 if 0.2<=features.get("hand_distance",0.3)<=0.6 else 75,1)
        m["speed"]=round(80 if features.get("movement_scope",0.1)<0.3 else 60,1)
        return m
    def get_feedback(self, metrics, features):
        fb=[{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]
        if features.get("arm_elevation",0.05)<0:
            fb.append({"type":"critical","message":"手臂位置过低，应保持在腰部以上","severity":"critical","metric":"posture"})
        if features.get("hand_distance",0.3)<0.15:
            fb.append({"type":"warning","message":"双手间距过近","severity":"warning","metric":"range_control"})
        if features.get("movement_scope",0.1)>0.8:
            fb.append({"type":"warning","message":"活动范围过大","severity":"warning","metric":"range_control"})
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history={}; self.feature_cache={}
