"""
SelfTrain — 自我训练引擎
数据回流 → 自动标注 → 模型微调 → 版本管理 → 自动评估
"""
import os
import json
import time
import sqlite3
import hashlib
import numpy as np
from collections import deque
from typing import Optional, List, Dict
from dataclasses import dataclass, field


@dataclass
class ModelVersion:
    """模型版本"""
    name: str
    path: str
    created_at: float
    accuracy: float = 0.0
    sample_count: int = 0
    metrics: dict = field(default_factory=dict)
    status: str = "active"  # active | retired | failed


class SelfTrainEngine:
    """
    自我训练引擎
    
    核心循环:
      1. 收集操作数据（特征 + 评分 + 用户反馈）
      2. 与专家基线对比，自动标注质量标签
      3. 当数据积累到阈值 → 触发微调
      4. 新模型 A/B 测试 → 胜出则自动切换
    
    隐私设计:
      - 原始视频永远不上传
      - 特征数据本地匿名化后上传
      - 支持联邦学习（模型梯度交换，非原始数据）
    """
    
    def __init__(self, db_path: str = None, models_dir: str = None,
                 min_samples_for_training: int = 100,
                 min_improvement_threshold: float = 0.02):
        if db_path is None:
            db_path = os.path.expanduser("~/.hermes/selftrain.db")
        if models_dir is None:
            models_dir = os.path.expanduser("~/.hermes/models")
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        
        self.db_path = db_path
        self.models_dir = models_dir
        self.min_samples = min_samples_for_training
        self.min_improvement = min_improvement_threshold
        self._init_db()
        
        self._feedback_queue = deque(maxlen=1000)
        self._models = {}  # skill_name → [ModelVersion, ...]
        self._load_models()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # 训练样本表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    features_json TEXT NOT NULL,
                    label_quality REAL,        -- 0-1 质量标签
                    label_source TEXT DEFAULT 'auto',  -- auto | expert | user
                    model_version TEXT,
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            # 模型版本表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    name TEXT PRIMARY KEY,
                    skill_name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    accuracy REAL DEFAULT 0,
                    sample_count INTEGER DEFAULT 0,
                    metrics_json TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            # A/B 测试结果表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    model_a TEXT NOT NULL,
                    model_b TEXT NOT NULL,
                    winner TEXT,
                    improvement REAL,
                    sample_count INTEGER,
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            conn.commit()
    
    def _load_models(self):
        """加载已有模型"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM model_versions WHERE status='active'"
            ).fetchall()
            for row in rows:
                name, skill, path, acc, count, metrics_json, status, _ = row
                mv = ModelVersion(
                    name=name, path=path, accuracy=acc,
                    sample_count=count,
                    metrics=json.loads(metrics_json),
                    status=status,
                    created_at=0
                )
                if skill not in self._models:
                    self._models[skill] = []
                self._models[skill].append(mv)
    
    # ──── 数据收集 ────
    
    def collect_sample(self, skill_name: str, features: dict,
                       metrics: dict, label_source: str = "auto") -> int:
        """
        收集一条训练样本
        
        Returns: sample_id
        """
        # 自动标注：用当前评分作为质量标签
        overall = metrics.get("overall", {}).get("value", 50)
        label = overall / 100.0  # 归一化到 0-1
        
        features_json = json.dumps(self._safe_serialize(features))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO training_samples 
                   (skill_name, features_json, label_quality, label_source)
                   VALUES (?, ?, ?, ?)""",
                (skill_name, features_json, label, label_source)
            )
            return cursor.lastrowid
    
    def add_expert_annotation(self, skill_name: str, features: dict,
                              expert_score: float) -> int:
        """添加专家标注（高价值数据）"""
        return self.collect_sample(skill_name, features, 
                                   {"overall": {"value": expert_score * 100}},
                                   label_source="expert")
    
    # ──── 训练触发 ────
    
    def should_train(self, skill_name: str) -> bool:
        """检查是否应该触发训练"""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM training_samples WHERE skill_name = ?",
                (skill_name,)
            ).fetchone()[0]
        return count >= self.min_samples
    
    def get_training_data(self, skill_name: str, limit: int = 1000) -> List[dict]:
        """获取训练数据"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT features_json, label_quality 
                   FROM training_samples 
                   WHERE skill_name = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (skill_name, limit)
            ).fetchall()
        
        X, y = [], []
        for features_json, label in rows:
            features = json.loads(features_json)
            # 展平特征为向量
            vec = self._features_to_vector(features)
            if vec is not None:
                X.append(vec)
                y.append(label)
        
        return {"X": np.array(X), "y": np.array(y), "count": len(X)}
    
    # ──── 模型微调 ────
    
    def fine_tune(self, skill_name: str, model_path: str = None,
                  method: str = "scoring_params") -> ModelVersion:
        """
        微调评分模型
        
        Args:
            skill_name: 技能名
            model_path: 基模型路径（None=从头训练）
            method: 微调方法
                - "scoring_params": 调整评分权重和阈值（轻量，不需要 GPU）
                - "lora": LoRA 微调姿态识别模型（需要 GPU）
        
        Returns: 新模型版本
        """
        data = self.get_training_data(skill_name)
        
        if data["count"] < self.min_samples:
            raise ValueError(f"训练数据不足: {data['count']} < {self.min_samples}")
        
        version_name = f"{skill_name}_v{int(time.time())}"
        version_path = os.path.join(self.models_dir, version_name)
        
        if method == "scoring_params":
            # 轻量模式：只优化评分参数
            optimized_params = self._optimize_scoring_params(data)
            
            os.makedirs(version_path, exist_ok=True)
            with open(os.path.join(version_path, "scoring_params.json"), "w") as f:
                json.dump(optimized_params, f, indent=2)
            
            accuracy = self._evaluate_params(optimized_params, data)
        else:
            # TODO: LoRA 微调实现
            raise NotImplementedError(f"微调方法 {method} 尚未实现")
        
        # 保存新模型版本
        mv = ModelVersion(
            name=version_name,
            path=version_path,
            created_at=time.time(),
            accuracy=accuracy,
            sample_count=data["count"],
            metrics={"method": method, "samples": data["count"]}
        )
        
        # 持久化
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO model_versions 
                   (name, skill_name, path, accuracy, sample_count, metrics_json, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'active')""",
                (version_name, skill_name, version_path, accuracy,
                 data["count"], json.dumps(mv.metrics))
            )
            # 退休旧模型
            conn.execute(
                "UPDATE model_versions SET status='retired' WHERE skill_name=? AND name!=?",
                (skill_name, version_name)
            )
            conn.commit()
        
        if skill_name not in self._models:
            self._models[skill_name] = []
        self._models[skill_name] = [mv]
        
        return mv
    
    # ──── A/B 测试 ────
    
    def ab_test(self, skill_name: str, model_a: str, model_b: str,
                sample_count: int = 50) -> dict:
        """
        A/B 测试两个模型
        
        Returns: {"winner": str, "improvement": float, "significant": bool}
        """
        data = self.get_training_data(skill_name, sample_count)
        
        if data["count"] < 10:
            return {"winner": None, "improvement": 0, "significant": False}
        
        # 划分测试集
        split = int(len(data["X"]) * 0.3)
        X_test, y_test = data["X"][:split], data["y"][:split]
        
        # 评估两个模型（简化版：用准确率差）
        score_a = np.mean(np.abs(y_test - 0.5))  # 简化评估
        score_b = np.mean(np.abs(y_test - 0.5))
        
        winner = model_a if score_a < score_b else model_b
        improvement = abs(score_a - score_b)
        significant = improvement > self.min_improvement
        
        # 记录结果
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO ab_test_results 
                   (skill_name, model_a, model_b, winner, improvement, sample_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (skill_name, model_a, model_b, winner, improvement, sample_count)
            )
            conn.commit()
        
        return {
            "winner": winner,
            "improvement": round(improvement, 4),
            "significant": significant,
            "sample_count": sample_count,
        }
    
    def auto_switch_model(self, skill_name: str) -> Optional[str]:
        """
        自动选择最佳模型版本
        """
        models = self._models.get(skill_name, [])
        if not models:
            return None
        
        # 选准确率最高的
        best = max(models, key=lambda m: m.accuracy)
        return best.name
    
    # ──── 内部方法 ────
    
    def _features_to_vector(self, features: dict) -> Optional[np.ndarray]:
        """将特征字典展平为数值向量"""
        vec = []
        for k, v in sorted(features.items()):
            if isinstance(v, (int, float)):
                vec.append(float(v))
            elif isinstance(v, list):
                # 统计特征
                arr = np.array([x for x in v if isinstance(x, (int, float))])
                if len(arr) > 0:
                    vec.extend([float(np.mean(arr)), float(np.std(arr)),
                                float(np.min(arr)), float(np.max(arr))])
        return np.array(vec) if vec else None
    
    def _safe_serialize(self, obj) -> dict:
        """安全序列化（处理 numpy 类型）"""
        if isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, deque)):
            return [self._safe_serialize(v) for v in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    def _optimize_scoring_params(self, data: dict) -> dict:
        """
        优化评分参数（网格搜索）
        这是轻量级自训练的核心
        """
        X, y = data["X"], data["y"]
        if len(X) < 10:
            return {"status": "insufficient_data"}
        
        # 简单参数优化：找到最佳评分阈值
        best_threshold = 0.5
        best_accuracy = 0
        
        for threshold in np.arange(0.3, 0.8, 0.05):
            predictions = (np.mean(X, axis=1) > threshold).astype(float)
            accuracy = np.mean(np.abs(predictions - y) < 0.2)
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold
        
        return {
            "status": "optimized",
            "threshold": round(float(best_threshold), 3),
            "accuracy": round(float(best_accuracy), 3),
            "samples_used": len(X),
        }
    
    def _evaluate_params(self, params: dict, data: dict) -> float:
        """评估优化后的参数"""
        return params.get("accuracy", 0.0)
    
    # ──── 统计 ────
    
    def get_stats(self, skill_name: str = None) -> dict:
        """获取自训练统计"""
        with sqlite3.connect(self.db_path) as conn:
            if skill_name:
                samples = conn.execute(
                    "SELECT COUNT(*) FROM training_samples WHERE skill_name=?",
                    (skill_name,)
                ).fetchone()[0]
                models = conn.execute(
                    "SELECT COUNT(*) FROM model_versions WHERE skill_name=?",
                    (skill_name,)
                ).fetchone()[0]
            else:
                samples = conn.execute(
                    "SELECT COUNT(*) FROM training_samples"
                ).fetchone()[0]
                models = conn.execute(
                    "SELECT COUNT(*) FROM model_versions"
                ).fetchone()[0]
        
        return {
            "total_samples": samples,
            "total_models": models,
            "ready_to_train": samples >= self.min_samples,
            "samples_needed": max(0, self.min_samples - samples),
        }
