"""
技能训练 Pipeline 引擎
编排: 输入 → AI推理 → 特征提取 → 评分 → 渲染 → 数据记录
"""
import time
from collections import deque

import cv2
import numpy as np

from .registry import SkillRegistry
from .data_hub import DataHub


class SkillPipeline:
    """
    执医技能训练流水线
    
    用法:
        from hermes_skills import SkillPipeline
        pipe = SkillPipeline("cpr", skills_dir="./skills")
        pipe.run(camera=0)
    """
    
    def __init__(self, skill_name: str, skills_dir: str = "./skills",
                 data_hub: DataHub = None):
        self.skill_name = skill_name
        self.skills_dir = skills_dir
        self.data_hub = data_hub or DataHub()
        
        # 加载技能
        registry = SkillRegistry(skills_dir)
        skill = registry.get_skill(skill_name)
        self.config = skill["config"]
        self.scorer = skill["scorer"]
        
        if self.scorer is None:
            raise RuntimeError(f"技能 '{skill_name}' 缺少 scoring.py")
        
        # 状态
        self._running = False
        self._session_id = None
        self._frame_count = 0
        self._latest_metrics = None
        self._fps = 30
        self._fps_counter = deque(maxlen=30)
        self._last_tick = time.time()
    
    # ---- 视频源 ----
    def _open_source(self, camera=0, video_path=None):
        if video_path:
            cap = cv2.VideoCapture(video_path)
        else:
            cap = cv2.VideoCapture(camera)
        
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频源: {'camera ' + str(camera) if video_path is None else video_path}")
        
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        if self._fps <= 0:
            self._fps = 30
        return cap
    
    # ---- 实时 FPS ----
    def _tick(self):
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        if dt > 0:
            self._fps_counter.append(1.0 / dt)
    
    # ---- 主循环 ----
    def run(self, camera=0, video_path=None, headless=False, 
            on_frame=None, on_metrics=None):
        """
        运行技能训练 Pipeline
        
        Args:
            camera: 摄像头编号
            video_path: 视频文件路径（优先于camera）
            headless: True=无窗口模式（用于测试/服务端）
            on_frame: 每帧回调(frame, metrics) → annotated_frame
            on_metrics: 指标更新回调(metrics)
        """
        cap = self._open_source(camera, video_path)
        self._session_id = self.data_hub.start_session(self.skill_name)
        self._running = True
        self._frame_count = 0
        
        ai_backend = self._init_ai_backend()
        
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                self._frame_count += 1
                self._tick()
                
                # 1. AI 推理
                landmarks = ai_backend.detect(frame)
                
                # 2. 特征提取
                if landmarks:
                    features = self.scorer.extract_features(
                        landmarks, self._frame_count, self._fps
                    )
                    self.data_hub.add_features(features)
                
                # 3. 评分
                feature_history = self.data_hub.get_feature_history()
                metrics = self.scorer.compute_metrics(feature_history)
                
                if metrics:
                    self._latest_metrics = metrics
                    self.data_hub.save_metrics(self._session_id, metrics)
                    if on_metrics:
                        on_metrics(metrics)
                
                # 4. 渲染
                fb = self.scorer.get_feedback(metrics) if metrics else []
                
                if on_frame:
                    frame = on_frame(frame, metrics, landmarks, fb, list(
                        feature_history.get("wrist_y_normalized", [])
                    ))
                
                # 5. 显示
                if not headless:
                    cv2.imshow(f"执医 AI — {self.config['display_name']}", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('r'):
                        self.reset()
        
        finally:
            cap.release()
            if not headless:
                cv2.destroyAllWindows()
            
            self.data_hub.end_session(
                self._session_id,
                {
                    "avg_score": self._latest_metrics.get("overall", {}).get("value")
                    if self._latest_metrics else None,
                    "frames": self._frame_count,
                }
            )
        
        return self._session_id
    
    def _init_ai_backend(self):
        """初始化 AI 后端"""
        from hermes_skills.ai.pose_landmarker import PoseLandmarkerBackend
        
        model_type = self.config.get("model", {}).get("type", "mediapipe_pose")
        model_path = self.config.get("model", {}).get("model_path", "")
        confidence = self.config.get("model", {}).get("min_detection_confidence", 0.5)
        
        if model_type == "mediapipe_pose":
            return PoseLandmarkerBackend(model_path, confidence)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def reset(self):
        """重置当前会话"""
        self._session_id = self.data_hub.start_session(self.skill_name)
        self._frame_count = 0
        self._latest_metrics = None
        print("🔄 评分已重置")
    
    def stop(self):
        """停止 Pipeline"""
        self._running = False
    
    @property
    def metrics(self):
        return self._latest_metrics
    
    @property
    def fps(self):
        return np.mean(self._fps_counter) if self._fps_counter else 0
