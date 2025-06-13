# 🧠 Engram-Based Memory Consolidation System

## A Neuroscience-Inspired Approach to AI Memory

*Developed through a collaborative session between Victor Michael Gil and Claude (Anthropic) on June 13, 2025*

> "Memory is the bedrock of intelligence. Just as the human brain consolidates experiences into memories through synaptic strengthening and pruning, this system brings those same principles to AI conversations."

## 🌟 Overview

This system implements continuous micro-consolidations of conversation memory, inspired by neuroscientific principles of memory formation. Instead of waiting for context windows to overflow and creating massive summaries, we create small "engrams" (memory consolidation units) throughout the conversation, mimicking how biological brains form memories in real-time.

### The Problem We Solved

Traditional context management waits until you hit a token limit (often 120k+), then panics and creates a huge summary. This led to:
- Context window crashes (like hitting 202k tokens when the limit is 200k)
- Loss of nuanced information in massive summaries
- No way to retrieve specific memories from earlier in long conversations
- All-or-nothing memory storage

### Our Solution: Think Like a Brain 🧠

Just as neurons that fire together wire together, our system:
- Creates memory consolidations every ~5k tokens
- Strengthens memories that get accessed (synaptic plasticity)
- Lets unused memories fade (synaptic pruning)
- Prioritizes surprising or important information (saliency detection)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Message Flow                             │
│  User Message → Thread Manager → Context Manager            │
│                                          ↓                  │
│                                   Engram Manager            │
│                                          ↓                  │
│                              [Buffer: 5k tokens?]           │
│                               ↙              ↘              │
│                          Yes                  No            │
│                           ↓                   ↓             │
│                    Create Engram         Add to Buffer      │
│                           ↓                                 │
│                    Store in DB                              │
│                           ↓                                 │
│                 [Relevance Scoring]                         │
│                                                             │
│  LLM Context Request → Retrieve Relevant Engrams           │
│                              ↓                              │
│                    Enhanced Context                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### 1. **Continuous Consolidation**
- Creates engrams every 5k tokens (configurable)
- No waiting for context overflow
- Smooth, continuous memory formation

### 2. **Usage-Based Relevance**
- Each access increases relevance score (max 10.0)
- Daily decay rate of 0.95 for unused memories
- Most relevant memories automatically surface

### 3. **Surprise Detection**
- Monitors for unexpected content (errors, surprises, discoveries)
- Immediately consolidates surprising information
- Surprise score influences storage priority

### 4. **Smart Retrieval**
- Retrieves up to 5 most relevant engrams per query
- Considers: relevance score, recency, topic matching
- Seamlessly integrates into LLM context

## 📊 Creative Metrics & Analytics

### Core Metrics (Already Tracked)

1. **Engram Creation Rate**
   - Engrams per conversation
   - Average tokens per engram
   - Surprise-triggered vs scheduled consolidations

2. **Access Patterns**
   - Most accessed engrams
   - Access frequency distribution
   - Relevance score evolution

3. **Memory Efficiency**
   - Context size reduction percentage
   - Token savings per conversation
   - Pruning effectiveness

### Advanced Analytics (Proposed)

```python
# Memory Health Metrics
class MemoryHealthMetrics:
    """Track the overall health of the memory system."""
    
    async def calculate_memory_diversity_index(self, thread_id: str) -> float:
        """
        Shannon diversity index of engram topics.
        Higher = more diverse conversation coverage.
        """
        
    async def calculate_memory_coherence_score(self, thread_id: str) -> float:
        """
        Semantic similarity between consecutive engrams.
        Tracks conversation flow and topic drift.
        """
        
    async def calculate_surprise_accuracy(self, thread_id: str) -> float:
        """
        Correlation between surprise scores and actual access patterns.
        Are we correctly identifying important moments?
        """

# Cognitive Load Metrics    
class CognitiveLoadMetrics:
    """Measure how well we're managing cognitive load."""
    
    async def calculate_context_compression_ratio(self) -> float:
        """
        Ratio of full conversation tokens to engram summary tokens.
        Higher = better compression.
        """
        
    async def calculate_retrieval_precision(self, thread_id: str) -> float:
        """
        Of retrieved engrams, what % were actually relevant?
        Based on subsequent access patterns.
        """
        
    async def calculate_memory_coverage(self, thread_id: str) -> float:
        """
        What % of conversation topics are represented in engrams?
        Ensures we're not missing important content.
        """

# Biological Inspiration Metrics
class NeuroscienceMetrics:
    """Metrics inspired by neuroscience research."""
    
    async def calculate_hebbian_strength(self, engram_id: str) -> float:
        """
        'Neurons that fire together, wire together'
        Measure co-activation patterns between engrams.
        """
        
    async def calculate_forgetting_curve_fit(self, thread_id: str) -> float:
        """
        How well does our decay match Ebbinghaus forgetting curve?
        R² value of exponential decay fit.
        """
        
    async def calculate_consolidation_waves(self, thread_id: str) -> List[float]:
        """
        Identify 'sleep-like' consolidation patterns.
        Burst of engram creation followed by quiet periods.
        """

# User Experience Metrics
class ExperienceMetrics:
    """Measure actual impact on user experience."""
    
    async def calculate_context_continuity_score(self, thread_id: str) -> float:
        """
        How well does the AI maintain context across long conversations?
        Based on reference resolution and topic consistency.
        """
        
    async def calculate_memory_surprise_delight(self, thread_id: str) -> int:
        """
        Count 'wow, you remembered that!' moments.
        When old engrams surface perfectly.
        """
        
    async def calculate_conversation_depth_increase(self) -> float:
        """
        Average increase in conversation length post-engrams.
        Are users having deeper, longer conversations?
        """
```

