import os


class LLMClient:
"""Thin wrapper used by summarizer. Replace internals with your LLM of choice.
If you use OpenAI, set OPENAI_API_KEY in env and implement call to OpenAI.
"""


def __init__(self):
self.api_key = os.environ.get('OPENAI_API_KEY')


def summarize(self, text: str, max_tokens: int = 300) -> str:
# Minimal fallback summarizer if no API key: simple extractive heuristics
if not self.api_key:
# naive: return the first 5 paragraphs trimmed
parts = [p.strip() for p in text.split('\n\n') if p.strip()]
return '\n\n'.join(parts[:5])
# If you want to use OpenAI, implement the API call here.
raise NotImplementedError('Add your LLM API call here')
