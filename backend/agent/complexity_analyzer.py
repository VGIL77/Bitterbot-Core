"""
Intelligent Task Complexity Analyzer for Dynamic Agent Mode Selection

This module analyzes incoming tasks to determine the appropriate execution mode:
- EFFICIENT: Standard limits for simple tasks
- BEAST: Maximum capabilities for complex tasks
- ADAPTIVE: Can upgrade mid-execution when needed
"""

import json
import re
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from services.llm import make_llm_api_call
from utils.logger import logger

class AgentMode(Enum):
    """Agent execution modes with different capability levels."""
    EFFICIENT = "efficient"     # Conservative limits, fast execution
    BEAST = "beast"            # Maximum capabilities, unlimited power
    ADAPTIVE = "adaptive"      # Can upgrade during execution

class ComplexityLevel(Enum):
    """Task complexity levels."""
    SIMPLE = 1      # Basic tasks, single tool usage
    MODERATE = 2    # Multi-step tasks, several tools
    COMPLEX = 3     # Multi-domain tasks, many iterations
    EXTREME = 4     # Massive projects, unlimited scope

@dataclass
class ComplexityScore:
    """Detailed complexity analysis results."""
    level: ComplexityLevel
    score: float  # 0-100
    reasoning: str
    recommended_mode: AgentMode
    confidence: float  # 0-1
    key_indicators: List[str]
    estimated_tool_calls: int
    estimated_iterations: int

@dataclass
class ModeConfig:
    """Configuration for different agent modes."""
    native_max_auto_continues: int
    max_iterations: int
    max_xml_tool_calls: int
    enable_thinking: bool
    reasoning_effort: str
    temperature: float
    enable_dual_calling: bool  # Both XML + native

# Predefined mode configurations
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

