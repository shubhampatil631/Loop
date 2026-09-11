import httpx
import time

def test_ollama():
    print("Testing Ollama localhost:11434...")
    t0 = time.time()
    try:
        res = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:1b", "prompt": "Say hello in Spanish in one word.", "stream": False},
            timeout=30.0
        )
        elapsed = time.time() - t0
        print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
        if res.status_code == 200:
            print("Response:", res.json().get("response"))
            return True
        else:
            print("Error response:", res.text)
            return False
    except Exception as e:
        print(f"Ollama failed: {e}")
        return False

if __name__ == "__main__":
    test_ollama()
