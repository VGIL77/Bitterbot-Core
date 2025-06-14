#!/usr/bin/env python3
"""Test script to verify BitterBot memory system imports"""

import sys
import traceback

def test_imports():
    """Test all memory system imports"""
    
    print("🧠 Testing BitterBot Memory System imports...\n")
    
    imports_to_test = [
        # Core memory modules
        ("memory", "from memory import BitterBotMemory"),
        ("memory.core", "from memory.core import BitterBotMemory"),
        ("memory.core.working_memory", "from memory.core.working_memory import WorkingMemory"),
        ("memory.core.episodic_memory", "from memory.core.episodic_memory import EpisodicMemory"),
        ("memory.core.semantic_memory", "from memory.core.semantic_memory import SemanticMemory"),
        ("memory.core.dream_memory", "from memory.core.dream_memory import DreamMemory"),
        
        # Storage modules
        ("memory.storage", "from memory.storage import VectorStore, SQLiteStore, RedisClient"),
        ("memory.storage.vector_store", "from memory.storage.vector_store import VectorStore"),
        ("memory.storage.sqlite_store", "from memory.storage.sqlite_store import SQLiteStore"),
        ("memory.storage.redis_client", "from memory.storage.redis_client import RedisClient"),
        
        # Retrieval modules
        ("memory.retrieval", "from memory.retrieval import BitterBotRAG, HybridRetriever"),
        ("memory.retrieval.rag_pipeline", "from memory.retrieval.rag_pipeline import BitterBotRAG"),
        ("memory.retrieval.hybrid_retriever", "from memory.retrieval.hybrid_retriever import HybridRetriever"),
        
        # Dream engine modules
        ("memory.dream_engine", "from memory.dream_engine import DreamCycle"),
        ("memory.dream_engine.dream_cycle", "from memory.dream_engine.dream_cycle import DreamCycle"),
    ]
    
    successful = 0
    failed = 0
    
    for module_name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {module_name}")
            successful += 1
        except Exception as e:
            print(f"❌ {module_name}: {str(e)}")
            failed += 1
            if "--verbose" in sys.argv:
                traceback.print_exc()
    
    print(f"\n📊 Results: {successful} successful, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All imports successful! Memory system structure is ready.")
    else:
        print("\n⚠️  Some imports failed. Check missing dependencies.")
        
    return failed == 0

def test_basic_instantiation():
    """Test basic instantiation of memory components"""
    
    print("\n🔧 Testing basic instantiation...\n")
    
    try:
        from memory.core import BitterBotMemory
        memory = BitterBotMemory(user_id="test_user")
        print("✅ BitterBotMemory instantiated successfully")
        
        from memory.core.working_memory import WorkingMemory
        working_mem = WorkingMemory()
        print("✅ WorkingMemory instantiated successfully")
        
        from memory.core.episodic_memory import EpisodicMemory
        episodic_mem = EpisodicMemory(db_path=":memory:")
        print("✅ EpisodicMemory instantiated successfully")
        
        print("\n🎉 Basic instantiation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Instantiation failed: {str(e)}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BitterBot Memory System Import Test")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test instantiation if imports succeeded
    if imports_ok:
        test_basic_instantiation()
    
    print("\n" + "=" * 60)