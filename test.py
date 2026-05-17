"""Test your agent against the SHL sample conversation."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_shl_sample_conversation():
    print("=" * 70)
    print("TESTING SHL SAMPLE CONVERSATION")
    print("=" * 70)
    
    # Track conversation history
    messages = []
    
    # Turn 1: Vague query
    print("\n📝 TURN 1 - User: We need a solution for senior leadership.")
    messages.append({"role": "user", "content": "We need a solution for senior leadership."})
    
    response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
    result = response.json()
    
    print(f"\n🤖 Agent Reply:\n{result['reply'][:300]}")
    print(f"\n📊 Recommendations: {len(result['recommendations'])} (expected: 0)")
    print(f"🏁 End of conversation: {result['end_of_conversation']} (expected: False)")
    
    # Add assistant response to history
    messages.append({"role": "assistant", "content": result['reply']})
    
    # Turn 2: More specific
    print("\n" + "=" * 70)
    print("\n📝 TURN 2 - User: The pool consists of CXOs, director-level positions; people with more than 15 years of experience.")
    messages.append({"role": "user", "content": "The pool consists of CXOs, director-level positions; people with more than 15 years of experience."})
    
    response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
    result = response.json()
    
    print(f"\n🤖 Agent Reply:\n{result['reply'][:400]}")
    print(f"\n📊 Recommendations: {len(result['recommendations'])} (expected: 0 or more)")
    print(f"🏁 End of conversation: {result['end_of_conversation']} (expected: False)")
    
    messages.append({"role": "assistant", "content": result['reply']})
    
    # Turn 3: Specify selection
    print("\n" + "=" * 70)
    print("\n📝 TURN 3 - User: Selection — comparing candidates against a leadership benchmark.")
    messages.append({"role": "user", "content": "Selection — comparing candidates against a leadership benchmark."})
    
    response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
    result = response.json()
    
    print(f"\n🤖 Agent Reply:\n{result['reply'][:500]}")
    print(f"\n📊 Recommendations: {len(result['recommendations'])} (expected: 3)")
    print(f"🏁 End of conversation: {result['end_of_conversation']} (expected: False)")
    
    if result['recommendations']:
        print("\n📋 Recommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec['name']}")
            print(f"     Type: {rec['test_type']}")
            print(f"     URL: {rec['url']}")
    
    messages.append({"role": "assistant", "content": result['reply']})
    
    # Turn 4: Confirmation
    print("\n" + "=" * 70)
    print("\n📝 TURN 4 - User: Perfect, that's what we need.")
    messages.append({"role": "user", "content": "Perfect, that's what we need."})
    
    response = requests.post(f"{BASE_URL}/chat", json={"messages": messages})
    result = response.json()
    
    print(f"\n🤖 Agent Reply:\n{result['reply'][:400]}")
    print(f"\n📊 Recommendations: {len(result['recommendations'])}")
    print(f"🏁 End of conversation: {result['end_of_conversation']} (expected: True)")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    print("\n⚠️ Make sure your server is running: python app.py")
    input("Press Enter to start testing...")
    test_shl_sample_conversation()