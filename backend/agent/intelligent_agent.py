"""
Intelligent Agent with Adaptive Mode Switching

This module creates an AI agent that can intelligently switch between 
efficient and beast modes based on task complexity analysis.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from services.llm import make_llm_api_call
from utils.logger import logger

class AgentMode(Enum):
    """Agent execution modes."""
    EFFICIENT = "efficient"  # Conservative limits
    BEAST = "beast"         # Maximum capabilities

class ComplexityLevel(Enum):
    """Task complexity levels.""" 
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    EXTREME = 4

@dataclass
class ModeConfig:
    """Configuration for different agent modes."""
    native_max_auto_continues: int
    max_iterations: int
    max_xml_tool_calls: int
    enable_thinking: bool
    reasoning_effort: str
    temperature: float
    enable_dual_calling: bool

# Mode configurations
MODE_CONFIGS = {
    AgentMode.EFFICIENT: ModeConfig(
        native_max_auto_continues=25,
        max_iterations=100,
        max_xml_tool_calls=5,
        enable_thinking=False,
        reasoning_effort='low',
        temperature=0.1,
        enable_dual_calling=False
    ),
    AgentMode.BEAST: ModeConfig(
        native_max_auto_continues=1000,
        max_iterations=10000,
        max_xml_tool_calls=0,  # Unlimited
        enable_thinking=True,
        reasoning_effort='high',
        temperature=0.3,
        enable_dual_calling=True
    )
}

class IntelligentAgent:
    """Agent that adapts its capabilities based on task complexity."""
    
    def __init__(self):
        self.complexity_patterns = self._init_patterns()
        self.upgrade_triggers = [
            # Complexity escalation indicators
            "more complex than expected",
            "more complicated than initially thought", 
            "requires deeper analysis",
            "need to expand the scope",
            "additional steps needed",
            "this is getting complex",
            "complexity has increased",
            
            # Resource exhaustion indicators  
            "need more iterations",
            "require additional tool calls",
            "need to perform more actions",
            "this will take longer than expected",
            
            # Scope expansion indicators
            "multiple dependencies found",
            "interconnected systems detected",
            "broader impact than anticipated",
            "need to handle edge cases",
            "requires comprehensive solution",
            
            # Technical complexity indicators
            "advanced implementation required",
            "sophisticated approach needed",
            "multiple technologies involved",
            "architectural considerations",
            "scalability requirements",
            "performance optimization needed",
            
            # Project scope indicators
            "full system integration",
            "end-to-end implementation",
            "enterprise-level solution",
            "production-ready deployment"
        ]
    
    def _init_patterns(self) -> Dict[str, Dict]:
        """Initialize SONNET 4 ENHANCED complexity detection patterns."""
        return {
            "simple": {
                "patterns": [
                    r"\b(what is|define|explain|tell me about|describe)\b",
                    r"\b(single|one|simple|small|quick)\b.*\b(file|function|script|fix|change)\b",
                    r"\b(show|display|print|list|view)\b",
                    r"\b(help|assist|guide).*\b(with|me)\b",
                    r"\b(calculate|compute|find|get)\b.*\b(value|number|result)\b"
                ],
                "score": 15
            },
            "moderate": {
                "patterns": [
                    r"\b(create|build|make|develop|write)\b.*\b(component|module|feature|tool)\b",
                    r"\b(test|debug|fix|troubleshoot|optimize)\b",
                    r"\b(integrate|connect|combine|merge)\b",
                    r"\b(refactor|improve|enhance|update)\b.*\b(code|system)\b",
                    r"\b(analyze|process|parse|extract)\b.*\b(data|content|information)\b",
                    r"\b(multiple|several|few)\b.*\b(files|functions|steps|components)\b"
                ],
                "score": 35
            },
            "complex": {
                "patterns": [
                    r"\b(application|system|platform|solution|framework)\b",
                    r"\b(full.stack|end.to.end|complete|comprehensive)\b",
                    r"\b(database|api|frontend|backend|server)\b.*\b(and|with|plus|\+)\b",
                    r"\b(deploy|production|scalable|enterprise|cloud)\b",
                    r"\b(architecture|design|infrastructure|workflow)\b",
                    r"\b(authentication|authorization|security|encryption)\b",
                    r"\b(automated|automation|pipeline|ci/cd)\b",
                    r"\b(dashboard|interface|management.system)\b"
                ],
                "score": 65
            },
            "extreme": {
                "patterns": [
                    r"\b(entire|comprehensive|complete)\b.*\b(system|platform|ecosystem|infrastructure)\b",
                    r"\b(microservices|distributed|enterprise|large.scale)\b",
                    r"\b(machine learning|ai|artificial intelligence)\b.*\b(pipeline|system|platform|model)\b",
                    r"\b(research|investigate|explore|discover)\b.*\b(extensively|thoroughly|deeply|comprehensively)\b",
                    r"\b(migration|refactor|rebuild|rewrite)\b.*\b(everything|all|complete|entire)\b",
                    r"\b(multi.tenant|high.availability|fault.tolerant|scalable)\b",
                    r"\b(real.time|streaming|event.driven|reactive)\b.*\b(system|architecture)\b"
                ],
                "score": 90
            }
        }
    
    async def analyze_task_complexity(self, user_message: str) -> Tuple[AgentMode, Dict[str, Any]]:
        """
        Analyze task complexity and recommend agent mode.
        
        Returns:
            Tuple of (recommended_mode, analysis_details)
        """
        logger.info(f"🧠 Analyzing task complexity: {user_message[:100]}...")
        
        # Pattern-based analysis
        complexity_score = self._pattern_analysis(user_message)
        
        # Determine mode based on score
        if complexity_score <= 25:
            mode = AgentMode.EFFICIENT
            level = "SIMPLE"
        elif complexity_score <= 45:
            mode = AgentMode.EFFICIENT
            level = "MODERATE"
        elif complexity_score <= 70:
            mode = AgentMode.BEAST
            level = "COMPLEX"
        else:
            mode = AgentMode.BEAST
            level = "EXTREME"
        
        analysis = {
            "complexity_score": complexity_score,
            "complexity_level": level,
            "recommended_mode": mode.value,
            "reasoning": f"Task scored {complexity_score}/100, indicating {level} complexity",
            "config": MODE_CONFIGS[mode]
        }
        
        logger.info(f"🎯 Complexity Analysis: {level} ({complexity_score}/100) → {mode.value.upper()} mode")
        
        return mode, analysis
    
    def _pattern_analysis(self, text: str) -> float:
        """Analyze text patterns to determine complexity score."""
        text_lower = text.lower()
        max_score = 10  # Base score
        matched_patterns = []
        
        for category, data in self.complexity_patterns.items():
            for pattern in data["patterns"]:
                if re.search(pattern, text_lower):
                    max_score = max(max_score, data["score"])
                    matched_patterns.append(f"{category}:{pattern}")
        
        # Boost score for certain keywords
        boost_keywords = {
            "comprehensive": 15,
            "complete": 10,
            "full": 8,
            "entire": 12,
            "complex": 10,
            "advanced": 8,
            "sophisticated": 10
        }
        
        for keyword, boost in boost_keywords.items():
            if keyword in text_lower:
                max_score += boost
        
        # Length factor (longer requests often more complex)
        if len(text) > 200:
            max_score += 5
        if len(text) > 500:
            max_score += 10
        
        return min(100, max_score)
    
    def should_upgrade_to_beast_mode(self, agent_response: str, iteration_count: int, tool_count: int, current_mode: AgentMode) -> bool:
        """
        Determine if agent should upgrade to beast mode mid-execution.
        """
        if current_mode == AgentMode.BEAST:
            return False
        
        response_lower = agent_response.lower()
        
        # Check for upgrade triggers
        for trigger in self.upgrade_triggers:
            if trigger in response_lower:
                logger.info(f"🚀 UPGRADE TRIGGER: {trigger}")
                return True
        
        # Check resource limits
        efficient_config = MODE_CONFIGS[AgentMode.EFFICIENT]
        
        if iteration_count >= efficient_config.max_iterations * 0.8:
            logger.info(f"🚀 UPGRADE: Approaching iteration limit ({iteration_count})")
            return True
        
        if tool_count >= efficient_config.max_xml_tool_calls * 0.8:
            logger.info(f"🚀 UPGRADE: Approaching tool limit ({tool_count})")
            return True
        
        return False
    
    def get_mode_config(self, mode: AgentMode) -> ModeConfig:
        """Get configuration for specified mode."""
        return MODE_CONFIGS[mode]

# Global instance
intelligent_agent = IntelligentAgent() 