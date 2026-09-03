"""
Quick test to verify LLM providers work.
Run: python test_llm.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import LLMService


def test_llm():
    print("=" * 60)
    print("  LLM Provider Test")
    print("=" * 60)

    # Show which keys are set
    print("\nEnvironment Variables:")
    print(f"  GEMINI_API_KEY:  {'✅ SET' if os.environ.get('GEMINI_API_KEY') else '❌ NOT SET'}")
    print(f"  GROQ_API_KEY:    {'✅ SET' if os.environ.get('GROQ_API_KEY') else '❌ NOT SET'}")
    print(f"  OPENAI_API_KEY:  {'✅ SET' if os.environ.get('OPENAI_API_KEY') else '❌ NOT SET'}")

    # Initialize service
    print("\nInitializing LLM Service...")
    llm = LLMService()

    # Show status
    status = llm.get_status()
    print(f"\nStatus:")
    print(f"  Available: {status['available']}")
    print(f"  Active Provider: {status['active_provider']}")
    print(f"  Active Model: {status['active_model']}")
    print(f"  All Providers: {status['providers_status']}")

    if not llm.is_available:
        print("\n⚠️  No LLM provider available!")
        print("Set one of these:")
        print("  set GEMINI_API_KEY=your_key  (free: aistudio.google.com/apikey)")
        print("  set GROQ_API_KEY=your_key    (free: console.groq.com/keys)")
        print("  set OPENAI_API_KEY=your_key  (paid: platform.openai.com)")
        return

    # Test basic generation
    print(f"\n🧪 Testing {llm.active_provider}...")
    
    result = llm.generate(
        prompt="Generate 2 Python interview questions. Return as a simple list.",
        system_prompt="You are a technical interviewer. Be concise.",
        max_tokens=300,
    )

    if result:
        print(f"\n✅ Response ({len(result)} chars):")
        print("-" * 40)
        print(result[:500])
        print("-" * 40)
    else:
        print("❌ No response received")

    # Test JSON generation
    print(f"\n🧪 Testing JSON generation...")
    
    json_result = llm.generate_json(
        prompt='Generate 2 Python questions as JSON array: ["q1", "q2"]',
    )

    if json_result:
        print(f"✅ JSON parsed: {json_result}")
    else:
        print("❌ JSON generation failed")

    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_llm()