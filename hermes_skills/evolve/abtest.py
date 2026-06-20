"""
ABTest — 自动 A/B 验证引擎
多模型并行评估 → 统计检验 → 自动切换最优模型
"""
import os
import json
import time
import sqlite3
import numpy as np
from typing import Optional, List, Dict
from dataclasses import dataclass
from collections import deque


@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    min_samples: int = 30           # 最少样本数
    significance_level: float = 0.05 # 显著性水平
    min_improvement: float = 0.02    # 最小改进阈值
    traffic_split: float = 0.5       # 流量分配（50/50）
    test_duration_hours: int = 24    # 测试时长
    auto_switch: bool = True         # 自动切换到胜出模型


class ABTestEngine:
    """
    自动 A/B 测试引擎
    
    工作流程:
      1. 注册新模型版本（候选）
      2. 并行评估新旧模型 → 收集指标
      3. 统计检验 → 判断是否显著改进
      4. 自动切换到胜出模型（或保留旧版）
      5. 记录所有测试结果
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.expanduser("~/.hermes/abtest.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._active_tests = {}  # skill_name → ABTestConfig
        self._results_buffer = {}  # model_name → deque of scores
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    model_a TEXT NOT NULL,       -- 当前生产模型
                    model_b TEXT NOT NULL,       -- 候选模型
                    score_a REAL,                -- 模型A的平均分
                    score_b REAL,                -- 模型B的平均分
                    improvement REAL,            -- 改进幅度
                    p_value REAL,                -- 统计显著性
                    significant INTEGER DEFAULT 0, -- 1=显著
                    winner TEXT,                 -- 胜出模型名
                    sample_count INTEGER,        -- 测试样本数
                    auto_switched INTEGER DEFAULT 0, -- 是否自动切换
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            # 评分记录表（用于实时计算）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS score_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    score REAL NOT NULL,         -- 0-100
                    features_hash TEXT,          -- 特征哈希（去重用）
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            conn.commit()
    
    # ──── 测试管理 ────
    
    def start_test(self, skill_name: str, model_a: str, model_b: str,
                   config: ABTestConfig = None) -> str:
        """
        启动一次 A/B 测试
        
        Args:
            skill_name: 技能名
            model_a: 当前生产模型（对照组）
            model_b: 候选模型（实验组）
            config: 测试配置
        
        Returns: test_id
        """
        if config is None:
            config = ABTestConfig()
        
        test_id = f"ab_{skill_name}_{int(time.time())}"
        self._active_tests[skill_name] = {
            "id": test_id,
            "model_a": model_a,
            "model_b": model_b,
            "config": config,
            "started_at": time.time(),
            "scores_a": [],
            "scores_b": [],
        }
        
        return test_id
    
    def record_score(self, skill_name: str, model_name: str, score: float):
        """记录一次评分结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO score_records (skill_name, model_name, score) VALUES (?, ?, ?)",
                (skill_name, model_name, score)
            )
            conn.commit()
        
        # 更新内存缓存
        if skill_name in self._active_tests:
            test = self._active_tests[skill_name]
            if model_name == test["model_a"]:
                test["scores_a"].append(score)
            elif model_name == test["model_b"]:
                test["scores_b"].append(score)
    
    def check_result(self, skill_name: str) -> Optional[dict]:
        """
        检查 A/B 测试结果
        
        Returns: None（还没够数据）或 dict（结果已出）
        """
        test = self._active_tests.get(skill_name)
        if not test:
            return None
        
        config = test["config"]
        scores_a = test["scores_a"]
        scores_b = test["scores_b"]
        
        n_a, n_b = len(scores_a), len(scores_b)
        
        # 还没够数据
        if n_a < config.min_samples or n_b < config.min_samples:
            # 检查是否超过时间限制
            if time.time() - test["started_at"] > config.test_duration_hours * 3600:
                return {
                    "status": "timeout",
                    "samples_a": n_a,
                    "samples_b": n_b,
                    "winner": None,
                }
            return None
        
        # 统计分析
        mean_a = np.mean(scores_a)
        mean_b = np.mean(scores_b)
        improvement = mean_b - mean_a
        
        # 简化 t-test
        std_a = np.std(scores_a, ddof=1)
        std_b = np.std(scores_b, ddof=1)
        se = np.sqrt(std_a**2/n_a + std_b**2/n_b)
        
        if se > 0:
            t_stat = improvement / se
            # 简化 p-value 近似
            p_value = min(1.0, np.exp(-abs(t_stat) * 0.5))
        else:
            p_value = 1.0
        
        significant = (p_value < config.significance_level and
                       abs(improvement) > config.min_improvement * 100)
        
        winner = None
        if significant and improvement > 0:
            winner = test["model_b"]  # 候选胜出
        elif significant and improvement < 0:
            winner = test["model_a"]  # 当前更好
        
        result = {
            "status": "complete",
            "score_a": round(mean_a, 1),
            "score_b": round(mean_b, 1),
            "improvement": round(improvement, 1),
            "p_value": round(p_value, 4),
            "significant": significant,
            "winner": winner,
            "sample_count": n_a + n_b,
        }
        
        # 持久化
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO ab_test_results 
                   (skill_name, model_a, model_b, score_a, score_b,
                    improvement, p_value, significant, winner, sample_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (skill_name, test["model_a"], test["model_b"],
                 mean_a, mean_b, improvement, p_value,
                 int(significant), winner, n_a + n_b)
            )
            conn.commit()
        
        return result
    
    def auto_switch(self, skill_name: str, result: dict) -> Optional[str]:
        """
        自动切换到胜出模型
        
        Returns: 新模型名（如果切换了），None（未切换）
        """
        if not result.get("significant"):
            return None
        
        winner = result.get("winner")
        if not winner:
            return None
        
        # 记录自动切换
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE ab_test_results SET auto_switched=1 WHERE winner=? AND skill_name=?",
                (winner, skill_name)
            )
            conn.commit()
        
        # 清理
        if skill_name in self._active_tests:
            del self._active_tests[skill_name]
        
        return winner
    
    # ──── 查询 ────
    
    def get_best_model(self, skill_name: str) -> Optional[str]:
        """获取当前最佳模型"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT winner FROM ab_test_results 
                   WHERE skill_name=? AND significant=1
                   ORDER BY created_at DESC LIMIT 1""",
                (skill_name,)
            ).fetchone()
            return row[0] if row else None
    
    def get_test_history(self, skill_name: str, limit: int = 10) -> List[dict]:
        """获取测试历史"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT skill_name, model_a, model_b, score_a, score_b,
                          improvement, p_value, significant, winner,
                          sample_count, auto_switched
                   FROM ab_test_results
                   WHERE skill_name=?
                   ORDER BY created_at DESC LIMIT ?""",
                (skill_name, limit)
            ).fetchall()
        
        return [
            {
                "model_a": r[1], "model_b": r[2],
                "score_a": r[3], "score_b": r[4],
                "improvement": r[5], "p_value": r[6],
                "significant": bool(r[7]), "winner": r[8],
                "samples": r[9], "auto_switched": bool(r[10]),
            }
            for r in rows
        ]
    
    def get_stats(self) -> dict:
        """获取全局统计"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM ab_test_results"
            ).fetchone()[0]
            switched = conn.execute(
                "SELECT COUNT(*) FROM ab_test_results WHERE auto_switched=1"
            ).fetchone()[0]
        
        return {
            "total_tests": total,
            "auto_switches": switched,
            "active_tests": len(self._active_tests),
        }
