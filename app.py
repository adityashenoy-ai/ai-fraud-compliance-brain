# app.py
import streamlit as st
import pandas as pd
import io
import pdfplumber
import textwrap
import json
from openai import OpenAI
from datetime import datetime

# ---------------------------
# Page & OpenAI init
# ---------------------------
st.set_page_config(page_title="AI Fraud & Compliance Brain (India FinTech)", layout="wide")
st.title("🛡️ AI Fraud & Compliance Brain — Indian FinTech")
st.caption("Ingest RBI / regulator PDFs → Extract changes → Summarize impact → Generate checklist → Predict risk exposure")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please add OPENAI_API_KEY to Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------------------
# Helpers
# ---------------------------
def extract_text_from_pdf_bytes(file_bytes):
    """Return extracted text from a PDF bytes object using pdfplumber."""
    try:
        text_chunks = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
        return "\n\n".join(text_chunks)
    except Exception as e:
        return ""

def chunk_text(text, max_chars=3000):
    """Simple char-based chunker to avoid very long prompts."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+max_chars]
        # extend to end of line for readability
        last_newline = chunk.rfind("\n")
        if last_newline > int(max_chars*0.6):
            chunk = text[i:i+last_newline]
            i = i + last_newline
        else:
            i = i + max_chars
        chunks.append(chunk.strip())
    return chunks

def call_llm_prompt(prompt, model="gpt-4o-mini", temperature=0.0, max_retries=2):
    """Call LLM, return content string or None."""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=temperature
            )
            # Many SDKs return choices[0].message.content
            return resp.choices[0].message.content
        except Exception as e:
            if attempt == max_retries-1:
                st.error(f"LLM call failed: {e}")
                return None

def build_extraction_prompt(chunk_text, context_label):
    return f"""You are an expert regulatory analyst focusing on Indian financial regulation (RBI, SEBI, IRDA, etc.).
You are given the following excerpt from a regulatory document labeled: {context_label}.

EXCERPT:
\"\"\"{chunk_text}\"\"\"

From this excerpt, extract:
1) Any specific regulatory *change* or *instruction* (short bullet, verbatim where possible).
2) The *affected entities* (who must comply — e.g., NBFCs, Payment System Providers, Banks, PSPs, merchants).
3) Any *compliance deadlines* or dates mentioned.
4) Any *penalty* or enforcement action described (if present).
5) Short *impact statement* on fintechs (1-2 sentences).
Return a JSON object with keys: "extractions" which should be a list of objects with keys:
- "source_label": <string>
- "change": <string>
- "affected": [<strings>]
- "deadline": <string or null>
- "penalty": <string or null>
- "impact": <string>

Return *only JSON*. Do not add any explanatory text.
"""

def build_aggregate_prompt(extractions_json):
    return f"""You are a senior regulatory consultant summarizing extracted rules for product and compliance teams at fintechs.

Given the following JSON array of extracted items from regulator documents:
{extractions_json}

Produce a structured summary in markdown that contains:
- Top 6 new/important compliance changes (bullet list with one-line explanation each)
- A consolidated compliance checklist for fintechs (checkbox-style markdown) grouped by function (KYC, Reporting, Risk, Technology, Payments)
- A short executive summary (3-4 lines) describing the overall risk posture for fintechs arising from these changes.

Return MARKDOWN only.
"""

def build_risk_prompt(company_row, extractions_json):
    """
    company_row: {name, entity_type (NBFC/PSP), annual_revenue, loan_portfolio_pct, npa_pct, region}
    """
    return f"""You are a FinTech risk analyst. Given the following company profile and recent regulatory extractions, estimate the company's near-term regulatory risk and fraud exposure.

Company:
{json.dumps(company_row)}

Recent compliance changes (short JSON):
{extractions_json}

Produce a JSON object:
{{
  "company": "{company_row.get('name')}",
  "risk_level": "low|medium|high",
  "risk_score": <0-100>,
  "top_risks": ["..."],
  "recommended_mitigations": ["... 3 to 5 items ..."],
  "notes": "short rationale (1-2 sentences)"
}}

