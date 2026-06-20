"""
defibrillation Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "defibrillation"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}

        lw=self._lm(landmarks,"left_wrist"); rw=self._lm(landmarks,"right_wrist")
        le=self._lm(landmarks,"left_elbow"); re=self._lm(landmarks,"right_elbow")
        ls=self._lm(landmarks,"left_shoulder"); rs=self._lm(landmarks,"right_shoulder")
        lh=self._lm(landmarks,"left_hip"); rh=self._lm(landmarks,"right_hip")
        f["lw_x"]=lw[0]; f["rw_x"]=rw[0]; f["lw_y"]=lw[1]; f["rw_y"]=rw[1]
        # Paddle position: wrist relative to chest (mid-shoulder to mid-hip)
        ms=((ls[0]+rs[0])/2,(ls[1]+rs[1])/2); mh=((lh[0]+rh[0])/2,(lh[1]+rh[1])/2)
        f["paddle_position"]=float(np.sqrt((lw[0]-ms[0])**2+(lw[1]-ms[1])**2)+
                                   np.sqrt((rw[0]-mh[0])**2+(rw[1]-mh[1])**2))
        f["arm_left_angle"]=self._a(ls,le,lw); f["arm_right_angle"]=self._a(rs,re,rw)
        if "lw_y" in self.landmark_history and "rw_y" in self.landmark_history:
            ly=self.landmark_history["lw_y"][-20:]; ry=self.landmark_history["rw_y"][-20:]
            if len(ly)>=10 and len(ry)>=10 and np.std(ly)>1e-6 and np.std(ry)>1e-6:
                f["hand_symmetry"]=float(abs(np.corrcoef(ly,ry)[0,1]))
        if "right_wrist" in self.landmark_history:
            rt=self.landmark_history["right_wrist"][-5:]
            if len(rt)>=2:
                sp=[np.sqrt((rt[i][0]-rt[i-1][0])**2+(rt[i][1]-rt[i-1][1])**2) for i in range(1,len(rt))]
                f["decisiveness"]=float(np.mean(sp)) if sp else 0.5
    
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

        pp=features.get("paddle_position",0.5)
        m["placement"]=round(90 if 0.3<=pp<=0.8 else 70,1)
        a1=features.get("arm_left_angle",90); a2=features.get("arm_right_angle",90)
        m["posture"]=round(85 if 60<=a1<=120 and 60<=a2<=120 else 65,1)
        m["coordination"]=round(features.get("hand_symmetry",0.7)*100,1)
        dv=features.get("decisiveness",0.5)
        m["efficiency"]=round(85 if dv>0.3 else 70,1)
    
        return m
    def get_feedback(self, metrics, features):
        fb = [{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]

        pp=features.get("paddle_position",0.5)
        if pp>1.0: fb.append({"type":"critical","message":"电极板位置异常：一个置于胸骨右缘第二肋间，一个置于心尖","severity":"critical","metric":"placement"})
        if features.get("hand_symmetry",0.7)<0.5: fb.append({"type":"warning","message":"双手位置不对称，应同时放置电极板","severity":"warning","metric":"coordination"})
    
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history = {}; self.feature_cache = {}
