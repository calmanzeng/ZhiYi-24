"""
intubation: 气管插管术 Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "intubation"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f={}
        nose=self._lm(landmarks,"nose"); ls=self._lm(landmarks,"left_shoulder")
        rs=self._lm(landmarks,"right_shoulder"); re=self._lm(landmarks,"right_elbow")
        rw=self._lm(landmarks,"right_wrist"); lw=self._lm(landmarks,"left_wrist")
        ms=((ls[0]+rs[0])/2,(ls[1]+rs[1])/2)
        f["head_position"]=nose[1]-ms[1]
        f["laryngoscope_angle"]=self._a(rs,re,rw)
        if "right_wrist" in self.landmark_history:
            h=self.landmark_history["right_wrist"][-10:]
            if len(h)>=3:
                sp=[np.sqrt((h[i][0]-h[i-1][0])**2+(h[i][1]-h[i-1][1])**2) for i in range(1,len(h))]
                f["insertion_speed"]=float(np.mean(sp)) if sp else 0
        if "right_wrist" in self.landmark_history:
            h=self.landmark_history["right_wrist"][-15:]
            if len(h)>=5:
                f["hand_stability"]=float(np.var([p[0] for p in h])+np.var([p[1] for p in h]))
        if "left_wrist" in self.landmark_history and "right_wrist" in self.landmark_history:
            lt=self.landmark_history["left_wrist"][-20:]; rt=self.landmark_history["right_wrist"][-20:]
            if len(lt)>=5 and len(rt)>=5:
                ld=[np.sqrt((lt[i][0]-lt[i-1][0])**2+(lt[i][1]-lt[i-1][1])**2) for i in range(1,len(lt))]
                rd=[np.sqrt((rt[i][0]-rt[i-1][0])**2+(rt[i][1]-rt[i-1][1])**2) for i in range(1,len(rt))]
                f["coordination"]=float(abs(np.mean(ld)-np.mean(rd))) if ld and rd else 0
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
        hp=features.get("head_position",0.1)
        if 0.05<=hp<=0.15: m["positioning"]=95
        elif hp>0: m["positioning"]=80
        else: m["positioning"]=50
        dev=abs(features.get("laryngoscope_angle",45)-45)
        m["angle_score"]=round(max(50,100-dev*0.8),1)
        sp=features.get("insertion_speed",0.04)
        if sp<0.02: m["time_efficiency"]=60
        elif sp<0.06: m["time_efficiency"]=90
        else: m["time_efficiency"]=70
        m["smoothness"]=round(max(50,100-features.get("hand_stability",0)*20-features.get("coordination",0)*50),1)
        return m
    def get_feedback(self, metrics, features):
        fb=[{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]
        if features.get("head_position",0)<0:
            fb.append({"type":"critical","message":"头位不正确，应置于嗅花位","severity":"critical","metric":"positioning"})
        la=features.get("laryngoscope_angle",45)
        if la<30: fb.append({"type":"critical","message":"喉镜提拉角度不足","severity":"critical","metric":"angle_score"})
        elif la>60: fb.append({"type":"warning","message":"喉镜角度过大","severity":"warning","metric":"angle_score"})
        if features.get("insertion_speed",0)>5.0:
            fb.append({"type":"warning","message":"插管速度过快","severity":"warning","metric":"time_efficiency"})
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history={}; self.feature_cache={}
