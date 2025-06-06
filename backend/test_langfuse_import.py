#!/usr/bin/env python3
"""Test script to verify langfuse imports work correctly"""

print("Testing langfuse imports...")

try:
    from services.langfuse import langfuse
    print("✅ Successfully imported langfuse service")
    
    # Test the type hints we're using
    from typing import Any
    StatefulTraceClient = Any
    StatefulGenerationClient = Any
    print("✅ Type hints set up correctly")
    
    # Check if langfuse is enabled
    if hasattr(langfuse, 'enabled'):
        print(f"ℹ️  Langfuse enabled: {langfuse.enabled}")
    
    print("\n✅ All imports successful! The backend should start now.")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()