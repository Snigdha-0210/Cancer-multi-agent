import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

payload = {
    "model": MODEL_NAME,
    "prompt": "Explain melanoma in two simple sentences for a cancer patient.",
    "stream": False,
}

request = urllib.request.Request(
    OLLAMA_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode("utf-8"))

print("\n--- QWEN RESPONSE ---\n")
print(result["response"])