"""
percussion: 心肺叩诊 Scoring Plugin
"""
import numpy as np
from typing import Dict, List, Any, Optional
class SkillScorer:
    def __init__(self, config=None):
        self.config = config or {}
        self.skill_name = "percussion"
        self.landmark_history = {}
        self.feature_cache = {}
    def extract_features(self, landmarks):
        f = {}
        lw = self._lm(landmarks, "left_wrist"); rw = self._lm(landmarks, "right_wrist")
        f["lw_y"]=lw[1]; f["rw_y"]=rw[1]; f["lw_x"]=lw[0]; f["rw_x"]=rw[0]
        if "lw_y" in self.landmark_history and len(self.landmark_history["lw_y"])>=15:
            yh=self.landmark_history["lw_y"][-15:]
            f["wrist_range"]=float(max(yh)-min(yh))
        if "lw_y" in self.landmark_history and len(self.landmark_history["lw_y"])>=30:
            yh=self.landmark_history["lw_y"][-30:]
            ym=np.mean(yh)
            zc=sum(1 for i in range(1,len(yh)) if (yh[i]-ym)*(yh[i-1]-ym)<0)
            f["percussion_rhythm"]=min(1.0,zc/8) if zc>0 else 0
        if "lw_y" in self.landmark_history and len(self.landmark_history["lw_y"])>=30:
            yh=self.landmark_history["lw_y"][-30:]
            peaks=[]
            for i in range(2,len(yh)-1):
                if yh[i]>yh[i-1] and yh[i]>yh[i+1]: peaks.append(yh[i])
            f["force_uniformity"]=float(np.std(peaks)/max(1,np.mean(peaks))) if peaks else 0.2
        if "lw_y" in self.landmark_history and "rw_y" in self.landmark_history:
            ly=self.landmark_history["lw_y"][-30:]; ry=self.landmark_history["rw_y"][-30:]
            if len(ly)>=10 and len(ry)>=10 and np.std(ly)>1e-6 and np.std(ry)>1e-6:
                f["symmetry"]=float(abs(np.corrcoef(ly,ry)[0,1]))
        for k,v in f.items():
            self.landmark_history.setdefault(k,[]).append(v)
            if len(self.landmark_history[k])>300: self.landmark_history[k]=self.landmark_history[k][-300:]
        self.feature_cache=f; return f
    def _lm(self, lm, name):
        if name in lm:
            v=lm[name]
            if isinstance(v,(list,tuple)): return (v[0],v[1],v[2],v[3] if len(v)>3 else 1.0)
        return (0,0,0,0)
    def compute_metrics(self, features):
        m={}
        m["rhythm"]=round(features.get("percussion_rhythm",0.7)*100,1)
        m["uniformity"]=round(max(40,100-features.get("force_uniformity",0.15)*100),1)
        m["symmetry_score"]=round(features.get("symmetry",0.7)*100,1)
        wr=features.get("wrist_range",0.05)
        m["positioning"]=round(90 if 0.02<=wr<=0.08 else (60 if wr>0.1 else 75),1)
        return m
    def get_feedback(self, metrics, features):
        fb=[{"type":"overall","message":f"总分：{min(100,max(0,sum(m*0.25 for m in metrics.values()))):.0f}/100","severity":"info"}]
        if features.get("percussion_rhythm",0.7)<0.6:
            fb.append({"type":"warning","message":"叩诊节奏不规律，保持2-3次/秒","severity":"warning","metric":"rhythm"})
        if features.get("force_uniformity",0.15)>0.3:
            fb.append({"type":"info","message":"叩击力度不均匀","severity":"info","metric":"uniformity"})
        if features.get("symmetry",0.7)<0.6:
            fb.append({"type":"warning","message":"左右叩诊不对称","severity":"warning","metric":"symmetry_score"})
        return fb if len(fb)>1 else fb+[{"type":"info","message":"操作完成","severity":"info"}]
    def reset(self):
        self.landmark_history={}; self.feature_cache={}
