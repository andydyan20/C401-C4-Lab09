import os
import sys
import json

# Add root directory to sys.path to allow importing workers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workers.retrieval import run as retrieval_run
from workers.policy_tool import run as policy_run
from workers.synthesis import run as synthesis_run

def test_retrieval():
    print("\n" + "="*50)
    print("TEST: Retrieval Worker")
    print("="*50)
    state = {'task': 'SLA ticket P1 là bao lâu?', 'history': []}
    print("\n--- state ---")
    print(state)
    result = retrieval_run(state)
    chunks = result.get('retrieved_chunks', [])
    print(f"Result: {len(chunks)} chunks found.")
    for i, chunk in enumerate(chunks, 1):
        print(f"  {i}. [{chunk['source']}] {chunk['text'][:100]}...")
    

def test_policy():
    print("\n" + "="*50)
    print("TEST: Policy Worker")
    print("="*50)
    state = {
        'task': 'Khách hàng Flash Sale yêu cầu hoàn tiền.',
        'retrieved_chunks': [
            {'text': 'Đơn hàng Flash Sale không được hoàn tiền theo Điều 3.', 'source': 'policy_refund_v4.txt'}
        ],
        'history': []
    }
    print("\n--- Retrieved Chunks ---")
    print(json.dumps(state.get("retrieved_chunks", []), indent=2, ensure_ascii=False))
    result = policy_run(state)
    pr = result.get('policy_result', {})
    print(f"Policy applies: {pr.get('policy_applies')}")
    print(f"Exceptions detected: {len(pr.get('exceptions_found', []))}")
    for ex in pr.get('exceptions_found', []):
        print(f"  - {ex['type']}: {ex['rule']}")


def test_synthesis():
    print("\n" + "="*50)
    print("TEST: Synthesis Worker")
    print("="*50)
    state = {
        'task': 'SLA ticket P1 là bao lâu?',
        'retrieved_chunks': [
            {'text': 'SLA P1: Phản hồi 15 phút, xử lý 4 giờ.', 'source': 'sla_p1_2026.txt', 'score': 0.95}
        ],
        'policy_result': {'policy_applies': True},
        'history': []
    }
    print("\n--- Retrieved Chunks ---")
    print(json.dumps(state.get("retrieved_chunks", []), indent=2, ensure_ascii=False))
    result = synthesis_run(state)
    print(f"Confidence: {result.get('confidence')}")
    print(f"Final Answer:\n{result.get('final_answer')}")


if __name__ == "__main__":
    try:
        test_retrieval()
        test_policy()
        test_synthesis()
        print("\n✅ Standalone worker tests complete.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
