# AI Fraud & Compliance Brain for Indian FinTech


**Purpose:** A reference implementation to parse RBI circulars/guidelines (PDFs), extract compliance changes, summarize the impact for fintechs, auto-generate a compliance checklist and predict risk exposure for NBFCs & PSPs.


This scaffold is designed to be developer-friendly so you can iterate quickly. It uses:
- FastAPI for backend APIs
- Streamlit for a quick demo UI
- pdfplumber + tika for PDF parsing
- scikit-learn for a simple risk model
- optional OpenAI or other LLM via `app/core/llm_client.py` for summarization / embeddings


## Quickstart (local)


1. Copy repository files.
2. Create a Python venv and install requirements:


```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
