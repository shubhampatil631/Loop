import re
import json
import httpx
from typing import Optional, List
from app.config import settings

def clean_llm_output(text: str) -> str:
    """Strip chain-of-thought <think>...</think> tags and markdown code fences from reasoning model outputs."""
    if not text:
        return ""
    # Remove closed <think>...</think> blocks (handles multi-line, whitespace variations)
    cleaned = re.sub(r"(?is)<\s*think\s*>.*?<\s*/\s*think\s*>", "", text).strip()
    # Remove anything after an unclosed <think> tag
    if re.search(r"(?i)<\s*think\s*>", cleaned):
        cleaned = re.sub(r"(?is)<\s*think\s*>.*", "", cleaned).strip()
    # Strip "Thinking Process:" or "Here's a thinking process:" preambles (Groq qwen-style)
    cleaned = re.sub(r"(?im)^(here[''s]*\s+a?\s*thinking process[:\.]?).*", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    # Remove orphaned lines that look like chain-of-thought numbering at the start
    cleaned = re.sub(r"^(\d+\.\s+.+\n){3,}", "", cleaned, flags=re.MULTILINE).strip()
    # Remove markdown code fences if wrapping json or text
    cleaned = re.sub(r"^```(?:json|markdown)?\s*\n", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\n```\s*$", "", cleaned).strip()
    return cleaned if cleaned else text.strip()


_last_ollama_failure = 0.0
OLLAMA_FAILURE_COOLDOWN = 45.0  # seconds to bypass Ollama if it previously timed out or was offline

def call_llm(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    json_mode: bool = False,
    timeout: float = 12.0
) -> str:
    """
    Centralized Multi-Provider LLM Invocation with Resilient Fallback Chain:
    1. Ollama local models: llama3.2:1b -> qwen2.5:1.5b (@ settings.OLLAMA_HOST)
    2. Groq cloud models: openai/gpt-oss-20b -> openai/gpt-oss-120b -> qwen/qwen3.8-27b -> qwen/qwen3.6-27b
    3. Gemini cloud models: gemini-flash-latest -> gemini-2.5-flash-lite -> gemini-pro-latest
    """
    global _last_ollama_failure
    import time
    now = time.time()

    # -------------------------------------------------------------
    # 1. PRIMARY: Ollama (Local multi-model fallback chain)
    # -------------------------------------------------------------
    if settings.OLLAMA_HOST and (now - _last_ollama_failure > OLLAMA_FAILURE_COOLDOWN):
        models_to_try = getattr(settings, "OLLAMA_MODELS", None) or [settings.OLLAMA_MODEL]
        ollama_timeout = min(float(getattr(settings, "OLLAMA_TIMEOUT", 3.5)), 3.5)
        ollama_keep_alive = getattr(settings, "OLLAMA_KEEP_ALIVE", "30m")
        for model_candidate in models_to_try:
            try:
                url = f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate"
                payload = {
                    "model": model_candidate,
                    "prompt": prompt,
                    "system": system_instruction,
                    "stream": False,
                    "keep_alive": ollama_keep_alive,
                    "options": {
                        "temperature": temperature
                    }
                }
                if json_mode:
                    payload["format"] = "json"

                with httpx.Client(timeout=httpx.Timeout(connect=1.0, read=ollama_timeout, write=2.0, pool=2.0)) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        output = data.get("response", "").strip()
                        if output:
                            return clean_llm_output(output)
                    else:
                        print(f"[LLM] Ollama ({model_candidate}) returned status {res.status_code}: {res.text}")
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as timeout_err:
                _last_ollama_failure = time.time()
                print(f"[LLM] Ollama ({model_candidate}) unavailable ({timeout_err}). Cooling down for {int(OLLAMA_FAILURE_COOLDOWN)}s; cascading to cloud.")
                break
            except Exception as e:
                _last_ollama_failure = time.time()
                print(f"[LLM] Ollama ({model_candidate}) fallback: {e}")
                break

    # -------------------------------------------------------------
    # 2. SECONDARY: Groq (Ultra low-latency cloud fallback)
    # -------------------------------------------------------------
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY, timeout=timeout)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            groq_models = [
                "openai/gpt-oss-20b",
                "openai/gpt-oss-120b",
                "qwen/qwen3.8-27b",
                "qwen/qwen3.6-27b",
                "allam-2-7b",
                "llama-3.3-70b-versatile"
            ]
            for model_candidate in groq_models:
                try:
                    kwargs = {
                        "model": model_candidate,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": 450
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}

                    completion = client.chat.completions.create(**kwargs)
                    output = completion.choices[0].message.content
                    if output and output.strip():
                        return clean_llm_output(output)
                except Exception:
                    # Retry without response_format if json_object not supported on model
                    if json_mode:
                        try:
                            kwargs_no_fmt = {
                                "model": model_candidate,
                                "messages": messages,
                                "temperature": temperature,
                                "max_tokens": 450
                            }
                            completion = client.chat.completions.create(**kwargs_no_fmt)
                            output = completion.choices[0].message.content
                            if output and output.strip():
                                return clean_llm_output(output)
                        except Exception:
                            pass
                    continue
        except Exception as e:
            print(f"[LLM] Groq fallback: {e}")

    # -------------------------------------------------------------
    # 3. TERTIARY: Gemini (Google GenAI)
    # -------------------------------------------------------------
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            config_args = {
                "temperature": temperature,
                "max_output_tokens": 512,
            }
            if system_instruction:
                config_args["system_instruction"] = system_instruction
            if json_mode:
                config_args["response_mime_type"] = "application/json"

            config = types.GenerateContentConfig(**config_args)
            
            gemini_models = [
                "gemini-flash-latest",
                "gemini-2.5-flash-lite",
                "gemini-pro-latest",
                "gemini-1.5-flash"
            ]
            for g_model in gemini_models:
                try:
                    response = client.models.generate_content(
                        model=g_model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        return clean_llm_output(response.text)
                except Exception:
                    continue
        except Exception as e:
            print(f"[LLM] Gemini fallback: {e}")

    return ""
