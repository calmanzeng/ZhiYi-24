# Hermes Skills Framework
# AI-Native clinical skills training platform
# 自我进化引擎: AutoSkill + SelfTrain + ABTest

from .core.engine import SkillPipeline
from .core.registry import SkillRegistry
from .core.data_hub import DataHub
from .evolve.autoskill import AutoSkillGenerator, generate_skill
from .evolve.selftrain import SelfTrainEngine
from .evolve.abtest import ABTestEngine, ABTestConfig

__version__ = "0.2.0-ai-native"
__all__ = [
    "SkillPipeline", "SkillRegistry", "DataHub",
    "AutoSkillGenerator", "generate_skill",
    "SelfTrainEngine", "ABTestEngine", "ABTestConfig",
]
