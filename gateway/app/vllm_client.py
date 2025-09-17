from typing import Any, Dict

# Placeholder: actual HTTPX client to vLLM should live here
async def chat_completions(payload: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: forward to VLLM and return response
    return {
        "id": "chatcmpl-skeleton",
        "object": "chat.completion",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "[skeleton response]"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

