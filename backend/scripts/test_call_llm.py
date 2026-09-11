import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import time
from app.llm import call_llm

def test_call_llm():
    print("Testing call_llm directly...")
    t0 = time.time()
    try:
        resp = call_llm("Say hello in Spanish in one word.", timeout=15.0)
        elapsed = time.time() - t0
        print(f"Elapsed: {elapsed:.2f}s")
        print("Response:", resp)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_call_llm()