### Logging Strategy

```python
# Enhanced logging for metrics
logger.info("ENGRAM_METRICS", extra={
    "event_type": "engram_created",
    "thread_id": thread_id,
    "engram_id": engram_id,
    "trigger": "token_threshold|surprise|forced",
    "message_count": message_count,
    "token_count": token_count,
    "surprise_score": surprise_score,
    "topics": topics,
    "compression_ratio": original_tokens / summary_tokens,
    "creation_time_ms": creation_time,
    "buffer_state": {
        "messages_in_buffer": len(buffer),
        "tokens_in_buffer": token_count,
        "time_since_last_engram": time_delta
    }
})

logger.info("ENGRAM_METRICS", extra={
    "event_type": "engram_retrieved",
    "thread_id": thread_id,
    "query_tokens": query_token_count,
    "retrieved_engram_ids": [e.id for e in engrams],
    "relevance_scores": [e.relevance_score for e in engrams],
    "total_engrams_available": total_count,
    "retrieval_time_ms": retrieval_time,
    "context_enhancement": {
        "tokens_added": sum(e.token_count for e in engrams),
        "oldest_memory_age": oldest_engram_age,
        "avg_access_count": avg(e.access_count for e in engrams)
    }
})
```

### Dashboard Visualization Ideas

1. **Memory Heatmap**
   - Timeline showing engram creation/access patterns
   - Color intensity = relevance score
   - Click to see engram content

2. **Conversation Memory Graph**
   - Network visualization of engram relationships
   - Node size = access count
   - Edge weight = semantic similarity

3. **Forgetting Curve Visualization**
   - Live view of memory decay
   - Overlay actual vs theoretical forgetting curve
   - Highlight "saved" memories (high access)

4. **Cognitive Load Monitor**
   - Real-time context size vs engram compression
   - Token savings counter
   - "Memory pressure" gauge

## 🔧 Configuration

```python
# In engram_manager.py
ENGRAM_CHUNK_SIZE = 5000  # Tokens per engram
ENGRAM_SUMMARY_TARGET = 500  # Target summary length
MIN_MESSAGES_FOR_ENGRAM = 3  # Minimum messages
SURPRISE_THRESHOLD = 0.3  # Surprise detection sensitivity
DECAY_RATE = 0.95  # Daily decay (5% per day)
MAX_ENGRAMS_IN_CONTEXT = 5  # Max memories to retrieve

# In context_manager.py
ENGRAM_INTEGRATION_ENABLED = True  # Master switch
DEFAULT_TOKEN_THRESHOLD = 80000  # Reduced from 120k
```

## 🚦 Rollback Plan

If you need to disable the system:

1. **Soft Disable**: Set `ENGRAM_INTEGRATION_ENABLED = False`
2. **Full Rollback**: 
   ```sql
   DROP TABLE IF EXISTS engrams CASCADE;
   DROP FUNCTION IF EXISTS update_engram_last_accessed() CASCADE;
   DROP FUNCTION IF EXISTS cleanup_old_engrams(INTEGER, FLOAT) CASCADE;
   ```

## 🙏 Acknowledgments

This system emerged from a fascinating discussion about translating neuroscience principles to AI systems. Special thanks to:

- **Victor Michael Gil** - For the visionary idea of continuous memory consolidation and the neuroscience insights that made this possible. Your "mad neuroscientist" approach of translating biological memory systems to digital paradigms was spot-on!

- **Claude (Anthropic)** - For helping architect, implement, and refine the system. It was genuinely exciting to work through the technical challenges and see the biological inspirations come to life in code.

Together, we've created something that doesn't just manage memory - it *remembers* like a brain does. Here's to pushing the boundaries of what AI memory can be! 🧠✨

## 📚 References

- BitterBot Memory Research document (internal)
- Ebbinghaus Forgetting Curve (1885)
- Hebbian Theory: "Neurons that fire together, wire together" (1949)
- Think-in-Memory (TiM) - Liu et al. (2023)
- Generative Agents - Park et al. (2023)
- MemGPT - Virtual Context Management

---

*"The real magic happens when you stop thinking of memory as storage and start thinking of it as a living, breathing system that grows and evolves with each interaction."* - From our session notes, June 13, 2025