Return JSON only.
"""

# ---------------------------
# Sidebar: Uploads & settings
# ---------------------------
st.sidebar.header("Inputs")
pdf_files = st.sidebar.file_uploader("Upload regulator PDFs (RBI circulars, guidelines). You can upload multiple.", type=["pdf"], accept_multiple_files=True)
st.sidebar.markdown("---")
company_csv = st.sidebar.file_uploader("(Optional) Upload companies CSV for risk scoring (columns: name,entity_type,annual_revenue,loan_portfolio_pct,npa_pct,region)", type=["csv"])
model = st.sidebar.selectbox("LLM Model", options=["gpt-4o-mini","gpt-4o"], index=0)
sample_mode = st.sidebar.checkbox("Use short sample mode (faster, less tokens)", value=True)
st.sidebar.info("Be mindful of token usage when analyzing long PDFs or many companies. Use sample mode for quick runs.")

# ---------------------------
# Main UI: PDF extraction
# ---------------------------
st.header("1) Ingest & Extract from PDFs")
if not pdf_files:
    st.info("Upload one or more regulator PDFs (RBI circulars, master directions, guidelines).")
else:
    raw_docs = []
    for f in pdf_files:
        bytes_data = f.read()
        text = extract_text_from_pdf_bytes(bytes_data)
        label = f.name
        raw_docs.append({"label": label, "text": text})

    st.success(f"Extracted text from {len(raw_docs)} documents.")
    for d in raw_docs:
        st.write(f"**{d['label']}** — {len(d['text'].split())} words")
        # show first 400 chars preview
        st.code(textwrap.shorten(d["text"], width=400, placeholder="..."))

    # chunk + extract per doc
    st.header("2) Extract Regulatory Changes (LLM)")
    extraction_results = []
    for doc in raw_docs:
        chunks = chunk_text(doc["text"], max_chars=2500)
        if sample_mode and len(chunks) > 3:
            chunks = chunks[:3]
        doc_extractions = []
        for i, ch in enumerate(chunks):
            label = f"{doc['label']} - chunk {i+1}"
            prompt = build_extraction_prompt(ch, label)
            with st.spinner(f"Analyzing {label}..."):
                out = call_llm_prompt(prompt, model=model, temperature=0.0)
            if out:
                try:
                    parsed = json.loads(out)
                    # accept both single extraction or list
                    if isinstance(parsed, dict) and "extractions" in parsed:
                        items = parsed["extractions"]
                    elif isinstance(parsed, list):
                        items = parsed
                    else:
                        # try to normalise
                        items = parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    # fallback: try to find JSON substring
                    # naive approach: look for first "{" and last "}"
                    try:
                        first = out.find("{")
                        last = out.rfind("}")
                        cand = out[first:last+1]
                        parsed = json.loads(cand)
                        items = parsed.get("extractions", [parsed])
                    except Exception:
                        items = [{"source_label": label, "change": out.strip(), "affected": [], "deadline": None, "penalty": None, "impact": ""}]
                # tag source label
                for it in items:
                    it["source_label"] = it.get("source_label", label)
                doc_extractions.extend(items)
        extraction_results.extend(doc_extractions)

    st.success(f"Extracted {len(extraction_results)} items across docs.")
    # show table preview
    preview_df = pd.DataFrame([{
        "source": e.get("source_label"),
        "change": (e.get("change") or "")[:200],
        "affected": ",".join(e.get("affected") or []),
        "deadline": e.get("deadline"),
        "penalty": e.get("penalty")
    } for e in extraction_results])
    st.dataframe(preview_df.head(50))

    # ---------------------------
    # Aggregate summary + Checklist
    # ---------------------------
    st.header("3) Consolidated Summary & Compliance Checklist")
    if st.button("Generate consolidated summary & checklist"):
        with st.spinner("Aggregating and summarizing (LLM)..."):
            extra_json = json.dumps(extraction_results, ensure_ascii=False)
            agg_prompt = build_aggregate_prompt(extra_json)
            agg_out = call_llm_prompt(agg_prompt, model=model, temperature=0.0)
            if agg_out:
                st.markdown("### Summary & Checklist")
                st.markdown(agg_out)
                # downloadable MD
                st.download_button("Download summary (.md)", data=agg_out, file_name=f"compliance_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md", mime="text/markdown")

    # ---------------------------
    # Risk Predictions for Companies
    # ---------------------------
    st.header("4) Risk Exposure Predictions for Companies (Optional)")
    if company_csv:
        companies_df = pd.read_csv(company_csv)
        st.write("Companies uploaded:", companies_df.shape[0])
        st.dataframe(companies_df.head())
        if st.button("Run risk scoring for uploaded companies"):
            # run LLM per company (be mindful of cost)
            rows = []
            extra_json = json.dumps(extraction_results, ensure_ascii=False)
            for idx, r in companies_df.iterrows():
                company = {
                    "name": str(r.get("name", "unknown")),
                    "entity_type": str(r.get("entity_type", "NBFC")),
                    "annual_revenue": float(r.get("annual_revenue", 0)),
                    "loan_portfolio_pct": float(r.get("loan_portfolio_pct", 0)),
                    "npa_pct": float(r.get("npa_pct", 0)),
                    "region": str(r.get("region", "")),
                }
                prompt = build_risk_prompt(company, extra_json)
                with st.spinner(f"Scoring {company['name']}..."):
                    out = call_llm_prompt(prompt, model=model, temperature=0.0)
                if out:
                    try:
                        parsed = json.loads(out)
                    except Exception:
                        # attempt to extract JSON substring
                        try:
                            first = out.find("{")
                            last = out.rfind("}")
                            cand = out[first:last+1]
                            parsed = json.loads(cand)
                        except Exception:
                            parsed = {"company": company["name"], "risk_level": "unknown", "risk_score": None, "top_risks": [], "recommended_mitigations": [], "notes": out[:400]}
                    rows.append(parsed)
            results_df = pd.DataFrame(rows)
            st.write("### Risk Scoring Results")
            st.dataframe(results_df)
            # download CSV
            st.download_button("Download risk scores (CSV)", data=results_df.to_csv(index=False), file_name="risk_scores.csv", mime="text/csv")
    else:
        st.info("Upload an optional companies CSV in the sidebar if you want to run risk scoring.")

    # ---------------------------
    # Quick export of raw extractions JSON
    # ---------------------------
    if extraction_results:
        st.download_button("Download raw extractions (JSON)", data=json.dumps(extraction_results, ensure_ascii=False, indent=2), file_name="extractions.json", mime="application/json")

st.markdown("---")
st.caption("Built for prototyping and product demos. For production use: sanitize data, ensure PII removal, manage tokens/costs, and apply secure storage & governance.")
