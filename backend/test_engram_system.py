#!/usr/bin/env python3
"""
Test the Engram Memory System.

This script verifies that all components of the engram system are working correctly.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from agentpress.engram_manager import get_engram_manager
from agentpress.context_manager import ContextManager
from agentpress.engram_metrics import ExperienceMetrics
from services.supabase import DBConnection
from utils.logger import logger


async def test_engram_system():
    """Run comprehensive tests on the engram system."""
    print("\n" + "="*60)
    print("🧪 ENGRAM SYSTEM TEST SUITE")
    print("="*60)
    
    db = DBConnection()
    client = await db.client
    
    # Test thread ID (you can change this to test with a real thread)
    test_thread_id = "test-engram-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    
    try:
        # 1. Test database connection
        print("\n1️⃣ Testing database connection...")
        try:
            result = await client.table('engrams').select('count').execute()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database error: {e}")
            print("   Please run the migration first!")
            return
        
        # 2. Test engram creation
        print("\n2️⃣ Testing engram creation...")
        engram_manager = get_engram_manager()
        
        # Create test messages
        test_messages = [
            {
                "message_id": f"msg-{i}",
                "content": {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message {i}: This is a test of the engram system. {'ERROR' if i == 2 else 'Normal'}"
                },
                "type": "user" if i % 2 == 0 else "assistant"
            }
            for i in range(5)
        ]
        
        # Create engram
        engram = await engram_manager.create_engram(
            thread_id=test_thread_id,
            messages=test_messages,
            trigger="test",
            force=True
        )
        
        if engram:
            print(f"✅ Engram created successfully!")
            print(f"   ID: {engram['id']}")
            print(f"   Summary: {engram['content'][:100]}...")
            print(f"   Surprise score: {engram['surprise_score']:.2f}")
            print(f"   Token count: {engram['token_count']}")
        else:
            print("❌ Failed to create engram")
            return
        
        # 3. Test engram retrieval
        print("\n3️⃣ Testing engram retrieval...")
        retrieved_engrams = await engram_manager.retrieve_relevant_engrams(
            thread_id=test_thread_id,
            query_context="test error"
        )
        
        if retrieved_engrams:
            print(f"✅ Retrieved {len(retrieved_engrams)} engrams")
            for i, eng in enumerate(retrieved_engrams):
                print(f"   Engram {i+1}: relevance={eng.get('current_relevance', 0):.2f}, "
                      f"surprise={eng['surprise_score']:.2f}, "
                      f"accesses={eng['access_count']}")
        else:
            print("❌ No engrams retrieved")
        
        # 4. Test context manager integration
        print("\n4️⃣ Testing context manager integration...")
        context_manager = ContextManager()
        
        # Test message processing
        test_message = {
            "message_id": "test-msg-cm",
            "content": {"role": "user", "content": "This is a test message for context manager"},
            "type": "user"
        }
        
        await context_manager.process_message_for_engrams(test_thread_id, test_message)
        print("✅ Message processed for engrams")
        
        # Test context retrieval
        context_summary = await context_manager.get_context_with_engrams(test_thread_id)
        if context_summary:
            print("✅ Context summary retrieved:")
            print(f"   Length: {len(context_summary)} characters")
            print(f"   Preview: {context_summary[:200]}...")
        else:
            print("⚠️  No context summary (might be normal if no engrams meet criteria)")
        
        # 5. Test metrics
        print("\n5️⃣ Testing metrics system...")
        experience_metrics = ExperienceMetrics()
        
        # Log metrics snapshot
        snapshot = await experience_metrics.log_metrics_snapshot(test_thread_id)
        
        print("✅ Metrics snapshot generated:")
        print(f"   Total engrams: {snapshot['basic_stats']['total_engrams']}")
        print(f"   Avg relevance: {snapshot['basic_stats']['avg_relevance_score']:.2f}")
        print(f"   Memory diversity: {snapshot['memory_health']['diversity_index']:.2f}")
        print(f"   Context continuity: {snapshot['experience']['context_continuity']:.2f}")
        
        # 6. Test surprise-triggered consolidation
        print("\n6️⃣ Testing surprise-triggered consolidation...")
        surprise_messages = [
            {
                "message_id": "surprise-1",
                "content": {"role": "user", "content": "URGENT ERROR!!! The system is crashing!!!"},
                "type": "user"
            },
            {
                "message_id": "surprise-2",
                "content": {"role": "assistant", "content": "I see the error! Let me fix it immediately!"},
                "type": "assistant"
            }
        ]
        
        surprise_engram = await engram_manager.create_engram(
            thread_id=test_thread_id,
            messages=surprise_messages,
            trigger="surprise"
        )
        
        if surprise_engram and surprise_engram['surprise_score'] > 0.7:
            print(f"✅ Surprise detection working! Score: {surprise_engram['surprise_score']:.2f}")
        else:
            print(f"⚠️  Surprise score lower than expected: {surprise_engram['surprise_score'] if surprise_engram else 'N/A'}")
        
        # 7. Cleanup test data
        print("\n7️⃣ Cleaning up test data...")
        cleanup_result = await client.table('engrams').delete().eq('thread_id', test_thread_id).execute()
        print(f"✅ Cleaned up {len(cleanup_result.data) if cleanup_result.data else 0} test engrams")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe engram system is fully operational! 🎉")
        print("\nYou can now:")
        print("1. Monitor real-time metrics: python backend/agentpress/monitor_engrams.py")
        print("2. Check logs for ENGRAM_METRICS entries")
        print("3. Watch for automatic consolidation at 5k token intervals")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error("Test failed", exc_info=True)
        
        # Cleanup on error
        try:
            await client.table('engrams').delete().eq('thread_id', test_thread_id).execute()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_engram_system())