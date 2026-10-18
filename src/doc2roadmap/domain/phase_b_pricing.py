"""Standard online text prices in USD per million tokens, checked 2026-10-18.

https://cloud.google.com/vertex-ai/generative-ai/pricing
https://ai.google.dev/gemini-api/docs/pricing

Gemini Embedding online is $0.00015 per 1,000 input tokens ($0.15/M).
Scripted generation model IDs use the configured generation price as before.
"""
from typing import Any, Mapping


GENERATION_MODEL = 'gemini-3.1-flash-lite'
EMBEDDING_MODEL = 'gemini-embedding-001'
PRICES_USD_PER_MILLION = {
    GENERATION_MODEL: {'input': 0.25, 'output': 1.50},
    EMBEDDING_MODEL: {'input': 0.15, 'output': 0.0},
}
PRICE_CHECKED_ON = '2026-10-18'
PRICE_SOURCE = 'https://cloud.google.com/vertex-ai/generative-ai/pricing'


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int = 0) -> float:
    model = str(model_id).split(':', 1)[0]
    price = PRICES_USD_PER_MILLION.get(model, PRICES_USD_PER_MILLION[GENERATION_MODEL])
    return (input_tokens * price['input'] + output_tokens * price['output']) / 1_000_000


def token_cost(model_id: str, usage: Mapping[str, Any]) -> float:
    incoming = int(usage.get('promptTokenCount', usage.get('input_tokens', 0)) or 0)
    outgoing = int(usage.get('candidatesTokenCount', usage.get('output_tokens', 0)) or 0)
    thoughts = int(usage.get('thoughtsTokenCount', usage.get('thought_tokens', 0)) or 0)
    return estimate_cost(model_id, incoming, outgoing + thoughts)


def embedding_cost(model_id: str, input_tokens: int) -> float:
    return estimate_cost(model_id, input_tokens)
