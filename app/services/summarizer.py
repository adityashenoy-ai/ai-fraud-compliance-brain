from app.core.llm_client import LLMClient




llm = LLMClient()




def summarize_changes(text: str) -> str:
"""Generate a concise summary of policy changes and impact lines.
Replace the LLMClient.summarize implementation with a real LLM call for improved results.
"""
prompt = ("Summarize the regulatory changes and key action items for an Indian fintech. "
"Return short bullets for: what changed, who is affected, action required.")
# For now, we pass raw text and let LLM client handle summarization or fallback.
return llm.summarize(text)