class ComplexityAnalyzer:
    """Intelligent analyzer for determining task complexity and optimal agent mode."""
    
    def __init__(self):
        self.complexity_patterns = self._load_complexity_patterns()
        self.upgrade_triggers = self._load_upgrade_triggers()
    
    def _load_complexity_patterns(self) -> Dict[str, Dict]:
        """Define patterns that indicate different complexity levels."""
        return {
            "simple_indicators": {
                "patterns": [
                    r"\b(what is|define|explain|tell me about)\b",
                    r"\b(single|one|simple)\b.*\b(file|function|script)\b",
                    r"\b(quick|fast|simple)\b.*\b(fix|change|update)\b",
                    r"\b(show me|display|print)\b",
                    r"\b(calculate|compute)\b.*\b(single|one)\b"
                ],
                "weight": 1.0
            },
            "moderate_indicators": {
                "patterns": [
                    r"\b(create|build|make)\b.*\b(component|module|feature)\b",
                    r"\b(multi|several|few)\b.*\b(files|functions|steps)\b",
                    r"\b(integrate|connect|combine)\b",
                    r"\b(test|debug|troubleshoot)\b",
                    r"\b(analyze|process|parse)\b.*\b(data|file|content)\b"
                ],
                "weight": 2.0
            },
            "complex_indicators": {
                "patterns": [
                    r"\b(application|system|platform|solution)\b",
                    r"\b(full.stack|end.to.end|complete)\b",
                    r"\b(architecture|design|infrastructure)\b",
                    r"\b(multiple|many|various)\b.*\b(technologies|frameworks|languages)\b",
                    r"\b(deploy|production|scalable)\b",
                    r"\b(database|api|frontend|backend)\b.*\b(and|with|plus)\b"
                ],
                "weight": 3.0
            },
            "extreme_indicators": {
                "patterns": [
                    r"\b(entire|complete|comprehensive)\b.*\b(system|platform|ecosystem)\b",
                    r"\b(microservices|distributed|enterprise)\b",
                    r"\b(machine learning|ai|automation)\b.*\b(pipeline|system)\b",
                    r"\b(migration|refactor|rebuild)\b.*\b(everything|all|complete)\b",
                    r"\b(research|investigate|explore)\b.*\b(extensively|thoroughly|deeply)\b"
                ],
                "weight": 4.0
            }
        }
    
    def _load_upgrade_triggers(self) -> List[str]:
        """Patterns that suggest mid-execution complexity upgrade needed."""
        return [
            "this requires more than expected",
            "need to expand the scope",
            "more complex than initially thought",
            "additional requirements discovered",
            "deeper analysis required",
            "multiple dependencies found",
            "scaling beyond original plan"
        ]
    
    async def analyze_task_complexity(self, user_message: str, context_messages: Optional[List[Dict]] = None) -> ComplexityScore:
        """
        Analyze a user's task to determine complexity and recommended agent mode.
        
        Args:
            user_message: The user's request
            context_messages: Previous conversation context
            
        Returns:
            ComplexityScore with detailed analysis
        """
        logger.info(f"🔍 Analyzing task complexity for: {user_message[:100]}...")
        
        # Step 1: Pattern-based quick analysis
        pattern_score = self._analyze_patterns(user_message)
        
        # Step 2: Use LLM for deep semantic analysis
        semantic_score = await self._semantic_analysis(user_message, context_messages)
        
        # Step 3: Combine scores with weights
        final_score = (pattern_score * 0.4) + (semantic_score.score * 0.6)
        
        # Step 4: Determine complexity level and mode
        complexity_level = self._score_to_complexity_level(final_score)
        recommended_mode = self._complexity_to_mode(complexity_level, final_score)
        
        # Step 5: Estimate resource requirements
        estimated_tools, estimated_iterations = self._estimate_resources(complexity_level, user_message)
        
        return ComplexityScore(
            level=complexity_level,
            score=final_score,
            reasoning=semantic_score.reasoning,
            recommended_mode=recommended_mode,
            confidence=semantic_score.confidence,
            key_indicators=semantic_score.key_indicators,
            estimated_tool_calls=estimated_tools,
            estimated_iterations=estimated_iterations
        )
    
    def _analyze_patterns(self, text: str) -> float:
        """Quick pattern-based complexity scoring."""
        text_lower = text.lower()
        total_score = 0
        max_weight = 0
        
        for category, data in self.complexity_patterns.items():
            category_score = 0
            for pattern in data["patterns"]:
                if re.search(pattern, text_lower):
                    category_score += 1
            
            if category_score > 0:
                weighted_score = category_score * data["weight"]
                total_score = max(total_score, weighted_score)  # Take highest category
                max_weight = max(max_weight, data["weight"])
        
        # Normalize to 0-100 scale
        if max_weight > 0:
            return min(100, (total_score / max_weight) * 25)
        return 10  # Default low complexity
    
    async def _semantic_analysis(self, user_message: str, context_messages: Optional[List[Dict]] = None) -> 'SemanticScore':
        """Use LLM to perform deep semantic analysis of task complexity."""
        
        # Prepare context
        context_summary = ""
        if context_messages:
            recent_messages = context_messages[-5:]  # Last 5 messages
            context_summary = f"\nRecent conversation context:\n{json.dumps(recent_messages, indent=2)}"
        
        analysis_prompt = f"""
You are an expert task complexity analyzer for an AI agent system. Analyze the following user request and determine its complexity level.

User Request: "{user_message}"
{context_summary}

Analyze this task on multiple dimensions:

1. **Scope**: Single action vs multi-step process vs full project
2. **Technical Complexity**: Simple operations vs complex integrations vs cutting-edge tech
3. **Domain Breadth**: Single domain vs cross-domain vs multi-disciplinary  
4. **Time Horizon**: Immediate vs multi-phase vs long-term project
5. **Resource Requirements**: Minimal tools vs extensive toolchain vs unlimited resources
6. **Iteration Depth**: One-shot vs iterative refinement vs deep exploration

Based on your analysis, provide:

1. **Complexity Score** (0-100): 
   - 0-25: Simple (single tool, straightforward task)
   - 26-50: Moderate (multi-step, several tools)
   - 51-75: Complex (multi-domain, many iterations)  
   - 76-100: Extreme (unlimited scope, maximum resources)

2. **Key Indicators**: List specific words/phrases that indicate complexity

3. **Reasoning**: Explain your analysis in 2-3 sentences

4. **Confidence**: How confident are you in this assessment (0.0-1.0)

Respond in this EXACT JSON format:
{{
    "score": <number 0-100>,
    "key_indicators": ["indicator1", "indicator2", "..."],
    "reasoning": "<explanation>",
    "confidence": <number 0.0-1.0>
}}
"""

        try:
            response = await make_llm_api_call(
                messages=[{"role": "user", "content": analysis_prompt}],
                model_name="anthropic/claude-3-haiku-20241022",  # Fast, cheap model for analysis
                temperature=0.1,
                max_tokens=500
            )
            
            # Extract JSON from response
            response_text = ""
            if hasattr(response, 'choices') and response.choices:
                response_text = response.choices[0].message.content
            else:
                # Handle streaming response
                full_response = ""
                async for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            full_response += delta.content
                response_text = full_response
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                return SemanticScore(
                    score=float(analysis_data.get('score', 50)),
                    reasoning=analysis_data.get('reasoning', 'No reasoning provided'),
                    confidence=float(analysis_data.get('confidence', 0.5)),
                    key_indicators=analysis_data.get('key_indicators', [])
                )
        
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
        
        # Fallback to moderate complexity
        return SemanticScore(
            score=50.0,
            reasoning="Analysis failed, defaulting to moderate complexity",
            confidence=0.3,
            key_indicators=["analysis_error"]
        )
    
    def _score_to_complexity_level(self, score: float) -> ComplexityLevel:
        """Convert numerical score to complexity level."""
        if score <= 25:
            return ComplexityLevel.SIMPLE
        elif score <= 50:
            return ComplexityLevel.MODERATE
        elif score <= 75:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.EXTREME
    
    def _complexity_to_mode(self, level: ComplexityLevel, score: float) -> AgentMode:
        """Determine optimal agent mode based on complexity."""
        if level in [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE]:
            return AgentMode.EFFICIENT
        elif level == ComplexityLevel.COMPLEX:
            # Use confidence score to decide between EFFICIENT and BEAST
            return AgentMode.BEAST if score > 60 else AgentMode.ADAPTIVE
        else:  # EXTREME
            return AgentMode.BEAST
    
    def _estimate_resources(self, level: ComplexityLevel, task: str) -> Tuple[int, int]:
        """Estimate tool calls and iterations needed."""
        base_estimates = {
            ComplexityLevel.SIMPLE: (3, 2),
            ComplexityLevel.MODERATE: (10, 5),  
            ComplexityLevel.COMPLEX: (25, 15),
            ComplexityLevel.EXTREME: (100, 50)
        }
        
        base_tools, base_iterations = base_estimates[level]
        
        # Adjust based on specific keywords
        multiplier = 1.0
        if any(word in task.lower() for word in ['build', 'create', 'develop', 'implement']):
            multiplier *= 1.5
        if any(word in task.lower() for word in ['test', 'debug', 'optimize', 'refine']):
            multiplier *= 1.3
        if any(word in task.lower() for word in ['deploy', 'production', 'scale']):
            multiplier *= 1.4
        
        return int(base_tools * multiplier), int(base_iterations * multiplier)
    
    def should_upgrade_mode(self, current_mode: AgentMode, agent_response: str, iteration_count: int, tool_call_count: int) -> bool:
        """
        Determine if agent should upgrade to beast mode mid-execution.
        
        Args:
            current_mode: Current agent mode
            agent_response: Latest agent response text
            iteration_count: Current iteration number
            tool_call_count: Total tool calls so far
            
        Returns:
            True if should upgrade to beast mode
        """
        if current_mode == AgentMode.BEAST:
            return False  # Already in beast mode
        
        # Check for explicit upgrade triggers in agent response
        response_lower = agent_response.lower()
        for trigger in self.upgrade_triggers:
            if trigger in response_lower:
                logger.info(f"🚀 Upgrade trigger detected: {trigger}")
                return True
        
        # Check resource exhaustion patterns
        config = MODE_CONFIGS[current_mode]
        
        # Near iteration limit
        if iteration_count >= config.max_iterations * 0.8:
            logger.info(f"🚀 Approaching iteration limit ({iteration_count}/{config.max_iterations})")
            return True
        
        # Near tool call limit  
        if config.max_xml_tool_calls > 0 and tool_call_count >= config.max_xml_tool_calls * 0.8:
            logger.info(f"🚀 Approaching tool call limit ({tool_call_count}/{config.max_xml_tool_calls})")
            return True
        
        # Pattern detection for emerging complexity
        complexity_phrases = [
            "more complex than expected",
            "additional steps required", 
            "need to investigate further",
            "requires deeper analysis",
            "expanding scope",
            "multiple dependencies"
        ]
        
        for phrase in complexity_phrases:
            if phrase in response_lower:
                logger.info(f"🚀 Complexity escalation detected: {phrase}")
                return True
        
        return False

@dataclass
class SemanticScore:
    """Results from semantic analysis."""
    score: float
    reasoning: str
    confidence: float
    key_indicators: List[str]

# Global analyzer instance
complexity_analyzer = ComplexityAnalyzer() 