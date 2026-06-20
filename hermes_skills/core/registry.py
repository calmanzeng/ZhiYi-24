"""
技能注册表 — 发现、加载、验证技能插件
"""
import os
import yaml
import importlib.util
from pathlib import Path


class SkillRegistry:
    """管理所有已注册的执医技能"""
    
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = Path(skills_dir)
        self._skills = {}  # name → {config, scorer_class, path}
        self._discover()
    
    def _discover(self):
        """扫描 skills/ 目录，发现所有有效技能"""
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue
            
            yaml_path = skill_dir / "skill.yaml"
            if not yaml_path.exists():
                continue
            
            try:
                self._load_skill(skill_dir)
            except Exception as e:
                print(f"  [WARN] 跳过 {skill_dir.name}: {e}")
    
    def _load_skill(self, skill_dir: Path):
        """加载单个技能"""
        # 读取 skill.yaml
        with open(skill_dir / "skill.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        name = config["name"]
        
        # 动态加载 scoring.py
        scoring_path = skill_dir / "scoring.py"
        scorer_class = None
        if scoring_path.exists():
            spec = importlib.util.spec_from_file_location(
                f"skills.{name}.scoring", scoring_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            scorer_class = getattr(module, "SkillScorer", None)
        
        self._skills[name] = {
            "config": config,
            "scorer_class": scorer_class,
            "path": str(skill_dir),
            "loaded_at": None,
        }
    
    def list_skills(self) -> list:
        """列出所有可用技能"""
        return [
            {
                "name": name,
                "display_name": info["config"]["display_name"],
                "category": info["config"].get("category", "other"),
                "version": info["config"].get("version", "0.0.0"),
                "has_scorer": info["scorer_class"] is not None,
            }
            for name, info in self._skills.items()
        ]
    
    def get_skill(self, name: str) -> dict:
        """获取技能配置和评分器"""
        if name not in self._skills:
            available = list(self._skills.keys())
            raise ValueError(f"技能 '{name}' 未找到。可用: {available}")
        
        info = self._skills[name]
        return {
            "name": name,
            "config": info["config"],
            "scorer": info["scorer_class"](info["config"]) if info["scorer_class"] else None,
            "path": info["path"],
        }
    
    def validate_skill(self, skill_dir: str) -> list:
        """验证技能目录合法性，返回错误列表"""
        errors = []
        path = Path(skill_dir)
        
        if not (path / "skill.yaml").exists():
            errors.append("缺少 skill.yaml")
            return errors
        
        try:
            with open(path / "skill.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"skill.yaml 语法错误: {e}")
            return errors
        
        # 必需字段检查
        required = ["name", "display_name", "model", "landmarks", "metrics"]
        for field in required:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检测 scoring.py
        if not (path / "scoring.py").exists():
            errors.append("缺少 scoring.py (可选但推荐)")
        
        return errors
